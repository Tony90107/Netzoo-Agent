# j8 gold review

## Changes

- **Z24, workflows**: `["PANDA"]` -> `["PANDA", "OTTER"]` (reason and evidence updated to match). OTTER takes the same three inputs and gives one aggregate TF-to-gene network, as Z09/Z27/Z40 already list. otter.yaml: "It produces an aggregate TF-to-gene network whose edge weight is the optimized OTTER W score."
- **Z04, fact_keywords**: `targets` -> `microrna` (generic word replaced by one specific to the fact). Contract fact: puma.yaml: "required_inputs: [expression_file, motif_file, ppi_file, mirna_file, output_file]".
- **Z48, fact_keywords**: `patients` -> `qc` (generic word replaced by one specific to the QC count). lioness-panda.yaml: "Require at least three expression samples before execution."

No prompt or reply was changed. No call changed.

## Borderline, kept unchanged

- **Z14** (GT, PANDA then CONDOR): CONDOR needs a thresholded, non-negative edge list from PANDA. Kept DO: the handoff is registered (panda.yaml: "handoff_targets: [run_condor]"; "Convert that network to a source-target-weight bipartite edge list before handing it to CONDOR."), so the conversion is part of the registered chain, not a failed condition.
- **Z04** (U, input_exists): on "yes", the TF motif prior and the miRNA-target prior are separate files and must be combined so every miRNA is in prior column one (puma.yaml: "require every miRNA in prior column one"). Kept DO: combining priors is file preparation, not a contract failure; on "no", nothing builds miRNA regulators, so DECLINE.
- **Z31** (U, data_property): raw counts -> DECLINE. Kept: bonobo.yaml "The agent requires the caller to declare log_transformed=true and centered=true"; no file check can settle the property, and no workflow normalizes implicitly.
- **Z38** (FT): BONOBO would also give per-sample co-expression, but the prompt does not declare log-transformed, centred data, so only LIONESS-COEXPRESSION is listed.
- **Z24** (FSN): GIRAFFE also returns an aggregate TF-by-gene matrix, but as a signed-effect artifact (giraffe.yaml "artifact_type: signed_regulatory_effect_network"), not the regulatory network asked for, so it is not listed.
- **Z26** (FT, BONOBO with p-values): needs sparsify + save_pvals; the delta limit with sparsify applies only to a manual delta (bonobo.yaml "Empty estimates it per sample"), and the user sets none.
- **Z20** (U, COBRA): site coded 1-4 is numeric, which meets the design condition as written (cobra.yaml "numeric covariates").
- Arithmetic re-checked: Z02 500 features -> 124,750 x 30 = 3,742,500; Z18 550 -> 150,975 x 25 = 3,774,375; Z22 1,800 -> 1,619,100 x 10 = 16,191,000 (pass) vs 4,000 -> 7,998,000 x 10 = 79,980,000 (fail); Z06 15,000 > 120; Z17 80 < 200; Z20 400 > 220 / 150 < 220; Z33 20,000 > 18; Z01 2<=2<=5<=85; Z25 2<=2<=6<=140; Z16 8 vs 2 against 3; Z48 5 vs 2 against 3.
