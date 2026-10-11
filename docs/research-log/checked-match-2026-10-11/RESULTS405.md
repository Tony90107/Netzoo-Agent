# Log 405 結果：依凍結規則撤回（G1c 不成立），其餘判定全部成立（2026-10-11）

事前凍結：`FREEZE405.md`（`18e1add`）。回合 `m13`：heldout13 30 題 × 2 臂 × 3 次，180 個 session，全部重放與錄製相同；provider 錯誤 0、檢查失敗 0。

## 標註

兩位盲標子代理各標全部 180 個 session／117 項需求。7 個 session 不一致，我逐一複核（理由在 `live/m13-labels-resolved.json`）：KN1 兩個基準 session 的 "CONDOR fits your goal" 定為 GIVEN 並記矛盾；P2 三個 "available from GIRAFFE" 對上卡片 "not a verified match" 比照 Log 404 S114 定 GIVEN＋矛盾；候選 CN3-2 理解段落寫 PUMA、未確認清單卻沒有 PUMA，記矛盾（對候選不利）；基準 P3-1 記矛盾。

## 數字

| 指標 | base | cand |
|---|---:|---:|
| 標註者矛盾 | 13 | 7 |
| 程式偵測的檢查／routing 衝突 | 6 | 1 |
| 正例被說可做 | 66 | 75 |
| FC 誤承諾 | 5 | 2 |
| FR 誤拒絕 | 0 | 0 |
| OM 遺漏 | 3 | 3 |
| CE 對照被說可做 | 12 | 12 |
| 規則發動（正確） | — | 6（6） |

規則發動：CP2-1、CP3-1（CONDOR）、CP4-2（GIRAFFE）、KP1×3（DRAGON），全部與金標準一致。CP2、CP4、KP1 在基準被標 UNCONFIRMED 的 9 次，候選都變成 GIVEN／GIVEN_WITH_STEP。

判定：V1、G1（7 ≤ 0.6×13）、G2、G3、G4（6/6）、G5、A1 成立；**G1c 不成立**（候選剩 1 個程式偵測的衝突）。

## 決定：撤回（`b5b337a` revert `1f52ab1`）

凍結規則是「所有判定成立或無資訊才保留」。G1c 唯一的失敗是候選 CN4-3：routing 驗證失敗，檢查把不支援的「每個 miRNA 對 target 是促進還是抑制」錯誤認可給 DRAGON 與 LIONESS-DRAGON 兩個 workflow；規則只採用單一 workflow，所以沒有發動——這正是應有的保留（發動的話會把錯誤判定升格成 exact）。基準 CN4 三次沒有出現這個衝突是 routing 驗證失敗的隨機性。也就是說，G1c 的定義（候選衝突 = 0）把規則刻意不處理的情況也算進來，是凍結時的設計錯誤；但它在執行前寫死，不在本題組上事後放寬。

## 下一步

若要保留這個規則，需要在新的未見題組上重量，G1c 改為只計「規則條件成立（檢查確認、單一 workflow 涵蓋全部結果）卻仍衝突」的 session，另報其他衝突。heldout13 已見。
