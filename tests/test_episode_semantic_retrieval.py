from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import Episode, RequestedOutcome  # noqa: E402
from netzoo_agent_core.memory.episodes import EpisodeStore  # noqa: E402
from netzoo_agent_core.memory.storage import _write_json_atomic  # noqa: E402
from netzoo_agent_core.graph import policy_memory  # noqa: E402
from netzoo_agent_core.framework_compat import HumanMessage  # noqa: E402


def test_typed_outcome_outranks_tool_name_overlap_for_memory_retrieval(tmp_path):
    store = EpisodeStore(tmp_path / "episodes")
    episodes = [
        Episode(
            episode_id="panda-history",
            profile_id="default",
            task_summary="PANDA regulatory network from expression",
            raw_task_excerpt="Run PANDA on the RNA-Seq matrix",
            workflow="PANDA",
            action="run_panda",
            status="completed",
        ),
        Episode(
            episode_id="lioness-history",
            profile_id="default",
            task_summary="LIONESS-PANDA patient-specific regulatory networks",
            raw_task_excerpt="Run LIONESS-PANDA on the expression matrix",
            workflow="LIONESS-PANDA",
            action="run_lioness_panda",
            status="completed",
        ),
        Episode(
            episode_id="sambar-history",
            profile_id="default",
            task_summary="SAMBAR cancer subtyping from sparse somatic mutation",
            raw_task_excerpt="Aggregate sparse mutations into pathway scores and cluster samples",
            workflow="SAMBAR",
            action="run_sambar",
            status="completed",
        ),
    ]
    for episode in episodes:
        _write_json_atomic(
            store.path_for(episode.profile_id, episode.episode_id),
            episode.model_dump(),
        )

    requested_outcome = RequestedOutcome(
        operation="analyze",
        input_artifacts=["mutation_matrix"],
        artifact_type="sample_cluster_assignment",
        entity_types=["sample"],
        granularity="aggregate",
    )
    query = (
        "Should I put this sparse WES mutation matrix into PANDA and "
        "LIONESS to obtain patient subtypes?"
    )

    hits = store.search_hits(
        "default",
        query,
        requested_outcome=requested_outcome,
    )

    assert [hit.episode.episode_id for hit in hits] == ["sambar-history"]
    assert hits[0].typed_score > 0
    assert hits[0].workflow_bonus == 0


def test_graph_memory_retrieval_receives_the_classified_outcome(monkeypatch):
    captured = {}

    class CapturingEpisodeStore:
        def search_hits(
            self, profile_id, query, limit=3, *, requested_outcome=None
        ):
            captured["requested_outcome"] = requested_outcome
            return []

    class ProfileStore:
        @staticmethod
        def load(profile_id):
            return SimpleNamespace(
                profile_id=profile_id,
                model_dump=lambda: {"profile_id": profile_id},
            )

    monkeypatch.setattr(policy_memory, "record_event", lambda *args, **kwargs: None)
    outcome = RequestedOutcome(
        operation="analyze",
        input_artifacts=["mutation_matrix"],
        artifact_type="sample_cluster_assignment",
        entity_types=["sample"],
        granularity="aggregate",
    )
    context = SimpleNamespace(
        profile_id="default",
        profile_store=ProfileStore(),
        episode_store=CapturingEpisodeStore(),
    )

    policy_memory.retrieve_memory(
        context,
        {
            "messages": [HumanMessage(content="Should I use PANDA for WES?")],
            "requested_outcome": outcome.model_dump(),
        },
    )

    assert captured["requested_outcome"] == outcome.model_dump()
