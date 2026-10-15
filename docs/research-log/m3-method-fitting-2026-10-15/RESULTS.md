# M3 修正：方法提問走 method_fitting、已驗證設定不再送文字條件檢查（2026-10-15，離線）

基底 63e98bf（round m3 的候選版本，未通過驗收）。round m3 的題組已經看過，這裡當開發集使用。

- 修正 919817c 先做離線驗證（下面「結論」到「重現方式」）。
- 經使用者同意後，跑了 14 個 session 的精簡 live（round m3f，見「live m3f」）。
- live 的 K05 又找到一個缺口，已離線修正，但**尚未重跑 live**。

## 結論

| | 9 個誤承諾 | 4 個設定相關誤拒絕（MX12、MX18、P05、P08） |
|---|---|---|
| 只改程式碼（錄下的模型輸出原樣重播） | 1 個改變：K05 | 2 個改變：P08、MX12 |
| 加上新合約欄位（反事實：模型填入請求層級的樣本數／特徵數） | 5 個改變：K05、N03、N15、N26、N28 | 同上 2 個 |
| 沒有改變 | K02、N07、N08、N20 | MX18、P05 |

- **沒有任何錄下的「可做」需求變成被拒**，也沒有任何原本核准的 run 失去核准（兩種重播都是）。
- 另外 N17（原本標 ASKED，未決定）也改成「不可做」，理由是 registry 記錄的無效組合。
- 「改變」指的是回覆所依據的檢查列改了（見下方每題的新回覆），不是新的盲標。實際分數要 live 才知道。
- 全部測試通過（見文末）。

## 改了什麼

### 1. 方法提問也套用 M1 的方法條件

| 原因 | 修法 |
|---|---|
| 請求層級的條件只有指定方法和設定，**沒有樣本數與特徵數**。N03、N15、N28 的數量只被放進 `has`（context），`request_method_limit` 無從判斷。 | 合約 `conditions_model` 加入 `sample_count`、`sample_count_quote`、`feature_counts`（與 ask 層級同型別）。`request_method` 保留驗證過的數量；`request_method_limit` 用它判斷樣本下限、組合規則與 LIONESS-DRAGON 上限。 |
| N26 的 ask 有樣本數 100，但沒有特徵數，所以上限沒有判斷。 | 只有一個結果時，請求層級的數量補進該結果（`with_request_method`），與設定的規則一樣；兩個以上結果時不補，因為可能是另一份資料。使用者說數量未知時，補進來的數量也拿掉。 |
| K05、N17 的 `save_pvals=true` 加 `sparsify=false`：兩個設定各自合法，但 registry 的 `conditional_outputs` 把這個組合標成 invalid（執行器會擋），檢查卻沒有讀。 | `combination_issues` 讀 registry 的 invalid 條件輸出，用與執行器相同的 `resolve_conditional_output`。只有在使用者陳述其中的控制項、而且字面能決定值時才判斷。 |
| 方法提問的不可做列，原本引用第一個設定的字。 | 改成引用真正不符合的字：無法套用的設定（F1 不變：「its alpha update rate」）；組合不成立時，從第一個設定到樣本數的整段（「kmin=2 and kmax=9 on exactly six mutation samples」）；樣本不足時用樣本數的字。 |

這是**合約形狀和程式碼的修改，沒有改 prompt 措辭**（使用者的長期規則）。新欄位的 description 只說明欄位本身。完整 schema 從 26,568 字元增加到 27,279 字元（+2.7%）；compact schema 的 enum 數量不變（559，上限 1000）。

### 2. 已驗證的設定不再送文字條件檢查

- P08：「set cluster=false」已經讀成 `SAMBAR.cluster=false`（合法、有接到執行器）；它又被當成 `how_computed` 送給 nemotron，nemotron 回答 violates，於是 SAMBAR 被拒。
- 修法是 `condition_pairs` 不再送「已驗證、屬於該 workflow、可照陳述使用」的設定字。判斷條件：設定的字（名稱加值）必須在需求的字裡，而且至少佔一半。所以「set cluster=false and keep only TP53-mutant samples」仍會被檢查。

### 2b. 無法套用的設定只限制它自己的需求（MX12）

- 規則：如果某個設定沒有任何被判定的 workflow 能套用（未註冊、沒接到執行器、超出範圍、runtime 不支援、值無法解析），**而且它和每個 ask 的字之間都隔著子句邊界**，它就成為一列獨立的「不可做」需求，結果本身照常判斷。子句邊界是逗號、分號、冒號、括號、破折號或句尾。run 仍然會暫停（partial_gap），因為使用者也要求了這個設定。
- 理由是 gold 的慣例：
  - a24b 的 MX04「...(motif, PPI and expression attached) on the GPU so it finishes faster」與 MX05「..., but set its regularisation lambda to 0.5」都把設定判成獨立需求，m3 的 MX12 也一樣。
  - a24b 的 N11（設定在 ask 的字裡）與 m1b 的 F6「LIONESS-PANDA networks for our 40 liver samples with an edge sparsity threshold of 0.3 applied inside the method」（中間沒有子句邊界）都整句判成不可做。第一版規則只看「在不在 ask 的字外」，會讓 F6 變成「網路可做＋門檻不可做」，可能被標成 PARTLY，所以加上子句邊界的條件。
  - 指定的方法是未註冊方法時不拆（TIGER 的 L1 penalty 屬於 TIGER，不屬於被判定的 GIRAFFE）。
- **MX18、P05 不在範圍內**：「k=3」和「leave-one-out」都在 ask 自己的字裡。P05 是模型把 LIONESS 本身的原理讀成未註冊設定，程式碼無法區分這是誤讀，還是真的要求一個不支援的設定。

## 驗證

### 重播工具的可信度

`replay.py` 用錄下的模型輸出重建 round m3 的每個檢查：
- proposal、re-read（使用錄下的 passages）；
- 條件檢查、redirect 與第二意見：依「哪個結果、哪個 workflow、哪段字」查錄下的答案，不依位置；
- run 的判定（含 `unbound_settings`）。

用基底 63e98bf 的程式碼重播，162 個回合全部重現：143 個最終檢查與錄下的完全相同，另外 19 個核准的 run 的判定也相同。

### round m3 的變化（`changes.json`）

新回覆的「What I understood」一段：

- **K05**（錄下即可）：`"keep save_pvals=true but set sparsify=false" -- not available here as asked. BONOBO: save_pvals requires sparsify. BONOBO itself can still run, with its own settings instead`
- **N17**（錄下即可）：同上，引用「sparsify=false and save_pvals=true」。
- **P08**（錄下即可）：`"Can SAMBAR return pathway mutation scores without assigning tumor clusters?" -- available from SAMBAR.` 條件檢查不再被呼叫。
- **MX12**（錄下即可，但見下方 live 註記）：
  - signed R、sample-varying TFA 都是 available from GIRAFFE；
  - `"exposed custom optimizer learning rate of 0.009" -- not available here as asked. NetZoo runs GIRAFFE with its package defaults ...`；
  - run 判定由 gap 變成 partial_gap，仍然暫停。
- **N03 / N15**（需新欄位）：`"exactly two expression samples" -- not available here as asked. LIONESS-PANDA needs at least 3 samples; the request has 2.`（BONOBO 同理）。這是 full gap，第二意見不會被問，因為沒有 workflow 能接受這個樣本數。
- **N28**（需新欄位）：`"kmin=2 and kmax=9 on exactly six mutation samples" -- not available here as asked. SAMBAR: kmax cannot exceed the number of mutation samples when clustering is enabled.`
- **N26**（需新欄位，兩次重複都是）：`"Run LIONESS-DRAGON" -- not available here as asked. LIONESS-DRAGON writes at most 20,000,000 values ...; 1,000 features and 100 samples give 49,950,000.` run 不再規劃。

反事實注入的數量放在 `request-counts.json`：41 個陳述數量的回合，依新欄位的 description 手動標註。使用者說數量未知的 U 題標成 null；只有特徵數未知的 U06、U12 只填樣本數。注入後，**所有陳述數量的「可做」題都沒有改變**，包括 P06、P10、P13、P18、P20、P24、P25、K06、K10 等。

### 沒有改變的誤承諾與誤拒絕

| 題目 | 原因 |
|---|---|
| K02 | 第 2 回合「use GPU only for OTTER」沒有被讀成請求層級的設定（第 1 回合有讀成 CPU）。欄位已經存在，這是模型行為，要 live 才知道。 |
| N07、N08、N20 | 問的是輸入類型（CONDOR 吃原始表現量、SAMBAR 用 RNA 取代突變、PANDA 只用共表現矩陣）。這不在樣本數、設定、硬體、資料量的方法條件裡，需要另一條規則（見下一步）。 |
| MX18、P05 | 設定在 ask 自己的字裡（見 2b）。 |
| MX15、P17、P18、P06 | 不屬於這兩個缺陷（需外部步驟的串接、呈現問題）。 |

### 較舊的錄音（`replay_all.py`，`.worktrees/*/.netzoo`）

1,729 個不同的檢查中，11 個改變（新舊 schema 都讀得到的部分；另有 1,312 個是 schema 改版前的錄音，讀不進來）：

| 錄音 | 變化 | 與 gold 比較 |
|---|---|---|
| m2a K09、m1b K09 | 「CPU is fine」「just use single precision」是已驗證的 OTTER 設定，不再送條件檢查 | gold 為可做，避免誤判 violates |
| m1a MX04、m1b MX04 | 「run OTTER」available，「on the GPU」獨立列為不可做 | 與 a24b gold 的拆法一致 |
| m1c MX05 | 「fit GIRAFFE」available，「regularisation lambda to 0.5」不可做 | 與 gold 一致 |
| m3 K05、N17、MX12、P08、P13 | 同上（P13 只少送「leave sparsify=false」，run 仍因 H2/H5 未讀而暫停） | |
| m1a P21 | 原本「run BONOBO」整個不可做（誤拒絕）；現在 available，但模型把資料描述「log2」「centred」讀成未註冊設定，所以多了兩列不可做 | 主需求由拒絕變成可做；多出的兩列是誤讀的副作用（當時 schema 還沒有「Not the input data」） |

m1b F6 沒有改變（仍判不可做），這是加上子句邊界條件的原因。

## live m3f（2026-10-15，經使用者同意，候選版本 919817c）

設定：
- 用 round m3 自己的 harness（`run_live_m3f.py` 只把輸出改到這個資料夾）。
- 候選版本是 919817c 的乾淨 clone，`freeze-code.json` 的白名單為空；每個 job 前後都核對 HEAD。
- 模型與 m3 相同：路由用 gpt-4o-mini，能力檢查用 nemotron。每題跑 1 次。
- `collect_m3f.py` 用 m3 的 `collect_session` 驗證擷取：14/14 通過。K10 第 2 回合停在輸入精靈，退出碼 2，m3 的規則接受。

| 題目 | 預期 | m3 | m3f | 模型讀到的請求層級欄位 |
|---|---|---|---|---|
| N03 | 不可做 | GIVEN_IF_INPUT | **不可做**：LIONESS-PANDA needs at least 3 samples; the request has 2（full gap） | samples 2 |
| N15 | 不可做 | GIVEN | **不可做**：BONOBO needs at least 3 samples（full gap） | samples 2 |
| N26 | 不可做 | GIVEN_IF_INPUT | **不可做**：49,950,000 values 超過 20,000,000（full gap，沒有規劃 run） | samples 100、features 1000 |
| N28 | 不可做 | GIVEN | **不可做**：「kmin=2 and kmax=9 on exactly six mutation samples」，kmax 超過樣本數 | kmin、kmax、samples 6 |
| N17 | 不可做 | ASKED | **不可做**：save_pvals requires sparsify | sparsify、save_pvals |
| K05 | 不可做 | GIVEN_IF_INPUT | **沒有改變**（見下方後續修正） | 方法 none；sparsify、save_pvals |
| P08 | 可做 | NOT_GIVEN | **可做**：available from SAMBAR，沒有呼叫條件檢查 | cluster=false |
| MX12 | 可做＋不可做 | NOT_GIVEN×2 | **signed R、TFA 可做；learning rate 不可做**；run 暫停，並說明 GIRAFFE 只涵蓋前兩項 | 未註冊的 learning rate |
| K02 | 不可做 | GIVEN_IF_INPUT | **無法判斷**：能力檢查兩個模型都失敗（見下方） | — |
| K10（守門） | 可做 | — | 可做，run 核准（agrees），停在輸入精靈 | kmin、kmax、samples 6 |
| P06（守門） | 可做 | — | 可做（available from COBRA）；「沒有單一 workflow」的呈現問題仍在，與這次無關 | samples 24、features 600 |
| P13（守門） | 可做 | UNCONFIRMED | 與 m3 相同：可做，但 run 因「H2 and H5」無法帶入而暫停 | samples 7 |
| P24、P25（守門） | 可做 | — | **無法判斷**：能力檢查兩個模型都失敗 | — |

- 能力檢查成功、而且請求陳述數量的 7 個 session，模型都填了新欄位，數字與引文都正確（N03、N15、N26、N28、K10、P06、P13）。守門題沒有因為新欄位被拒。
- 可以判斷的 11 題中，**10 題與重播預測一致**：
  - 7 題照預期改變：N03、N15、N17、N26、N28、P08、MX12；
  - 守門題 K10、P06、P13 維持原判。

  不一致的是 K05：沒有改變。
- **服務錯誤 3/14（K02、P24、P25）**：
  - nemotron 先逾時（72–118 秒），備援 gpt-4o-mini 在 36–51 毫秒內回傳 `OpenAIConnectionError`。
  - 這是網路中斷，不是 schema 問題：同一批其他 11 個 session 的檢查都成功。
  - harness 規定不覆寫既有 job，重跑要用新的 tag。
- 用 919817c 的程式碼離線重播 m3f 的錄音：有檢查的 13 個回合全部重現。

### live 之後的修正（離線驗證，尚未重跑 live）

K05 第 2 回合，模型這次把方法讀成 `none`：BONOBO 只出現在前一個目標裡。兩個設定讀成 `BONOBO.sparsify`／`BONOBO.save_pvals`，引文只有「sparsify」「save_pvals」。這暴露兩個缺口：

1. `request_method_limit` 只在有指定方法時執行。改為沒有指定方法時，由已註冊設定所指的**唯一** workflow 代替；設定指向兩個 workflow 時不判斷。
2. 只有設定名稱的引文，第一次出現在前一個目標的「sparsify=true and save_pvals=true」（這是合法組合）。`verified_method` 取的是第一次出現的位置。改為：
   - 在設定的字後面、同一句內找它陳述的值；
   - 組合不成立時，選出所有事實合起來最短的位置。

驗證：
- m3f 的 K05 重播後是 `"save_pvals=true but set sparsify=false" -- not available here as asked. BONOBO: save_pvals requires sparsify`。
- round m3 的 162 個回合、較舊的 1,729 個檢查、以及 m3f 的其他 13 個檢查都沒有改變。
- 新增測試 `test_m3f_k05_no_method_named_the_settings_name_the_workflow`。

### 若要再跑 live

4 個 session，都用新的 commit：
- K05：驗證後續修正；
- K02、P24、P25：補上這次因網路錯誤無法判斷的部分。

標記建議用 `m3f2`。

## 測試

- 新增 `tests/test_m3_method_fitting.py`（13 個測試，含 live 之後的 K05）。每題都用 round m3 錄下的讀法，以及修正所需的新欄位：
  - N03、N15、N28、K05、N26 的不可做；
  - registry 規則改變時檢查跟著變；
  - 兩個結果時不補數量，數量未知時也不補；
  - 舊錄音沒有新欄位也能讀；
  - P08 不送條件檢查（含 router 層級）；
  - MX12 的拆分；
  - F6 不拆。
- 更新 `tests/test_method_conditions.py` 的兩個 M1 測試，分別覆蓋「與 ask 相連」和「獨立子句」兩種情況（m1a MX04 與 request-method 的測試）。
- 全部測試：`/opt/anaconda3/bin/python -m pytest tests -q` 結果為 3778 passed、51 skipped（基底是 3765 passed，加上 13 個新測試）。

## 重現方式

在 repo 根目錄執行。原始 trace（`session.json`、`events.jsonl`）不在 git 裡，與 round m3 的慣例相同：
- m3 的放在主 checkout 的 `m3-clarification-2026-10-15/live/m3/`，腳本會自動找到；
- m3f 的放在主 checkout 的 `m3-method-fitting-2026-10-15/live/m3f/`，用 `--recordings` 指定。

```sh
git archive 63e98bf scripts workflows AGENTS.md | tar -x -C /tmp/base
REPLAY_CODE_ROOT=/tmp/base python docs/research-log/m3-method-fitting-2026-10-15/replay.py base.json
python docs/research-log/m3-method-fitting-2026-10-15/replay.py new.json
python docs/research-log/m3-method-fitting-2026-10-15/replay.py inject.json --inject docs/research-log/m3-method-fitting-2026-10-15/request-counts.json
python docs/research-log/m3-method-fitting-2026-10-15/compare.py base.json new.json inject.json --out changes.json
python docs/research-log/m3-method-fitting-2026-10-15/collect_m3f.py m3f --dotenv <main checkout>/.env
python docs/research-log/m3-method-fitting-2026-10-15/replay.py m3f.json --recordings docs/research-log/m3-method-fitting-2026-10-15/live/m3f
REPLAY_CODE_ROOT=/tmp/base python docs/research-log/m3-method-fitting-2026-10-15/replay_all.py all-base.json
python docs/research-log/m3-method-fitting-2026-10-15/replay_all.py all-new.json
```

## 下一步（不在這次範圍內）

1. **方法提問的輸入類型**（N07、N08、N20）：請求層級的「使用者要給的輸入」型別，與 registry 的 `accepted_input_modalities`／必要輸入比對。
2. **P05 類誤讀**：方法名稱本身的原理（leave-one-out）被讀成未註冊設定。可考慮在 schema 中把「方法的變體／原理」與「設定」分開。
3. **m1a P21 類誤讀**：資料描述被讀成設定。現在的 schema 已經寫了「Not the input data」，要看 live 是否還會發生。
