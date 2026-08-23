"""Bounded, profile-partitioned episode repository."""

from __future__ import annotations

from dataclasses import dataclass
import re
import time
import uuid
from pathlib import Path

from pydantic import BaseModel

from workflow_registry import REQUIRED_INPUTS

from ..contracts.decisions import TaskDecision
from ..contracts.memory import Episode
from ..contracts.planning import WorkflowPlan
from ..contracts.results import EvaluationResult, ToolExecutionResult
from ..outcomes import effective_results, terminal_failed
from ..settings import (
    DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS,
    DEFAULT_EPISODE_FAILED_RETENTION_DAYS,
    DEFAULT_EPISODE_MAX_BYTES,
    DEFAULT_EPISODE_MAX_COUNT,
    DEFAULT_EPISODE_RETENTION_DAYS,
    EPISODE_ROOT,
)
from .normalization import normalize_episode_memory
from .storage import (
    _ensure_private_directory,
    _exclusive_file_lock,
    _safe_memory_id,
    _write_json_atomic,
)

__all__: list[str] = []


class EpisodeCleanupReport(BaseModel):
    """Observable maintenance result returned by the EpisodeStore interface."""

    migrated: int = 0
    expired: int = 0
    overflow: int = 0
    corrupt: int = 0

    @property
    def deleted(self) -> int:
        return self.expired + self.overflow


@dataclass(frozen=True, slots=True)
class EpisodeSearchHit:
    """One selected episode plus the deterministic ranking explanation."""

    episode: Episode
    final_score: int
    overlap_tokens: list[str]
    workflow_bonus: int
    status_bonus: int

    def trace_payload(self) -> dict[str, object]:
        return {
            "episode_id": self.episode.episode_id,
            "workflow": self.episode.workflow,
            "final_score": self.final_score,
            "overlap_tokens": self.overlap_tokens,
            "workflow_bonus": self.workflow_bonus,
            "status_bonus": self.status_bonus,
        }


class EpisodeStore:
    """Private, bounded, profile-partitioned outcomes behind one storage interface."""

    def __init__(
        self,
        root: Path | None = None,
        max_episodes: int = DEFAULT_EPISODE_MAX_COUNT,
        retention_days: int = DEFAULT_EPISODE_RETENTION_DAYS,
        max_bytes: int = DEFAULT_EPISODE_MAX_BYTES,
        dry_run_retention_days: int = DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS,
        failed_retention_days: int = DEFAULT_EPISODE_FAILED_RETENTION_DAYS,
    ):
        self.root = root or EPISODE_ROOT
        self.max_episodes = max(int(max_episodes), 1)
        self.retention_days = max(int(retention_days), 1)
        self.max_bytes = max(int(max_bytes), 1)
        self.dry_run_retention_days = min(
            max(int(dry_run_retention_days), 1),
            self.retention_days,
        )
        self.failed_retention_days = min(
            max(int(failed_retention_days), 1),
            self.retention_days,
        )
        self.lock_path = self.root / ".episodes.lock"

    def profile_root(self, profile_id: str) -> Path:
        return self.root / _safe_memory_id(profile_id)

    def path_for(self, profile_id: str, episode_id: str) -> Path:
        return self.profile_root(profile_id) / f"{_safe_memory_id(episode_id)}.json"

    def _retention_days_for(self, status: str) -> int:
        if status == "failed":
            return self.failed_retention_days
        if status == "dry_run":
            return self.dry_run_retention_days
        return self.retention_days

    def _quarantine_locked(
        self,
        path: Path,
        report: EpisodeCleanupReport,
    ) -> None:
        quarantine = self.root / ".corrupt"
        _ensure_private_directory(quarantine)
        destination = quarantine / (
            f"{path.stem}-{int(time.time())}-{uuid.uuid4().hex[:8]}{path.suffix}"
        )
        try:
            path.replace(destination)
            destination.chmod(0o600)
        except OSError:
            path.unlink(missing_ok=True)
        report.corrupt += 1

    def _prepare_layout_locked(self, report: EpisodeCleanupReport) -> None:
        """Migrate legacy flat files once, then keep retrieval profile-local."""
        _ensure_private_directory(self.root)
        for path in self.root.glob("*.json"):
            try:
                episode = Episode.model_validate_json(path.read_text(encoding="utf-8"))
                safe_profile_id = _safe_memory_id(episode.profile_id)
                safe_episode_id = _safe_memory_id(episode.episode_id)
                if (
                    safe_profile_id != episode.profile_id
                    or safe_episode_id != episode.episode_id
                ):
                    raise ValueError("Unsafe episode or profile id.")
            except (OSError, ValueError):
                self._quarantine_locked(path, report)
                continue
            destination = self.path_for(safe_profile_id, safe_episode_id)
            _ensure_private_directory(destination.parent)
            if destination.exists():
                path.unlink(missing_ok=True)
            else:
                path.replace(destination)
                destination.chmod(0o600)
                report.migrated += 1
        for directory in self.root.iterdir():
            if directory.is_dir() and not directory.is_symlink():
                directory.chmod(0o700)

    def _load_profile_locked(
        self,
        profile_id: str,
        report: EpisodeCleanupReport,
    ) -> list[tuple[Path, Episode]]:
        profile_root = self.profile_root(profile_id)
        if not profile_root.exists():
            return []
        _ensure_private_directory(profile_root)
        episodes = []
        for path in profile_root.glob("*.json"):
            try:
                path.chmod(0o600)
                episode = Episode.model_validate_json(path.read_text(encoding="utf-8"))
                if (
                    episode.profile_id != _safe_memory_id(profile_id)
                    or episode.episode_id != path.stem
                ):
                    raise ValueError(
                        "Episode identity does not match its storage partition."
                    )
            except (OSError, ValueError):
                self._quarantine_locked(path, report)
                continue
            episodes.append((path, episode))
        return episodes

    def _prune_profile_locked(
        self,
        profile_id: str,
        report: EpisodeCleanupReport,
        *,
        now: float,
    ) -> list[tuple[Path, Episode]]:
        records = self._load_profile_locked(profile_id, report)
        retained = []
        for path, episode in records:
            cutoff = now - self._retention_days_for(episode.status) * 86_400
            if episode.created_at < cutoff:
                path.unlink(missing_ok=True)
                report.expired += 1
            else:
                retained.append((path, episode))
        retained.sort(key=lambda item: item[1].created_at, reverse=True)

        protected_paths = set()
        protected_workflows = set()
        for path, episode in retained:
            if (
                episode.status == "completed"
                and episode.workflow not in protected_workflows
            ):
                protected_paths.add(path)
                protected_workflows.add(episode.workflow)

        keep_paths = set()
        used_count = 0
        used_bytes = 0
        for path, _ in retained:
            if path not in protected_paths:
                continue
            size = path.stat().st_size if path.exists() else 0
            if used_count < self.max_episodes and used_bytes + size <= self.max_bytes:
                keep_paths.add(path)
                used_count += 1
                used_bytes += size
            else:
                path.unlink(missing_ok=True)
                report.overflow += 1
        for path, _ in retained:
            if path in protected_paths:
                continue
            size = path.stat().st_size if path.exists() else 0
            if used_count < self.max_episodes and used_bytes + size <= self.max_bytes:
                keep_paths.add(path)
                used_count += 1
                used_bytes += size
            else:
                path.unlink(missing_ok=True)
                report.overflow += 1
        return [item for item in retained if item[0] in keep_paths]

    def _cleanup_quarantine_locked(
        self,
        report: EpisodeCleanupReport,
        *,
        now: float,
    ) -> None:
        quarantine = self.root / ".corrupt"
        if not quarantine.exists():
            return
        cutoff = now - self.failed_retention_days * 86_400
        for path in quarantine.iterdir():
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink(missing_ok=True)
                report.expired += 1

    def _profile_ids_locked(self) -> list[str]:
        profile_ids = []
        for path in self.root.iterdir():
            if not path.is_dir() or path.name.startswith("."):
                continue
            try:
                safe_name = _safe_memory_id(path.name)
            except ValueError:
                continue
            if safe_name == path.name:
                profile_ids.append(path.name)
        return profile_ids

    def maintain(self, profile_id: str | None = None) -> EpisodeCleanupReport:
        """Migrate, secure, validate and prune memory without calling an LLM."""
        report = EpisodeCleanupReport()
        with _exclusive_file_lock(self.lock_path):
            self._prepare_layout_locked(report)
            profile_ids = (
                [_safe_memory_id(profile_id)]
                if profile_id is not None
                else self._profile_ids_locked()
            )
            now = time.time()
            for current_profile_id in profile_ids:
                self._prune_profile_locked(
                    current_profile_id,
                    report,
                    now=now,
                )
            self._cleanup_quarantine_locked(report, now=now)
        return report

    def record(
        self,
        profile_id: str,
        task: str,
        plan: WorkflowPlan,
        results: list[ToolExecutionResult],
        evaluation: EvaluationResult,
        replan_count: int = 0,
    ) -> Episode:
        results = effective_results(results)
        decision = TaskDecision.model_validate(plan.decision)
        inputs = {}
        for field_name in REQUIRED_INPUTS.get(decision.action, ()):
            if field_name in {"output_file", "lioness_output", "output_dir"}:
                continue
            value = getattr(decision, field_name, None)
            if value:
                inputs[field_name] = str(value)
        artifacts = []
        logs = []
        metrics: dict[str, int | float | str | bool] = {}
        errors = []
        for result in results:
            artifacts.extend(
                path for path in result.artifacts if path not in artifacts
            )
            if result.log_file:
                logs.append(result.log_file)
            metrics.update(
                {
                    f"{result.action}.{key}": value
                    for key, value in result.metrics.items()
                }
            )
            errors.extend(result.errors)
        error_signature = None
        if errors:
            compact = re.sub(r"\s+", " ", errors[0]).strip().casefold()
            error_signature = (
                f"{results[-1].action if results else decision.action}:{compact[:180]}"
            )
        recovery_actions = []
        if replan_count:
            recovery_actions = [step.action for step in plan.steps]
        episode_status = (
            "failed"
            if terminal_failed(results, evaluation)
            else (
                "dry_run"
                if any(result.status == "dry_run" for result in results)
                else "completed"
            )
        )
        normalized_memory = normalize_episode_memory(task, plan, results, evaluation)
        episode = Episode(
            episode_id=uuid.uuid4().hex,
            profile_id=_safe_memory_id(profile_id),
            workflow=plan.workflow,
            status=episode_status,
            inputs=inputs,
            artifacts=artifacts,
            metrics=metrics,
            error_signature=error_signature,
            recovery_actions=recovery_actions,
            log_files=logs,
            policy_hash=plan.policy_hash,
            **normalized_memory,
        )
        report = EpisodeCleanupReport()
        with _exclusive_file_lock(self.lock_path):
            self._prepare_layout_locked(report)
            _write_json_atomic(
                self.path_for(episode.profile_id, episode.episode_id),
                episode.model_dump(),
            )
            self._prune_profile_locked(
                episode.profile_id,
                report,
                now=time.time(),
            )
            self._cleanup_quarantine_locked(report, now=time.time())
        return episode

    @staticmethod
    def _tokens(text: str) -> set[str]:
        normalized = text.casefold()
        tokens = set(re.findall(r"[a-z0-9][a-z0-9_-]{1,}", normalized))
        for segment in re.findall(r"[\u3400-\u9fff]+", normalized):
            tokens.add(segment)
            tokens.update(
                segment[index : index + 2] for index in range(len(segment) - 1)
            )
        return tokens

    @classmethod
    def _query_tokens(cls, query: str) -> set[str]:
        tokens = cls._tokens(query)
        normalized = query.casefold()
        if re.search(r"(上次|之前|沿用|重跑|再跑|reuse|previous|last run)", normalized):
            tokens.add("memory-history")
        return tokens

    def search_hits(
        self,
        profile_id: str,
        query: str,
        limit: int = 3,
    ) -> list[EpisodeSearchHit]:
        """Return ranked episodes with the score components used to select them."""
        safe_profile_id = _safe_memory_id(profile_id)
        query_tokens = self._query_tokens(query)
        report = EpisodeCleanupReport()
        with _exclusive_file_lock(self.lock_path):
            self._prepare_layout_locked(report)
            now = time.time()
            records = self._prune_profile_locked(
                safe_profile_id,
                report,
                now=now,
            )
            self._cleanup_quarantine_locked(report, now=now)
        scored: list[tuple[int, float, EpisodeSearchHit]] = []
        for _, episode in records:
            episode_tokens = self._tokens(
                " ".join(
                    [
                        "memory-history",
                        episode.task_summary,
                        episode.raw_task_excerpt or "",
                        episode.workflow,
                        episode.action or "",
                        episode.intent_type or "",
                        episode.validation_status,
                        episode.execution_mode,
                        *episode.input_roles,
                        *episode.output_roles,
                        *episode.parameters,
                        *episode.memory_tags,
                        *episode.domain_metadata.values(),
                        *episode.inputs.values(),
                    ]
                )
            )
            overlap_tokens = sorted(query_tokens & episode_tokens)
            overlap = len(overlap_tokens)
            workflow_bonus = (
                3
                if any(
                    name in query.casefold() and name in episode.workflow.casefold()
                    for name in ("panda", "puma", "lioness", "condor")
                )
                else 0
            )
            base_score = overlap + workflow_bonus
            status_bonus = (
                2
                if episode.status == "completed"
                else 1
                if episode.status == "failed"
                else 0
            )
            score = base_score + status_bonus if base_score else 0
            if score:
                scored.append(
                    (
                        score,
                        episode.created_at,
                        EpisodeSearchHit(
                            episode=episode,
                            final_score=score,
                            overlap_tokens=overlap_tokens,
                            workflow_bonus=workflow_bonus,
                            status_bonus=status_bonus,
                        ),
                    )
                )
        scored.sort(key=lambda item: (-item[0], -item[1]))
        return [hit for _, _, hit in scored[:limit]]

    def search(self, profile_id: str, query: str, limit: int = 3) -> list[Episode]:
        """Return ranked episodes while preserving the original public interface."""
        return [
            hit.episode
            for hit in self.search_hits(profile_id, query, limit=limit)
        ]

    def list_for_profile(self, profile_id: str) -> list[Episode]:
        safe_profile_id = _safe_memory_id(profile_id)
        report = EpisodeCleanupReport()
        with _exclusive_file_lock(self.lock_path):
            self._prepare_layout_locked(report)
            now = time.time()
            records = self._prune_profile_locked(
                safe_profile_id,
                report,
                now=now,
            )
            self._cleanup_quarantine_locked(report, now=now)
        return [episode for _, episode in records]

    def delete_for_profile(self, profile_id: str) -> int:
        safe_profile_id = _safe_memory_id(profile_id)
        report = EpisodeCleanupReport()
        with _exclusive_file_lock(self.lock_path):
            self._prepare_layout_locked(report)
            profile_root = self.profile_root(safe_profile_id)
            if not profile_root.exists():
                return 0
            count = 0
            for path in profile_root.glob("*.json"):
                path.unlink(missing_ok=True)
                count += 1
            try:
                profile_root.rmdir()
            except OSError:
                pass
            return count
