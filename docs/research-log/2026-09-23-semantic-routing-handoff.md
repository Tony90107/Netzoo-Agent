# Handoff：Semantic routing 根因追查與修正（2026-09-23）

專案：`/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`
完整研究紀錄：`docs/research-log/2026-09-23-semantic-contract-routing-session-report.md` §19–§22

> **更新（round 6 之後）：** 第 5 節第 2 項（錯誤 fallback 計數）已完成。另外新增 F7 請求一致性規則，使錯誤推薦在兩契約皆為 0（研究紀錄 §22）。第 1 項「拒絕降級式 review」**尚未實作**，已移到新清單的 P3。目前待辦以 `docs/research-log/2026-09-23-open-issues-for-agent.md` 為準。

## 0. 目前狀態（先讀）

- **全部未 commit。** 工作樹同時有前一個 session 留下的未 commit 修改（desktop/、server/、engine/ 等，以及部分與本輪相同的檔案）。不要 reset／checkout；commit 前需分辨哪些是本輪的。
- 測試：`~/.venvs/netzoo-qa/bin/python -m pytest -q` → 2070 passed、35 skipped。本輪修改的檔案 Ruff 都通過；`routing/candidate_ranking.py` 有一個 HEAD 就存在的 F401，不是本輪造成。
- **Claims 契約仍不升為 production default。**
- 專案規則（沿用）：
  - 不以 system prompt 措辭誘導行為，只改契約形狀、驗證規則或 registry 宣告。
  - gpt-4o-mini 的 live round 已預先授權；gpt-4o 要先問。
  - 每次 live round 前把判準寫進研究紀錄。
  - 分數差 ≤ 3–4 不下結論，以結構性計數為主。
  - 使用者實際以英文操作：英文失敗優先，中文題只當回歸防護。

## 1. 這輪做了什麼

1. **保存原始 trial 再找根因。** 原本的 evaluator report 沒有 raw claims／reviewer I/O。本輪寫了擷取工具，逐 trial 記錄 provider 輸入輸出、`finish_reason`、token usage 與 routing events，再把記錄下來的模型輸出**離線重放**過 decode → apply → restore → validate → match，逐一確認根因。
2. **修正確定性層**（F1–F5、N1），每項都對應一個已重放確認的根因。
3. **Claims reviewer 的結構化 repair feedback**（F6）。
4. **擴充評估語料**：`tests/routing_semantic_families.json`，32 個不同 prompt，四家族各 8 題（granularity、history/current、role/entity、中文），含方向相反的配對與真正歧義的對照題。
5. 共 4 輪 traced live paired A/B（legacy 與 claims 同時段，repeat=3，原 8 題＋32 題），約 2,700 次 gpt-4o-mini 呼叫。

## 2. 找到的根因與修正

| 代號 | 根因（已重放確認） | 修正 | 檔案 |
| --- | --- | --- | --- |
| F1 | Aggregate 0/3 是**確定性 matcher 問題**：LIONESS-PUMA 也宣告 `aggregate`，與 PUMA 在 stated 維度打平，完全正確的 aggregate 解讀仍被回問粒度 | 若候選 pipeline 的 `guidance_predecessors` 也在候選中，且該 predecessor 能產出**被陳述的**粒度，就移除該 pipeline | `routing/requested_outcome_matching.py`、`routing/outcome_matching.py` |
| F2 | 「不需要每位病患各自的網路」的 `不需要` 不在否定詞表；中文 witness 有 3 個假陽性（整體突變負荷量、單一樣本網路、每個樣本的 TFA 矩陣） | 補否定詞；中文粒度 witness 必須連到網路名詞 | `interpretation/request_integrity.py` |
| F3 | 請求逐字陳述了粒度，但模型把 evidence 標成 inferred（或引文對不上），擋住 witness，semantic wrapper 就當成「未陳述」→ PUMA/LIONESS-PUMA 平手 | 唯一 witness 取代同值但 inferred 或未 grounded 的 granularity evidence；不改不同值 | `interpretation/stated_field_restoration.py` |
| F4 | Claims reviewer 0/11：`repairs` 清單允許重複 `hypothesis_index`；模型把 outcome 重寫 2–3 次，違反 apply，也撐爆 1,200 token 輸出上限 | `SemanticClaimRepair` 改為單一 `hypothesis_index`＋`outcome`（與 legacy patch 同形） | `contracts/semantic_claims.py`、`graph/claim_invocation.py` |
| F5 | 模型把「每位病患」寫成 regulator→target 網路的 `sample` 節點 | 對 `regulatory_network`／`signed_regulatory_effect_network` 移除 `sample` entity（TF-activity artifact 除外） | `interpretation/stated_field_restoration.py` |
| N1 | "If I later obtain … I might cluster patients" 被當成目前的分群目標 | `patient_clustering_goal` 跳過 hypothetical 子句；`_UNCERTAIN` 加 `也許／或許` | `interpretation/request_integrity.py` |
| F6 | Claims reviewer 對本體衝突類 issue 只收到 issue 代碼（legacy 有結構化 feedback），這類只有 4/27、5/27 通過 | 只對本體衝突類 issue 附上結構化資料（可修欄位、目標值、artifact 約束、restoration 後的欄位值、請求逐字 witness）；不搬散文 instruction；引文錯誤類的訊息不變 | `interpretation/claim_prompt.py` |

**反轉了一個既有設計決定：** `tests/test_exact_needs_a_stated_discriminator.py` 原本把「aggregate 的 PUMA vs LIONESS-PUMA」釘為 ambiguous。現在改為：被陳述的 aggregate 會選 PUMA；未陳述粒度時仍 ambiguous（原則保留）。

**測試：** 新增 `tests/test_granularity_history_role_regressions.py`（41 個）；`tests/test_semantic_claims.py` 新增 F4／F6 測試；另更新 `test_stated_field_restoration.py`、`test_capability_corpus_coverage.py`。

## 3. 為什麼這樣改會有效（以及哪些還沒被證明）

共同原則：**讓確定性層不去丟掉請求已經陳述、模型也已經答對的事實**，而不是要求模型寫得更好。

- **F1 已驗證。** 失敗在模型答對之後才發生，所以只要修 matcher 就夠。原 8 題的兩個 aggregate prompt 兩契約都從 0/3 → 3/3，之後各輪維持。10,395 個生成 outcome 的前後比對中，只有 aggregate regulatory network 的歧義變化，沒有任何 exact 結果被改變。
- **F4 已驗證。** 重複 index 在 schema 上變得寫不出來，這是結構保證，不靠模型。重複 index 與截斷從每輪數次變為 0；8 題 reviewer validation 0/11 → 4/5。
- **N1 已驗證。** 假設題兩契約從 0/3 → 3/3；真正要分群的題目仍會被標記衝突。
- **F2／F3**：原理是讓已陳述的粒度被當成已陳述。離線重放時，Claims 的第一次 interpretation 從整輪 13/24 通過變成 18/24 直接 exact。Live 上與 F1 一起貢獻了 8 題的改善，但沒有單獨隔離。
- **F5 尚未被 live 證明。** 驗證輪中模型幾乎沒再寫 `sample`，只觸發 1 次（行為正確）。
- **F6 只有部分效果。** 本體衝突類 review 通過驗證 5/27 → 13/25，**但真正修對仍是 4/25**。允許值包含 `unknown`，reviewer 會把被陳述的值降成 `unknown` 或刪 evidence 來通過驗證，因此多了錯誤的 fallback 推薦（DRAGON×3）。依事前撤回條件，F6 暫時保留，但不能宣稱 reviewer 能力提升。

## 4. 數字總覽（gpt-4o-mini、`when_needed`、repeat=3）

| 輪次 | 原 8 題 legacy | 原 8 題 claims | 32 題 legacy | 32 題 claims |
| --- | ---: | ---: | ---: | ---: |
| 修正前（traced） | 14/24 | 13/24 | — | — |
| F1–F4 | 20/24 | 21/24 | 69/96* | 56/96* |
| ＋F5、N1 | 22/24 | 21/24 | 74/96 | 62/96 |
| ＋F6 | 23/24 | 20/24 | 70/96 | 66/96 |

\* 已更正一個語料錯誤後重新計分。

- Legacy 在後兩輪之間程式沒變，卻從 74 → 70，所以約 ±4 是同輪漂移。
- Claims 在 32 題上仍明顯落後：逐題配對較差多於較好；reviewer validation 較低；unmatched evidence 約 70 對 legacy 約 5。
- unsafe execution 各輪皆 0。

## 5. 下一步（建議順序）

1. **拒絕「以降級化解本體衝突」的 review（最優先）。** 若 review 把有 request witness 支持的粒度或角色改成 `unknown`，或刪掉其 evidence，就丟棄該 review，保留第一次的狀態。可沿用 `interpretation/outcome_downgrade.py`。事前判準要同時包含「真正修對數」與「錯誤 fallback 數」，不能只看通過驗證數。
2. **把錯誤 fallback 列為常設安全計數**，與錯誤 exact 並列，最好直接加進 `scripts/evaluate_routing.py` 的 summary。
3. **英文 artifact 誤判**（claims 較嚴重）：
   - TF per-sample 被判成 `regulatory_network_and_tf_activity`。
   - 「同時有 miRNA 與 TF」被判成 `multi_omic_network`：`role-both-*` 兩題兩契約都 0/3。
   不能靠 prompt 措辭修。可考慮擴充英文 witness（例如 "separately in each patient"、"regulate their target genes"），讓 request_facts 有值；但要在**不同於語料的新 prompt** 上驗證，避免照著語料調 regex。
4. **Claims 的 `operation` 引文錯誤**是 unmatched evidence 最大宗。Guidance matching 本來就把 operation 抹成 unknown，是否讓 guidance 模式下的 operation 引文錯誤不再致命，需要先做政策決定。
5. **F5 的 live 證據**：若要確認，需要一批會誘發 `sample` 節點的英文 prompt。
6. **前一個 session 未 commit 的 claims reviewer prompt 措辭**（"Do not return an empty patch … Do not translate or paraphrase a quote"）違反專案規則，而且 traced 結果顯示無效；請決定是否撤回。
7. Commit 時分開本輪與前一個 session 的修改。

## 6. 重現與工具

- 擷取工具：`docs/research-log/live-semantic-trace-2026-09-23-harness.py`
  ```bash
  set -a; . ./.env; set +a
  ~/.venvs/netzoo-qa/bin/python docs/research-log/live-semantic-trace-2026-09-23-harness.py claims 3 /tmp/out.json tests/routing_semantic_families.json
  ```
  參數依序為：契約（legacy／claims）、repeat、輸出檔、語料、可選的逗號分隔 case id。工具只檢查 `OPENROUTER_API_KEY` 是否存在，不讀取、不輸出其值。
- 各輪 traced reports：`docs/research-log/live-semantic-trace-2026-09-23-{prefix,postfix,round3,round4}-*.json`（system prompt 以 SHA-256 取代）。
- 語料：原 8 題 `tests/routing_semantic_variants.json`；32 題 `tests/routing_semantic_families.json`。
