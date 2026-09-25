# P4 legacy original-eight review failures: root cause

Date: 2026-09-23

## Round-5 failure and later status

In the saved round-5 trace, `mirna-case-lower` fell back after semantic review
failed. Its round-6 trace no longer has a failing trial; the original-eight
legacy batch is 22/24 overall with 24/24 route passes, and the remaining two
failures are `mirna-per-person` review-acceptance failures.

## Current failure mechanism

For `mirna-per-person`, round-6 trials 2 and 3 already have an exact
`run_lioness_puma` route. The initial interpretation leaves `operation` as
`unknown`; the reviewer changes it to `explain` and adds an `explicit`
`operation=explain` evidence entry without a verbatim `text_span`. The typed
`SemanticPatch` rejects those additions because explicit evidence must quote
the request. The router keeps the initial exact route but correctly records
that no semantic review was accepted.

This is not a wrong-method or unsafe-execution failure. It is a reviewer
evidence-policy failure: “Which registered method ...? I only want advice.”
supports guidance mode, but it does not contain the literal operation value
`explain`.

## Decision boundary

Making this pass would require changing what counts as evidence for
`operation=explain` in guidance mode, or changing the semantic-acceptance rule
when a reviewer patch fails only on operation evidence. Either changes the
interpretation contract. I made no code change here; that policy is independent
of the P2 and P3 routing fixes above.

## Follow-up after user authorization (2026-09-24)

The user approved deriving `explain` from explicit advice intent in guidance
requests. The implementation is limited to that condition: a request must
contain advice/recommendation language, the effective request mode must be
`guidance`, and the operation must be `explain`. Only then is unquoted
`operation=explain` support normalized from `explicit` to `inferred`. Other
unquoted fields keep the strict explicit-quote requirement.

The same provenance rule now applies to both semantic contracts. Claims that
label `explain` explicit are changed to inferred under the same advice/guidance
condition. For legacy review patches, an unquoted `entity_type` addition is
given an exact quote only when an explicit regulator-to-target witness in the
request entails that entity; this handles the accompanying `mirna`/`gene`
additions without relaxing evidence validation.

Offline replay of the saved round-6 legacy `mirna-per-person` trials 2 and 3
now parses each patch, passes outcome validation, and matches exactly to
`run_lioness_puma`. The saved claims trials 1–3 remain valid and match the same
action; their `explain` support is now correctly recorded as inferred. A control
with the advice phrase removed receives no normalization. These were saved
provider-response replays; no new model call or workflow execution occurred.

Python compilation, Ruff, and `git diff --check` passed. No full test suite or
new live round was run.
