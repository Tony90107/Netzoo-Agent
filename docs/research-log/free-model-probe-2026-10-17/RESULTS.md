# 免費模型探測（2026-10-17）

目的：在不花錢的前提下，看 OpenRouter 免費模型能否接手兩個關鍵讀取角色，並記錄 schema 相容、延遲與限流。這不是完整 session，也不評估答對與否。

- 腳本：`probe.py`（只接受 `:free` 模型 id；遇到 429 等待 20 秒、最多重試 3 次，其他錯誤不重試）、`summarize.py`
- 原始結果：`probe-1.json`、`probe-1.log`
- 題目：core-judgment `items.json` 的 C04、C07、C17、C32、C36、C39、C41、C45、C53、C58
- 角色與送法都與正式版相同：
  - capability check：function calling、strict、`proposal_model`、上限 16,000 tokens
  - semantic interpreter：function calling、`SemanticInterpretation`、正式 prompt
- 費用：US$0。執行前後 `usage_daily` 都是 0，總用量 21.2574318 不變；免費請求用了 47/1000。

## 結果

| 模型 | capability check 解碼成功 | semantic interpreter 解碼成功 | 主要錯誤 | 中位延遲（check） |
|---|---|---|---|---|
| nemotron-3-super-120b（**現用**） | **9/10** | 4/10 | semantic 失敗 6 次都是同一種：`outcome_hypotheses` 回成 JSON 字串而不是 list | 116 s（p5r 同題 143 s） |
| nemotron-3.5-super-vl | 3/10 | 3/10 | 13 次 502（Nvidia 內部錯誤） | 74 s，最長 321 s |
| dots-3-note-preview | 5/10 | 0/10 | 違反 schema：缺欄位、多欄位、字串過長、空 list | 62 s |
| nemotron-3-ultra-550b | 0/10 | 0/10 | 20/20 是 503（provider 過載） | – |
| gemma-4-31b | 0/10 | 0/10 | 上游 429，每次重試 3 次仍然失敗 | – |
| inkling | 0/10 | 0/10 | 403：只開放給特定的 agent 應用 | – |

解碼成功的 capability check，程式都接受它們的引文：rejected 0、unchecked 0。

## 附帶發現：正式版的語意讀取第一次多半被程式退回

- p5r 中，gpt-4o-mini 的第一次 `semantic_interpreter` 呼叫在 51 個 session 裡有 38 個標為 failed。
- 這些多半不是解碼失敗，而是被確定性的證據驗證退回，例如 `missing_evidence`、`ungrounded_evidence`、`conflicting_evidence`。之後由 reviewer／patch 補救。
- 最後仍然失敗的 session 有 8 個，也就是 RESULTS-P5 記錄的「語意讀取失敗 8」。
- 這表示 semantic 讀取的 schema 與證據規則對 gpt-4o-mini 也很難，靠多輪補救才撐起來，屬於架構面的成本。

## 結論

- 這 10 題上，沒有任何免費模型比現用的 nemotron-3-super 更好：
  - 更大的 ultra 過載。
  - 更新的 3.5 不穩定。
  - dots 不遵守 schema。
  - gemma 被限流。
  - inkling 不開放一般 API。
- 「換成強模型會不會好很多」這個問題，目前無法用免費端點回答。
- 免費端點的狀態會變動。這是單一時段的觀察，不代表長期可用性。
