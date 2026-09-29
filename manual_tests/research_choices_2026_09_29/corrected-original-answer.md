There are different analyses to consider here. The useful distinction is what each method assumes and what you want to learn from the data.

For “不可逆的DNA損傷累積”:

**SAMBAR**. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.

You would need somatic mutation matrix, gene/exon-size CSV, cancer-gene list, GMT pathway file. The analysis would provide gene-by-sample mutation scores, not pathway scores; pathway-by-sample mutation scores, not cluster labels; sample-to-cluster labels, separate from score and distance matrices; pairwise sample distances, not cluster labels.

For “細胞當下系統連線的動態重組”:

**PANDA → LIONESS-PANDA**. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.

You would need expression matrix, motif/prior, PPI network. The analysis would provide inferred regulator-to-target associations.

To turn this into patient subtypes, use a TF-by-sample out-degree matrix -- each TF's summed edge weights to its targets in each sample's network (how strongly the TF is wired). Clustering the samples on that matrix (for example hierarchical clustering or k-means) is not a NetZoo workflow; run it separately.

Per-sample networks from LIONESS are derived from the same cohort, so they are not statistically independent; account for this in any test across samples.

Clusters are unsupervised: whether they predict an outcome such as treatment response has to be tested against that outcome, keyed by the same sample IDs.

To use subtypes for chemotherapy resistance or another clinical outcome, you would also need outcome labels matched to the patients. Check cluster stability and confounding, then evaluate prediction on held-out patients. Fit feature selection and cohort-dependent network estimation within the training split to avoid information leakage.

No files were inspected and no analysis ran.

Which scientific question should we start with, and which of these inputs do you have? We can also investigate the hypotheses in parallel.
