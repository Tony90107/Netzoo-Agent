# p4b、p4c 兩輪都錯的 6 題：原因、修法與離線驗證（2026-10-16）

## 結論

- 6 題中，spec 範圍內的 3 題已修好並完成離線驗證：C59、C52、C39 的 goal 部分；C10 的「點名兩個 workflow」規則也已加入。
- 用錄製資料重放（不重跑 session），四態成本分數的估計是：p4b 89.6 → **92.2**，p4c 79.0 → **80.8**，兩輪平均 84.3 → **86.5**。
- 仍然錯的有兩類：
  - 等使用者決定的設計變更：C10 的順序、C24、C45。
  - 不在本次範圍的問題：C39 的 fact agent 問錯事實；C52 在 p4c 被條件檢查誤拒。
- 這是重放估計，讀取結果沿用錄製資料，不是實測。全套測試 3,852 個通過。

## 每題的原因與處理

| 題目 | 原因 | 處理 | 重放結果 |
|---|---|---|---|
| C59 | run 的判定把路由推薦的 PUMA 也列進 `workflows`，被算成多給選項 | run 只寫它要跑的 workflow | p0–p4c 共 6 輪全部變對 |
| C52 | 「saved as HDF5」對 `.h5`、`.hdf` 都比不到（原草案寫「兩個都比到」，實際是都沒比到），BONOBO 因此被判不能用自己的預設格式 | enum 控制項加 `value_names`，在 registry 與 YAML 都宣告 `HDF5 → .h5`；loader 檢查每個稱呼都對到允許值 | p3、p4b 變對；p4c 另有一列「log2-transformed and centered」被條件檢查判成 BONOBO 不符，仍為部分拒絕 |
| C39 | goal 讀取把「Can PUMA model the small RNAs …?」判成 `purpose_only`，所以 fact agent 被跳過。原草案說「沒有候選」是錯的：路由其實有給 PUMA | goal 引文恰好點名一個 workflow 時，目標就是該方法，不判 CLARIFY | 兩輪都從 CLARIFY 變 ASK，但問的是「有沒有確定的 miRNA ID 清單」，不是金標的「這些小 RNA 是 miRNA 還是 piRNA」，所以仍算問錯事實 |
| C10 | ① p4b 把「COBRA or CONDOR」讀成 `method_named`；② 兩輪都在研究假設路徑失敗，UNCHECKED 排在 CLARIFY 前面 | ① 點名兩個以上 workflow、讀取為 `method_named` 且沒有結果列時，判 CLARIFY；② 未做（C37 同一順序問題，待使用者決定） | 兩輪都不變，仍為 UNCHECKED |
| C24 | fact agent 把「不知道審稿人要哪種網路」當成要追問的事實，其實是目標不明 | 未做（設計變更：FactProposal 加 `about` 欄位） | — |
| C45 | 讀取只記到 300 個 miRNA，沒記到「200 還是 2,000 個蛋白質」這組候選數量，fact agent 改問資料格式 | 未做（設計變更：由程式算出數量的反事實） | — |

## 改動（不是設計變更，已記入 spec 變更紀錄）

- `method_names.workflows_in`：goal 引文中點名的方法，只認 registry 的拼法（含大小寫）。這些名稱也是動物名，「the panda cohort」不算點名。
- `core_decision.goal_unclear`：
  - 恰好點名一個方法時，不判目標不明。
  - 點名兩個以上、讀取為 `method_named`、而且沒有結果列時，判目標不明。
- `fact_check.fact_candidates`：goal 引文點名的方法排在候選最前面。證據是 p4c 的 C48：只讀到方法問題，判定上也沒有路由動作，所以 fact agent 沒有候選、沒有執行；p3 與 p4b 的 C48 都有執行，而且問對了。
- `core_decision.decide_core`：run 的 `workflows` 是它要跑的 workflow。
- `value_names`：新增在 `WorkflowControlDefinition`、`WorkflowControlSpec` 與 `bonobo.yaml`。`enum_value` 把允許值本身和它的其他稱呼合併比對，只對到一個才算數，所以「HDF5 or CSV」仍視為無法確定。

## 離線驗證

`offline_both_wrong.py`：同一份錄製決策分別交給修正前的程式（`e7f2162b` 的暫時 worktree）和這份程式判定，列出所有改變。

- **基準 6 輪（p0、p1、p2、p3、p4b、p4c，共 336 個 session）**：改變 18 個判定，沒有任何一個從對變錯。
  - C59 ×6、C52 ×2：從錯變對。
  - C41 p1：basis 由 `no_result_read` 改為 `goal_unclear`，仍然正確。
  - C43 ×3：run 只列 LIONESS-PANDA，結果不變（仍是沒先追問就做）。
  - 6 個從 goal_unclear 放行的回合，因為錄製時路由選項已被清掉，要再跑 fact agent 才能定案（見下）。
- **m3 開發集（120 個 session）**：只改變 1 個判定，N26 的 LIONESS-DRAGON run 不再多列 DRAGON。m3 錄製時還沒有 goal 欄位，所以 goal 規則在 m3 上沒有作用。
- **放行的回合**：`offline_released_facts.py` 從 trace 還原路由選項，每個回合呼叫一次 fact agent（gpt-4o-mini，7 次，約 US$0.005），再由 `decide_core` 判定：

| 回合 | 類別 | 修正前 | 修正後 |
|---|---|---|---|
| p3 C27 | 不該做 | CLARIFY（猶豫） | DECLINE（對） |
| p1 C32 | 該做 | CLARIFY（多問） | DO DRAGON（對） |
| p3 C51 | 該做 | CLARIFY（多問） | DO OTTER（對） |
| p2 C51 | 該做 | CLARIFY（多問） | DO，路由列出 11 個 workflow（多給選項，仍錯） |
| p4b C39、p4c C39 | 該追問 | CLARIFY（問錯種類） | ASK，問 miRNA 清單（問錯事實，仍錯） |
| p4c C48 | 該追問 | CLARIFY（問錯種類） | ASK「是不是同一批 58 人」（對） |

- 錄製資料中，goal 引文只點名一個 workflow 的「目標不明」判定共 6 個，金標全都不是「太模糊」。太模糊類的題目，goal 引文點名的都是兩個（C10、C41）。

## 費用

fact agent 7 次呼叫，約 US$0.005；沒有跑完整 session。
