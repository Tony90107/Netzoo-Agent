# Log 403 事前凍結：每項需求一個判定、問句也檢查、結果形式、未確認不承諾（2026-10-10，執行前寫下）

對應使用者 2026-10-10 交辦的修復清單 A1–A6（`docs/reviews/2026-10-09-netzoo-audit/REPAIR-PLAN.zh-TW.md`）。

## 候選與基準

- 基準 `base`：上線版本 `8e6f2a9`，放在 `.worktrees/netzoo-verdict-base`（detached、乾淨）。
- 候選 `cand`：`c6e8c77`，放在 `.worktrees/netzoo-verdict-cand`（detached、乾淨）。兩臂都不含另一個 session 尚未提交的 `extraction.py` 改動。
- 單元測試：候選 3465 passed、35 skipped（主工作樹）；候選 worktree 另跑一次，結果記在結果段落。

候選分成三部分，每部分有自己的判定（見下方「保留規則」）：

| 部分 | 對應清單 | 內容 |
|---|---|---|
| A | A4、卡片 | per-reading 回覆與 reading 卡片讀能力檢查對同一段文字的判定（SC1）；方法超過卡片容量時只略過方法題，不再整張卡消失 |
| B | A6、A5 | 檢查什麼都沒確認時（無法執行、只有備援、第二意見欠著卻沒回答），routing 的 workflow 以「未確認」清單呈現，不說 fit／selected／recommended；檢查之後的讀取呼叫共用檢查的額外 token；詞表後備不再對已點名的資料說「你沒有提到」 |
| C | A2、A3、A5 | 以問句問的結果也是需求（`asked_as`）；結果形式（重疊成員、時間動態、空間鄰點，取自 Log 402）；第二意見可答 part（部分可做）；routing 平手也問第二意見 |

## 部分 A 的確定性證據（已在凍結前量完）

離線重放 2,310 個已錄 session（h1–h9、f10、o10；不呼叫模型），比較 `8e6f2a9` 與只含部分 A 的程式碼：

- 回覆改變的只有 f10 SC1 的 3 個 session（那 3 個正是 Log 402 G2 的假缺口），卡片改變的也只有這 3 個。
- 卡片建立失敗：21 → 0（都是 11–13 個方法平手）。
- 修正後回歸測試：`tests/test_requirement_verdicts.py` 以錄下的 3 個 SC1 決策固定重放。

## 題組

`heldout11.json`，42 題，凍結前從未跑過。每題列出需求與金標準（supported、with_step、needs_input、not_supported）：

- C 支援 12（其中 VC1–VC4 各有陳述句／問句兩版）、N 近似 10（多數與 C 題只差一個必要條件，見 `pair`；VN1、VN2 也有兩版）、U 不支援 5、P 部分 5、M 缺資料 4、A 歧義 3、T 多輪修正 3（以最後一輪為準）。

## 回合

- **n11（一般）**：routing 用 mini，檢查用 nemotron（`.env`）。每題 3 次，兩臂交錯，`run_heldout11.py n11 3`。
- **s11（模擬斷線）**：`OUTAGE=1`，檢查模型設成不存在的 ID（Log 401 的作法），不用 nemotron 額度。每題 2 次，`run_heldout11.py s11 2`。

## 標註（盲標）

每個 session 交給兩個獨立子代理各標一次（不分半），看不到臂別與金標準，只看請求、需求文字清單、完整回覆與卡片（卡片以該臂程式碼從錄下的決策重建）。每項需求標成以下一種：

`GIVEN`（說有 workflow 直接給）、`GIVEN_WITH_STEP`（workflow 輸出加 NetZoo 外的步驟）、`GIVEN_IF_INPUT`（說可做，但缺某個輸入，問或說明）、`PARTLY`（說部分可做）、`NOT_GIVEN`（說沒有登錄的 workflow 給）、`UNCONFIRMED`（說無法確認）、`ASKED`（只反問、沒有判定）、`OMITTED`（沒提到）。

每個 session 另標：`contradiction`（回覆／卡片對同一需求前後矛盾：是／否＋引文）；A 題另標 `ambiguity`（OPTIONS／DISCRIMINATING_QUESTION／VAGUE_QUESTION／SINGLE／REFUSED）。

兩位標註者不一致的需求，由我（Claude）逐一複核後定案，並列出清單。使用者無法人工標註，這一步由我代行並記錄。

## 指標（每項需求 × 每個 session；重複抽樣不當成獨立題目，另報按題的多數結果）

- 正例需求：金標準 supported、with_step、needs_input；負例：not_supported。
- **FC 誤承諾**：負例被標 GIVEN、GIVEN_WITH_STEP 或 GIVEN_IF_INPUT。PARTLY 另報為「軟承諾」。
- **FR 誤拒絕**：正例被標 NOT_GIVEN。正例被標 PARTLY 另報為「軟拒絕」。
- **OM 遺漏**：OMITTED。**UC 未確認**：UNCONFIRMED。**AK 反問**：ASKED。
- **PC 部分完整**：P 題 session 中，正例都是 GIVEN／GIVEN_WITH_STEP／GIVEN_IF_INPUT，且負例都是 NOT_GIVEN。
- **TW 問句／陳述一致**：同 rep 的兩版，每項需求的判定類別（正／負／其他）都相同的比例。
- **MT 多輪**：T 題最後一輪的判定類別等於金標準類別。
- **CS 矛盾**：程式偵測（理解段落說可做、正文說沒有 workflow；或檢查未確認時正文／卡片仍出現 "Selected path"、"These all fit"、"fits that result"、Recommended／Best match）＋標註者的 contradiction。

## 判定

**n11（一般）**

| 判定 | 條件 |
|---|---|
| N-V1 | 每臂 provider 錯誤或逾時 ≤ 10；檢查沒成功的 no_tool session ≤ 10（超過則作廢重跑） |
| N-G1 | FC 次數：cand ≤ 0.6 × base |
| N-G2 | FR 次數：cand ≤ base + 2 |
| N-G3 | OM 次數：cand ≤ base + 2 |
| N-G4 | PC：cand ≥ base |
| N-G5 | TW：cand ≥ base，且 cand ≥ 0.80 |
| N-G6 | AK 次數（C、N、U、P 題）：cand ≤ base + 3 |
| N-G7 | M 題的 NOT_GIVEN：cand ≤ base |
| N-G8 | CS：cand 程式偵測 0；標註者 contradiction cand ≤ base |
| N-G9 | MT：cand ≥ base |

**s11（模擬斷線）**

| 判定 | 條件 |
|---|---|
| S-G1 | cand 中檢查未確認、回覆或卡片仍把 workflow 說成已確認答案（程式偵測）：0 |
| S-G2 | FR 次數：cand ≤ base + 2 |
| S-G3 | FC 次數：cand ≤ base |
| S-G4 | cand 的 no_tool session 都有檢查（provisional）或「無法檢查」說明：100% |

## 保留規則（逐部分）

- **A**：確定性證據已成立；另需 N-G8 成立。
- **B**：S-G1–S-G4 與 N-G2、N-G7 成立。
- **C**：N-G1–N-G6、N-G9 成立。
- 某部分不成立就只撤回那部分。若 C 撤回而 B 保留，B 的 s11 在不含 C 的程式碼上重跑一次（只用 mini）再定案。

## 額度

n11 約 270 個 turn，nemotron 約 300–350 次；今天 Log 402 已用約 370 次，合計低於每日 1000。若中途碰到上限，N-V1 會擋下，作廢的 pair 隔天 08:00 後重跑。s11 不用 nemotron。

## 事前預測

- C：VN1、VN5、VN6（形式）與 VU2、VU4（問句）最可能從 FAB 轉為 HONEST；VN7（每樣本正負號）最難，兩臂可能都錯。
- TW：base 的問句版大多沒被檢查，預期 base 不一致較多。
- 風險：問句被讀成需求後，C 問句題若檢查給空白判定、routing 沒有 exact，第二意見會問平手的 workflow；若仍判定空白，FR 會上升（N-G2 會擋）。
