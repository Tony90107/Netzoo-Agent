"""Log 318 offline evidence: recorded bare preferences under PW.

Usage (repository root):
  python docs/research-log/preference-witness-2026-10-03/replay_pw.py          # prototype only
  python docs/research-log/preference-witness-2026-10-03/replay_pw.py --tree   # prototype vs repository

Every traced trial whose condition recommender returned a MethodComparisonReview
with a preference is replayed from the recorded payload. Only trials where the
preference path decides (no condition claim accepted or rejected) and today's
`_recommend_from_preference` recommends are counted. The prototype keeps a
recommendation when the request states, by an axis witness, a separating
condition preferring the preferred workflow and none preferring only others.
With --tree the repository's `stated_preference_basis` must agree on every
trial's study conditions (it may add a quoted method signal, Log 318
supplement; trials kept on a signal alone are listed), and blind verdicts are recomputed from the final decision with the
replayed recommendation (score_blind's rule, as in Logs 290-316).
"""
import collections
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import MethodPreference, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph import condition_recommender as cr  # noqa: E402

BLIND = json.loads((ROOT / "docs" / "research-log" / "blind" / "expectations.json").read_text(encoding="utf-8"))


def prototype(task, preference, options):
    stated = [o for o in options if (w := cr._witness(o)) and re.search(w, task, re.I)]
    if not stated or any(preference.action not in o.actions for o in stated):
        return None
    return sorted(o.condition for o in stated)


def facts(candidates):
    return [{"action": a, "selection_tags": sorted(OUTPUT_CAPABILITIES[a].selection_tags),
             "regulator_types": sorted(OUTPUT_CAPABILITIES[a].regulator_types)}
            for a in candidates if a in OUTPUT_CAPABILITIES]


def verdict(case, decision, reason_code):
    accept, forbid = set(case.get("accept", [])), set(case.get("forbid", []))
    matched = set(decision.get("matched_actions") or [])
    candidates = set(decision.get("hypothesis_actions") or [])
    recommended = (decision.get("advisory_recommendation") or {}).get("action")
    if reason_code == "semantic_fallback":
        return "FALLBACK"
    if matched & forbid or recommended in forbid:
        return "WRONG"
    if case.get("no_tool"):
        return "OK" if not matched and decision.get("action") == "no_tool" else "WRONG"
    if decision.get("capability_match_status") in ("exact", "fallback") and matched & accept:
        return "OK"
    if recommended in accept:
        return "OK"
    if decision.get("capability_match_status") == "ambiguous" and candidates & accept:
        return "PARTIAL"
    return "WRONG"


def traces():
    for path in sorted({*ROOT.glob("docs/research-log/**/live-*.json"), *ROOT.glob("docs/research-log/**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if trace:
                yield path, row.get("id"), trace


def main(tree: bool):
    kept, removed, disagree = collections.Counter(), collections.Counter(), []
    blind = collections.Counter()
    tag_only, tag_basis = [], collections.Counter()
    for path, case, trace in traces():
        start = next((e["payload"] for e in trace.get("events", [])
                      if e.get("type") == "routing.selection_conditions_started"), None)
        call = next((c for c in trace.get("calls", []) if c.get("schema") == "MethodComparisonReview"), None)
        if not start or not call or not isinstance(call.get("parsed"), dict) or not call["parsed"].get("preference"):
            continue
        task, candidates, parsed = trace["prompt"], start["candidate_actions"], call["parsed"]
        try:
            preference = MethodPreference.model_validate(parsed["preference"])
            claims = SelectionConditionClaims.model_validate(
                {k: v for k, v in parsed.items() if k in ("claims", "capability_gap", "preference")})
        except ValueError:
            continue
        options = cr.condition_options(candidates)
        recommendation, rejected = cr.recommend_from_claims(task, claims, options, candidates)
        if recommendation is not None or rejected:
            continue
        decision = TaskDecision.model_validate(trace["decision"])
        today = cr._recommend_from_preference(task, preference, facts(candidates), decision.requested_outcome)
        if today is None:
            continue
        basis = prototype(task, preference, options)
        key = (task[:110], preference.action, tuple(basis or ()))
        (kept if basis else removed)[key] += 1
        if tree:
            new = cr.stated_preference_basis(task, today, options, preference, facts(candidates))
            # Log 318 supplement: the repository also accepts a quoted method
            # signal; study conditions must match the prototype exactly, and
            # a trial kept on a tag alone is listed.
            got = sorted(f"{c.axis}:{c.value}" for c in new.conditions if c.axis != "selection_tag") if new else None
            tags_only = new is not None and not got
            if (got or None) != basis and not tags_only:
                disagree.append((case, task[:80], basis, got))
            if tags_only:
                tag_only.append((case, task[:80], [c.value for c in new.conditions]))
            if new is not None:
                tag_basis.update(c.value for c in new.conditions if c.axis == "selection_tag")
            blind_key = (case or "").split("-")[0]
            recorded = trace["decision"]
            rec = (recorded.get("advisory_recommendation") or {}).get("action")
            if blind_key in BLIND and rec == today.action:
                after = dict(recorded, advisory_recommendation=new.model_dump() if new else None)
                before_v = verdict(BLIND[blind_key], recorded, trace.get("reason_code"))
                after_v = verdict(BLIND[blind_key], after, trace.get("reason_code"))
                blind[(blind_key, before_v, after_v)] += 1
    print(f"bare preferences that recommend today: {sum(kept.values()) + sum(removed.values())}")
    print(f"kept {sum(kept.values())}:")
    for (task, action, basis), n in kept.most_common():
        print(f"  {n:3d} {action:25s} {list(basis)} | {task!r}")
    print(f"removed {sum(removed.values())}:")
    for (task, action, _), n in removed.most_common():
        print(f"  {n:3d} {action:25s} | {task!r}")
    if tree:
        print(f"prototype vs repository disagreements: {len(disagree)}")
        print(f"kept on a quoted method signal alone: {len(tag_only)}")
        for item in tag_only[:10]:
            print("  ", item)
        print(f"method signals also recorded beside a condition: {dict(tag_basis)}")
        for item in disagree[:10]:
            print("  ", item)
        print("blind verdicts (case, before, after):")
        for key, n in sorted(blind.items()):
            print(f"  {n:3d} {key}")


if __name__ == "__main__":
    main("--tree" in sys.argv)
