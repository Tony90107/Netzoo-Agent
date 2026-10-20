# Live smoke 計畫

使用者於 2026-10-20 明確要求跑一次 live 測試，授權本輪模型呼叫；本輪取代前一輪的 $0／不 live 限制。沿用開發工作樹 `7aab4b37`，不修改 production 或模型提示。

- 6 個全新情境、7 個回合，包含 DO／DECLINE／ASK／CLARIFY，以及一次追問後補答。題目與預期結果先凍結於 items.json，不把預期答案送給模型。
- 使用真實 CLI 與現行模型設定：gpt-4o-mini 路由／語意／回覆，Nemotron free 能力核對。獨立 session／profile，不混入既有對話記憶。
- 費用預算 US$0.50。OpenRouter 模型 metadata 核對的 prompt／completion 每 token 費率：mini 0.00000015／0.0000006；Nemotron free 0／0。各回合維持既有 30k task + 30k reading token 額度，7 回合保守 token 費用約不超過 $0.252；價格快照與各次 usage 另存。此為估算，非供應商帳單。
- 最多兩個 session 同時跑，不重跑既有 job，不因失敗自動換模型／改題／調提示。各 turn 外層 timeout 600 秒。
- 沿用既有 live harness 的 CLI 執行與 card 觀察方式；不提供 /execute，不允許科學工具實際執行。保留 stdout、stderr、session、events、cards、manifest。
- 核對原文讀取、core.decision、core.view、實際回覆及執行授權；不能只看最終類別。過程中若發現供應商或額度問題，記錄失敗原因，避免無意義重跑。
- 本輪是作者自行出題的新題 smoke，並非由獨立出題者建立的正式盲測。
