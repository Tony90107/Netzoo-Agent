# Minimal pairs `s1` summary

| id | rep | status | candidates | recommended | card question; understood goal | compare_step | causal_limit | predictor | outside_netzoo | calls | $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A0 | 1 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which regulator type should the network model: transcription; Understood goal: a cohort-level regulatory network from expression data. |  | y | y |  | 6 | 0.0030 |
| A0 | 2 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which regulator type should the network model: transcription; Understood goal: a cohort-level regulatory network from expression data. |  | y | y |  | 6 | 0.0019 |
| A0 | 3 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0021 |
| A1 | 1 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0027 |
| A1 | 2 | ambiguous | run_giraffe, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a cohort-level TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0019 |
| A1 | 3 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda, run_puma |  | Which reading should we start with? | y | y | y |  | 6 | 0.0030 |
| A2 | 1 | exact | run_lioness_panda |  |  |  |  |  |  | 4 | 0.0013 |
| A2 | 2 | exact | run_lioness_panda |  |  |  |  |  |  | 4 | 0.0013 |
| A2 | 3 | ambiguous | run_lioness_panda, run_lioness_puma |  | Which regulator type should the network model: transcription; Understood goal: a per-sample TF-gene regulatory network from expression data. |  |  | y |  | 6 | 0.0023 |
| A3 | 1 | exact | run_giraffe |  |  |  | y | y |  | 4 | 0.0020 |
| A3 | 2 | exact | run_giraffe |  |  |  | y | y |  | 4 | 0.0012 |
| A3 | 3 | exact | run_giraffe |  |  |  | y | y |  | 4 | 0.0013 |
| A4 | 1 | ambiguous | run_giraffe, run_lioness_panda, run_lioness_puma, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0025 |
| A4 | 2 | ambiguous | run_giraffe, run_lioness_panda, run_lioness_puma, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0019 |
| A4 | 3 | ambiguous | run_giraffe, run_lioness_panda, run_lioness_puma, run_otter, run_panda, run_puma |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y | y |  | 6 | 0.0025 |
| A5 | 1 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 6 | 0.0023 |
| A5 | 2 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 6 | 0.0019 |
| A5 | 3 | ambiguous | run_giraffe, run_lioness_panda, run_otter, run_panda |  | Which method fits your study?; Understood goal: a TF-gene regulatory network from expression data. |  | y |  |  | 6 | 0.0023 |
| B1 | 1 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. |  |  |  |  | 6 | 0.0021 |
| B1 | 2 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. |  |  |  |  | 6 | 0.0019 |
| B1 | 3 | ambiguous | run_cobra, run_lioness_coexpression |  | Which method fits your study?; Understood goal: a cohort-level co-expression network from expression data. |  |  |  |  | 6 | 0.0017 |
| B2 | 1 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 4 | 0.0014 |
| B2 | 2 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 4 | 0.0015 |
| B2 | 3 | ambiguous |  |  | Which reading should we start with? | y |  | y | y | 4 | 0.0014 |
| B3 | 1 | None |  |  |  |  |  |  |  | 2 | 0.0017 |
| B3 | 2 | None |  |  |  |  |  |  |  | 2 | 0.0017 |
| B3 | 3 | None |  |  |  |  |  |  |  | 2 | 0.0017 |

## Modal shape per prompt

- A0: ('ambiguous', ('run_giraffe', 'run_otter', 'run_panda', 'run_puma'), None) ×3
- A1: ('ambiguous', ('run_giraffe', 'run_otter', 'run_panda', 'run_puma'), None) ×2
- A2: ('exact', ('run_lioness_panda',), None) ×2
- A3: ('exact', ('run_giraffe',), None) ×3
- A4: ('ambiguous', ('run_giraffe', 'run_lioness_panda', 'run_lioness_puma', 'run_otter', 'run_panda', 'run_puma'), None) ×3
- A5: ('ambiguous', ('run_giraffe', 'run_lioness_panda', 'run_otter', 'run_panda'), None) ×3
- B1: ('ambiguous', ('run_cobra', 'run_lioness_coexpression'), None) ×3
- B2: ('ambiguous', (), None) ×3
- B3: (None, (), None) ×3

Total cost $0.0525