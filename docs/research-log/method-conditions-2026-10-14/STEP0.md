# M1 Step 0：方法、參數與資料條件的既有規則盤點（2026-10-14，只讀）

交接計畫：`output/handoff/2026-10-14_下一個session交接計畫.md` §2。基準版本 6c8c79f；錄製資料取自 `.worktrees/netzoo-final-live`（a24b，3529927）。

## 1. 既有規則來源

| 條件 | 位置 | 形式 | 內容 |
|---|---|---|---|
| 已註冊的方法 | `workflow_registry.ACTION_DEFINITIONS`（`run=True`）；`workflows/*.yaml` | 常數 | 13 個：PANDA、PUMA、LIONESS-PANDA、LIONESS-PUMA、LIONESS-COEXPRESSION、LIONESS-DRAGON、DRAGON、OTTER、GIRAFFE、BONOBO、COBRA、CONDOR、SAMBAR。變體只有 `LIONESS-X`，且只有 X ∈ {PANDA, PUMA, DRAGON, COEXPRESSION}。 |
| 控制項（名稱、型別、範圍） | `workflow_registry.WORKFLOW_CONTROLS`（2217 行） | 常數；`policy._validate_controls` 檢查 yaml 與程式一致 | PANDA：with_header。CONDOR：prefix。SAMBAR：norm_patient、kmin≥2、kmax≥2、gmt_msigdb、subset_cancer_genes、distance、linkage、cluster。DRAGON：output_format、lambda1/lambda2 ∈ [0,1]。LIONESS-DRAGON：lambda1/lambda2 ∈ [0,1]。OTTER：output_format、computing、precision、lam ∈ [0,1]、gamma≥0、iterations≥1、eta≥0、bexp≥0。BONOBO：11 個（含 bonobo_confidence ∈ [0,1]、delta ∈ [0,1]）。**PUMA、LIONESS-PANDA、LIONESS-PUMA、LIONESS-COEXPRESSION、GIRAFFE、COBRA：沒有控制項。** |
| 實際傳給執行器的欄位 | `ActionDefinition.executor_fields`（1314 行起） | 常數 | 13 個 workflow 的控制項**全部**都在 executor_fields 中。「套件支援但 agent 沒接通」的參數（例如 GIRAFFE 的 lambda、OTTER 的 L1）在程式中沒有記錄，只寫在 yaml 說明文字（giraffe.yaml:38、otter.yaml:112）。因此判定只能是「不在控制項中 → 沒有接通」，無法區分套件是否支援。 |
| 執行環境限制 | `runtime_constraints._CONSTRAINTS` | 常數 | 只有一項：OTTER computing=gpu 不可用（改用 cpu）。 |
| 最少樣本數 | 見下表 | **多數是函式內的數字，不是常數** | — |
| 資料量上限 | `data/lioness_dragon.py:28` `LIONESS_DRAGON_MAX_VALUES = 20_000_000`；`lioness_dragon_size(n, f) = f(f-1)/2 × n` | 常數 | 只有 LIONESS-DRAGON 有上限。 |
| 層數與樣本配對 | `data/dragon.py` `load_and_align_dragon_layers`；能力表 `layers`、`samples_matched` 條件（Log 412） | 已有型別判定 | DRAGON／LIONESS-DRAGON 恰好兩層、樣本 ID 完全相同。已由既有型別屬性處理，K02 的失敗屬於多輪問題（M2）。 |
| 跨控制項規則 | `execution.py:750`、`execution_lioness_dragon.py:49`（lambda1、lambda2 必須一起給）；`data/sambar.py:83`（kmax ≥ kmin）、`:145`（分群時 kmax ≤ 樣本數）；BONOBO delta 在 sparsify 時須 < 1/3（控制項說明，Log 224） | 函式內 | 不在 7 個失敗中；列為後續項目。 |

最少樣本數（硬性拒絕者）：

| workflow | 最少 | 位置 |
|---|---|---|
| LIONESS-PANDA、LIONESS-PUMA、LIONESS-COEXPRESSION | 3 | `data/preflight.py:93`、`execution.py:333`、`data/bundles.py:217, 265`（四處各寫一次 `3`） |
| LIONESS-DRAGON | 3 | `data/lioness_dragon.py:26` `LIONESS_DRAGON_MIN_SAMPLES`（唯一的具名常數） |
| BONOBO | 3 | `data/bonobo.py:196` |
| DRAGON | 3（每層） | `data/dragon.py:73` |
| COBRA | 2，且基因數須多於樣本數 | `data/cobra.py:84, 86` |
| GIRAFFE | 2 | `data/giraffe.py:121` |
| OTTER（給表現量時） | 2 | `data/otter.py:126` |
| PANDA、PUMA | 無硬性下限（少於 2 只有警告） | `data/tables.py:366` |

## 2. 七個失敗：錄製的能力檢查讀到了什麼

| 題目 | 錄製的讀取（a24b） | 為何沒被擋下 | 對應的既有規則 |
|---|---|---|---|
| N11 OTTER 加 L1 0.1（run） | ask 引文包含整句；`other_requirements` 有 how_computed「with an L1 sparsity penalty of 0.1 …」 | `stated_requirements` 丟掉與 ask 同句的條件（Log 414 前置規則，為了避免 PC4 的誤判），所以條件檢查沒跑 | OTTER 控制項沒有 L1 |
| MX05 GIRAFFE lambda=0.5 | 第 1 次：ask 引文包含整句；第 2 次：lambda 那段歸為 context。兩次都有 how_computed | 同上 | GIRAFFE 沒有任何控制項 |
| N36 指定 TIGER | ask「infer TF activities」→ GIRAFFE；「with the TIGER Bayesian model specifically」重讀後仍未讀到 | 沒有「指定方法」這個型別欄位 | 13 個已註冊方法不含 TIGER |
| N12 LIONESS-OTTER | 模型正確引用 `otter.no_per_sample`，判為 full gap；**第二意見把 LIONESS-PANDA 判為 all**，回覆變成「available from LIONESS-PANDA」 | 第二意見把替代方法當成照原要求做到 | 沒有註冊 LIONESS-OTTER |
| N35 PUMA 用 miRNA 表現量 | ask「Build a PUMA network」；how_computed「miRNA-gene edge weights are driven by … miRNA expression levels」 | 同 N11（同句被丟掉）；能力表已有 near miss `puma.no_mirna_expression_use`，但這次沒被引用，且 near miss 從不決定判定 | PUMA 的輸入不含 miRNA 表現量 |
| N13 只有 2 個樣本 | 「exactly two RNA-seq samples」歸為 `which_data`（從不檢查） | 沒有樣本數欄位 | LIONESS／BONOBO 至少 3 |
| N22 LIONESS-DRAGON 20,000＋800 × 300（run） | 「all 20,000 genes and 800 proteins」「our 300 patients」歸為 context | 沒有特徵數與樣本數欄位 | 20,800×20,799/2×300 ≈ 6.5×10¹⁰，超過 2×10⁷ |

配對正例在 a24b 的結果：K06、P19 為 GIVEN_IF_INPUT；P20 兩項都是 GIVEN；MX18 第 1 項 GIVEN；P09 為 UNCONFIRMED（備援模型讀取，與 M1 無關）。

## 3. 結論

- 7 項中有 6 項（N11、MX05、N36、N12、N13、N22）可以用計畫的四個型別欄位（方法名、參數、樣本數、特徵數）加上既有常數判定。
- **N35 不在這四個欄位中**：它不是參數、方法名或數量，而是「結果要依據哪種資料」。**使用者決定（2026-10-14）：移到 M2**，與同一句中被丟掉的 how_computed 條件（條件歸屬）一起處理；M1 的判準改為 6 類。
- Step 1 要「只從既有常數組出」，但 LIONESS、BONOBO、DRAGON、COBRA、GIRAFFE、OTTER 的最少樣本數都是函式內的數字。需要先把它們改成具名常數，原檢查改讀常數，行為不變。
