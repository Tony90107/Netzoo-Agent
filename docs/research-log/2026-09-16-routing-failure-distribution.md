# 路由失敗分布分析（round18/19/20，297 trials）

不花任何 provider call，只分析已記錄的三輪。三輪的 corpus、policy、model、
repeat 指紋相同，程式碼只在統計方式上不同，所以可以合併看。

## 先推翻兩個先前的說法

**「`missing_evidence:operation` 是主要殘餘」——錯。** 它只佔全部 701 個問題的
5.3%，遠低於 `missing_current_input:expression_matrix`（17.3%）和
`missing_evidence:entity_type`（14.6%）。這個判斷來自一筆手挑的失敗 payload，
不是來自分布。round20 因此是 null result。

**「`entity_type` 問題在調和後不降反升」——也錯。** 23 → 33 → 38 → 30 → 34，
但前兩個數字是同碼兩輪，本身就差 10。整個序列都在噪音裡，沒有訊號。

## 問題計數不等於失敗原因

`diagnostic_details` 記的是 attempt 1 的問題，之後的修復會把多數修掉。
按「出現該問題的 trial 最後有沒有通過」重算：

| 問題 | 出現 | 通過率 |
| --- | --- | --- |
| `missing_current_input:mutation_matrix` | 54 | 75.9% |
| `missing_evidence:artifact_type` | 41 | 46.3% |
| `missing_current_input:expression_matrix` | 106 | 29.2% |
| `missing_evidence:granularity` | 30 | 13.3% |
| `inconsistent_not_applicable_outcome` | 28 | **0%** |
| `conflicting_evidence:entity_type` | 11 | **0%** |
| `artifact_granularity:community_assignment` | 9 | **0%** |

數量最大的那個有 76% 會被救回來，數量小的三個必死。

**而且 attempt 1 完全沒有問題的 trial，通過率只有 45.5%（15/33）。**
證據契約就算修到完美，上限也只有四成五左右。失敗主要不在契約。

## 真正的失敗模式

13 個 case 是 0/9（三輪九次全掛），佔全部失敗的 63%。它們高度集中在三個簽名上：

| 失敗模式 | trial 數 | 佔全部 | 佔失敗 |
| --- | --- | --- | --- |
| A 對已經完整的目標多問一句澄清 | 77 | 25.9% | 41.8% |
| B `input_artifacts` 是空的 | 67 | 22.6% | 36.4% |
| C 只靠 workflow_name 命中，缺語意驗證 | 63 | 21.2% | 34.2% |
| D 該說 unsupported 卻說 ambiguous | 9 | 3.0% | 4.9% |
| E 選錯 workflow | 2 | 0.7% | 1.1% |

（會重疊，一個 trial 可能同時中 A 和 B。）

**A** 的錯誤訊息一字不差都是
`clarification: unnecessary question for a complete scientific goal`，
七個 case 共用：reverse-history-expression、aggregate-tf-activity、
per-sample-coexpression、per-sample-coexpression-bayesian、
aggregate-tf-baseline-misspelled、run-named-tool-finished-then-new-goal、
tfa-factorization-rejects-named-panda。

**B** 是 `input_artifacts: expected [X], got []`。這正是輸出調和想解決的，
但調和是從「有出處的 explicit 證據」回填；模型根本沒產出那筆證據時就無從填起。
而 `missing_current_input` 用的確定性文字證人**知道那個 artifact 在請求裡**，
且 `_required_evidence` 已經把 `confirmed_inputs` 排除在舉證要求之外——
同一個來源已經被信任，用它回填是一致的，不是放寬。

**C** 是 run-named-panda-with-files 和 run-two-named-tools。它們用工作流名稱
正確命中，但 harness 要求語意驗證通過才算數。

## 下一步的優先序

1. **B**：用確定性證人回填 `input_artifacts`。來源已被契約信任，不需要新的授權路徑。
2. **A**：查澄清問題的觸發條件為何在目標已完整時仍然成立。
3. **C**：先釐清這是路由缺陷還是 harness 期望的問題，再決定要不要動。

**不要再用單一失敗案例推論優先序。** 這份分析的起因就是上一次那樣做的代價。
