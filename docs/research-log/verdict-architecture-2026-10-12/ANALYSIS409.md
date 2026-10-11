# Log 409 分析：哪些架構點造成可執行性誤判（2026-10-12）

使用者要求（2026-10-11 深夜）：找出會造成誤判的架構點，並先做「每項需求單一判定」。

資料：已標註的 5 輪一般回合（n11、b12、m13、r14、x15；856 個 session、404 項負例、590 項正例），另報模擬斷線的 s11。腳本 `attribute.py`（歸因）、`arbitration.py`（衝突時誰對），都只讀錄製與標籤，不呼叫模型。

## 判定的流程（`graph/router_invocation.py`、`graph/response.py`）

1. routing（mini）把請求投影到固定的結果詞彙，給出 exact／ambiguous／fallback 與候選 workflow。
2. 檢查（nemotron）逐句讀請求，對每項結果給 sheet 條目（`delivered_by`），必要時重讀（Log 406）與第二意見（Logs 390–407）。
3. 檢查**只在兩種情況改變 routing**：整題都不可做（full gap，清空候選），或 routing 沒有主張且檢查把所有結果都認給同一個 workflow（Log 405 `checked_match`）。其他情況檢查只寫開頭的 "What I understood"。
4. 回覆正文由約 20 個 renderer 依序讀 **routing 的** decision 決定（Selected path、These all fit、Fallback recommendation、卡片、下一步）。
5. routing 與檢查都只讀**最新一則**使用者訊息（`latest_user_task`）。

## 誤判歸因

最近 4 臂（Log 405 之後的程式；310 個 session）：

| 結果 | 數量 | 來源 |
|---|---:|---|
| 誤承諾 | 19 | 檢查自己認可 10；檢查沒讀出需求、routing 的推薦照樣成立 5；沒讀出、也沒推薦 4（r14 KN2 pseudo-bulk 路線，金標準可議） |
| 誤拒絕 | 2 | 檢查拒絕（x15 PL6，第二意見 "part"） |
| 負例含糊 | 16 | 檢查沒讀出、routing 推薦照樣成立 10（兩段式請求的後半、追問）；檢查未確認 3；其他 3 |
| 正例含糊 | 8 | 檢查認可、正文沒照做 6；其他 2 |
| 矛盾 session | 36 | 程式偵測的「理解段落 vs 正文選擇」15；其他 21 |

全部 5 輪：誤承諾 44 = 檢查認可 21＋檢查沒讀出而 routing 推薦成立 19＋其他 4。

## 衝突時誰對（`arbitration.py`）

routing 提供的 workflow 與檢查認可的 workflow **完全不重疊**時，以金標準評：

| routing 狀態 | 檢查對、routing 錯 | routing 對、檢查錯 | 兩邊都錯（負例） | 其他 |
|---|---:|---:|---:|---|
| fallback | 11 | 0 | 0 | |
| exact | 5 | 1 | 1 | 1 兩邊都是金標準 |
| ambiguous | 0 | 0 | 5 | 6 為組合（VM4s：PANDA→CONDOR，兩邊各對一步） |

最近 4 臂：檢查對 7、routing 對 0。

檢查在整個請求裡完全沒讀出結果、routing 卻有推薦時：routing 的推薦含金標準 38 次，負例（任何推薦都錯）36 次。最近 4 臂分別是 5 與 7，全部 7 個負例都是多輪追問（KN1、KN3）。

## 架構點（依造成的誤判排序）

1. **兩個讀者，正文只聽 routing。** 檢查的判定不能決定正文選哪個 workflow。它造成全部的「理解 vs 正文」矛盾，以及「檢查認可、正文沒照做」的含糊；衝突時檢查較常是對的。
2. **每一輪被單獨判斷。** routing 和檢查都只讀最新一句，所以「那些其實是空間 spot」只剩這句，routing 把它投影成 sample distance matrix（SAMBAR）。最近的誤承諾裡，非檢查本身錯的，幾乎都在這裡。CLI 的下一步提示還寫 "the next turn checks it against your original request"，實際沒有這麼做。
3. **沒有判定等於放行。** 檢查沒讀出某段需求時，routing 對那段的推薦仍說 "fits"；這種狀態下 routing 對錯約各半。Log 404 part 1（一律改為未確認）因正例代價撤回，所以要先修第 2 點，讓這種狀態變少。
4. **routing 對結果的解讀跟著被採用的 workflow 走。** Log 405 採用檢查的 workflow 時，正文仍寫 routing 的解讀。例：x15 PS1-1 "Your question asks for a cohort-level TF activity matrix. **LIONESS-PANDA** fits that result and scale"，卡片也一樣。
5. 檢查模型本身的判斷（過度認可、"part" 誤拒）不屬於架構，靠架構無法消除。

## 第 1 步：單一判定（本 Log 的候選）

`interpretation/checked_match.py` 從 Log 405 的規則推廣：

- 檢查已確認，且把所有「可做的結果」都認給同一個 workflow。不可做的結果不再阻擋，仍照常報為不可做。
- 這時，若 routing 沒有主張，或 routing 的主張與該 workflow 完全不重疊，就改由該 workflow 為 match。例外：使用者點名的 workflow、routing 的 workflow 與它有登錄的上下游關係（組合），這兩種情況維持 routing。
- 被採用的 workflow 不產出 routing 解讀的結果或尺度時，丟掉 routing 的解讀，正文與卡片改成描述該 workflow 實際產出的東西（架構點 4）。

第 2 步（多輪追問時檢查讀上一輪請求）會增加模型呼叫，需另跑真實回合。
