"""What the agent remembers across sessions, for the desktop Memory view.

Two stores, as in the terminal's memory commands: confirmed preferences
(``UserProfileStore``, written only when the person confirms one) and episodes
(``EpisodeStore``, compact outcomes of earlier runs that planning may reuse).
Like Claude's memory, the person can see each item, why it is there, and remove
it. Whether a remembered input file is still the one that run checked is the
same sha256 check reuse applies (``freshness``); it reads whole files, so it is
computed for one episode on request, never for the whole list.
"""

from __future__ import annotations


__all__ = ["check_episode", "describe_memory", "forget_episode", "forget_preference", "profile_id"]

PREFERENCE_LABELS = {
    "allow_demo_autofill": "Fill inputs from the demo data when I ask for a demo",
    "reuse_last_inputs": "Reuse the input files of my last successful run",
    "default_output_dir": "Default output folder",
    "preferred_workflow": "Preferred workflow",
}


def _worker_memory():
    """The stores exactly as a session worker builds them (same retention limits),
    so listing here never prunes more than a session would."""
    import sys

    from ..cli.arguments import parse_args
    from ..cli.bootstrap import bootstrap_memory

    saved = sys.argv
    sys.argv = saved[:1]
    try:
        return bootstrap_memory(parse_args())
    finally:
        sys.argv = saved


def profile_id() -> str:
    """The profile desktop sessions run under (the worker's --profile default)."""
    return _worker_memory().profile_id


def _stores():
    memory = _worker_memory()
    return memory.profile_store, memory.episode_store


def describe_memory(limit: int = 200) -> dict:
    profiles, episodes = _stores()
    profile = profiles.load(profile_id())
    remembered = sorted(episodes.list_for_profile(profile.profile_id), key=lambda item: -item.created_at)
    return {
        "profile_id": profile.profile_id,
        "preferences": [
            {"key": key, "label": PREFERENCE_LABELS.get(key, key), "value": value,
             "source": profile.sources.get(key, "")}
            for key, value in sorted(profile.preferences.items())
        ],
        "episodes": [
            {
                "episode_id": item.episode_id,
                "created_at": item.created_at,
                "workflow": item.workflow,
                "status": item.status,
                "task_summary": item.task_summary,
                "inputs": dict(item.inputs),
                "artifacts": list(item.artifacts)[:20],
                "fingerprinted": sorted(item.input_revisions),
            }
            for item in remembered[:limit]
        ],
        "episode_count": len(remembered),
        "retention_days": {
            "completed": episodes.retention_days,
            "failed": episodes.failed_retention_days,
            "dry_run": episodes.dry_run_retention_days,
        },
        "max_episodes": episodes.max_episodes,
    }


def check_episode(episode_id: str) -> dict:
    """Whether each remembered input is still the file that run checked."""
    from ..data.artifact_revision import freshness
    from ..policy import ProjectPolicyLoader
    from ..settings import PROJECT_ROOT

    _, episodes = _stores()
    found = next((item for item in episodes.list_for_profile(profile_id()) if item.episode_id == episode_id), None)
    if found is None:
        raise KeyError(episode_id)
    try:
        policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    except Exception:  # noqa: BLE001 - without a policy the rule comparison says "changed", never "same"
        policy = None
    checks = {}
    for field, path in found.inputs.items():
        try:
            state, words = freshness(found.input_revisions.get(field), path, found.action or "", policy)
        except OSError as error:
            state, words = "missing", f"it could not be read ({error.strerror or error})"
        checks[field] = {"path": path, "state": state, "detail": words}
    return {"episode_id": episode_id, "inputs": checks}


def forget_preference(key: str) -> bool:
    profiles, _ = _stores()
    return profiles.forget(profile_id(), key)


def forget_episode(episode_id: str) -> bool:
    _, episodes = _stores()
    return episodes.delete_episode(profile_id(), episode_id)
