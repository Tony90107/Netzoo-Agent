# A1 labelling brief (blind): what each request asks for

For each request below, label what result(s) it asks NetZoo to deliver, using ONLY the request text and this menu.

## Results on the menu
- `regulatory_network`: A weighted regulator-to-gene network (TF, or TF and miRNA).
- `targeting_scores`: Each regulator's out-degree or each gene's in-degree in a regulatory network.
- `tf_activity`: Each TF's activity in each sample, estimated apart from its own mRNA level.
- `coexpression_network`: An undirected gene-gene co-expression network.
- `covariate_adjustment`: Co-expression split by, or adjusted for, covariates in a design matrix (and a network built from it).
- `multi_omic_network`: An undirected partial-correlation network within and between two matched omics layers.
- `edge_significance`: A p-value per edge, to filter a network by significance.
- `communities`: Communities in a regulator-gene network, with memberships and each node's core score.
- `community_enrichment`: Pathway enrichment of each community's genes.
- `patient_subtypes`: Patient subtypes from somatic mutations, with gene and pathway mutation scores.

## Kinds of result (a generic word)
- `network` = one of regulatory_network, coexpression_network, covariate_adjustment, multi_omic_network
- `regulation` = one of regulatory_network, targeting_scores, tf_activity

## Registered workflows and the results they give
- BONOBO: coexpression_network
- COBRA: covariate_adjustment
- CONDOR: communities, community_enrichment
- DRAGON: edge_significance, multi_omic_network
- GIRAFFE: regulatory_network, tf_activity
- LIONESS-COEXPRESSION: coexpression_network
- LIONESS-DRAGON: multi_omic_network
- LIONESS-PANDA: regulatory_network, targeting_scores
- LIONESS-PUMA: regulatory_network, targeting_scores
- OTTER: regulatory_network, targeting_scores
- PANDA: regulatory_network, targeting_scores
- PUMA: regulatory_network, targeting_scores
- SAMBAR: patient_subtypes

## Rules
- `results`: the menu results the words ask for. A result named outright -> that result. Only a generic word ('a network', 'regulation') -> every result of that kind, and `open: true`. Two or more results and the user does not know which -> those results, and `open: true`. A result no registered workflow gives (a filtered VCF, differentially expressed genes, a phylogenetic tree) -> `off_menu`.
- A request that only names a workflow to run ('Run PANDA on ...') with no result named -> `results: []`, `open: false`.
- Only a purpose or topic, a choice between methods ('COBRA or CONDOR?') or a question about what can be done, and no result named -> `results: []`, `open: true`.
- A comparison the user will do later is a purpose, not a result. Several things asked: union of their results; `open` true if any of them is open.
- Judge only what the words say; do not judge whether NetZoo can do it.

Output: JSON object {id: {"results": [...], "open": true|false, "why": "<= 15 words"}} for all 85 ids.

## Requests
- **accept24:U01**: I want a network from our 80 maize leaf RNA-seq samples, but honestly I don't know yet whether we need regulators linked to their target genes or just genes linked to genes.
- **accept24:U02**: The core facility sent a matrix with 3,000 columns labelled cells_x_genes, and I'm not sure whether those columns are single cells or pooled bulk samples. We want a TF-gene network for each column; motif and PPI priors are ready.
- **accept24:U03**: We have a proteomics table and an RNA-seq table from the same hospital biobank, but I don't know whether they were measured on the same patients. Can we get one joint network linking proteins and transcripts?
- **accept24:U04**: Our collaborator's prior file might include miRNA-target edges as well as TF motifs - I haven't opened it yet. We want one regulators-to-genes network for 55 liver samples; expression and PPI are ready.
- **accept24:U05**: We're still deciding whether to add metabolomics to the methylation and expression data from the same 70 mice. Either way, we want one network across all the layers we end up using.
- **accept24:U06**: We haven't decided whether we want per-sample TF activity scores or per-sample TF-gene networks for our 90 psoriasis skin biopsies. Motif prior, PPI and expression are all available, so please get started.
- **accept24:U07**: Our pilot may yield 2 or 20 biopsies - we won't know until next month. Whatever we get, we want a co-expression network for each biopsy (log2, centred).
- **accept24:U08**: Our sequencing partner sent a variant-by-gene count table for 190 patients and I'm not sure whether it holds somatic tumour mutations or germline variants. We'd like pathway mutation scores and patient subgroups from it; gene lengths, the cancer-gene list and a GMT file are ready.
- **accept24:U10**: I inherited a network file from a former student and can't tell whether it holds TF-to-gene edges or gene-gene co-expression edges. Can you find communities in it?
- **accept24:U11**: The second layer for our 110 tumours is either binary mutation calls or continuous copy-number values - I need to check with our bioinformatician. We want a partial-correlation network between it and the matched expression.
- **accept24:U12**: My PI wants 'the regulators of the EMT genes' in our 64 tumours, and I'm not sure if she means transcription factors or lncRNAs. We have expression, a TF motif prior and a PPI.
- **accept24:U16**: We have 'miRNA data' for 60 gastric samples from an old project, and I'm not sure if it's measured miRNA expression or a table of predicted miRNA targets. We want miRNAs linked to the genes they affect; gene expression for the same samples is ready.
- **accept24:U17**: Not sure yet whether we want the co-expression changes associated with age or just the overall co-expression network for our 120 blood samples; age is a numeric column in the sample sheet.
- **accept24:U18**: We have a 10-time-point series of mouse liver after partial hepatectomy, one sample per time point, plus motif and PPI priors. We haven't decided whether we want one network per time point or the time delays between regulators and their targets.
- **m3:U01**: Run BONOBO on lunar.tsv for our lunar-cycle algae experiment. The expression table has a header and numeric values, but I do not know whether the upstream export was log-transformed and centered. Please establish that before proceeding.
- **m3:U02**: Can BONOBO analyze our archived salamander expression cohort? The archive catalog does not say whether it contains two total samples or six; all other format and preprocessing requirements are met.
- **m3:U03**: Run LIONESS-PANDA for the validated acorn RNA panel with matching priors. I am waiting to learn whether the panel has two independent samples or five.
- **m3:U04**: Can LIONESS-PUMA handle the zebrafish injury panel? Every required input is available, but the lab has not confirmed whether there are two samples or twelve.
- **m3:U05**: Run LIONESS-COEXPRESSION for the night-shift experiment. The table is valid expression, but the sample count might be two or twenty depending on which release was approved.
- **m3:U06**: Can COBRA analyze the midge experiment? The valid expression/design pair is ready, but after filtering I do not know whether 20 or 200 genes remain for the 40 samples.
- **m3:U07**: Run COBRA for the wheat site-effect analysis. All sample IDs match, but I do not know whether the design columns encode sites numerically or still contain text labels.
- **m3:U08**: Can CONDOR analyze edges_release.tsv? Its source and target sets are disjoint and the file has source,target,weight columns, but the provider has not confirmed whether weight contains numeric values or text confidence labels. No conversion is authorized.
- **m3:U09**: Run DRAGON on the two stellar-radiation cell-culture tables. Their shapes and headers are correct, but it is unknown whether the sample ID sets match exactly.
- **m3:U10**: Can DRAGON combine the two assay exports for the marine parasite project? The second assay may contain continuous concentrations or categorical low/medium/high calls; the collaborator has not clarified which.
- **m3:U11**: Run LIONESS-DRAGON on two valid-format layers for the mosquito diapause study. They may contain two or ten paired samples; that count is not yet known.
- **m3:U12**: The data management team has not finished the export for this project, and I cannot infer the number of measured features from its working filename. There are two plausible releases: a compact targeted panel and a large untargeted panel. Both releases have the same participants and would otherwise satisfy the paired-table requirements. Our funding milestone requires retaining every pair of features and every participant in a single run. Reducing the panel, dropping people, or splitting the requested output into multiple independent runs has not been approved. I need a capability judgment that waits for the size fact rather than assuming the smaller release. Can LIONESS-DRAGON process all feature pairs for our 100 participants? There are either 100 or 1000 total features across the two layers; the export manifest has not arrived.
- **m3:U13**: Run OTTER for the conifer seed study using our validated expression, seed and PPI files. The grant requires a particular device, but I have not checked whether CPU is allowed or GPU is mandatory.
- **m3:U14**: Can OTTER run with the value in our approved lam setting? The note is unreadable: it could be 0.3 or 3.0, and I cannot authorize changing it.
- **m3:U15**: Run GIRAFFE on the validated desert moss files. We need our published optimizer settings preserved, but I have not determined whether they are package defaults or customized values.
- **m3:U16**: Can SAMBAR subtype the leukemia panel into up to seven groups? The number of mutation samples is either five or fifteen; the final inclusion list is pending.
- **m3:U17**: Run SAMBAR using the provided four reference/data files. I do not yet know whether their gene identifier sets share any gene across all four files.
- **m3:U18**: Can PANDA use covariance_bundle.tsv as coexpression_file alongside our valid expression, motif and PPI files? All gene IDs and dimensions match, but the analyst has not confirmed whether the square matrix is symmetric or asymmetric; no repair is authorized.
- **m3:U19**: Run aggregate PUMA for the oyster infection analysis. The miRNA file exists and is well formatted, but it is unknown whether all listed miRNA IDs occur in column one of the regulator prior.
- **m3:U20**: Can BONOBO honor the approved sparsification setup? We know save_pvals=true, but the lab has not confirmed whether sparsify was set to true or false and we must preserve that setting.
- **m3:U21**: Run BONOBO with sparsify=true using the fixed delta in our protocol. The protocol owner must confirm whether delta is 0.2 or 0.5; do not substitute another value.
- **m3:U22**: Can OTTER take network_input.tsv as coexpression_file? Its author has not confirmed whether it is an aggregate gene-by-gene matrix or a collection of per-sample networks.
- **m3:U23**: Run DRAGON with lambda1=0.45. My collaborator is checking whether a lambda2 value was also fixed by the protocol or must remain absent; preserve that decision.
- **m3:U24**: The study combines several seedling samples and asks for a result that differs between individuals. In discussions, the authors have used the words regulation, activity, and personalized network interchangeably, and that has made the planned deliverable unclear. The expression matrix and both biological priors have already passed the file checks, so requesting another file will not settle the issue. Before recommending an execution path, we need to identify what numerical object the authors intend to compare across the individual samples. Please keep the unresolved scientific endpoint visible rather than silently selecting one interpretation. Can GIRAFFE meet the requirement for an individual result in our beet-root paper? The authors have not decided whether individual means TF activity per sample or a different regulatory wiring matrix per sample.
- **m3:U25**: Run CONDOR using the file called network.tsv after we confirm its structure. I have not been told whether it is a source-target edge list or raw gene-by-sample expression.
- **m3:U28**: Can SAMBAR score this insect tumor dataset? The assay lead has not said whether the matrix records somatic mutation counts or RNA abundance; the filename does not resolve it.
- **m3:U30**: Can LIONESS-PANDA fulfill our requirement for personalized regulation? We have adequate expression and priors, but the committee has not decided whether it needs network wiring for each sample or TF activity values for each sample.
- **accept24:N25**: Could you build a phylogenetic tree of the bHLH transcription factor family across 20 vertebrate genomes?
- **m3:N20**: We deleted the expression file. Can aggregate PANDA execute solely from a co-expression matrix, motif and PPI without reconstructing expression?
- **m3:N30**: Can BONOBO accept positional sample indices 0 and 2 in sample_names without translating them into actual sample IDs?
- **heldout18:CS3**: We have proteomics for 50 patients and RNA-seq for a different set of 60 patients. We want a partial-correlation network linking proteins and transcripts.
- **m3:N24**: Can OTTER preserve the exact fractional PPI interaction confidence values inside P? I prohibit binarization.
- **accept24:N03**: Can we get, for every one of our 40 sepsis patients, a TF-gene network where each edge is labelled as activating or repressing in that patient?
- **m3:N13**: Can registered OTTER produce a separate optimized network per individual using LIONESS-OTTER?
- **accept24:N15**: How can we quantify, with differential modularity, how the community structure of our control PANDA network is reorganised in the disease network?
- **m3:N25**: Can DRAGON run with lambda1=0.4 and leave lambda2 unspecified while keeping lambda1 fixed?
- **heldout19:UN6**: We have expression and methylation for 80 matched samples. We want a network linking them. Each link must come with a bootstrap confidence interval.
- **m3:N05**: Can LIONESS-COEXPRESSION guarantee the direction of causal regulation between genes from expression alone?
- **accept24:N27**: Email the CONDOR community files from yesterday's run to my co-author right now.
- **accept24:N02**: We'd like a network in which lncRNAs act as the regulators of protein-coding genes across our 60 prostate tumours.
- **heldout18:CS5**: We have Visium data for 4,000 spots with motifs and PPI. Each spot's network has to take its neighbouring spots into account. We want TF-gene networks per spot.
- **accept24:N24**: Go ahead and call somatic SNVs and indels from our 30 tumour/normal BAM pairs with Mutect2.
- **m3:N06**: Can COBRA run on 15 genes measured in 60 samples without changing the dimensions?
- **heldout19:UN5**: We want the communities of our bipartite TF-gene network. They must be found with the Louvain algorithm.
- **heldout19:UN1**: We have expression and PPI for 70 samples. We want one TF-gene network. No motif or binding-site information may be used.
- **m3:N12**: Can this agent run OTTER on the GPU when CPU execution is unacceptable and I need the current runtime to execute it?
- **m3:N16**: Can BONOBO output a cohort-level aggregate prior network directly, instead of its per-sample matrices?
- **heldout11:VN5q**: We measured expression every 2 hours for 48 hours after heat shock, with motifs and PPI. Is there a method that models how each TF-gene edge at one time point depends on the edges at the previous time point?
- **accept24:N29**: Build us an interactive web dashboard where lab members can browse the networks and search for their favourite gene.
- **heldout13:CE1**: We have RNA-seq from 110 kidney samples, TF motifs and a PPI network. We want one TF-gene regulatory network for the whole cohort.
- **m3:P06**: Our plant RNA table has 600 genes and 24 samples; the numeric design table has exactly those 24 sample IDs and an intercept. Can COBRA produce the adjusted gene-by-gene co-expression artifact?
- **m3:P29**: The PI wants the leave-one-out co-expression network for sample R17 in a 45-sample root microbiome expression cohort. Can LIONESS-COEXPRESSION retain its sample identity and keep that result separate from the aggregate?
- **heldout19:UP5**: We have expression and proteomics for 100 matched samples. We want a network linking them. Each link must be conditional on all other measured features.
- **heldout18:XP3**: We have expression for 140 samples with a batch covariate. We want the co-expression with the batch part separated.
- **heldout12:BP3**: We have expression, motifs and PPI from 75 tumors. We want each TF's activity in each tumor and a signed TF-gene regulatory matrix.
- **heldout14:CE3**: We have a bipartite TF-gene network. We want its communities.
- **heldout11:VM2s**: We have expression from 70 colon samples. We want a TF-gene network for each sample.
- **heldout17:PI1**: We want one network of how TFs and miRNAs regulate genes in our 70 samples.
- **m3:P13**: Run BONOBO on centered_log.tsv: a validated, labeled, log-transformed and centered gene-by-sample matrix with seven samples. Select sample IDs H2 and H5, save CSV networks, and leave sparsify=false.
- **heldout17:PQ2**: We have expression of 90 samples. Is there a method that gives each sample its own Pearson co-expression network?
- **accept24:P15**: Using our 66 melanoma samples (expression, motif prior and PPI are in /data/mel/), please estimate TF activity for each sample and then tell us which TFs' activity is associated with overall survival.
- **m3:P18**: Our regulatory analysis must use relaxed graph matching after adjustment for sequencing plate. We have 900 genes, 40 samples, an appropriate numeric COBRA design, and compatible OTTER priors. Plan COBRA then OTTER with explicit adjusted-matrix validation.
- **heldout15:PI1**: We have expression from 90 samples and want one TF-gene regulatory network for them.
- **heldout11:VC2q**: From expression, motifs and PPI of 110 lymphoma samples, which method gives a separate TF-gene network for each sample?
- **heldout18:XP2**: We have somatic mutation calls for 160 tumors. We want subtypes from pathway mutation scores.
- **heldout13:CP8**: From expression, motifs and PPI of 70 tumors, we want each TF's activity in each tumor, estimated separately from the TF's own mRNA level.
- **heldout11:VC7s**: From expression, motifs and PPI of 88 patients with survival follow-up, we want a network for each patient and then a test of which TFs' targeting relates to survival.
- **heldout18:CP3**: We have expression and methylation from the same 85 tumors. We want a partial-correlation network linking them.
- **heldout13:CP1**: We have expression and proteomics from 120 matched samples. We want the links between the two layers and a Benjamini-Hochberg adjusted p-value for every link.
- **m3:P12**: Can GIRAFFE jointly estimate the aggregate signed regulatory coefficient matrix and TF activities for our pancreatic differentiation samples? We will provide gene expression, motif priors and a TF interaction prior.
- **heldout14:QP4**: We have a bipartite TF-gene network. Which method identifies its communities and each node's core score?