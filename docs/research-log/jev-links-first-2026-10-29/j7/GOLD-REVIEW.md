# j7 gold review

## Changes

- **Y05**, `names_workflow`: false -> true. The opening request names a registered workflow (PANDA) as the source of the user's network; AUTHOR-BRIEF.md: "`names_workflow` is true when the opening request names a registered workflow." It names no grouping workflow, so `sub` go_unnamed, the call (DECLINE) and the rest of the gold stay. check_format.py also counts PANDA as named in one prompt.

No prompt or reply was changed.

## Borderline items kept unchanged

- **Y14** (U, input_exists): the registry has a `download_string` action (STRING-DOWNLOAD, `required_inputs=("taxon", "string_network_type")`), but no workflow contract says a missing PPI is fetched automatically. otter.yaml: "required_inputs: [motif_file, ppi_file, output_file]". So if no PPI exists, the request as asked is still DECLINE; the gold is kept. The assistant may still offer a STRING download as a separate step.
- **Y20** (N, n_do, COBRA): the gene count is not stated, but bulk RNA-seq on adipose has far more genes than 210 samples. cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples." DO is kept.
- **Y22** (U, data_property, BONOBO): if the data are not log-transformed, the named BONOBO run fails its declared requirement as asked. bonobo.yaml: "The agent requires the caller to declare log_transformed=true and centered=true because BONOBO assumes log-transformed centered expression." The final DECLINE is kept (log-transforming first would be a separate step the user did not ask for).
- **Y06** (SA, OTTER): PANDA could also build per-diet aggregate networks, but the stated preference for an explicit-objective fit points to OTTER (otter.yaml description: "solving a continuous-relaxation graph-matching optimization with an explicit objective"). Either is DO, so the call does not depend on the choice.
- **Y28** (U, count): recomputed. F = 1,200 + 800 = 2,000; 2,000 x 1,999 / 2 = 1,999,000 pairs; x 10 = 19,990,000 (not above 20,000,000, runs); x 12 = 23,988,000 (refused). lioness-dragon.yaml: "runs above 20,000,000 values are refused before they start".
- **Y25** (U, count): 400 > 150 passes and 120 < 150 fails; cobra.yaml: "Expression must be a labeled gene-by-sample matrix with more genes than samples."
- **Y09** (FSN): the prompt says plainly that positions will not be used. That is not a request for the excluded form, so the item stays in FSN with DO via LIONESS-COEXPRESSION (aggregate plus per-sample).
