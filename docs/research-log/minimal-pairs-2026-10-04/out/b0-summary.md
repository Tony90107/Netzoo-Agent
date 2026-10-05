# Minimal pairs `b0` summary

| id | rep | status | candidates | recommended | card question; understood goal | compare_step | causal_limit | predictor | outside_netzoo | calls | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which regulator type should the network model: transcription; Understood goal: a cohort-level regulatory network from expression data. |  | y | y |  | 7 | 0.0027 |
| A0 | 2 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which regulator type should the network model: transcription; Understood goal: a cohort-level regulatory network from expression data. |  | y | y |  | 7 | 0.0020 |
| A0 | 3 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which regulator type should the network model: transcription; Understood goal: a cohort-level regulatory network from expression data. |  | y | y |  | 7 | 0.0019 |
| A1 | 1 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. | y | y | y |  | 7 | 0.0024 |
| A1 | 2 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. | y | y | y |  | 7 | 0.0022 |
| A1 | 3 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. | y | y | y |  | 7 | 0.0020 |
| A2 | 1 | ambiguous | run_lioness_panda, run_lioness_puma |  | Which regulator type should the network model: transcription; Understood goal: a per-sample TF-gene regulatory network from expression data. | y |  | y |  | 7 | 0.0023 |
| A2 | 2 | ambiguous | run_lioness_panda |  |  | y | y |  |  | 4 | 0.0013 |
| A2 | 3 | ambiguous | run_lioness_panda, run_lioness_puma |  | Which regulator type should the network model: transcription; Understood goal: a per-sample TF-gene regulatory network from expression data. | y |  | y |  | 7 | 0.0019 |
| A3 | 1 | exact | run_giraffe |  |  | y | y | y |  | 5 | 0.0018 |
| A3 | 2 | exact | run_giraffe |  |  | y | y | y |  | 5 | 0.0013 |
| A3 | 3 | exact | run_giraffe |  |  | y | y | y |  | 5 | 0.0013 |
| A4 | 1 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. | y | y |  |  | 7 | 0.0023 |
| A4 | 2 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. | y | y |  |  | 7 | 0.0020 |
| A4 | 3 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. | y | y |  |  | 7 | 0.0019 |
| A5 | 1 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 7 | 0.0024 |
| A5 | 2 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 7 | 0.0020 |
| A5 | 3 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 7 | 0.0020 |
| B1 | 1 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. | y |  |  |  | 7 | 0.0022 |
| B1 | 2 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. | y |  |  |  | 7 | 0.0020 |
| B1 | 3 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. | y |  |  |  | 7 | 0.0019 |
| B2 | 1 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 5 | 0.0016 |
| B2 | 2 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 5 | 0.0019 |
| B2 | 3 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 5 | 0.0015 |
| B3 | 1 | ambiguous | run_giraffe, run_lioness_panda, run_lioness_puma, run_otter, run_panda, run_puma |  | Do you also have a motif prior and a PPI network?; Understood goal: a regulatory network from expression data. |  | y | y | y | 7 | 0.0025 |
| B3 | 2 | None |  |  |  |  |  | y | y | 3 | 0.0019 |
| B3 | 3 | None |  |  |  |  |  | y | y | 3 | 0.0013 |

## Modal shape per prompt

- A0: ('ambiguous', ('run_giraffe', 'run_otter', 'run_panda', 'run_puma'), None) ×3
- A1: ('ambiguous', ('run_giraffe', 'run_otter', 'run_panda', 'run_puma'), None) ×3
- A2: ('ambiguous', ('run_lioness_panda', 'run_lioness_puma'), None) ×2
- A3: ('exact', ('run_giraffe',), None) ×3
- A4: ('ambiguous', ('run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'), None) ×3
- A5: ('ambiguous', ('run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'), None) ×3
- B1: ('ambiguous', ('run_cobra', 'run_lioness_coexpression'), None) ×3
- B2: ('ambiguous', (), None) ×3
- B3: (None, (), None) ×2

Total cost $0.0526