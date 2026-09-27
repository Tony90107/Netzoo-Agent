"""Re-validate every recorded semantic_fallback with the current code.

Usage: python docs/research-log/tools/replay_fallbacks.py <out.json>

For each traced fallback, takes the last rejected interpretation, restores
stated fields, validates it (keeping a valid subset of several hypotheses, as
Log 156 does) and matches whatever survives. Reports how many a change would
rescue and which issues remain. Generalised from the Log 182 replay.
"""
import json
import sys
from pathlib import Path

from traces import ROOT, traced_rows

sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.partial_validity import _valid_subset  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

out = {}
for path, index, row in traced_rows():
    trace = row["_trace"]
    if trace.get("reason_code") != "semantic_fallback":
        continue
    failures = [e for e in trace.get("events", []) if e["type"] == "routing.semantic_interpreter_failed"]
    rejected = failures and failures[-1]["payload"].get("rejected_interpretation")
    if not rejected:
        continue
    task = trace.get("prompt") or row.get("prompt")
    try:
        interpretation = SemanticInterpretation.model_validate(rejected)
    except Exception:
        continue
    interpretation, _ = restore_stated_fields(task, interpretation, align_artifact_constraints=True,
                                              restore_explicit_scalar_evidence=True)
    validation = validate_outcome_hypotheses(task, [h.model_copy(deep=True) for h in interpretation.outcome_hypotheses],
                                             interpretation.request_mode)
    kept = interpretation.outcome_hypotheses if validation.valid else None
    if kept is None and len(interpretation.outcome_hypotheses) >= 2:
        subset, dropped = _valid_subset(task, interpretation)
        if subset and dropped and validate_outcome_hypotheses(task, [h.model_copy(deep=True) for h in subset],
                                                              interpretation.request_mode).valid:
            kept = subset
    match = None
    if kept is not None:
        found = match_semantic_request(task, [h.model_copy(deep=True) for h in kept], request_mode=interpretation.request_mode)
        match = [found.status, found.matched_actions, found.hypothesis_actions]
    out[f"{path.name}#{row.get('id')}#{index}"] = [kept is not None, sorted(validation.issues), match]
Path(sys.argv[1]).write_text(json.dumps(out, indent=1, sort_keys=True))
print("fallbacks with an interpretation:", len(out), "rescued:", sum(1 for value in out.values() if value[0]))
