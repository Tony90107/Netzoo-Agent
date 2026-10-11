# Log 410 事前凍結：追問時的條件與接續的 session（2026-10-12，執行前寫下）

承接 Log 409 架構點 2（每輪單獨判斷）。實測後修正為兩件事：

- **2a**：`--resume` 與桌面版重開的 session 沒有還原追問上下文，第一句被當成全新請求單獨判斷。量測工具（`--resume --task`）一直走這條路；heldout15 KN1 的 SAMBAR 就出在這裡。
- **2b**：互動路徑的回覆解析器遇到「補充或更正條件」的回覆時，在 needs_detail 與 follow_up 之間擺盪（gpt-4o-mini 信心 0.75–0.85，門檻 0.80），或判成 new_goal，於是上一輪請求遺失。

## 候選與基準

- 基準 `base`：`bc49ba3`（上線版，含 Log 409 第 1 步），`.worktrees/netzoo-mt-base`。
- 候選 `cand`：`9f8232b`，`.worktrees/netzoo-mt-cand`。改動：
  - 2a：bootstrap 保留接續 session 的最後一輪；machine 重建 next prompt 與 follow-up context，`--task` 的第一句改經解析器。
  - 2b：新增回覆類型 `adds_condition`，處理方式等同 follow_up。
- 單元測試全過；`test_resume_follow_up.py`、`test_reply_resolution.py` 新增 6 個測試。

## 預先量測（凍結前已做，只呼叫 mini，未標註）

`resolver_ab.py`，24 句回覆 × 3 次。這組題已被看過，不是 held-out：

| 回覆類型 | base | cand |
|---|---|---|
| 補充／更正條件（10 句） | 7 句 follow_up、1 句 needs_detail、2 句 new_goal | 10 句全部 follow_up |
| 道謝類 5、新目標 3、提問 3、接受 2、返回 1 | 全部正確 | 全部正確 |

## 題組

`heldout16.json`，20 題兩輪對話，執行前從未跑過；措辭都不在預先量測的題庫裡：

| 族 | 題數 | 第二輪的作用 | 金標準 |
|---|---:|---|---|
| NC | 8 | 補充條件後，目標變成做不到 | 負例 |
| PC | 6 | 補充條件後，目標仍可做 | 正例 |
| QS | 1 | 提問 | 正例 |
| QN | 1 | 提問 | 負例 |
| GS | 1 | 另起新目標 | 正例 |
| GN | 1 | 另起新目標 | 負例 |
| AK | 2 | 只是道謝，沒有需求；系統要求補充細節才算對 | — |

## 回合（受 nemotron 每日免費額度限制，今日已用 803 次）

`f16`：
- `cand` 每題 2 次，走 `--session` 開第一輪、`--resume --task` 接第二輪；有了 2a，這等同互動路徑。
- `base` 每題 1 次，走互動路徑（stdin 依序送兩輪），也就是現在產品的實際行為。

共 60 個 session，`run_heldout16.py f16`。若任一臂的檢查改由備援 mini 執行的 session 超過 3 個，該批於 08:00 額度重置後重跑。

## 標註（單人盲標＋我抽查）

- 一個盲標子代理標每個 session 第二輪的回覆，看得到兩輪原文，標籤與 `LABELING.md` 相同。
- AK 由程式判斷：第二輪沒有跑新的回合，而是要求補充細節。
- 我複核每個誤判、每個矛盾，以及兩臂結果不同的題目。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 60 個 session 齊全；provider 錯誤 ≤ 3；每臂備援 ≤ 3 |
| G1 | 負例誤承諾率（含 PARTLY）：cand ≤ base |
| G2 | 正例誤拒絕率：cand ≤ base＋10 個百分點 |
| G3 | AK：cand 4 次全部要求補充細節，沒有任何回覆說某個 workflow 適合 |
| G4 | 2a 生效：cand 的 NC／PC／QS／QN 第二輪，存下的使用者訊息全部以 "Previous NetZoo goal:" 開頭 |

全部成立才保留；否則撤回，不在本題組上重量。另報：兩臂負例明確拒絕率、正例明確承諾率、矛盾數。

## 事前預測與風險

- 收益：base 互動路徑會把一部分條件追問判成「請補充細節」（ASKED）或新目標；cand 會把條件和上一輪一起讀。
- 風險：一起讀之後，檢查可能只認上一輪的目標、忽略新條件，因而誤承諾。探針中 r14-KN2「其實是 40 個 single nuclei」合併後仍推薦 PANDA。這正是 G1 要把關的。
