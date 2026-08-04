"""Confirmed user preferences and bounded, profile-local episode memory."""

from __future__ import annotations

import fcntl
import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel

from workflow_registry import (
    PROFILE_PREFERENCE_KEYS,
    REQUIRED_INPUTS,
    WORKFLOW_MEMORY_METADATA,
)

from .contracts import (
    DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS,
    DEFAULT_EPISODE_FAILED_RETENTION_DAYS,
    DEFAULT_EPISODE_MAX_BYTES,
    DEFAULT_EPISODE_MAX_COUNT,
    DEFAULT_EPISODE_RETENTION_DAYS,
    EPISODE_ROOT,
    Episode,
    EvaluationResult,
    INPUT_ROLE_FIELDS,
    OUTPUT_ROLE_FIELDS,
    PARAMETER_FIELDS,
    PROFILE_ROOT,
    PROJECT_ROOT,
    PreferenceProposal,
    TaskDecision,
    ToolExecutionResult,
    UserProfile,
    WorkflowPlan,
    _display_path,
    _is_demo_request,
)
from .outcomes import effective_results, terminal_failed

__all__ = [
    "_safe_memory_id",
    "_safe_json_text",
    "_sanitize_json_payload",
    "_ensure_private_directory",
    "_harden_private_tree",
    "_exclusive_file_lock",
    "_write_private_text",
    "_write_json_atomic",
    "UserProfileStore",
    "_episode_intent_type",
    "_meaningful_parameter_value",
    "normalize_episode_memory",
    "compact_episode_payload",
    "EpisodeCleanupReport",
    "EpisodeStore",
]


def _safe_memory_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")
    if not cleaned:
        raise ValueError("Memory id must contain a letter or number.")
    return cleaned[:80]


def _safe_json_text(value: str) -> str:
    """Replace invalid Unicode surrogates before writing UTF-8 JSON files."""
    return value.encode("utf-8", errors="replace").decode("utf-8")


def _sanitize_json_payload(value):
    if isinstance(value, str):
        return _safe_json_text(value)
    if isinstance(value, dict):
        return {
            _safe_json_text(str(key)): _sanitize_json_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_json_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json_payload(item) for item in value]
    return value


def _ensure_private_directory(path: Path) -> None:
    """Create a local state directory and make it owner-only."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)


def _harden_private_tree(root: Path) -> None:
    """Repair permissions on existing local state without following symlinks."""
    if not root.exists() or root.is_symlink():
        return
    root.chmod(0o700)
    for path in root.rglob("*"):
        if path.is_symlink():
            continue
        path.chmod(0o700 if path.is_dir() else 0o600)


@contextmanager
def _exclusive_file_lock(path: Path):
    """Serialize local load-modify-write sequences across processes."""
    _ensure_private_directory(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(descriptor, "a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _write_private_text(path: Path, text: str) -> None:
    """Write a new owner-only UTF-8 text file."""
    _ensure_private_directory(path.parent)
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", errors="replace") as handle:
        handle.write(_safe_json_text(text))
        handle.flush()
        os.fsync(handle.fileno())


def _write_json_atomic(path: Path, payload: dict) -> None:
    """Atomically replace JSON using collision-free, owner-only files."""
    _ensure_private_directory(path.parent)
    temporary = path.parent / f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    serialized = json.dumps(
        _sanitize_json_payload(payload),
        ensure_ascii=False,
        indent=2,
    )
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", errors="replace") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        path.chmod(0o600)
    finally:
        temporary.unlink(missing_ok=True)


class UserProfileStore:
    """Confirmed long-term preferences. Nothing is inferred or written implicitly."""

    def __init__(self, root: Path | None = None):
        self.root = root or PROFILE_ROOT
        self.lock_path = self.root / ".profiles.lock"
        if self.root.exists():
            _harden_private_tree(self.root)

    def path_for(self, profile_id: str) -> Path:
        return self.root / f"{_safe_memory_id(profile_id)}.json"

    def _load_unlocked(self, profile_id: str) -> UserProfile:
        safe_profile_id = _safe_memory_id(profile_id)
        path = self.path_for(profile_id)
        if not path.exists():
            return UserProfile(profile_id=safe_profile_id)
        path.chmod(0o600)
        try:
            profile = UserProfile.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ValueError(f"Profile memory is invalid: {path}") from error
        if profile.profile_id != safe_profile_id:
            raise ValueError(
                f"Profile memory id mismatch: expected {safe_profile_id}, "
                f"found {profile.profile_id}."
            )
        if profile.version != 1:
            raise ValueError(f"Unsupported profile memory version: {profile.version}.")
        unknown_keys = set(profile.preferences) - PROFILE_PREFERENCE_KEYS
        if unknown_keys:
            raise ValueError(
                "Profile memory contains unsupported preference keys: "
                + ", ".join(sorted(unknown_keys))
            )
        normalized_preferences = {}
        for key, value in profile.preferences.items():
            proposal = PreferenceProposal(
                key=key,
                value=str(value),
                reason="Revalidated while loading local profile memory.",
            )
            normalized_preferences[key] = self.normalize(proposal)
        unknown_sources = set(profile.sources) - set(normalized_preferences)
        if unknown_sources:
            raise ValueError(
                "Profile memory contains sources for unknown preferences: "
                + ", ".join(sorted(unknown_sources))
            )
        profile.preferences = normalized_preferences
        profile.sources = {
            key: _safe_json_text(str(value))[:500]
            for key, value in profile.sources.items()
        }
        return profile

    def load(self, profile_id: str) -> UserProfile:
        if self.root.exists():
            _ensure_private_directory(self.root)
        return self._load_unlocked(profile_id)

    def normalize(self, proposal: PreferenceProposal) -> str | bool | list[str]:
        value = proposal.value.strip()
        if proposal.key in {"allow_demo_autofill", "reuse_last_inputs"}:
            normalized = value.casefold()
            if normalized in {"true", "yes", "1", "on"}:
                return True
            if normalized in {"false", "no", "0", "off"}:
                return False
            raise ValueError(f"{proposal.key} must be true or false.")
        if proposal.key == "default_output_dir":
            raw = Path(value).expanduser()
            resolved = (
                raw.resolve() if raw.is_absolute() else (PROJECT_ROOT / raw).resolve()
            )
            allowed_root = (PROJECT_ROOT / "outputs").resolve()
            if not resolved.is_relative_to(allowed_root):
                raise ValueError(
                    "default_output_dir must be inside the project outputs/ directory."
                )
            return _display_path(resolved)
        if proposal.key == "preferred_workflow":
            normalized = value.casefold().replace("-", "_").removeprefix("run_")
            allowed = {
                "panda",
                "puma",
                "lioness_panda",
                "lioness_puma",
                "lioness_coexpression",
                "condor",
            }
            if normalized not in allowed:
                raise ValueError(
                    "preferred_workflow is not an allow-listed NetZoo workflow."
                )
            return normalized
        raise ValueError(f"Unsupported preference key: {proposal.key}")

    def pending(
        self, profile: UserProfile, proposals: list[PreferenceProposal]
    ) -> list[PreferenceProposal]:
        pending = []
        for proposal in proposals:
            try:
                normalized = self.normalize(proposal)
            except ValueError:
                continue
            if profile.preferences.get(proposal.key) != normalized:
                pending.append(proposal)
        return pending

    def confirm(
        self, profile_id: str, proposals: list[PreferenceProposal]
    ) -> UserProfile:
        with _exclusive_file_lock(self.lock_path):
            profile = self._load_unlocked(profile_id)
            now = time.time()
            for proposal in proposals:
                profile.preferences[proposal.key] = self.normalize(proposal)
                profile.sources[proposal.key] = proposal.reason[:500]
            profile.updated_at = now
            _write_json_atomic(self.path_for(profile_id), profile.model_dump())
        return profile

    def delete(self, profile_id: str) -> bool:
        with _exclusive_file_lock(self.lock_path):
            path = self.path_for(profile_id)
            if not path.exists():
                return False
            path.unlink()
            return True


def _episode_intent_type(decision: TaskDecision, task: str) -> str:
    """Prefer router intent, with deterministic fallback for older/router-less tests."""
    if decision.intent_type != "unknown":
        return decision.intent_type
    if _is_demo_request(task):
        return "demo_run"
    if decision.action.startswith("run_"):
        return "run_analysis"
    if decision.action.startswith("inspect_"):
        return "inspect_input"
    if decision.action in {"format_expression", "convert_expression"}:
        return "prepare_input"
    return "unknown"


def _meaningful_parameter_value(value) -> bool:
    return value not in (None, False, "auto", "", [])


def normalize_episode_memory(
    task: str,
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult,
) -> dict:
    """Build workflow-agnostic memory metadata from typed harness contracts."""
    results = effective_results(results)
    decision = TaskDecision.model_validate(plan.decision)
    required = REQUIRED_INPUTS.get(decision.action, ())
    intent_type = _episode_intent_type(decision, task)
    input_roles = [
        field_name
        for field_name in required
        if field_name in INPUT_ROLE_FIELDS and getattr(decision, field_name, None)
    ]
    output_roles = [
        field_name
        for field_name in required
        if field_name in OUTPUT_ROLE_FIELDS and getattr(decision, field_name, None)
    ]
    parameters = [
        field_name
        for field_name in sorted(PARAMETER_FIELDS)
        if _meaningful_parameter_value(getattr(decision, field_name, None))
    ]
    validation_steps = [
        step.action for step in plan.steps if step.action.startswith("inspect_")
    ]
    execution_steps = [
        step.action for step in plan.steps if step.action.startswith("run_")
    ]
    validation_results = [
        result for result in results if result.action.startswith("inspect_")
    ]
    if any(result.status == "failed" for result in validation_results):
        validation_status = "failed"
    elif validation_results:
        validation_status = "passed"
    else:
        validation_status = "not_applicable"
    execution_mode = (
        "dry_run"
        if any(result.status == "dry_run" for result in results)
        else "executed"
    )
    domain_metadata = WORKFLOW_MEMORY_METADATA.get(decision.action, {})
    tags = [
        f"workflow:{plan.workflow.casefold()}",
        f"action:{decision.action}",
        f"intent:{intent_type}",
        f"evaluation:{evaluation.status}",
        f"mode:{execution_mode}",
        f"validation:{validation_status}",
        *[f"input:{field_name}" for field_name in input_roles],
        *[f"output:{field_name}" for field_name in output_roles],
        *[f"param:{field_name}" for field_name in parameters],
        *[f"{key}:{value}" for key, value in sorted(domain_metadata.items()) if value],
    ]
    readable_workflow = plan.workflow.replace("-", " ")
    task_summary = (
        f"{readable_workflow} {intent_type.replace('_', ' ')}; "
        f"mode={execution_mode}; validation={validation_status}; "
        f"inputs={','.join(input_roles) or 'none'}."
    )
    return {
        "task_summary": task_summary[:500],
        "raw_task_excerpt": task[:500],
        "action": decision.action,
        "intent_type": intent_type,
        "input_roles": input_roles,
        "output_roles": output_roles,
        "parameters": parameters,
        "validation_steps": validation_steps,
        "execution_steps": execution_steps,
        "validation_status": validation_status,
        "execution_mode": execution_mode,
        "memory_tags": tags,
        "domain_metadata": domain_metadata,
    }


def compact_episode_payload(episode: Episode) -> dict:
    """Human-friendly memory-status view; verbose mode can still dump the full model."""
    inferred_action = episode.action
    if not inferred_action:
        inferred_action = "run_" + episode.workflow.casefold().replace("-", "_")
    execution_mode = (
        "dry_run" if episode.status == "dry_run" else episode.execution_mode
    )
    input_roles = episode.input_roles or [
        field_name for field_name in episode.inputs if field_name in INPUT_ROLE_FIELDS
    ]
    memory_tags = episode.memory_tags or [
        f"workflow:{episode.workflow.casefold()}",
        f"action:{inferred_action}",
        f"status:{episode.status}",
        f"mode:{execution_mode}",
        *[f"input:{field_name}" for field_name in input_roles],
    ]
    return {
        "episode_id": episode.episode_id,
        "created_at": episode.created_at,
        "workflow": episode.workflow,
        "action": inferred_action,
        "intent_type": episode.intent_type,
        "status": episode.status,
        "execution_mode": execution_mode,
        "validation_status": episode.validation_status,
        "input_roles": input_roles,
        "output_roles": episode.output_roles,
        "parameters": episode.parameters,
        "inputs": episode.inputs,
        "artifacts": episode.artifacts,
        "memory_tags": memory_tags,
        "policy_hash": episode.policy_hash,
    }


class EpisodeCleanupReport(BaseModel):
    """Observable maintenance result returned by the EpisodeStore interface."""

    migrated: int = 0
    expired: int = 0
    overflow: int = 0
    corrupt: int = 0

    @property
    def deleted(self) -> int:
        return self.expired + self.overflow


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
            artifacts.extend(path for path in result.artifacts if path not in artifacts)
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

    def search(self, profile_id: str, query: str, limit: int = 3) -> list[Episode]:
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
        scored: list[tuple[int, float, Episode]] = []
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
            overlap = len(query_tokens & episode_tokens)
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
                scored.append((score, episode.created_at, episode))
        scored.sort(key=lambda item: (-item[0], -item[1]))
        return [episode for _, _, episode in scored[:limit]]

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
