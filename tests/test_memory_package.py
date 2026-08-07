from __future__ import annotations

import importlib
import inspect
import sys
import uuid
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import netzoo_agent as legacy_agent  # noqa: E402
import netzoo_agent_core.memory as memory  # noqa: E402


MEMORY_EXPORTS = [
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


def test_memory_is_a_package_with_responsibility_owners():
    assert hasattr(memory, "__path__")
    for name in ("storage", "profiles", "normalization", "episodes"):
        importlib.import_module(f"netzoo_agent_core.memory.{name}")


def test_memory_surface_and_owner_identity_are_preserved():
    assert memory.__all__ == MEMORY_EXPORTS
    owners = {
        **{name: "storage" for name in MEMORY_EXPORTS[:8]},
        "UserProfileStore": "profiles",
        **{name: "normalization" for name in MEMORY_EXPORTS[9:13]},
        "EpisodeCleanupReport": "episodes",
        "EpisodeStore": "episodes",
    }
    for name, owner_name in owners.items():
        owner = importlib.import_module(f"netzoo_agent_core.memory.{owner_name}")
        assert getattr(memory, name) is getattr(owner, name)
        assert getattr(legacy_agent, name) is getattr(owner, name)


def test_uuid_json_sanitization_survives_package_conversion():
    value = uuid.uuid4()
    assert memory._sanitize_json_payload({"run_id": value}) == {
        "run_id": str(value)
    }


def test_store_signatures_are_preserved():
    assert str(inspect.signature(memory.UserProfileStore)) == (
        "(root: 'Path | None' = None)"
    )
    assert str(inspect.signature(memory.EpisodeStore)) == (
        "(root: 'Path | None' = None, max_episodes: 'int' = 200, "
        "retention_days: 'int' = 180, max_bytes: 'int' = 10485760, "
        "dry_run_retention_days: 'int' = 60, "
        "failed_retention_days: 'int' = 30)"
    )
