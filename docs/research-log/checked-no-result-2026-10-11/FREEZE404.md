# Log 404 事前凍結：檢查讀不到結果時不確認任何 workflow；blank 判定逐項問第二意見（2026-10-11，執行前寫下）

對應 Log 403 接手報告（`docs/reviews/2026-10-09-netzoo-audit/MIDDAY-TAKEOVER.zh-TW.md`）剩下的 P1：

1. 結果問句被當成方法問題（heldout11 VN5q，3/3 誤承諾）。
2. 混合需求的第二意見只在整題 full gap 才啟動（VC4s-2，core genes 誤拒絕）。
3. 矛盾檢查沒涵蓋所有 renderer（VT2 3 筆：卡片說 CONDOR fits，正文說每個節點只在一個社群）。

## 診斷（錄製資料，未呼叫模型）

- VN5q 與 VT2 根源相同：檢查自己的模型讀完請求、卻沒讀出任何結果（VN5q 歸為 about_methods，VT2 歸為 context），所以 routing 的 workflow 沒有被任何東西驗證，卻被說成 "These all fit"／"fits that result"。n11 候選臂 126 個 session 中，這個狀態剛好 6 個，就是這 6 個失敗，沒有任何正例。
- VC4s-2：core genes 是 blank 判定（沒有理由），typed 屬性 `input_network: regulator_gene` 指向 CONDOR，但 Log 397 的 blank→typed-implied 第二意見只在整題 full gap 時問。若改成逐項並加入 sibling／exact 的 workflow，n11 會多問 13 對，其中 12 對是正確拒絕的 P 題負例；只用 typed-implied，1885 個歷史檢查中只觸發 4 次（VC4s-2，以及 h7 OP4×3，後者在現行 `group_membership` 屬性下會被 `_fitting` 排除）。
- 量測工具錯誤：Log 403 的 `run_heldout11.py` 每一輪都用 `--session`，那只命名 session、不接續，所以 heldout11 的 T 題只量到最後一句，MT 9/9 不是多輪結果。改用 `--resume` 時，CLI 因 trace 已封存而崩潰；修好後，上一輪已用的 token（19,738／30,000）又被帶進新的一輪，routing 因預算不足直接回「LLM router was unavailable」。兩個都是產品錯誤，`332af36` 一併修正：封存的 run 由新 run 接續，新的一輪有新的預算（與互動模式相同）。冒煙測試（不在題組內的兩輪對話）確認第二輪有呼叫模型。

## 不在本候選內（已知、另案）

冒煙測試另外看到：第二輪「We also need it adjusted for the covariates.」檢查判定 COBRA，routing 卻 exact 選 SAMBAR，回覆同時說「available from COBRA」與「Selected path: SAMBAR … fits」。錄製資料中，檢查已確認且有結果、routing exact 的 408 個 turn，有 16 個的 exact workflow 不在檢查認可的 workflow 內（h1 HC9、h6 NP1、f10 SC4、n11 VT1-2 等），對錯依題而定，需要逐項仲裁，留待下一輪。

## 候選與基準

- 基準 `base`：`2eee5e3`（上線版）＋ `332af36` 的 resume 修正（cherry-pick 成 `263a9bb`），`.worktrees/netzoo-p1-base`。
- 候選 `cand`：`332af36`（＝ `7d9b023` 候選＋同一個 resume 修正），`.worktrees/netzoo-p1-cand`。
- 兩臂只差 `7d9b023`。單元測試 3503 passed、35 skipped。

| 部分 | 內容 |
|---|---|
| 1 | 檢查自己的模型讀完、沒讀出任何結果（且方法問題沒點名已登錄 workflow）時，routing 的 workflow 以「未確認」列出（沿用 Log 403 B），不說 fit／selected，卡片沒有 confirm／plan，下一輪不能直接接續 |
| 2 | 非整題 gap 時，blank 的 not_available 結果也依自己的 typed 屬性問第二意見（Log 397 規則逐項套用；不問 sibling、不問已引用 near miss 的） |

## 部分 1 的確定性證據（凍結前已量）

以 `2eee5e3` 為基準重放全部錄製（未呼叫模型）：現行檢查契約錄的 211 個 session 中，改變的只有 VN5q×3、VT2×3；舊契約（沒有 `asked_as`）錄的臂改變較多（ve base 33/210、ce 143/2310），其中有正例問句——代表若模型仍把正例問句歸成方法問題，正例會變成「未確認」。這是本輪 QP、M 題要量的成本。

## 題組

`heldout12.json`，34 題、38 項需求（正例 25、負例 13），執行前從未跑過：

- QN 6：不支援的結果，以「有沒有方法能／哪個方法…」的機制問句問（VN5q 型）。
- QP 6：同句型，結果支援。
- K 6：兩輪，第二輪只加限制或修正（KN 3 負例、KP 3 正例），第二輪以 `--resume` 接續。
- M 6：方法諮詢正對照，MN 3 題點名已登錄方法、MC 3 題不點名；不列需求，標 `consult`。
- B 6：同一 workflow 的兩個結果，第二個是次要產出（core score、edge p-value、TF activity＋signed matrix、cohort＋per-sample、enrichment、survival）。
- P 4：一個支援、一個不支援。

## 回合

`b12`：routing 用 mini、檢查用 nemotron（`.env`），每題 3 次，兩臂交錯，`run_heldout12.py b12 3`（5 平行）。約 240 個 turn；nemotron 約 300–400 次（含第二意見），低於每日 1000。

## 標註（盲標）

與 Log 403 相同：每個 session 兩個獨立子代理各標一次，看不到臂別與金標準（`LABELING.md`，M 題另標 `consult`：EXPLAINED／LISTED_ONLY／REFUSED／OTHER）。不一致的由我（Claude）逐一複核定案並保存理由。

## 指標（每項需求 × 每個 session；重複抽樣不當成獨立題目）

- **FC 誤承諾**：負例標 GIVEN、GIVEN_WITH_STEP、GIVEN_IF_INPUT。
- **FR 誤拒絕**：正例標 NOT_GIVEN（PARTLY 另報為軟拒絕）。
- **SR 正例未給**：正例標 UNCONFIRMED、NOT_GIVEN、PARTLY、OMITTED 之一。
- **OM 遺漏**：OMITTED。
- **CL 諮詢未回答**：M 題標 LISTED_ONLY 或 REFUSED。
- **CS 矛盾**：程式偵測（檢查沒確認任何東西——無法執行、只有備援、第二意見欠著、或讀不到結果——正文／卡片仍出現 fit／selected／recommended 字樣或 badge；或可做的 reading 被說成沒有 workflow）＋標註者 contradiction。
- **SO2 範圍**：候選中部分 2 的第二意見實際發動的 session 數與答案（從 trace 的 `routing.capability_second_opinion` 事件，且發動前檢查不是 full gap）。

## 判定

| 判定 | 條件 |
|---|---|
| V1 | 每臂 provider 錯誤或逾時 ≤ 10 個 session；檢查沒成功的 no_tool session ≤ 10；兩臂 102 個 session 齊全；重放與錄製相同（不成立則作廢重跑） |
| 1-G1 | QN＋KN 負例的 FC：cand ≤ 0.5 × base。base FC < 4 時此判定「無資訊」（本題組沒重現 base 的失敗），不計成立或不成立 |
| 1-G2 | QP＋KP 正例的 SR：cand ≤ base + 2 |
| 1-G3 | M 題 CL：cand ≤ base + 1，且 MN（點名方法）CL：cand ≤ base |
| 1-G4 | CS：cand 程式偵測 0；標註者 contradiction：cand ≤ base |
| 2-G1 | B 題正例的 FR＋軟拒絕（NOT_GIVEN、PARTLY）：cand ≤ base |
| 2-G2 | P 題負例的 FC：cand ≤ base |
| A-G1 | 全部正例 FR：cand ≤ base + 2；全部 OM：cand ≤ base + 2 |

## 保留規則（逐部分）

- **部分 1**：1-G2、1-G3、1-G4、A-G1 成立，且 1-G1 成立或無資訊。
- **部分 2**：2-G1、2-G2、A-G1 成立。SO2 為 0 時照實報告「本輪沒有發動」，保留只依據不造成傷害與錄製證據。
- 某部分不成立只撤回該部分；撤回後不在本題組上重量（heldout12 已見）。

## 事前預測

- 1-G1：base 在 QN（尤其 QN1、QN6 這類「models how X depends on Y」）可能重現 VN5q；若檢查已能把多數 QN 讀成結果，base FC 可能 < 4，1-G1 無資訊。
- 1-G2 風險：QP 問句若被歸成方法問題，候選會給「未確認」，SR 上升。
- 1-G3：MN 三題點名方法，部分 1 不影響；MC 三題可能因 routing 有候選且讀不到結果而變成 LISTED_ONLY——這是部分 1 最可能的代價。
- K 題首次真正接續：檢查只讀本輪文字，KN 第二輪可能仍讀不到結果；部分 1 會把它變成未確認，而不是 fit。
- 部分 2 可能很少發動（n11 只有 1 次）。
