"""Log 384 live gates (precision and no regression), from both arms' sessions and traces. Nothing calls a model.

Usage (any directory): python3 docs/research-log/precision-plan-2026-10-06/pp_analyze.py <tag> <repeats>
Imports the candidate worktree's code (the shipped renderer) and writes live/<tag>-analysis.txt.
HELDOUT=<path relative to this folder> selects another labelled set (the self-test).

Read from the reply text, identically for both arms:
- a data question: a sentence ending in "?" that asks whether the user has something ("do you (also/
  already) have", "have you got/built/obtained/assembled"). Log 380 counted any question naming the
  data, which took in a tie's own "Do the regulators include miRNAs ...?" (its M1);
- a priors question: a data question that names a motif, binding, PPI or protein interaction;
- a miRNA question: a data question that names miRNA, microRNA or small RNA;
- "says ruled out": the candidate's sentence "... which you said you do not have";
- offered as the answer: "Selected path: **X**", "Fallback recommendation: **X**", or the decision's
  advisory recommendation;
- a model-written reply: a session with a `response` call, or the budget fallback text. These cannot
  be re-rendered offline, so H2 covers the others and B1 counts them per arm (Log 380 self-test).
"""
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
WORKTREES = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
ARMS = {"base": WORKTREES / "netzoo-item3-base", "cand": WORKTREES / "netzoo-dp-cand"}
sys.path.insert(0, str(ARMS["cand"] / "scripts"))
from langchain_core.messages import HumanMessage  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, REQUIRED_INPUTS  # noqa: E402

ITEMS = {item["id"]: item for item in json.loads((HERE / os.environ.get("HELDOUT", "heldout23/heldout.json")).read_text())["items"]}
POLICY = ProjectPolicyLoader(ARMS["cand"]).load()
NAME = {definition.workflow.upper(): action for action, definition in ACTION_DEFINITIONS.items()}
MODEL_ERRORS = {"ValueError", "ValidationError", "JSONDecodeError", "OutputParserException", "KeyError", "TypeError",
                "AssertionError"}
PRIORS_WORDS = re.compile(r"motif|binding|\bPPI\b|protein[- ]protein|protein interaction", re.I)
MIRNA_WORDS = re.compile(r"mi(?:cro)?[- ]?RNA|\bmiR\b|small[- ]RNA", re.I)
POSSESSION = re.compile(r"\bdo you (?:also |already )?have\b|\bhave you (?:got|built|obtained|assembled)\b", re.I)
BUDGET_FALLBACK = "No additional response-model call was made"
OFFERED = re.compile(r"(?:Selected path|Fallback recommendation): \*\*(.+?)\*\*")


def actions(names):
    return {NAME.get(name.upper(), name) for name in names}


def needs(action, kind):
    fields = {"priors": {"motif_file", "ppi_file"}, "mirna": {"mirna_file"}}[kind]
    return bool(fields & set(REQUIRED_INPUTS.get(action, ())))


def questions(text):
    sentences = re.split(r"(?<=[.?!])\s+|\n+", text.replace("**", ""))
    return [s.strip() for s in sentences if s.strip().rstrip('")\'').endswith("?")]


def traces(arm, tag):
    """session id -> {event_type: last payload, 'errors': [...]} for this tag's sessions."""
    found = {}
    for manifest in glob.glob(str(ARMS[arm] / ".netzoo" / "traces" / "*" / "manifest.json")):
        try:
            session = json.loads(Path(manifest).read_text()).get("session_id", "")
        except ValueError:
            continue
        if not session.startswith(f"hp-{tag}-"):
            continue
        entry = found.setdefault(session, {"errors": []})
        for line in open(Path(manifest).parent / "events.jsonl"):
            event = json.loads(line)
            payload = event.get("payload") or {}
            entry[event.get("event_type")] = payload
            if payload.get("error_type"):
                entry["errors"].append(payload["error_type"])
    return found


def load(tag, arm, key, rep):
    path = ARMS[arm] / ".netzoo" / "sessions" / f"hp-{tag}-{arm}-{key}-{rep}.json"
    if not path.exists():
        return None
    session = json.loads(path.read_text())
    decision = (session.get("plan") or {}).get("decision") or {}
    reply = next((str(m.get("content")) for m in reversed(session.get("messages", []))
                  if m.get("type") in ("ai", "AIMessage") or m.get("role") == "assistant"), "")
    calls = (session.get("token_usage") or {}).get("calls", [])
    return {"decision": decision, "reply": reply, "roles": [c["role"] for c in calls],
            "cost": sum(c.get("cost_micro_usd") or 0 for c in calls) / 1e6, "plan": session.get("plan") or {}}


def measure(session):
    decision = session["decision"]
    reply = session["reply"]
    asked = [q for q in questions(reply) if POSSESSION.search(q)]
    offered = {NAME.get(name.strip().upper(), name.strip())
               for match in OFFERED.findall(reply) for name in match.split("→")}
    if (decision.get("advisory_recommendation") or {}).get("action"):
        offered.add(decision["advisory_recommendation"]["action"])
    listed = {*decision.get("matched_actions", []), *decision.get("hypothesis_actions", []),
              *decision.get("recommended_actions", []), *offered}
    return {
        "asks_priors": any(PRIORS_WORDS.search(q) for q in asked),
        "asks_mirna": any(MIRNA_WORDS.search(q) for q in asked),
        "says_ruled_out": "which you said you do not have" in reply,
        "offered": offered,
        "selected": {NAME.get(n.strip().upper(), n.strip()) for m in re.findall(r"Selected path: \*\*(.+?)\*\*", reply)
                     for n in m.split("→")},
        "lists_priors": any(needs(action, "priors") for action in listed),
        "model_written": "response" in session["roles"] or reply.startswith(BUDGET_FALLBACK),
        "budget_fallback": reply.startswith(BUDGET_FALLBACK),
    }


def render(task, decision, purpose):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None, "study_purpose": purpose, "data_facts": decision.data_facts}
    try:
        out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    except Exception as error:  # noqa: BLE001 -- reported, never hidden
        return f"<render failed: {type(error).__name__}>"
    return str(out["messages"][-1].content)


def pct(part, whole):
    return f"{part}/{whole}" + (f" ({100 * part / whole:.0f}%)" if whole else "")


def main(tag, repeats):
    lines = []
    out = lambda text="": lines.append(text)  # noqa: E731
    sessions = {arm: {} for arm in ARMS}
    traced = {arm: traces(arm, tag) for arm in ARMS}
    for arm in ARMS:
        for key in ITEMS:
            for rep in range(1, repeats + 1):
                sessions[arm][(key, rep)] = load(tag, arm, key, rep)
    measured = {arm: {k: measure(s) for k, s in sessions[arm].items() if s} for arm in ARMS}

    out(f"# Log 384 live analysis `{tag}` ({repeats} repeats, {len(ITEMS)} items)")
    out()
    for arm in ARMS:
        missing = [f"{k}-{r}" for (k, r), s in sessions[arm].items() if s is None]
        errors = Counter(e for entry in traced[arm].values() for e in entry["errors"])
        provider = {e: n for e, n in errors.items() if e not in MODEL_ERRORS}
        cost = sum(s["cost"] for s in sessions[arm].values() if s)
        out(f"V1 {arm}: sessions {sum(1 for s in sessions[arm].values() if s)}/{len(sessions[arm])}, "
            f"missing {missing}, provider errors {provider}, all errors {dict(errors)}, cost ${cost:.4f}")
    out()

    def select(arm, rule):
        return [(k, r) for (k, r) in measured[arm] if rule(ITEMS[k])]

    gates = {}
    # A1: asks about priors when the question needs them and the request leaves them unstated.
    a1 = {}
    for arm in ARMS:
        keys = select(arm, lambda item: item["data_question"] == "priors")
        a1[arm] = (sum(measured[arm][k]["asks_priors"] for k in keys), len(keys))
    rate = {arm: a1[arm][0] / a1[arm][1] if a1[arm][1] else 0.0 for arm in ARMS}
    gates["N1"] = a1["cand"][0] >= a1["base"][0]
    out(f"N1 asks about priors where data_question=priors (no regression): base {pct(*a1['base'])}, cand {pct(*a1['cand'])} "
        f"-> {'PASS' if gates['N1'] else 'FAIL'} (cand >= base)")
    for arm in ARMS:
        keys = select(arm, lambda item: item["data_question"] == "priors")
        listing = [k for k in keys if measured[arm][k]["lists_priors"]]
        out(f"   (report) {arm}: where it lists a workflow needing priors {pct(sum(measured[arm][k]['asks_priors'] for k in listing), len(listing))}; "
            f"elsewhere {pct(sum(measured[arm][k]['asks_priors'] for k in keys if k not in listing), len(keys) - len(listing))}")
    # A2: never asks about priors the request states or rules out.
    a2 = {}
    for arm in ARMS:
        keys = select(arm, lambda item: item["priors_label"] in {"stated", "ruled_out"})
        a2[arm] = [f"{k}-{r}" for k, r in keys if measured[arm][(k, r)]["asks_priors"]]
    gates["P1"] = len(a2["cand"]) <= 2
    out(f"P1 priors questions where priors stated or ruled out: base {len(a2['base'])} {a2['base']}, "
        f"cand {len(a2['cand'])} {a2['cand']} -> {'PASS' if gates['P1'] else 'FAIL'} (cand <= 2)")
    p2 = {arm: [f"{k}-{r}" for (k, r), m in measured[arm].items()
                if ITEMS[k]["data_question"] == "none" and (m["asks_priors"] or m["asks_mirna"])] for arm in ARMS}
    gates["P2"] = len(p2["cand"]) <= len(p2["base"]) // 3 if len(p2["base"]) >= 3 else len(p2["cand"]) <= len(p2["base"])
    out(f"P2 data questions where data_question=none: base {len(p2['base'])} {p2['base']}, cand {len(p2['cand'])} "
        f"{p2['cand']} -> {'PASS' if gates['P2'] else 'FAIL'} (cand <= base // 3 when base >= 3, else cand <= base)")
    # A3: precision of the candidate's priors questions.
    asks = [(k, r) for (k, r), m in measured["cand"].items() if m["asks_priors"]]
    good = [(k, r) for k, r in asks if ITEMS[k]["data_question"] == "priors"]
    # (report) precision of the priors questions; P1/P2 gate the needless ones
    wrong = sorted({k for k, _ in asks} - {k for k, _ in good})
    out(f"A3 cand priors questions on data_question=priors: {pct(len(good), len(asks))}; elsewhere on {wrong} "
        f"(report)")
    # R1: the candidate says what the request ruled out, where it lists a workflow needing it.
    keys = [k for k in select("cand", lambda item: item["priors_label"] == "ruled_out") if measured["cand"][k]["lists_priors"]]
    said = sum(measured["cand"][k]["says_ruled_out"] for k in keys)
    gates["R1"] = bool(keys) and said / len(keys) >= 0.60
    out(f"R1 cand says the priors were ruled out, where it lists a workflow needing them: {pct(said, len(keys))} "
        f"-> {'PASS' if gates['R1'] else 'FAIL'} (>= 60%)")
    # R2: a workflow the data cannot run (ruled out) or may not run (unstated) offered unconditionally.
    r2 = {}
    for arm in ARMS:
        ruled, unstated = [], []
        for (k, r), m in measured[arm].items():
            item = ITEMS[k]
            for kind, label in (("priors", item["priors_label"]), ("mirna", item["mirna_label"])):
                if label == "ruled_out" and any(needs(a, kind) for a in m["offered"]):
                    ruled.append(f"{k}-{r}:{kind}")
                if label == "unstated" and any(needs(a, kind) for a in m["selected"]):
                    unstated.append(f"{k}-{r}:{kind}")
        r2[arm] = (ruled, unstated)
    total = {arm: len(r2[arm][0]) + len(r2[arm][1]) for arm in ARMS}
    gates["R2"] = total["cand"] <= total["base"] // 3 if total["base"] >= 3 else total["cand"] <= total["base"]
    for arm in ARMS:
        out(f"R2 {arm}: offered though ruled out {len(r2[arm][0])} {r2[arm][0]}; "
            f"selected though unstated {len(r2[arm][1])} {r2[arm][1]}")
    out(f"R2 total base {total['base']}, cand {total['cand']} -> {'PASS' if gates['R2'] else 'FAIL'} "
        f"(cand <= base // 3 when base >= 3, else cand <= base{'; not exercised' if total['base'] < 3 else ''})")
    # M1: no miRNA question where the request states or rules out miRNA data.
    m1 = {}
    for arm in ARMS:
        keys = select(arm, lambda item: item["mirna_label"] in {"stated", "ruled_out"})
        m1[arm] = [f"{k}-{r}" for k, r in keys if measured[arm][(k, r)]["asks_mirna"]]
    gates["M1"] = len(m1["cand"]) <= max(1, len(m1["base"]))
    out(f"M1 miRNA questions where miRNA stated or ruled out: base {len(m1['base'])} {m1['base']}, "
        f"cand {len(m1['cand'])} {m1['cand']} -> {'PASS' if gates['M1'] else 'FAIL'} (cand <= max(1, base))")
    # H2: live reply = offline render of the recorded decision.
    # Plan layer (cand): the plan each session built, against the labels.
    plans = {}
    for (key, rep), session in sessions["cand"].items():
        event = traced["cand"].get(f"hp-{tag}-cand-{key}-{rep}", {}).get("routing.data_plan_built")
        if session is not None and event is not None:
            planned = event["data_plan"].get("needs") or []
            plans[(key, rep)] = {"asks": [n["kind"] for n in planned if n["action"] == "ask"],
                                 "says": [n["kind"] for n in planned if n["action"] == "say_ruled_out"],
                                 "basis": event["data_plan"].get("basis")}
    l1 = [f"{k}-{r}" for (k, r), p in plans.items() if "tf_priors" in p["asks"] and ITEMS[k]["data_question"] != "priors"]
    out(f"(report) L1 plan asks for priors where data_question != priors: {len(l1)} {l1}")
    need_keys = [(k, r) for (k, r) in measured["cand"] if ITEMS[k]["data_question"] == "priors"]
    l2 = sum(1 for k in need_keys if "tf_priors" in plans.get(k, {}).get("asks", []))
    out(f"(report) L2 plan asks for priors where data_question = priors: {pct(l2, len(need_keys))} "
        f"(no plan: {sum(1 for k in need_keys if k not in plans)})")
    # Render layer: the reply shows the plan, and asks nothing beyond it.
    shown, total, says_shown, says_total, beyond = 0, 0, 0, 0, []
    for k, plan in plans.items():
        m = measured["cand"][k]
        if m["model_written"]:
            continue
        for kind, field in (("tf_priors", "asks_priors"), ("mirna", "asks_mirna")):
            if kind in plan["asks"]:
                total += 1
                shown += m[field]
            elif m[field]:
                beyond.append(f"{k[0]}-{k[1]}:{kind}")
        if plan["says"]:
            says_total += 1
            says_shown += m["says_ruled_out"]
    gates["L3"] = total == 0 or shown / total >= 0.95
    gates["L4"] = says_total == 0 or says_shown / says_total >= 0.95
    gates["L5"] = len(beyond) <= 2
    out(f"L3 reply asks what the plan asks: {pct(shown, total)} -> {'PASS' if gates['L3'] else 'FAIL'} (>= 95%)")
    out(f"L4 reply says what the plan rules out: {pct(says_shown, says_total)} -> {'PASS' if gates['L4'] else 'FAIL'} (>= 95%)")
    out(f"L5 reply asks beyond the plan: {len(beyond)} {beyond} -> {'PASS' if gates['L5'] else 'FAIL'} (<= 2)")
    mq = [k for k in measured["cand"] if ITEMS[k[0]]["data_question"] == "mirna"]
    n2 = {arm: sum(measured[arm][k]["asks_mirna"] for k in mq if k in measured[arm]) for arm in ARMS}
    gates["N2"] = n2["cand"] >= n2["base"]
    out(f"N2 miRNA asks where data_question = mirna (no regression): base {pct(n2['base'], len(mq))}, "
        f"cand {pct(n2['cand'], len(mq))} -> {'PASS' if gates['N2'] else 'FAIL'} (cand >= base)")
    out(f"(report) plan basis: {dict(Counter(p['basis'] for p in plans.values()))}")
    b1 = {arm: [f"{k}-{r}" for (k, r), m in measured[arm].items() if m["model_written"]] for arm in ARMS}
    gates["B1"] = len(b1["cand"]) <= len(b1["base"]) + 1
    for arm in ARMS:
        fallback = [f"{k}-{r}" for (k, r), m in measured[arm].items() if m["budget_fallback"]]
        out(f"B1 {arm}: model-written replies {len(b1[arm])} {b1[arm]}; of them the budget fallback {fallback}")
    out(f"B1 -> {'PASS' if gates['B1'] else 'FAIL'} (cand <= base + 1)")
    h2 = []
    for (key, rep), session in sessions["cand"].items():
        if session is None or session["plan"].get("status") != "respond_only":
            continue
        if measured["cand"][(key, rep)]["model_written"]:
            continue
        entry = traced["cand"].get(f"hp-{tag}-cand-{key}-{rep}", {})
        purpose = entry.get("routing.study_purpose_detected")
        purpose = {k: purpose.get(k) for k in ("source", "design", "design_quote", "claims")} if purpose else None
        decision = TaskDecision.model_validate(session["decision"])
        if render(ITEMS[key]["prompt"], decision, purpose) != session["reply"]:
            h2.append(f"{key}-{rep}")
    gates["H2"] = not h2
    out(f"H2 cand respond-only replies differing from the offline render: {len(h2)} {h2} -> "
        f"{'PASS' if gates['H2'] else 'FAIL'}")
    roles = {arm: set(r for s in sessions[arm].values() if s for r in s["roles"]) for arm in ARMS}
    gates["H3"] = roles["cand"] - roles["base"] <= {"data_facts"}
    out(f"H3 roles cand - base: {sorted(roles['cand'] - roles['base'])}; base - cand: "
        f"{sorted(roles['base'] - roles['cand'])} -> {'PASS' if gates['H3'] else 'FAIL'}")
    complete = all(s is not None for arm in ARMS for s in sessions[arm].values())
    gates["V1"] = complete
    out(f"V1 every session present: {'PASS' if complete else 'FAIL'}")
    out(f"ALL GATES: {'HOLD' if all(gates.values()) else 'FAIL ' + str([g for g, ok in gates.items() if not ok])}")
    out()

    # Reports (not gates)
    out("(report) per label, arm: sessions | priors asks | miRNA asks | says ruled out | lists a priors workflow")
    table = defaultdict(Counter)
    for arm in ARMS:
        for (k, r), m in measured[arm].items():
            item = ITEMS[k]
            row = (arm, item["priors_label"], item["data_question"])
            table[row]["n"] += 1
            for field in ("asks_priors", "asks_mirna", "says_ruled_out", "lists_priors"):
                table[row][field] += m[field]
    for row, c in sorted(table.items()):
        out(f"  {row[0]:4} priors={row[1]:9} data_question={row[2]:6}: {c['n']:3} | {c['asks_priors']:3} | "
            f"{c['asks_mirna']:3} | {c['says_ruled_out']:3} | {c['lists_priors']:3}")
    reading, dropped, assessed = Counter(), [], 0
    for (key, rep), session in sessions["cand"].items():
        entry = traced["cand"].get(f"hp-{tag}-cand-{key}-{rep}", {})
        if (facts := entry.get("routing.data_facts_detected")) is not None:
            reading[("priors", ITEMS[key]["priors_label"], facts.get("priors"))] += 1
            reading[("mirna", ITEMS[key]["mirna_label"], facts.get("mirna"))] += 1
        if (judged := entry.get("routing.applicability_assessed")) is not None:
            assessed += 1
            if judged.get("recommendation_dropped"):
                dropped.append(f"{key}-{rep}:{judged['recommendation_dropped']}")
    out(f"(report) data-facts reading (kind, annotated -> read): {dict(sorted(reading.items()))}")
    owned = Counter()
    for (key, rep), session in sessions["cand"].items():
        facts = traced["cand"].get(f"hp-{tag}-cand-{key}-{rep}", {}).get("routing.data_facts_detected")
        for item in (facts or {}).get("rejected") or []:
            if item.get("reason") == "not_in_own_current_words":
                owned[(key, item["field"], ITEMS[key][f"{item['field'] if item['field'] == 'mirna' else 'priors'}_label"])] += 1
    out(f"(report) stated readings downgraded as not the user's own current words (item, kind, annotated): {dict(sorted(owned.items()))}")
    out(f"(report) applicability assessed in {assessed} cand sessions; recommendations dropped {dropped}")
    for arm in ARMS:
        recs = [(k, m["offered"]) for (k, _), m in measured[arm].items()]
        made = [(k, o) for k, o in recs if o]
        good = [(k, o) for k, o in made if o <= actions(ITEMS[k]["acceptable_candidates"])]
        out(f"(report) {arm}: offered an answer in {len(made)}/{len(recs)}, all acceptable in {len(good)}")
    per_item = defaultdict(lambda: {arm: [0, 0] for arm in ARMS})
    for arm in ARMS:
        for (k, _), m in measured[arm].items():
            per_item[k][arm][0] += m["asks_priors"]
            per_item[k][arm][1] += m["says_ruled_out"]
    out("(report) per item: priors asks base/cand, says ruled out cand")
    for k in ITEMS:
        item = ITEMS[k]
        out(f"  {k:3} priors={item['priors_label']:9} needs={item['question_needs']:20} dq={item['data_question']:6} "
            f"asks {per_item[k]['base'][0]}/{per_item[k]['cand'][0]} ruled {per_item[k]['cand'][1]}")
    text = "\n".join(lines)
    (HERE / "live").mkdir(exist_ok=True)
    (HERE / "live" / f"{tag}-analysis.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
