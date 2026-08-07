"""Confirmed preferences and bounded episode memory."""

from . import episodes, normalization, profiles, storage
from .episodes import EpisodeCleanupReport, EpisodeStore
from .normalization import (
    _episode_intent_type,
    _meaningful_parameter_value,
    compact_episode_payload,
    normalize_episode_memory,
)
from .profiles import UserProfileStore
from .storage import (
    _ensure_private_directory,
    _exclusive_file_lock,
    _harden_private_tree,
    _safe_json_text,
    _safe_memory_id,
    _sanitize_json_payload,
    _write_json_atomic,
    _write_private_text,
)

_MEMORY_IMPLEMENTATION_MODULES = (
    storage,
    profiles,
    normalization,
    episodes,
)

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
