"""Traced live reproduction of the noisy-prior reply and method-tie controls.

Usage (spends gpt-4o-mini calls): python run_live.py <out.json> <repeat> [ids,comma,sep]
Without --live nothing is sent. Output keeps raw structured provider I/O,
routing events, the decision and the rendered answer for each trial.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

CASES = [
    {
        "id": "noisy-prior-zh", "language": "zh", "category": "positive",
        "prompt": (
            "延續基準地圖的建立，我們發現我們研究的物種沒有專屬的結合位點資料，只能借用近緣物種的預測結果。"
            "這代表我們的『先驗骨架』充滿了雜訊和不確定性。如果模型死板地信任這些先驗，結果一定會被帶偏。"
            "有沒有一種分析哲學，是可以在整合過程中，把這種『先驗不可靠的程度』透過機率的方式量化，讓數據自己去權衡？"
        ),
        "expected": {"status": "ambiguous", "actions": []},
    },
    {
        "id": "noisy-prior-en", "language": "en", "category": "paraphrase",
        "prompt": (
            "Continuing with the baseline map: the species we study has no binding-site data of its own, "
            "so we can only borrow predictions from a closely related species. Our prior skeleton is "
            "therefore full of noise and uncertainty. If the model trusts these priors rigidly, the "
            "result will be biased. Is there an analysis philosophy that quantifies, probabilistically, "
            "how unreliable the prior is during integration, and lets the data weigh it?"
        ),
        "expected": {"status": "ambiguous", "actions": []},
    },
]


def blind(case_id):
    for case in json.loads((ROOT / "docs/research-log/blind/blind_en.json").read_text()):
        if case["id"] == case_id:
            return case
    raise KeyError(case_id)


def main():
    if "--live" not in sys.argv:
        print("Refusing to spend provider calls without --live")
        return 2
    args = [a for a in sys.argv[1:] if a != "--live"]
    out, repeat = Path(args[0]), int(args[1])
    wanted = set(args[2].split(",")) if len(args) > 2 else None
    cases = CASES + [blind("case2-en"), blind("case3-en")]
    cases = [c for c in cases if wanted is None or c["id"] in wanted]
    from dotenv import load_dotenv
    from evaluate_routing import RoutingScenario, _TraceCapture, evaluate
    from netzoo_agent_core.llm import build_llm
    load_dotenv(ROOT / ".env", override=False)
    model = "openai/gpt-4o-mini"
    provider = build_llm(model, 0.0, max_output_tokens=2000, timeout_seconds=45)
    capture = _TraceCapture()
    rows = []
    report = evaluate([RoutingScenario.model_validate(c) for c in cases], provider=provider,
                      model_name=model, source="live", repeat=repeat, trace_capture=capture)
    for row in report["results"]:
        rows.append(row)
    answers = {}
    for trial in capture.trials:
        answers.setdefault(trial["id"], [])
    out.write_text(json.dumps({"report": report, "trace": capture.document({"model": model})},
                              ensure_ascii=False, indent=2, default=str) + "\n")
    for row in rows:
        roles = [c.get("role") for c in (row.get("usage") or {}).get("calls", [])]
        print(row["id"], row.get("trial"), row.get("reason_code"), row.get("status"),
              row.get("hypothesis_actions") or row.get("candidates"), roles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
