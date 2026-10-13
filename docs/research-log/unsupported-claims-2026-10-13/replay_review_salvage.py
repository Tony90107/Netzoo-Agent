# Offline replay of recorded review replies that did not parse, through salvage_review (and, when the salvaged
# reading still has unsupported claims, without_unsupported_claims). Run from the repository root; no model call.
import sys, json, glob, collections
sys.path.insert(0, "scripts")
from pydantic import ValidationError
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview
from netzoo_agent_core.graph.semantic_review_validation import salvage_review
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses
from netzoo_agent_core.interpretation.unsupported_claims import without_unsupported_claims
from netzoo_agent_core.routing.outcome_matching import match_semantic_request

W = "../.worktrees"
tasks = {}
for f in glob.glob(f"{W}/*/.netzoo/sessions/*.json"):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    users = [m["content"] for m in d.get("messages", []) if m.get("role") == "user"]
    if d.get("run_id") and users:
        tasks[d["run_id"]] = users[-1]
stats, statuses, seen = collections.Counter(), collections.Counter(), set()
for path in glob.glob(f"{W}/*/.netzoo/traces/*/events.jsonl"):
    run = path.split("/")[-2]
    for line in open(path):
        if "semantic_interpreter_failed" not in line:
            continue
        event = json.loads(line)
        payload = event["payload"]
        if event.get("event_type") != "routing.semantic_interpreter_failed" or payload.get("error_type") != "ValidationError":
            continue
        reply, task = payload.get("provider_payload"), tasks.get(run)
        if not isinstance(reply, dict) or "outcome_hypothesis" not in reply or not task:
            continue
        key = (task, json.dumps(reply, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        try:
            SemanticReview.model_validate(reply)
            stats["parsed already"] += 1
            continue
        except ValidationError as error:
            found = salvage_review(reply, error)
        if found is None:
            stats["still unparsable"] += 1
            continue
        review = SemanticReview.model_validate(found[0])
        reading = SemanticInterpretation(request_mode=review.request_mode, semantic_goal=review.semantic_goal,
                                         outcome_hypotheses=[review.outcome_hypothesis])
        validation = validate_outcome_hypotheses(task, reading.outcome_hypotheses, reading.request_mode)
        if validation.valid:
            stats["parses and validates"] += 1
        elif (kept := without_unsupported_claims(task, reading, validation.issues)) is not None:
            stats["parses, valid after A/B"] += 1
            reading = kept
        else:
            stats["parses, still invalid"] += 1
            continue
        match = match_semantic_request(task, reading.outcome_hypotheses, request_mode=reading.request_mode)
        statuses[(match.status, tuple(match.matched_actions or match.hypothesis_actions)[:3])] += 1
        if match.status == "exact" and "--exact" in sys.argv:
            print("   EXACT", match.matched_actions, "|", task[:150], "| salvaged", [r.get("value") for r in found[1] if "value" in r])
for key, value in stats.most_common():
    print(value, key)
print("--- match status of kept readings")
for key, value in statuses.most_common(10):
    print(value, key)
