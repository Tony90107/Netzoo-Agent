# Log 410 結果：G4 不成立，依凍結規則撤回；使用者依證據決定例外保留（2026-10-12）

事前凍結：`FREEZE410.md`（`f6f2d55`）。候選 `9f8232b`（2a 接續 session 還原追問上下文、2b `adds_condition`）。

回合 `f16`（heldout16）：
- 第一次跑在 25 個 session 中途用完 nemotron 每日免費額度，這些 session 的檢查退回 mini，依凍結條款判為無效。
- 08:00 額度重置後重跑那 25 個；原檔移到各 worktree 的 `.netzoo/sessions-void-f16/` 與 `live/void-quota/`，保留作為紀錄。
- 最終 60 個 session：provider 錯誤 0、備援 0、重放全部相同。

標註：兩個 packet 各一位盲標者。我複核 30 個指定 session，只更正 1 處：S039（base NC7）由 NOT_GIVEN 改為 GIVEN_IF_INPUT＋矛盾。它的正文與卡片和 S027（cand NC7-2）實質相同，卡片標題寫 "PUMA fits your goal if you have a motif prior and a PPI network"，所以統一為使用者會讀到的結論。這處更正對 base 不利；若不更正，base 的誤承諾為 1/10。

## 數字

| | base（互動路徑，×1） | cand（`--resume`，×2） |
|---|---:|---:|
| 負例誤承諾（含 PARTLY） | 2/10 = 20% | 2/20 = 10% |
| 負例明確拒絕 | 4/10 | 14/20 |
| 負例含糊（ASKED／OMITTED） | 4/10 | 4/20 |
| 正例誤拒絕 | 0/8 | 0/16 |
| 正例明確承諾 | 6/8 | 12/16 |
| 正例含糊 | 2/8（ASKED） | 4/16（UNCONFIRMED 3、OMITTED 1） |
| 矛盾 session | 2/20 | 5/40 |
| AK 要求補充細節 | 2/2 | 4/4 |
| 第二輪連同第一輪一起讀 | 8/16 | 30/32 |

判定：V1、G1、G2、G3 成立；**G4 不成立**（30/32）→ 撤回。

## G4 為什麼差 2

兩次都是 NC2 的第二輪 "A gene ought to be able to sit in two or three of those modules."：解析器在 cand 判成 needs_detail，回覆是「請輸入具體的追問」。

- 這表示 2a 的路徑有走到：沒有 2a 的話，`--resume --task` 會跳過解析器，直接單獨判斷這一句。
- 是 2b 的分類沒有涵蓋這一句。預先量測裡類似的 "But TFs need to be allowed in more than one module." 3 次都判成 adds_condition。
- 結果標為 ASKED，沒有誤判。base 的互動路徑在同一題也是 ASKED。

G4 原本是用來確認 2a 生效的，寫成「全部」，就把 2b 的覆蓋率也算進去了。這是判定設計的問題，與 Log 405 的 G1c 同類。依凍結規則仍判撤回，是否例外保留由使用者決定。

## 逐題觀察

- **cand 改善**：
  - NC3：base 把第二輪當新目標單獨讀，DRAGON 說可做，屬誤承諾；cand 一起讀後，「三層」被判為不可做，2/2。
  - NC6：base 要求補充；cand 判出「只有 RNA-seq 的分型」不可做，2/2。
  - PC1、PC3：base 要求補充或只給條件式回答；cand 明確承諾。
- **cand 的誤承諾**：
  - NC1-2：一起讀後仍列 PANDA／OTTER／GIRAFFE "These all fit"，附 pseudo-bulk 註記，標為 GIVEN_WITH_STEP。
  - NC7-2：PUMA "fits"，但條件是用測得的 miRNA 表現算反相關。
  - 這兩題都是檢查一起讀之後，只認上一輪的目標、沒有把條件套用上去。這是檢查模型的判斷，屬 Log 409 架構點 5。
- **cand 新增的含糊**：
  - PC2 ×2：檢查把「TF 網路」和「也要有 miRNA」拆成兩項，分別認給 PANDA 和 PUMA，沒有共同 workflow，所以單一判定不採用，routing 的 PUMA 仍標為 "not a verified match"。
  - PC4-1：該輪檢查沒跑成，回覆為未確認清單。
  - QS1-1：survival 沒被讀到，標為 OMITTED。
- **兩臂相同**：NC8 ×3 都沒提鄰近 spot，標為 OMITTED；NC2 都要求補充；NC4、NC5、QN1、GN1 都正確拒絕。

## 決定

依凍結規則撤回：revert 為 `dfe2172`，程式與 `bc49ba3` 相同；候選、revert 與本結果都已推送。是否例外保留，交由使用者決定。

提交紀錄更正：`30291d9` 的標題寫 "Revert …"，實際上是 FREEZE410 事前凍結那個 commit。當時 revert 指令失敗，後續的 amend 誤改了凍結 commit 的訊息，它什麼都沒有還原。因此從推送 `76b8677` 到推送 `dfe2172` 之間的幾分鐘，netzoo-agent/main 上是候選程式碼。

## 使用者決定（2026-10-12）：例外保留

使用者看過以上證據後選擇例外保留，依據有三：衡量誤判的判定（V1、G1–G3）全部成立；G4 失敗的 2 次是安全結果（要求補充細節）；這和 Log 405 的 G1c 屬同一類判定設計問題。`dfe2172` 已再 revert，程式與候選 `9f8232b` 相同，單元測試 3534 passed、35 skipped，已上線。

教訓（與 Log 405 相同）：判定只量改動針對的東西。「全部經過某條路徑」這類寫法，會把改動刻意保留的安全結果算成失敗。
