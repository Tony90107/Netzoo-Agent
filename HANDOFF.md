# NetZoo agent — 接手 prompt

專案在 `netzoo_agent/`。跑測試：`python -m pytest tests/ -q`
（基準：**1603 過 / 93 失敗**，那 93 個是既有的，不要以為是你弄壞的）。
LLM 相關的要在 Docker 跑：`docker compose run --rm -T netzoo python ...`

## 待辦（唯一一項，已定位到單行）

`routing/outcome_matching.py` 的 `_match_semantic_request`，guidance 模式下
**無條件把 `operation` 抹成 unknown**。用意是避開 `explain`，但把 `infer` 也殺了。

證明：同一個 outcome，`operation=infer` → `exact ['run_lioness_panda']`（正確）；
`operation=unknown` → `ambiguous []`（實跑得到的，然後問一句多餘的澄清）。

**修法**：只抹「不是產生該 artifact 的動作」。`contracts/artifact_semantics.py`
已有 `produced_by` 欄位（目前只宣告 `regulatory_network={"infer"}`）可以判斷。
`explain` 不在 produced_by → 照抹（現行測試 `test_guidance_operation_is_not_
required_for_registry_candidate_matching` 用的就是 explain，不會壞）。

影響 38 個 trial（12.8%）。

## 三條硬規則

1. **改動前先 grep 測試。** 我今天兩次提案被既有測試直接反證（`operations` 宣告、
   用確定性證人回填 `input_artifacts`），都是沒先查就開口。
2. **不准用「改 prompt 措辭」當補救。** 使用者已試過六次無效。要改就改契約形狀。
3. **pass_rate 的噪音是 2–3 點。** 同碼兩輪就差這麼多，低於這個幅度不是訊號。

## 已量到的事實（別再重新推導）

- pass_rate 卡在 36–39%。**天花板不在證據契約**：完全沒有驗證問題的 trial
  通過率也只有 45.5%，所以契約最多值 7 點。
- 13 個 case 三輪九次全掛，佔全部失敗 63%。
- `selection_tags` 一等欄位化**是錯的目標**——需要區分的 77 個 trial 裡 64 個
  候選數是零（沒有平手可分），只值 13 個，卻要動 ~20 模組。
- discriminator 機制有效（有跑的通過率 56% vs 全體 38%），只是多數情況到不了它。

完整分析：`docs/research-log/2026-09-16-routing-failure-distribution.md`

## 量測協定

`docker compose run --rm -T netzoo python scripts/evaluate_routing.py --live \
  --repeat 3 --model openai/gpt-4o-mini --max-calls 300 --timeout 60 --json \
  > docs/research-log/live-full-corpus-roundN-<label>.json`

已有 round16–20（16/17 舊碼、18/19 調和、20 +produced_by）可比。
gpt-4o-mini 使用者已預先授權；**gpt-4o 要先問**。
連續輪次不是獨立樣本，要下結論至少跑兩輪同條件。
