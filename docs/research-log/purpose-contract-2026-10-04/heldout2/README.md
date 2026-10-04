# Held-out set 2: comparison design and claim kind

## How it was written

A subagent wrote this set without access to the project. It did not open, list or search any project file, did not run the agent, called no model API and used no web pages. Everything came from the task message: the label vocabulary, the 13-tool registry with its inputs, the list of scenarios not to reuse, and the format rules. The prompts are plain biologist wording. They were not checked against any keyword list and do not follow a shared template. Every item was labelled before anything was run.

A generator script built `heldout.json`. The script also checks that:
- there are 30 items;
- each `prompt` equals `data_sentence + " " + purpose_sentence`;
- each family has one data sentence, four different purposes, at least one `none` control and one design;
- the families include 2 `paired`, 3 `groups` and 1 `none`;
- every claim kind appears at least 3 times in the 24 family prompts (`none` appears 6 times);
- there are 2 negation traps and 4 precision traps;
- no prompt names a tool;
- every prompt is 35-40 words.

Family controls are at different letters, not always at `d`.

## Families (data sentence shared, 4 purposes each)

- **G1** (paired): 18 asthmatic children, with nasal brushings taken during an acute attack and again six weeks after recovery. RNA-seq plus motif and PPI priors.
- **G2** (paired): matched tumor and adjacent non-tumor gastric mucosa from the same 32 patients. Microarray only, with no priors stated.
- **G3** (groups): ten APP/PS1 mice and ten wild-type littermates, hippocampus. RNA-seq plus mouse motif and PPI priors.
- **G4** (groups): eutopic endometrium from 26 women with endometriosis and 22 without. RNA-seq, small-RNA-seq, and TF, PPI and miRNA-target priors.
- **G5** (groups): liver from 16 rats on a high-fructose diet and 16 on chow. RNA-seq plus methylation arrays.
- **G6** (none): 85 cardiac fibroblast lines, each from a different donor. RNA-seq plus motif and PPI priors.

## Traps

- **T1** (negation, causal): BRCA1 carriers vs non-carriers. The user rules out a causal claim and asks for the TFs whose targeting differs most. Labels: groups / regulator_change.
- **T2** (negation, prediction): leukemia bone marrow at diagnosis and at relapse. The user rules out predicting relapse and asks whose networks changed most. Labels: paired / individual_change.
- **T3** (precision, processing): one Arabidopsis count matrix saved "before and after" normalization and filtering. Labels: none / none.
- **T4** (precision, regulator types): "transcription factors versus miRNAs", "RNA-seq and small-RNA-seq", and "predicted miRNA targets" as a prior. Labels: none / none.
- **T5** (precision, method comparison): the user wants to compare two inference approaches to see whether their results "differ". Labels: none / none.
- **T6** (precision, technical variance): co-expression "attributable to batch or library size", with a batch/age/sex covariate table. Labels: none / none.

## Judgement calls to review

1. **G6-a and G6-d**: claim kinds labelled with no comparison design. G6-a asks which donors stand out and is labelled `individual_change`. G6-d asks which TFs vary most from line to line and is labelled `regulator_change`. I read "differ the most" as covering variation across samples when there are no conditions. If the vocabulary means change between conditions only, both labels would change.
2. **T4**: "how much regulation comes from TFs versus miRNAs" is labelled `none` (a description of the regulatory landscape), not `regulator_change`. It does not ask which regulators differ between conditions. This trap also contains two lexical patterns: "versus" and "predicted ... targets".
3. **T6**: four sequencing batches are labelled design `none`, not `groups`. They are technical batches, not a planned comparison of groups of people. The covariate table holds age and sex, but the purpose compares neither. Claim is `none`, although the wording says "attributable to".
4. **T1**: "Normal breast tissue" could look like one side of a tumor/normal pair. The real design is carriers vs non-carriers, so it is labelled `groups`.
5. **T2**: "relapse" is both the second time point and the word in the negated prediction. The label stays `paired` / `individual_change`.
6. **G1-a**: "Does regulation ... shift between attack and recovery across the cohort" is labelled `group_difference`. It is a population-level change across conditions in a paired design. It does not ask about individuals or rank regulators.
7. **G4-c**: "which women have the most atypical networks relative to the rest of the cohort" is labelled `individual_change`, even though the design is `groups`. The purpose ranks individuals and does not compare the two groups.
8. **Outcomes in prediction and causal items are not stated in the data.** These are G2-d (metastasis), G5-a (liver fat) and G3-d (memory deficit). The expectations ask the answer to point out the missing labels or phenotype.

Some rules for the candidate lists:
- COBRA is listed only where a covariate table is stated (T6). Group or tissue labels that are only implied do not count.
- CONDOR appears only as an optional downstream step in G3-a.
- BONOBO is listed for every expression-only item, even when the sample count is moderate.
- For T3, the expectation recommends the normalized, filtered matrix. That is a methods judgement, not a label.
