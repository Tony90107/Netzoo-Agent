# 付費強模型跑一輪 56 題的報價（2026-10-17）

範圍：只把讀取角色換成強模型，也就是 router、semantic（含 study purpose 等）和 capability check。回覆模型維持 gpt-4o-mini。程式碼是 p5r 那份（run worktree `54d08ce7`，乾淨）。

## 選定的模型：openai/gpt-4o

- 讀取角色：`OPENROUTER_ROUTER_MODEL=OPENROUTER_SEMANTIC_MODEL=openai/gpt-4o`。
- capability check：`OPENROUTER_CAPABILITY_MODEL=openai/gpt-4o-2024-11-20`。這是同一個模型的日期 id，目的是讓 check 保留自己的模型槽與 16,000 token 上限。
- 兩個 id 都要加進 `NETZOO_ROUTER_MODEL_ALLOWLIST`。

試過但不能直接用的模型：

| 模型 | 問題 |
|---|---|
| openai/gpt-4.1 | `SemanticInterpretation` 的 function call 回空參數（`args={}`、輸出 0 token），strict 模式也一樣。gpt-4o-mini 和 gpt-4o 用同一個 schema 都正常。session `live/sg41` 因此無效。 |
| anthropic/claude-sonnet-5.5 | 程式強制指定 tool（`tool_choice`），OpenRouter 路由到的 Amazon Bedrock 不支援，回 400。要改程式才能用。 |
| 推理型模型（gemini-3.1-pro、gpt-5.6 等） | 沒估。推理 token 會吃掉每題 30,000 token 的預算，可能被預算擋下，混淆結果。 |

## 實測：3 個 session（`live/sg4o`：C32、C04、C45）

| | gpt-4o（sg4o） | 同題 p5r（現況） |
|---|---|---|
| 讀取呼叫 | 6 / 10 / 7 | 7 / 10 / 7 |
| 失敗呼叫 | 0 / 1 / 0 | 1 / 1 / 1（第一次語意讀取都被退回） |
| 輸入 token（平均） | 29,063 | 35,752 |
| 模型時間 | 11 / 20 / 15 s | 262 / 336 / 219 s |
| 費用（OpenRouter 帳戶實扣，含回覆） | US$0.166，平均每題 US$0.055 | – |
| 核心判定 | C32 DO、C04 DO(partial)、C45 ASK（`count_fact`） | C32 DECLINE、C04 DO、C45 ASK（`fact_agent`） |

- 3 題的判定只是個案，不能當成準確率證據。
- 和 gold 對照：C32 變對（p5r 誤拒）；C04 變成 partial，計分會算錯；C45 兩邊都對。

## 報價

- 實測外推：每題 US$0.055 × 56 題 ≈ **US$3.1**。
- 離線估算（`estimate.py`，用 p5r 的呼叫數與 token 量）：US$4.6–5.8。gpt-4o 需要的補救呼叫較少，所以實際會偏低。
- **預估一輪 US$3–5，建議硬上限 US$6。** 若要每題跑 2 次估變異：US$6–10。
- 時間：模型時間大約從每題 4–5 分鐘降到 15–20 秒。整輪用 5 個 worker，預估 15–30 分鐘。

## 這次量測已花的錢

今天帳戶 `usage_daily` 是 US$0.2295，全部來自這次量測：

- 約 US$0.064：gpt-4.1 的 1 次 id 測試、1 個 session、診斷呼叫，以及 gpt-4o-mini、gpt-4o、Claude 的 schema 測試。
- US$0.166：3 個 gpt-4o session。
