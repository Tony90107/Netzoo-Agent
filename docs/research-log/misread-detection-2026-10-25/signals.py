"""Misread detection (ROUND.md), no model calls: for every recorded B2 reading, the frozen code's replayed call and
the declared signals X1-X7 (two differently shaped recorded readings disagree) and Q1-Q6 (code-verifiable structure
of one reading).

Each signal is computed as declared in ROUND.md and nothing else, and recorded whenever it fires; `measure.py` adds
the shared condition (the call is DO or DECLINE, so asking would change it). The replay is `stability-round13/harness.py`'s, with a spy on `decide_core`
for the decision it reads (as `harness-repair/attribution/evidence.py`).

Usage: python3 signals.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
REPAIR = LOGS / "harness-repair-2026-10-23"
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
sys.path.insert(0, str(REPAIR))

GIVEN = frozenset({"available", "with_step", "partial"})
ACTING = frozenset({"DO", "DECLINE"})
R1 = "R1 the check did not read these words as the user being unsure"
SIGNALS = ("X1", "X2", "X3", "X4a", "X4b", "X5a", "X5b", "X6", "X7", "Q1", "Q2", "Q3", "Q4", "Q5", "Q6")
GOAL_SIGNALS = frozenset({"X1", "X2", "X3"})
"""Flagged, these ask the goal (CLARIFY); every other signal asks a fact (ASK)."""


def first(found: list[dict], kind: str) -> dict | None:
    return next((e.get("payload") or {} for e in found if e.get("event_type") == kind), None)


def kinds(found: list[dict]) -> set[str]:
    return {e.get("event_type") for e in found}


def workflow_of(key: str) -> str:
    from netzoo_agent_core.interpretation.core_decision import _workflow
    return _workflow(key)


def action_workflows(actions) -> list[str]:
    from workflow_registry import workflow_name
    return list(dict.fromkeys(workflow_name(a) for a in actions or [] if a and a != "no_tool"))


def same(task: str, a: str, b: str) -> bool:
    from netzoo_agent_core.interpretation.request_spans import same_words
    return bool(a and b) and same_words(task, a, b)


def given_rows(check) -> list:
    return [row for row in (check.results() if check is not None else []) if row.status in GIVEN]


def credited(check) -> set[str]:
    return {workflow_of(key) for row in given_rows(check) for key in row.delivered_by}


def named_method(row) -> bool:
    named = (row.method or {}).get("named")
    return bool(named) and named not in ("none", "unregistered")


# --- X: two differently shaped readings disagree -------------------------------------------------------------------

def x1(decision, check, found, core, task) -> str | None:
    match = first(found, "routing.registry_match_completed")
    if not match or match.get("status") != "ambiguous":
        return None
    routed = action_workflows([*(match.get("matched_actions") or []), *(match.get("hypothesis_actions") or []),
                               *(decision.recommended_actions or [])])
    seen = kinds(found)
    if len(routed) < 2 or "routing.semantic_discriminator_accepted" in seen \
            or "routing.selection_conditions_recommended" in seen:
        return None
    if (decision.action or "").startswith("run_") or any(named_method(row) for row in check.results()):
        return None
    picked = credited(check)
    if picked and picked < set(routed):
        return f"routing {sorted(routed)} -> check {sorted(picked)}"
    return None


def x2(decision, check, found, core, task) -> str | None:
    bases = first(found, "routing.hypothesis_bases_matched")
    if bases and bases.get("question_mode") == "unclear_goal":
        return f"hypothesis reader unclear_goal; call {core.kind}/{core.basis}"
    return None


def x3(decision, check, found, core, task) -> str | None:
    outcome = decision.requested_outcome
    if outcome is None:
        return None
    artifact, operation = getattr(outcome, "artifact_type", None), getattr(outcome, "operation", None)
    if artifact == "unknown" or operation in ("unknown", "explain"):
        return f"routing outcome {artifact}/{operation}; call {core.kind}/{core.basis}"
    return None


def x4a(decision, check, found, core, task) -> str | None:
    match = first(found, "routing.registry_match_completed")
    if match and match.get("status") == "unsupported" and core.kind == "DO" and given_rows(check):
        return f"routing unsupported; check credits {sorted(credited(check))}"
    return None


def x4b(decision, check, found, core, task) -> str | None:
    match = first(found, "routing.registry_match_completed")
    if match and match.get("status") == "exact" and match.get("matched_actions") and core.kind == "DECLINE":
        return f"routing exact {action_workflows(match['matched_actions'])}; call DECLINE/{core.basis}"
    return None


def _r1_rejected(decision, said_unknown: bool) -> list[dict]:
    agent = getattr(decision, "fact_check", None)
    if agent is None:
        return []
    found = []
    for rejected in agent.rejected:
        proposal = rejected.proposal or {}
        if rejected.rule != R1:
            continue
        if (proposal.get("yes_outcome"), proposal.get("yes_workflow") or "") == \
                (proposal.get("no_outcome"), proposal.get("no_workflow") or ""):
            continue
        if said_unknown and proposal.get("uncertainty") != "said_unknown":
            continue
        found.append(proposal)
    return found


def x5a(decision, check, found, core, task) -> str | None:
    if kept := _r1_rejected(decision, False):
        return "; ".join(f"{p.get('uncertainty')}: {p.get('user_quote', '')[:60]!r}" for p in kept)
    return None


def x5b(decision, check, found, core, task) -> str | None:
    if kept := _r1_rejected(decision, True):
        return "; ".join(repr(p.get("user_quote", "")[:60]) for p in kept)
    return None


def reread_checks(task: str, payload: dict, reread: dict | None, found: list[dict]):
    """The first reading and the re-read, each built by this code (as `replay_full.replay` builds them)."""
    from replay import _proposal
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.input_bindings import bound_expression_samples

    if not reread or not reread.get("reread"):
        return None
    proposal = _proposal(payload)
    study = first(found, "routing.study_purpose_detected") or {}
    claims = {claim: quote for claim, quote in study.get("claims") or ()}
    counted = bound_expression_samples(task)
    one, _ = build_capability_check(task, proposal, claims, counted)
    raw = reread["reread"]
    model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
    again, _ = build_capability_check(
        task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)), claims, counted)
    return one, again


def x6(pair, core, task) -> str | None:
    if pair is None:
        return None
    one, again = pair
    for a in one.results():
        for b in again.results():
            if not same(task, a.quote, b.quote):
                continue
            if (a.status in GIVEN) != (b.status in GIVEN) and "not_available" in (a.status, b.status):
                return f"{a.quote[:50]!r}: {a.status} vs re-read {b.status}"
            wa, wb = {workflow_of(k) for k in a.delivered_by}, {workflow_of(k) for k in b.delivered_by}
            if a.status in GIVEN and b.status in GIVEN and wa and wb and not wa & wb:
                return f"{a.quote[:50]!r}: {sorted(wa)} vs re-read {sorted(wb)}"
    return None


def x7(decision, check, found, core, task) -> str | None:
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation.ruled_out import INPUT_KIND
    from workflow_registry import ACTION_DEFINITIONS

    facts = first(found, "routing.data_facts_detected")
    if not facts:
        return None
    ruled = set(check.ruled_out)
    needs = set()
    for row in given_rows(check):
        for key in row.delivered_by:
            try:
                action = entry(key).action
            except KeyError:
                continue
            definition = ACTION_DEFINITIONS.get(action)
            needs |= {INPUT_KIND.get(name) for name in (getattr(definition, "required_inputs", ()) or ())}
    priors, mirna = {"motif_prior", "ppi"}, {"mirna_list"}
    if facts.get("priors") == "ruled_out" and needs & priors and not ruled & priors:
        return f"data facts: no priors; credited needs {sorted(needs & priors)}"
    if facts.get("mirna") == "ruled_out" and needs & mirna and not ruled & mirna:
        return "data facts: no miRNA; credited needs mirna_list"
    if facts.get("priors") == "stated" and ruled & priors:
        return f"data facts: priors stated; check ruled out {sorted(ruled & priors)}"
    if facts.get("mirna") == "stated" and ruled & mirna:
        return "data facts: miRNA stated; check ruled out mirna_list"
    return None


# --- Q: one reading's structure ------------------------------------------------------------------------------------

def q1(check, core, task) -> str | None:
    if check.unchecked:
        return f"unread: {[s[:50] for s in check.unchecked]}"
    return None


def q2(check, core, task) -> str | None:
    if check.needed_facts():
        return None
    uncertain = [*check.uncertain_quotes, *(item[1] for item in check.unknowns if len(item) > 1)]
    attached = [row.unknown_quote for row in check.requirements if row.unknown_quote]
    for words in uncertain:
        if words and not any(same(task, words, quote) for quote in attached):
            return f"unattached uncertainty {words[:60]!r}"
    return None


def q3(check, core, task) -> str | None:
    for stated in check.stated_quotes:
        for unsure in check.uncertain_quotes:
            if same(task, stated, unsure):
                return f"stated {stated[:40]!r} and unsure {unsure[:40]!r}"
    return None


def q4(check, core, task) -> str | None:
    for row in given_rows(check):
        if row.delivered_by and row.not_by:
            return f"{row.quote[:50]!r}: credited {row.delivered_by[:2]} and near-miss {row.not_by[:2]}"
    return None


def q5(check, core, task) -> str | None:
    from netzoo_agent_core.interpretation.sentence_ownership import request_sentences

    results = check.results()
    for start, end in request_sentences(task):
        sentence = task[start:end]
        inside = [row for row in results if same(task, row.quote, sentence)]
        if any(row.status in GIVEN for row in inside) and any(row.status == "not_available" for row in inside):
            return f"sentence {sentence[:60]!r} split into doable and not doable rows"
    return None


def q6(check, core, task) -> str | None:
    if check.fact_conflicts:
        return f"fact conflicts: {len(check.fact_conflicts)}"
    return None


def compute(decision, core, found, task, payload, reread) -> dict:
    """Every declared signal that fires: {id: detail} (the shared DO-or-DECLINE condition is `measure.py`'s)."""
    check = decision.capability_check
    if check is None:
        return {}
    fired = {}
    for name, function in (("X1", x1), ("X2", x2), ("X3", x3), ("X4a", x4a), ("X4b", x4b), ("X5a", x5a),
                           ("X5b", x5b), ("X7", x7)):
        if (detail := function(decision, check, found, core, task)) is not None:
            fired[name] = detail
    try:
        pair = reread_checks(task, payload, reread, found)
    except Exception as error:  # noqa: BLE001 -- an old-schema re-read: reported, never hidden
        pair, fired["X6_error"] = None, f"{type(error).__name__}: {error}"[:200]
    if (detail := x6(pair, core, task)) is not None:
        fired["X6"] = detail
    for name, function in (("Q1", q1), ("Q2", q2), ("Q3", q3), ("Q4", q4), ("Q5", q5), ("Q6", q6)):
        if (detail := function(check, core, task)) is not None:
            fired[name] = detail
    return fired


def labels() -> dict:
    found = {}
    for path in sorted((REPAIR / "attribution").glob("labels-replay-*.json")):
        found.update(json.loads(path.read_text()))
    return found


def main(out: str):
    import harness  # noqa: E402  (sets the import paths to this checkout's scripts)
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from score import kind_of

    relabels = json.loads((REPAIR / "gold-p2.json").read_text())["relabels"]
    by_session, core_gold = harness._gold()
    known = labels()
    original, seen, rows = core_decision.decide_core, {}, []

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        gold = harness._label(sid, by_session, core_gold)
        if (relabel := relabels.get(sid)) and folder.name == "t1":
            gold = relabel["to"]
        seen.clear()
        core_decision.decide_core = spy
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        except Exception as error:  # noqa: BLE001 -- the old-schema readings harness.py reports
            rows.append({"key": key, "session": sid, "turn": folder.name, "gold": gold, "call": "error",
                         "error_text": f"{type(error).__name__}: {error}"[:200]})
            continue
        finally:
            core_decision.decide_core = original
        if "core" not in seen:
            rows.append({"key": key, "session": sid, "turn": folder.name, "gold": gold, "call": "no_core"})
            continue
        core = seen["core"]
        where = harness._item(sid)
        label = known.get(key)
        rows.append({
            "key": key, "session": sid, "turn": folder.name, "set": where[0] if where else None,
            "item": where[1] if where else None, "gold": gold, "call": core.kind, "basis": core.basis,
            "partial": bool(core.partial), "error": kind_of(gold, core.kind) if gold else None,
            "layer": label and label["layer"], "subtype": label and label["subtype"],
            "confidence": label and label.get("confidence"), "request": task[:400],
            "signals": compute(seen["decision"], core, found, task, payload, reread)})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows if r.get("gold") and r.get("error")]
    print(f"{len(rows)} readings; labelled {len(labelled)}; right {sum(r['error'] == 'right' for r in labelled)}; "
          f"errors with a label {sum(bool(r.get('layer')) for r in labelled if r['error'] != 'right')}; "
          f"replay errors {sum(r.get('call') in ('error', 'no_core') for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
