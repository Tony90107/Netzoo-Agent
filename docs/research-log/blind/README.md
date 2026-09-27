# Blind tool-selection test (10 cases, English and Chinese)

The prompts are the ten cases of `TEST_PROMPTS_推論與工具選擇.md`, with every
path rewritten to the neutral folders `data/blind-neutral/case-N/` (tracked in
the repo) so that no folder name gives the answer away. Case 10 uses
`data/blind-tests/case-1/`, whose file names deliberately do not match their
contents. Since Log 191 path tokens no longer name workflows, but the neutral
folders are kept so results stay comparable with Logs 179–204.

- `blind_en.json`, `blind_zh.json` — corpora the traced harness can load. Their
  `expected` field is a placeholder: `RoutingExpectation` holds one status, and
  several cases accept an exact match *or* a tie with a recommendation.
- `expectations.json` — what is actually graded: accepted and forbidden
  workflows per case, and the reply notes case 10 must show.
- `score_blind.py` — grades traced reports (see its docstring for verdicts).

Run (gpt-4o-mini rounds are pre-authorized; ask before gpt-4o):

```bash
set -a; . ./.env; set +a
python docs/research-log/live-semantic-trace-2026-09-23-harness.py legacy 3 /tmp/blind_en.json docs/research-log/blind/blind_en.json
python docs/research-log/blind/score_blind.py /tmp/blind_en.json
```

Reference results: Log 179 (English 20 correct, 5 partial, 5 fallback) and
Log 204 (28 correct, 1 fallback, 1 wrong); both reports are in the repo.
