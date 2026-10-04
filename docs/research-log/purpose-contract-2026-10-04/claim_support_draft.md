# `CLAIM_SUPPORT` 草稿（階段 1 回覆文字，待審）

這份是階段 1 要加進 registry 的回覆文字。回覆是英文，所以句子用英文；說明用中文。
每句都標了來源：

- **[R]** 沿用 registry 既有句子（先前的 Log 已查證）
- **[COBRA]** Micheletti, Schlauch, Quackenbush, Ben Guebila. *Higher-order correction of persistent batch effects in correlation networks.* Bioinformatics 40(9): btae531, 2024。論文說可以把變數放進 design matrix，取出「該共變數對應的共表現成分」，做 covariate-specific co-expression；也提到部分成分值會落在 [−1, 1] 之外。
- **[lionessR]** Kuijjer, Hsieh, Quackenbush, Glass. *lionessR: single sample network inference in R.* BMC Cancer 19:1003, 2019。論文用 LIMMA 找兩組之間權重有顯著差異的 LIONESS 邊。
- **[S]** 一般統計推理，不是 NetZoo 特有的說法。

撰寫時序要說清楚：字詞表在讀保留集之前就凍結了（`2dc0773`），但這份文字是在讀過保留集之後才定稿。唯一受影響的地方是因果說明裡那句「前後比較沒有未處理組」：它本來就只適用配對設計，現在明確限定 `design=paired` 才出現。分組設計（例如 knockout）不會說這句。這點會寫進宣告。

---

## 1. 規則

- 回覆只對**已宣告**的格子說話。沒宣告的格子保持沉默，不推論成「做不到」。
- 「做不到」只來自第 3 節的全域說明。
- 鍵是 (workflow, claim, design)。design 可以是 `paired`、`groups`，或 `*`（任何設計，包含未說明）。查找順序：先找 (workflow, claim, design)，找不到再找 (workflow, claim, `*`)。
- v1 不宣告 CONDOR、SAMBAR、DRAGON、LIONESS-DRAGON（照提案）。

## 2. 每個 workflow 的格子

### PANDA／PUMA／OTTER（整體網路）

**`group_difference`, `groups`**：
> Build one network per group on the same genes and priors, then compare edge weights or each regulator's targeting score (out-degree) between the group networks. [R]
> Two aggregate networks give one value per edge per group: they show where the groups differ, but give no per-sample spread to test it. For a statistical test, use the per-sample version and test between the groups. [S]（per-sample 後做組間檢定：[lionessR]）

**`group_difference`, `paired`**：
> Build one network for each time point on the same genes and priors, then compare edge weights or targeting scores between them. [R]
> This compares the time points across all patients but does not use the pairing: each patient's own before and after samples are pooled into separate networks. To keep the pairing, use the per-sample version and compare each patient's samples. [S]

**`regulator_change`, `*`**：
> Comparing each regulator's targeting score (out-degree) between networks built separately for each condition shows regulators whose targeting changes. [R]
> Without per-sample networks this ranks regulators by the size of the change, with no test of whether it exceeds chance. [S]

OTTER 另加一句 [R]：「OTTER weights are on a different scale from PANDA's; compare OTTER networks only with other OTTER networks built with the same parameters.」

### LIONESS-PANDA／LIONESS-PUMA（每份樣本一個網路）

**`group_difference`, `groups`**：
> Each sample gets its own network, so each edge weight or targeting score can be tested between the groups across samples -- for example with a linear model such as limma. [lionessR]

**`group_difference`, `paired`**：
> Each sample gets its own network, so each patient's before and after networks can be compared directly: test the within-patient differences of edge weights or targeting scores, for example with a paired test or a linear model with a patient term. [S]

**`individual_change`, `paired`**：
> Each patient has a network for each time point; the difference between a patient's own networks (or their regulators' targeting scores) measures how much that patient changed, and ranks patients by it. [S]

**`individual_change`, `*`**：
> Each sample gets its own network; comparing each sample's network or targeting scores with the rest of the cohort shows which individuals stand out. [S]

**`regulator_change`, `*`**：
> Per-sample targeting scores (out-degree) give a regulator-by-sample matrix; test each regulator between the conditions (paired when the same individuals give both), with multiple-testing correction across regulators. [R][S]

**所有格子共用的注意事項** [R]：
> All LIONESS networks are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

### GIRAFFE（TF 活性矩陣）

**`regulator_change`, `*`**：
> GIRAFFE's TF-by-sample activity matrix gives each TF's activity in each sample; test each TF's activity between the conditions (paired when the same individuals give both), with multiple-testing correction. [R][S]

**`individual_change`, `paired`**：
> The difference between a patient's activity profiles at the two time points measures how much that patient's TF activity changed. [S]

**`group_difference`, `*`**：
> The activity matrix compares TF activity, not network wiring, between the conditions; test it per TF as above. [R][S]

### COBRA（只有 `groups` 有宣告，而且是唯一的 `direct`）

**`group_difference`, `groups`**（direct）：
> Put the group label in COBRA's design matrix: it returns a co-expression component for that variable -- the part of each gene pair's co-expression associated with the group -- alongside components for any other covariates you include, such as batch. [COBRA]
> Some component values fall outside -1 to 1; read them as contributions, not correlations. Deciding which gene pairs differ beyond chance is a separate analysis. [COBRA][S]

`paired` 不宣告：論文沒有描述在 design matrix 加個體項的用法。

### LIONESS-COEXPRESSION／BONOBO（每份樣本的共表現網路）

**`group_difference`, `*`**：
> Per-sample gene degree or edge weights can be compared between the groups or time points (paired when the same individuals give both). [R]

**`individual_change`, `*`**：
> Comparing each sample's network with the rest of the cohort -- or, with repeated samples, with the same individual's other sample -- shows which individuals change or stand out. [S]

注意事項：LIONESS-COEXPRESSION 用上面的「不獨立」那句 [R]；BONOBO 用既有的 p-value 那句 [R]。

## 3. 全域「做不到」說明（`UNSUPPORTED_CLAIMS`）

**`causal`**：
> None of the registered workflows can show that one thing causes another: they estimate associations or model coefficients from observational data, and the networks can describe what differs or changes. [S]

只在 `design=paired` 時加：
> A before-and-after comparison without an untreated comparison group also cannot separate the treatment's effect from time or other changes. [S]

**`prediction`**：
> No registered workflow builds a model that predicts an outcome for new samples. Per-sample results -- targeting scores from per-sample networks, GIRAFFE's TF activities, or subtypes -- can serve as features for a classifier you build outside NetZoo, which then needs the outcome for each sample and testing on samples not used to build it. [S]

## 4. 樣本數（A2 修正，`design=paired`）

- 原句 [R]：「N samples take N+1 PANDA runs and give N network files (for your 24 patients, 25 PANDA runs).」
- 當 `design=paired`、`timepoint_count` 有值，而且引用的數字是個體數（patients／volunteers／mice…）時：
  > (for your 24 patients × 2 samples each = 48 samples, 49 PANDA runs)
- `design=paired` 但倍數不明時：不引用個體數，只說「count samples, not patients: each patient contributes more than one」。

## 5. 階段 2 的追問（A5 型）

卡片問題：
> Which do you want to find out: whether regulation changes in the cohort as a whole, which individuals change most, or which regulators change most?

三個選項分別對應 `group_difference`、`individual_change`、`regulator_change`。只在追問軸沒有 witness 時取代它。

推薦（B1 型）：
> COBRA, because you stated the groups to compare: "<引文>".

## 6. 要你看的地方

1. 科學上有沒有說錯或說過頭的句子，特別是 COBRA 的 `direct`，以及 LIONESS 配對檢定的寫法。
2. 整體網路「不能檢定」那句：允許標籤置換（label permutation）作為整體網路的顯著性方法嗎？保留集的 F4-b／F4-c 把它列為可接受做法。我沒寫，因為手上沒有 NetZoo 的出處；要寫的話需要來源。
