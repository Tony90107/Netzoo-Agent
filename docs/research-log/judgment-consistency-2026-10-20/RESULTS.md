# 判斷一致性修復：數量疑問只判斷一次

日期：2026-10-20。開發位置：`.worktrees/netzoo-closed-menu`，分支 `closed-menu-phase0`。起點：`cf31e7f3c6bf48f96553601eb292c66e272780f5`。本輪有修改程式；沒有新增模型、改模型讀取 schema／prompt、增加輸入字詞表、呼叫付費模型或執行科學 workflow。API 費用 $0。

## 改好了什麼

修復範圍是盤點中的 **K6 數量不確定性雙入口、K8 數量歸屬**，以及這些判斷進入追問、回覆與執行授權的接縫。

1. 專用數量候選與通用 unknown_facts 讀到**重疊原文、完整相同的候選集合**時，先彙整再判斷。專用候選提供數量的種類；通用欄位不再另外把同組蛋白數當樣本數。採用與擱置的 fact ID 都保存在 `count_reading_precedence`。
2. 去掉的是重複決策，疑問及其作用範圍仍保留。原本被明確疑問取代的舊數量，不能因去重而恢復成確定值。候選的範圍隨共用紀錄一起編譯；多個結果的數量疑問可以保持各自歸屬。
3. 明確離散的樣本候選，無論寫在哪個欄位，程式算出的決定性追問都標成 `by_code`。事實模型沒有留下自己的問題時，不得因此把程式算出的追問解除。初讀與 second opinion 共用這個規則。
4. 已驗證的結果範圍以文字包含關係核對，容忍大小寫與空白，**不再用 70% 詞語相似度判斷歸屬**。例如 confirmed cohort 與 archive cohort 不能只因句子幾乎相同就共用一個疑問。

沒有重寫 K1～K10 所有模組；模型重填欄位的數量也沒有減少。這是把已確認的一類重複判斷收斂，並保護它的判定結果。

## 能做、不能做、需要追問

以下是使用相同 LIONESS-PANDA 最低 3 個樣本規格的回歸案例。測試固定模型讀取，並模擬後段事實模型成功完成、但沒有留下問題：

| 使用者尚未確認的樣本數 | 程式對候選的核對 | 最終核心判定 |
|---|---|---|
| 8 或 15 | 兩者均可行 | DO，不追問此數量 |
| 1 或 2 | 兩者均不可行 | DECLINE，不以追問拖延否決 |
| 2 或 10 | 2 不可行、10 可行 | ASK，保留兩個結果並等待回答 |

同一候選寫在 `unknown_facts` 或同時寫在 `count_alternatives`，以上判定相同。ASK 的實際回覆使用確定性模板，並清除 `action`、`should_execute`、`execution_requested`，回答前不選 workflow。

DO 表示能力判定可行；原有的使用者執行授權、必要檔案、輸入驗證、Plan Evaluator 與 Executor 閘門仍必須通過。修復沒有放寬這些條件。

## 根因與來源

| 根因／責任 | 修改位置 |
|---|---|
| 同組候選走兩次反事實核對；錯誤種類移除正確病人數 | [FactRecord.read_doubts](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_facts.py:275>)、[reconcile_unknown_counts](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_facts.py:281>) |
| 同一數量因欄位不同而被當作可移除的 legacy wait | [fact_update](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/needed_facts.py:314>)；初讀與 `wait_on_asked` 都引用它 |
| 歸屬使用模糊引文恢復，將相近 cohort 混合 | [scope_applies](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/request_spans.py:50>) |
| 去重後仍需保留舊數量被擱置，以及候選的作用範圍 | [weigh_sample_doubts](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/count_alternatives.py:117>)、[count_update](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/scripts/netzoo_agent_core/interpretation/count_alternatives.py:78>) |

來源的圖索引 generation 為 `2026-10-16T10:16:00Z`，排除整個工作樹。已先查圖與 coverage，再以限定原始碼補查；詳 `graph-coverage.json`。未宣稱圖已索引本輪修改。

## 測試結果

- 新增 [test_count_consistency.py](</Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-closed-menu/tests/test_count_consistency.py>)：19 個回歸案例。先確認 C45、追問被清掉、相似結果誤配及去重恢復舊數量等失敗，再修復。
- 相關數量、未知事實、共用紀錄、合約、模組邊界：**107 passed**，見 `focused-test.log`。
- 全套：**4749 passed、51 skipped、0 failed**，見 `full-test.log`。跳過的是 35 個需啟用 Docker 的數值／SAMBAR 容器檢查，以及 16 個沒有本機 Executor 的遠端 action 參數案例。跳過項目不算通過。
- 首次全套有 2 個檢查未過：主檔新增一行超過 1000 行，以及新增內部衝突類型造成 schema pin 變動。已將疑問讀取整合在共用紀錄入口，沒有放寬長度上限；schema 差異驗證只有 `FactConflict.reason` 新增值，才更新 TaskDecision pin。其他 11 個 schema pin 不變。初次輸出保留在 `full-test-initial.log`；精確差異見 `schema-change.json`。
- `git diff --check` 通過；固定重放輸出可重現，來源及輸入雜湊吻合，見 `verification.json`。

## 979 份離線重放

固定原始模型輸出，修復前後各重建 **979 份能力核對**，無解析失敗。另固定每個 archived session 的 routing、fact-agent 回答及 run verdict，僅替換 check，再重放既有 fact-wait 清理、核心決策及 ASK 模板：

| 指標 | 結果 |
|---|---:|
| 核對結果有改變 | 21 / 979 |
| 核心判定類別改變 | 2 / 979，均為 DO → ASK |
| 核心類別或 ASK 回覆改變 | 9 / 979 |
| 原 h1～h4 金標可重放回合 | 189，核心類別全部維持 |
| 無法解析／缺少 session | 0 |

其中：

- `cj-g4o1-C43-1`、`cj-g4o2-C43-1`：使用者不知道是 24 位病人的矩陣，還是平均成 2 欄的版本。程式已能算出最低樣本數差異；本輪避免該疑問被 fact agent 清掉，DO 改 ASK，三個執行授權欄位均被清除。
- `cj-g4o1-C45-1`、`cj-g4o2-C45-1`：保留已讀到的 50 位病人，將 200／2000 的疑問放回特徵數；核心仍 ASK，但改由程式提供正確類別的兩個候選結果與資料量限制。
- 其餘改變主要為去除重複未知事實、保留 `by_code` 或追問模板／出處改變。逐項前後核心、問題文字、授權及來源均保存在 `changed.json`；完整核心類別見 `core-replay.json`。

**這不是新的盲測分數，也不是整個 Router／Planner 端到端準確率。** h1～h4 的 189 個核心類別未變，不代表原有 35 個非 correct 評分都修好了；新規則是否改善新問題，仍須另以新盲題驗收。本輪沒有呼叫模型重讀，也沒有重跑 second opinion／fact agent。

## 未解決的邊界

- 原始讀取完全漏掉數量、種類讀錯而沒有另一份正確候選、或把大約數量當成使用者不知道，仍可能錯。已知 `cj-p1-C45-1`、H46 屬此類；這輪沒有宣稱修好它們。
- 專用候選欄位是本輪明定的數量種類來源；這項優先權本身不能證明模型語意一定正確。兩個專用候選彼此衝突、沒有有效歸屬，以及更一般的範圍／未限定數量，仍有各自的既有規則，不能由本輪推論已完全收斂。
- 歷史 K10 的 5 個 renderer mismatch 沒有在本輪新增修法；本輪驗證的是數量追問確實走 ASK 回覆及撤銷授權。沒有為了歷史標記任意改動 renderer。

## 重現命令

在工作樹根目錄執行；Python 使用既存依賴，沒有安裝新套件：

```sh
/opt/anaconda3/bin/python3 -m pytest tests/test_count_consistency.py tests/test_count_doubts.py tests/test_count_alternatives.py tests/test_needed_facts.py tests/test_request_facts.py tests/test_contracts_package.py tests/test_agent_module_boundaries.py -q
/opt/anaconda3/bin/python3 -m pytest tests -q -ra
/opt/anaconda3/bin/python3 -I docs/research-log/request-facts-round03-2026-10-20/replay.py checks /private/tmp/netzoo-judgment-after-checks.json
/opt/anaconda3/bin/python3 -I docs/research-log/judgment-consistency-2026-10-20/replay.py
/opt/anaconda3/bin/python3 docs/research-log/judgment-consistency-2026-10-20/verify.py
```

`before-checks.json.gz`、`after-checks.json.gz` 保存本輪固定快照；最後兩個命令比較這些快照。若要驗證後續新的程式修改，必須先重建並更新 after 快照，不能只對舊 fixture 重播。輸入、來源與腳本 SHA 均在 `manifest.json`。

Schema 驗證使用與 pytest 相同的 Python 環境，verify.py 不加 `-I`；隔離環境中的另一個舊版 Pydantic 無法產生部分既有模型的 JSON schema。固定 check 重建與核心重放則使用上述 `-I` 命令。沒有為此修改依賴。
