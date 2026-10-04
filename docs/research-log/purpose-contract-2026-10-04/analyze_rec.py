"""Log 363 gates: (a'') tie recommendations on the candidate-only live round.

Usage (repository root): HELDOUT=heldout9/heldout.json python3 docs/research-log/purpose-contract-2026-10-04/analyze_rec.py <tag> <repeats>
For each candidate session (hp-<tag>-cand-<id>-<rep>): the decision and reply it
saved, the study purpose its trace recorded, the recommendation recomputed from
them, and the reply re-rendered offline with and without (a'') (recommended_actions
patched to return nothing). Writes live/<tag>-rec-analysis.txt. Nothing calls a model.
"""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_live as A  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation import study_purpose_notes  # noqa: E402
from netzoo_agent_core.routing.study_purpose import StudyPurpose  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS  # noqa: E402

RECOMMEND = study_purpose_notes.recommended_actions


def name(action):
    return ACTION_DEFINITIONS[action].workflow


def known_roles():
    roles = set()
    for tag in ("s7", "s8"):
        for path in glob.glob(str(A.ROOT / ".netzoo" / "sessions" / f"hp-{tag}-cand-*.json")):
            calls = (json.loads(Path(path).read_text()).get("token_usage") or {}).get("calls", [])
            roles |= {call["role"] for call in calls}
    return roles


def main(tag, repeats):
    purposes = A.trace_purposes("cand")
    roles_before = known_roles()
    counts = Counter()
    r1_outside, r2_violations, h2_failures, agreement, new_roles = [], [], [], Counter(), set()
    lines = [f"# Log 363 (a'') live `{tag}` (candidate arm only)", ""]
    for item in A.ITEMS:
        key, task = item["id"], item["prompt"]
        label_rec = set(item.get("recommended_subset") or [])
        for rep in range(1, repeats + 1):
            run = A.load(tag, "cand", key, rep)
            if run is None:
                counts["missing"] += 1
                continue
            session = f"hp-{tag}-cand-{key}-{rep}"
            new_roles |= run["roles"] - roles_before
            traced = purposes.get(session)
            purpose = (StudyPurpose(traced.get("design"), traced.get("design_quote") or "",
                                    tuple(tuple(claim) for claim in traced.get("claims") or ()))
                       if traced else StudyPurpose())
            decision = TaskDecision.model_validate(run["decision"])
            recommended = RECOMMEND(decision, purpose, task)
            names = {name(action) for action in recommended}
            counts["trials"] += 1
            if recommended:
                counts["recommended_trials"] += 1
                if names <= set(item["acceptable_candidates"]):
                    counts["r1_within"] += 1
                else:
                    r1_outside.append(f"{key}-{rep}: {sorted(names)} vs acceptable {item['acceptable_candidates']}")
            if item["claim_kind"] in {"none", "causal", "prediction"} and recommended:
                r2_violations.append(f"{key}-{rep} ({item['claim_kind']}): {sorted(names)}")
            # Agreement with the labelled subset (report only).
            if label_rec and recommended:
                agreement["exact" if names == label_rec else "overlap" if names & label_rec else "disjoint"] += 1
            elif label_rec:
                agreement["missed"] += 1
            elif recommended:
                agreement["extra"] += 1
            # H2: the live reply is the offline render with (a''), and (a'') only adds to the render without it.
            with_a, kind = A.render(task, decision, True, traced)
            study_purpose_notes.recommended_actions = lambda *args, **kwargs: []
            without_a, _ = A.render(task, decision, True, traced)
            study_purpose_notes.recommended_actions = RECOMMEND
            text = run["reply"]
            if kind == "response_model":
                counts["h2_response_model"] += 1
            elif with_a != text:
                h2_failures.append(f"{key}-{rep}: live reply differs from its offline render ({kind})")
            elif not A.only_adds(without_a, with_a):
                h2_failures.append(f"{key}-{rep}: (a'') changed text ({kind})")
            else:
                counts["h2_ok"] += 1
                counts["h2_changed"] += with_a != without_a
            lines.append(f"- {key} r{rep}: purpose {traced and (traced.get('design'), [c for c, _ in traced.get('claims') or []])}"
                         f" | candidates {[name(a) for a in decision.hypothesis_actions]} | recommended {sorted(names)}"
                         f" | label {sorted(label_rec)}")
    r1 = counts["r1_within"] / counts["recommended_trials"] if counts["recommended_trials"] else None
    labelled = sum(1 for item in A.ITEMS if item.get("recommended_subset")) * repeats
    summary = [
        f"trials {counts['trials']}, missing {counts['missing']}",
        f"R1 precision: {counts['r1_within']}/{counts['recommended_trials']} = {r1} (gate >= 0.90); outside: {r1_outside}",
        f"R2 recommendations on none/causal/prediction labels (gate 0): {r2_violations}",
        f"H2: ok {counts['h2_ok']} (changed by a'' {counts['h2_changed']}), response_model {counts['h2_response_model']}, "
        f"failures {h2_failures}",
        f"H3 roles beyond the seventh/eighth candidate arms (gate none): {sorted(new_roles)}",
        f"report: agreement with recommended_subset {dict(agreement)}; labelled trials {labelled}",
    ]
    (HERE / "live" / f"{tag}-rec-analysis.txt").write_text("\n".join(summary + [""] + lines) + "\n", encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
