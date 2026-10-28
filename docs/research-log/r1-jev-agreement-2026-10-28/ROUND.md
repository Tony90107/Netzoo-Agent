# A fact-agent question R1 rejected is asked when Jev picks the same sentence (2026-10-28, user: "下一階段的修復")

## Trace (j5 W40, gold ASK -> DO)

"I'm not sure whether the variant matrix our core facility sent contains somatic calls from tumour-normal pairs or
germline variants." The check typed no doubt (`uncertain_quotes` empty, `mutation_origin` not_stated). The fact
agent proposed the right question ("Does the variant matrix contain somatic calls from tumour-normal pairs?") and
R1 rejected it: "the check did not read these words as the user being unsure". The guard's Jev read said ASK (p 0.72)
on that very sentence (sentence confidence 1.0) but its kind confidence 0.63 < 0.7, so it did not act. DO SAMBAR.

## Evidence (recorded labelled sets j1-j5, h9, h10; turn 1)

Sessions with an R1-rejected proposal whose user words match Jev's picked sentence: 26, all on gold-ASK items, 0 on
non-ASK items. 20 already ended ASK; 4 were guard-off runs (Jev >= 0.95, the guard would ask); the rule changes 3,
all gold ASK: j1 J46 x2 (Jev 0.45, 0.37), j5 W40 (0.63).

## Change (guard flag on only; coordinated with jev-guard, whose module this is)

When the turn's call is DO, a fact-agent proposal was rejected only by that R1 rule, and Jev's read picks a sentence
holding the proposal's user words, the turn asks that proposal's question (two independent readers agree on the
doubt; Jev's kind confidence is not used). Every other R1 / R2 rule still applies to the proposal.

## Gates (declared before the code)

- **G1 (hard, precision)** recorded labelled sets: 0 sessions on non-ASK items change; the changed ones are listed.
- **G2** recorded: J46 and W40 sessions change to ASK.
- **G3** flags-off harness replay 0 of 1388; clean-env tests no new failures.
- **G4 live** (after the user agrees): W40, J46 (targets) and W18, S14, R21 (non-ASK items stating an irrelevant
  doubt; must not newly ask), turn 1, about US$0.05.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.

## Amendment (jev-guard's constraints, before any code)

- Precondition stated exactly: Jev's sentence exists only when its kind is ASK (`_read`), so the rule is "Jev kind ASK
  at any confidence + Jev's sentence holds the proposal's user words + the proposal was rejected by that R1 rule".
  R1-only is strict: the proposal is re-run through the fact check's own rules (`kept_facts`) with Jev's sentence
  added to the uncertain quotes; any other rule (R2 workflow / contract words, R3, R4 stated, R6, R7) still rejects it.
- The question is the proposal's own, asked as a fact-agent fact (basis `jev_agent`, `depends_on` unchanged, not
  `jev:`), so its answer goes the normal way and the guard's answer read (which can decline) does not apply.
- Its own function, called in `apply_jev_guard` before `guarded_core`, only when the call is DO or DECLINE; it keeps
  `asked_sentences`; a `core.jev_agent` event is recorded in shadow mode too.
- G4 controls must include non-ASK doubts Jev reads as ASK; W18, S14, R21 are the three required.

## Live addendum G4 (declared after the offline pass, before any run)

`run_live.py` (tag ra1): W40, J46 (targets), W18, S14, R21 (controls), turn 1, cap US$0.08.
- **G4a (hard):** no control ends turn 1 with a `jev_agent` ask.
- **G4b:** W40 and J46 end turn 1 ASK (any basis); reported which.
