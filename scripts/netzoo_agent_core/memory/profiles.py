"""Confirmed long-term user preference storage."""

from __future__ import annotations

import time
from pathlib import Path

from workflow_registry import PROFILE_PREFERENCE_KEYS

from ..contracts.decisions import PreferenceProposal
from ..contracts.memory import UserProfile
from ..presentation import _display_path
from ..settings import PROFILE_ROOT, PROJECT_ROOT
from .storage import (
    _ensure_private_directory,
    _exclusive_file_lock,
    _harden_private_tree,
    _safe_json_text,
    _safe_memory_id,
    _write_json_atomic,
)

__all__: list[str] = []


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
        self,
        profile: UserProfile,
        proposals: list[PreferenceProposal],
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
        self,
        profile_id: str,
        proposals: list[PreferenceProposal],
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
