# P3 多輪 live 回覆全文（live/p3live）

## S01-C45（complete）

預期：2000 bound; not re-asked; DECLINE with the answer quoted

### t1：ASK/fact_agent

**使用者**：We'd like a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients, from 300 serum miRNAs and a plasma proteomics panel measured on the same patients (complete, continuous, matching IDs). The catch: I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel, and the files are still on the CRO's server.

**task_state**：`{"id": "625e234a", "status": "active", "rounds": 1, "pending": [["agent", "LIONESS-DRAGON"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Do you have at least three samples for each panel?
>   You wrote: "I don't remember whether the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel". LIONESS-DRAGON's contract: "Require at least three samples".
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DECLINE/full_gap

**使用者**：It's the 2,000-protein discovery panel.

**task_state**：`{"id": "625e234a", "status": "closed", "rounds": 1, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "a separate miRNA-protein partial-correlation network for each of our 50 heart-failure patients" -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set.
>
> I couldn't match this to a result any registered NetZoo workflow produces, so none is offered.
>
> No files were inspected and no analysis ran.

## S02-J48（complete）

預期：4 bound; not re-asked; DO (LIONESS-PANDA)

### t1：ASK/count_fact

**使用者**：I want LIONESS-PANDA networks for our zebrafish heart regeneration study, one per fish. After QC we kept either two or four libraries; the sequencing core still hasn't told me which. We have the zebrafish motif prior and PPI.

**task_state**：`{"id": "516b0b83", "status": "active", "rounds": 1, "pending": [["count", "sample_count"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Which of these is right: 2 or 4?
>   You wrote: "After QC we kept either two or four libraries; the sequencing core still hasn't told me which".
>   - 2: no registered workflow can do this as asked -- LIONESS-PANDA needs at least 3 samples; the request has 2
>   - 4: LIONESS-PANDA can do this
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DO/results_given

**使用者**：We kept 4 libraries.

**task_state**：`{"id": "516b0b83", "status": "closed", "rounds": 1, "pending": [], "facts": [["count", "sample_count", "4", "known"]]}`

**回覆**：

> What I understood you are asking for:
> 1. "I want LIONESS-PANDA networks for our zebrafish heart regeneration study, one per fish." -- available from LIONESS-PANDA.
>
> Selected path: **LIONESS-PANDA**.
>
> Your question asks for a regulatory network. **LIONESS-PANDA** fits that result.
>
> **LIONESS-PANDA** — Infer aggregate PANDA and sample-specific LIONESS-PANDA networks. LIONESS represents the cohort network through sample contributions: W_q = N*W_all - (N-1)*W_without_q, where N is the cohort size and the same base estimator is fitted with and without sample q. The leave-one-out network alone is not the patient's network. This borrows cohort information; it does not estimate a correlation from one isolated observation or prove causality. With PANDA, edge weights are inferred regulatory support, not measured binding strength. Cross-sectional networks do not establish temporal rewiring. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
>
> Required workflow inputs:
>
> - `expression_file`: expression matrix
> - `motif_file`: motif/prior
> - `ppi_file`: PPI network
>
> Cost: LIONESS runs PANDA once on all samples and once more without each sample, so N samples take N+1 PANDA runs and give N network files. Plan the runtime and disk space, and filter edges before downstream statistics.
>
> Outputs:
>
> - `regulatory_network`: Inferred regulator-to-target associations.
>
> Out-degree measures how strongly a TF is wired to its targets in each sample. If you mean TF activity instead -- how active a TF is apart from its own mRNA level -- GIRAFFE's TF-by-sample activity matrix is the other reading, from the expression, motif and PPI inputs.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

## S03-J14（complete）

預期：4500 bound; not re-asked; the whole-cohort condition read (DRAGON, DO)

### t1：ASK/count_fact

**使用者**：LIONESS-DRAGON for 40 paired RNA and miRNA profiles from the same placentas would be ideal. The miRNA layer has 300 features, but I can't remember whether we kept 450 or 4,500 genes in the RNA layer after filtering.

**task_state**：`{"id": "f495cf12", "status": "active", "rounds": 1, "pending": [["count", "feature_count"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Which of these is right: 450 or 4,500?
>   You wrote: "whether we kept 450 or 4,500 genes in the RNA layer after filtering".
>   - 450: LIONESS-DRAGON can do this
>   - 4,500: no registered workflow can do this as asked -- LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 4,500 features and 40 samples give 404,910,000
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DECLINE/full_gap

**使用者**：4,500 genes. And we'd now prefer one network for the whole cohort rather than one per placenta.

**task_state**：`{"id": "f495cf12", "status": "closed", "rounds": 1, "pending": [], "facts": [["count", "feature_count", "4500", "known"]]}`

**回覆**：

> What I understood you are asking for:
> 1. "40 paired RNA and miRNA profiles from the same placentas" -- not available here as asked. LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 4,800 features and 40 samples give 460,704,000.
>
> No registered workflow can give this as you asked it (above), so none is offered as asked.
>
> No files were inspected and no analysis ran.

## S04-J19（complete）

預期：per_sample bound; not re-asked; DO (LIONESS-DRAGON), or not available with the answer quoted

### t1：ASK/fact_agent

**使用者**：We have paired proteome (250 proteins) and phosphoproteome (150 sites) tables from 46 kidney tumours and want a partial-correlation network linking the two layers. The aims page says one network for the whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant.

**task_state**：`{"id": "6b9ab303", "status": "active", "rounds": 1, "pending": [["agent", "LIONESS-DRAGON"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Do you want one network per tumour?
>   You wrote: "The aims page says one network for the whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant". LIONESS-DRAGON's contract: "LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample".
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DECLINE/full_gap

**使用者**：One per sample, please.

**task_state**：`{"id": "6b9ab303", "status": "closed", "rounds": 1, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "want a partial-correlation network linking the two layers" -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set.
>
> I couldn't match this to a result any registered NetZoo workflow produces, so none is offered.
>
> No files were inspected and no analysis ran.

## S05-J19（complete）

預期：nothing bound by code; the reading takes 'each tumour'; scale not re-asked

### t1：ASK/fact_agent

**使用者**：We have paired proteome (250 proteins) and phosphoproteome (150 sites) tables from 46 kidney tumours and want a partial-correlation network linking the two layers. The aims page says one network for the whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant.

**task_state**：`{"id": "e49d6c51", "status": "active", "rounds": 1, "pending": [["agent", "LIONESS-DRAGON"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Do you want one network per tumour?
>   You wrote: "The aims page says one network for the whole cohort, the grant narrative says one per tumour, and I can't tell which my PI meant". LIONESS-DRAGON's contract: "LIONESS-DRAGON estimates DRAGON's two shrinkage values once on all samples, then derives each sample's network from the all-sample network and the network refitted without that sample".
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：CLARIFY/goal_unclear

**使用者**：My PI confirmed: a separate network for each tumour.

**task_state**：`{"id": "e49d6c51", "status": "active", "rounds": 2, "pending": [["goal", ""]], "facts": []}`

**回覆**：

> I can't tell yet which result you want, so I have not chosen a workflow.
>
> The registered workflows give these results:
> - One weighted TF-to-gene regulatory network across all the samples given (PANDA)
> - One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
> - One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
> - One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
> - One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
> - Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
> - The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
> - Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
> - One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
> - One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
> - One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
> - A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
> - One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)
>
> Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?
>
> Nothing was selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

## S06-C56（not_exercised）

預期：somatic bound; origin not re-asked; DO or ASK on other facts only

### t1：DO/results_given

**使用者**：Can SAMBAR subtype our 160 pediatric medulloblastomas? The sequencing core sent a samples-by-genes variant-count matrix along with gene lengths, a cancer-gene list and a KEGG GMT, but their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls, and I can't tell from the file itself.

**task_state**：`{"id": null, "status": null, "rounds": null, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "Can SAMBAR subtype our 160 pediatric medulloblastomas?" -- available from SAMBAR.
>
> Selected path: **SAMBAR**.
>
> Why this recommendation:
>
> Gene length normalization addresses the greater opportunity for mutations in longer genes; gene/exon sizes are therefore required, not just the mutation matrix.
>
> Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.
>
> **SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.
>
> Required workflow inputs:
>
> - `mutation_file`: somatic mutation matrix
> - `exon_size_file`: gene/exon-size CSV
> - `cancer_gene_file`: cancer-gene list
> - `pathway_file`: GMT pathway file
>
> Outputs:
>
> - `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
> - `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
> - `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
> - `sample_distance_matrix`: Pairwise sample distances, not cluster labels.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

## S07-C56（not_exercised）

預期：t3: somatic superseded, germline known; DECLINE with the answer quoted

### t1：DO/results_given

**使用者**：Can SAMBAR subtype our 160 pediatric medulloblastomas? The sequencing core sent a samples-by-genes variant-count matrix along with gene lengths, a cancer-gene list and a KEGG GMT, but their README doesn't say whether the counts are tumour-only somatic mutations or germline variant calls, and I can't tell from the file itself.

**task_state**：`{"id": null, "status": null, "rounds": null, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "Can SAMBAR subtype our 160 pediatric medulloblastomas?" -- available from SAMBAR.
>
> Selected path: **SAMBAR**.
>
> Why this recommendation:
>
> Gene length normalization addresses the greater opportunity for mutations in longer genes; gene/exon sizes are therefore required, not just the mutation matrix.
>
> Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.
>
> **SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.
>
> Required workflow inputs:
>
> - `mutation_file`: somatic mutation matrix
> - `exon_size_file`: gene/exon-size CSV
> - `cancer_gene_file`: cancer-gene list
> - `pathway_file`: GMT pathway file
>
> Outputs:
>
> - `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
> - `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
> - `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
> - `sample_distance_matrix`: Pairwise sample distances, not cluster labels.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

## S08-M06（complete）

預期：not re-prompted for detail; agent yes recorded; DO (SAMBAR)

### t1：ASK/fact_agent

**使用者**：SAMBAR pathway-based subtypes are what we want for 210 tumours, from a mutation matrix our core facility produced. I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left.

**task_state**：`{"id": "ba3c65ba", "status": "active", "rounds": 1, "pending": [["agent", "SAMBAR"]], "facts": []}`

**回覆**：

> Before I choose a workflow, please tell me:
> - Are the calls somatic mutations?
>   You wrote: "I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left". SAMBAR's contract: "SAMBAR consumes a samples-by-genes somatic mutation CSV".
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DO/results_given

**使用者**：yes

**task_state**：`{"id": "ba3c65ba", "status": "closed", "rounds": 1, "pending": [], "facts": [["agent", "SAMBAR", "yes", "known"]]}`

**回覆**：

> What I understood you are asking for:
> 1. "SAMBAR pathway-based subtypes are what we want for 210 tumours, from a mutation matrix our core facility produced." -- available from SAMBAR.
>
> Selected path: **SAMBAR**.
>
> Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.
>
> Why this recommendation:
>
> Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.
>
> **SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.
>
> Required workflow inputs:
>
> - `mutation_file`: somatic mutation matrix
> - `exon_size_file`: gene/exon-size CSV
> - `cancer_gene_file`: cancer-gene list
> - `pathway_file`: GMT pathway file
>
> Outputs:
>
> - `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
> - `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
> - `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
> - `sample_distance_matrix`: Pairwise sample distances, not cluster labels.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

## S09-M06（not_exercised）

預期：agent no recorded; DECLINE with a verifiable reason

### t1：DO/results_given

**使用者**：SAMBAR pathway-based subtypes are what we want for 210 tumours, from a mutation matrix our core facility produced. I honestly don't know whether their calls are somatic (tumour versus matched normal) or germline variants; the README doesn't say and the analyst has left.

**task_state**：`{"id": null, "status": null, "rounds": null, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "SAMBAR pathway-based subtypes are what we want for 210 tumours, from a mutation matrix our core facility produced." -- available from SAMBAR.
>
> Selected path: **SAMBAR**.
>
> Your question asks for a cohort-level sample cluster assignment. **SAMBAR** fits that result and scale.
>
> Why this recommendation:
>
> Pathway aggregation turns gene mutation scores into pathway-by-sample scores; sample distances are then calculated from those profiles, and clustering assigns sample labels. These are separate artifacts, not patient-specific mutation networks.
>
> **SAMBAR** — Subtype somatic-mutation samples through pathway mutation scores with SAMBAR. SAMBAR reduces sparse mutation data to pathway-level scores with gene-length and, when configured, patient mutation-burden normalization. Patient distances and subtype labels depend on the downstream clustering settings; they are distinct from gene communities in a regulatory network. This is pathway aggregation followed by distance-based clustering, not non-negative matrix factorization; a mutation score does not establish permanent functional loss or equivalence of every mutation in a pathway.
>
> Required workflow inputs:
>
> - `mutation_file`: somatic mutation matrix
> - `exon_size_file`: gene/exon-size CSV
> - `cancer_gene_file`: cancer-gene list
> - `pathway_file`: GMT pathway file
>
> Outputs:
>
> - `gene_mutation_scores`: Sample-by-gene mutation scores, not pathway scores.
> - `pathway_mutation_matrix`: Pathway-by-sample mutation scores, not cluster labels.
> - `sample_cluster_assignment`: Sample-to-cluster labels, separate from score and distance matrices.
> - `sample_distance_matrix`: Pairwise sample distances, not cluster labels.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

## S10-L14（not_exercised）

預期：if t1 asked two: nothing bound, ASK again

### t1：DECLINE/full_gap

**使用者**：I want DRAGON on serum proteomics and stool metabolomics from our IBD study, 60 profiles in each table. I'm not sure the two tables cover the same people, though: the proteomics came from the 2023 visit and the metabolomics may be a different subset of patients.

**task_state**：`{"id": null, "status": null, "rounds": null, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "I want DRAGON on serum proteomics and stool metabolomics from our IBD study, 60 profiles in each table." -- I couldn't match this to anything a registered NetZoo workflow produces or lets you set. DRAGON gives: one undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples. A p-value and a Benjamini-Hochberg adjusted p-value for every edge (adjusted within each layer and across the layers), to filter edges by significance.
>
> I couldn't match this to a result any registered NetZoo workflow produces, so none is offered.
>
> No files were inspected and no analysis ran.

## S11-C12（complete）

預期：t3 opens with the exhausted note, CLARIFY, nothing run or declined

### t1：CLARIFY/goal_unclear

**使用者**：Please run the network analysis on expr_sle_monocytes.tsv and send me the results.

**task_state**：`{"id": "2a9b2122", "status": "active", "rounds": 1, "pending": [["goal", ""]], "facts": []}`

**回覆**：

> I can't tell yet which result you want, so I have not chosen a workflow.
>
> The registered workflows give these results:
> - One weighted TF-to-gene regulatory network across all the samples given (PANDA)
> - One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
> - One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
> - One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
> - One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
> - Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
> - The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
> - Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
> - One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
> - One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
> - One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
> - A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
> - One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)
>
> Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?
>
> Nothing was selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：CLARIFY/goal_unclear

**使用者**：I'm not sure, whatever is standard.

**task_state**：`{"id": "2a9b2122", "status": "active", "rounds": 1, "pending": [["goal", ""]], "facts": []}`

**回覆**：

> I can't tell yet which result you want, so I have not chosen a workflow.
>
> The registered workflows give these results:
> - One weighted TF-to-gene regulatory network across all the samples given (PANDA)
> - One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
> - One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
> - One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
> - One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
> - Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
> - The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
> - Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
> - One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
> - One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
> - One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
> - A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
> - One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)
>
> Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?
>
> Nothing was selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t3：CLARIFY/goal_unclear

**使用者**：Still not sure, sorry.

**task_state**：`{"id": "2a9b2122", "status": "active", "rounds": 1, "pending": [["goal", ""]], "facts": []}`

**回覆**：

> I can't tell yet which result you want, so I have not chosen a workflow.
>
> The registered workflows give these results:
> - One weighted TF-to-gene regulatory network across all the samples given (PANDA)
> - One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
> - One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
> - One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
> - One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
> - Communities in one bipartite network, with regulator-side and gene-side memberships, by bipartite modularity (CONDOR)
> - The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
> - Patient subtypes from somatic mutations -- gene mutation scores summarized into pathway mutation scores, then hierarchical clustering of the patients on them... (SAMBAR)
> - One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
> - One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
> - One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
> - A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
> - One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)
>
> Which of these results do you want, or what question should the analysis answer? And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, or a second omics layer)?
>
> Nothing was selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

## S12-H13（complete）

預期：t3 opens with the exhausted note, ASK

### t1：ASK/needs_fact

**使用者**：Can CONDOR find modules in the network a collaborator emailed me? It's a three-column weighted edge list, but I genuinely have no idea whether it's a TF-to-gene regulatory network or a gene-gene co-expression network - she only called it 'the network'.

**task_state**：`{"id": "d21e7686", "status": "active", "rounds": 1, "pending": [["dimension", "network_given"]], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "Can CONDOR find modules in the network a collaborator emailed me?" -- CONDOR needs a regulator-gene (source-target-weight) network, and the request does not say whether you have one: if you do, CONDOR; if not, building one first (OTTER, PANDA, PUMA) is a separate run the request does not name.
> 2. "It's a three-column weighted edge list, but I genuinely have no idea whether it's a TF-to-gene regulatory network or a gene-gene co-expression network - she only called it 'the network'." -- I couldn't match this to a result any registered NetZoo workflow produces. CONDOR does not give it: one network at a time.
>
> Before I choose a workflow, please tell me: Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：ASK/needs_fact

**使用者**：I really don't know.

**task_state**：`{"id": "d21e7686", "status": "active", "rounds": 1, "pending": [["dimension", "network_given"]], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "Can CONDOR find modules in the network a collaborator emailed me?" -- CONDOR needs a regulator-gene (source-target-weight) network, and the request does not say whether you have one: if you do, CONDOR; if not, building one first (OTTER, PANDA, PUMA) is a separate run the request does not name.
> 2. "It's a three-column weighted edge list, but I genuinely have no idea whether it's a TF-to-gene regulatory network or a gene-gene co-expression network - she only called it 'the network'." -- I couldn't match this to a result any registered NetZoo workflow produces. CONDOR does not give it: one network at a time.
>
> Before I choose a workflow, please tell me: Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t3：ASK/needs_fact

**使用者**：Still no idea, she hasn't replied.

**task_state**：`{"id": "d21e7686", "status": "active", "rounds": 1, "pending": [["dimension", "network_given"]], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "Can CONDOR find modules in the network a collaborator emailed me?" -- CONDOR needs a regulator-gene (source-target-weight) network, and the request does not say whether you have one: if you do, CONDOR; if not, building one first (OTTER, PANDA, PUMA) is a separate run the request does not name.
> 2. "It's a three-column weighted edge list, but I genuinely have no idea whether it's a TF-to-gene regulatory network or a gene-gene co-expression network - she only called it 'the network'." -- I couldn't match this to a result any registered NetZoo workflow produces. CONDOR does not give it: one network at a time.
>
> Before I choose a workflow, please tell me: Do you already have a regulator-gene (source-target-weight) network for CONDOR to run on?
>
> No workflow has been selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

## S13-C24（complete）

預期：new task, no old facts; DO (PANDA)

### t1：CLARIFY/goal_unclear

**使用者**：Reviewers asked for 'a network analysis' of our placenta study. We have mRNA-seq and small-RNA-seq from 45 preeclampsia and control placentas. Honestly I don't know what kind of network they expect or what it's supposed to show. The two groups are roughly balanced and both libraries come from the same placentas; can you set something up that would satisfy them?

**task_state**：`{"id": "8c05c744", "status": "active", "rounds": 1, "pending": [["goal", ""]], "facts": []}`

**回覆**：

> I can't tell yet which result you want, so I have not chosen a workflow.
>
> With expression data, the registered workflows can give these results:
> - One weighted TF-to-gene regulatory network across all the samples given (PANDA)
> - One weighted network of how TFs and miRNAs regulate genes, across all samples (PUMA)
> - One TF-gene network per sample, plus the aggregate network (LIONESS-PANDA)
> - One TF/miRNA-gene network per sample, plus the aggregate network (LIONESS-PUMA)
> - One gene-gene co-expression network per sample, plus the aggregate (LIONESS-COEXPRESSION)
> - The part of each gene pair's co-expression associated with each covariate in a design matrix (e.g. group, batch), and a covariate-adjusted co-expression matrix (COBRA)
> - One undirected partial-correlation network within and between two matched omics layers (any two, e.g. expression and methylation), across all samples (DRAGON)
> - One two-layer partial-correlation network per sample, plus the aggregate (LIONESS-DRAGON)
> - One weighted TF-to-gene regulatory network across all samples, fitted so that it agrees with the PPI network and gene co-expression (OTTER)
> - A signed TF-to-gene regulatory matrix (positive activating, negative repressing), across all samples (GIRAFFE)
> - One gene-gene co-expression network per sample, estimated with a Bayesian model; optionally per-edge p-values per sample (BONOBO)
>
> Which of these results do you want, or what question should the analysis answer?
>
> Nothing was selected and nothing runs before you answer.
>
> No files were inspected and no analysis ran.

### t2：DO/results_given

**使用者**：Forget that request. New question: build one PANDA TF-to-gene network for our liver RNA-seq; we have expression, a motif prior and a PPI.

**task_state**：`{"id": null, "status": null, "rounds": null, "pending": [], "facts": []}`

**回覆**：

> What I understood you are asking for:
> 1. "build one PANDA TF-to-gene network for our liver RNA-seq" -- available from PANDA.
>
> Selected path: **PANDA**.
>
> Your question asks for a cohort-level regulatory network. **PANDA** fits that result and scale.
>
> **PANDA** — Infer an aggregate TF-to-gene regulatory network with PANDA. Message passing iteratively reconciles a regulator-target prior with other biological evidence networks. Other evidence can revise the initial edge support, but the resulting weights are integrated network scores, not calibrated posterior probabilities of prior reliability.
>
> Required workflow inputs:
>
> - `expression_file`: expression matrix
> - `motif_file`: motif/prior
> - `ppi_file`: PPI network
>
> Outputs:
>
> - `regulatory_network`: Inferred regulator-to-target associations.
>
> Ask for the workflow's controls and defaults if you want to set them.
>
> This is workflow guidance only; no execution was authorized. No files were inspected and no analysis ran.

