"""A run request whose other named workflows only name its input is still one named run (2026-11-06)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.provider_fallback import recover_explicit_run  # noqa: E402
from netzoo_agent_core.routing.named_labels import run_target_with_named_inputs  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

WORKFLOWS = dict.fromkeys(ACTION_DEFINITIONS)
# Live 2026-11-06 (gpt-4o-mini): the semantic interpreter failed validation twice on this request, and the turn
# ended in "Did you mean PORCUPINE's result?" because two labels (PORCUPINE, LIONESS-PANDA) were named.
PORCUPINE = ("Run PORCUPINE on the LIONESS-PANDA networks /data/porc/lioness_panda_network.txt "
             "with pathways /data/porc/pathways.gmt.")


def test_the_run_target_is_kept_when_the_other_label_produces_its_input():
    assert run_target_with_named_inputs(PORCUPINE) == "run_porcupine"
    assert run_target_with_named_inputs("Run CONDOR on the PANDA network /data/x/net.tsv.") == "run_condor"
    recovered = recover_explicit_run(PORCUPINE, WORKFLOWS, ValueError("semantic validation failed"))
    assert recovered is not None and recovered.action == "run_porcupine"
    assert recovered.match_basis == "workflow_name"


def test_other_shapes_keep_failing_closed():
    for task in (
        "Run PANDA on /data/raw/cpm.tsv with motif m.tsv and ppi p.tsv, then run CONDOR on the result.",  # two runs
        "Run PORCUPINE on the PANDA network /data/x.tsv.",      # aggregate network: not PORCUPINE's per-sample input
        "Run PANDA or PUMA on expr.tsv.",                        # two candidate targets
        "Should I run PORCUPINE on my LIONESS-PANDA networks?",  # a question
    ):
        assert run_target_with_named_inputs(task) is None, task
    assert recover_explicit_run(PORCUPINE, WORKFLOWS, None) is None  # a transport failure still fails closed


def test_a_partial_reading_does_not_replace_a_named_run():
    # Live 2026-11-06 (trace e682f258): after two rejected readings the claims without evidence were dropped and the
    # rest matched PANDA-family workflows. The attempt loop now returns no reading, so `_semantic_failure` recovers
    # the named run; this checks the condition it uses.
    from netzoo_agent_core.graph import semantic_attempts

    assert semantic_attempts.recover_explicit_run is recover_explicit_run
    assert recover_explicit_run(PORCUPINE, WORKFLOWS, ValueError("semantic interpretation failed")) is not None


def test_a_named_run_whose_reading_matched_no_workflow_is_recovered():
    # Live 2026-11-06 (trace ddc159c9): the reading was accepted but matched no workflow (no_tool -> full_gap -> "Did
    # you mean PORCUPINE's result?"). The user named the run, so the router keeps it, with the same gates.
    from netzoo_agent_core.interpretation.provider_fallback import named_run_unmatched

    recovered = named_run_unmatched(PORCUPINE, WORKFLOWS)
    assert recovered is not None and recovered.action == "run_porcupine"
    assert named_run_unmatched("Run CONDOR on /data/x/net.tsv.", WORKFLOWS).action == "run_condor"
    for task in (
        "Should I run PORCUPINE on my LIONESS-PANDA networks?",
        "Should I run CONDOR on /data/x/net.tsv?",
        "Run PANDA on /data/raw/cpm.tsv with motif m.tsv and ppi p.tsv, then run CONDOR on the result.",
        "Which pathways in /data/porc/pathways.gmt vary most across patients?",
    ):
        assert named_run_unmatched(task, WORKFLOWS) is None, task
