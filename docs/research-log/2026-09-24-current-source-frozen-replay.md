# 2026-09-24 current-source frozen-response replay

## Scope

Continued the semantic-routing review using the saved routing-family traces. No
provider or network calls were made. The replay used saved structured responses
only, matched the complete recorded message sequence (including system-message
hashes), and did not reuse any saved response. Corpus, policy, and contract
prompt/schema fingerprints match rounds 3–6.

The saved corpus contains 32 prompts with three repetitions each. Historical
system-message bodies are redacted, so matching the recorded system-message
hash is the available guard for that part of the input. These replay results
measure only the prompts for which the current call sequence has an exact saved
response; they do not estimate live model accuracy.

## Change made

The role witness recognized `TF-to-gene`, but missed the hyphenated
`transcription-factor-to-gene` form, the English phrase “microRNAs regulate
their target genes”, and the Chinese construction “miRNA 如何調控基因”. Added
these bounded forms to the existing explicit role-pair witness in
`request_integrity.py`.

The restoration helper already removed `unknown` regulator/target placeholders
when an explicit role pair closed those dimensions. When the known role values
were already present, however, no restoration record was emitted. Its final
no-change guard then returned the original outcome and silently restored the
placeholders. It now records that placeholder resolution against the explicit
request span, so the corrected outcome is retained in
`stated_field_restoration.py`.

## Replay results

| Contract | Exact semantic-call coverage | Exact full-pipeline coverage | Full-pipeline covered trials passing |
| --- | ---: | ---: | ---: |
| Legacy | 75/96 | 70/96 | 70/70 |
| Claims | 78/96 | 65/96 | 62/65 |

“Full-pipeline coverage” requires exact saved replies for every model call in
that trial, including intent routing. All 75 legacy trials with exact semantic
responses reached the expected route and passed semantic scoring. Claims had
three full-coverage failures: the route status was the expected `ambiguous`, but
the semantic-completeness reviewer returned a no-op or invalid response. The
affected trials were two repetitions of `gran-mirna-unstated-control` and one
of `role-tf-agg-control-en`.

The targeted role cases improved in all three claims repetitions:

- `gran-tf-ss-individual-en` → exact `run_lioness_panda` (3/3)
- `role-mirna-ss-en` → exact `run_lioness_puma` (3/3)
- `zh-compare-patients-ss` → exact `run_lioness_puma` (3/3)

The latter two were previously falling back despite explicit miRNA/gene and
sample-specific evidence. This is a case-level non-regression result; the
contract-wide denominators differ because the changed route can produce
different reviewer and intent prompts for which historical responses do not
exist.

## Remaining issue and next step

The residual failures are concentrated in semantic-completeness review of
ambiguous guidance. The frozen trace shows the router selecting the expected
ambiguous status, but the claims evaluator does not accept the interpretation
without a successful review response. Changing that acceptance rule from replay
evidence alone would risk accepting a genuinely incomplete ambiguity, so the
next useful check is a small live A/B on five prompts: the three targeted role
cases above plus `gran-mirna-unstated-control` and `role-tf-agg-control-en`, in
both contracts, one repetition each. Cap the batch at 40 provider calls (four
per prompt/contract maximum). No live calls are included in this report.

## Verification

- Frozen-response replay: completed for legacy and claims, rounds 3–6.
- `git diff --check`: passed.
- Automated test suite: not run.
