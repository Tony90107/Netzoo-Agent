# Answered counts -- live A4 (2026-10-29, user "跑 live"): PASS -> KEPT

Runs ac1 (X02, X22, up to 3 turns) and ac2 (W40 t1): code b29b5d52, app settings, gpt-4o-mini. Spent **US$0.034**.

| item | t1 | t2 | final vs gold |
|---|---|---|---|
| j6 X22 (150 or 400 metabolites) | ASK/count_fact "Which of these is right: 150 or 400?" | "400" bound; `jev_agent: already_asked`; **DECLINE/full_gap**: "LIONESS-DRAGON writes at most 20,000,000 values (features x (features - 1) / 2 x samples); 800 features and 100 samples give 31,960,000." | **right** (DECLINE) |
| j6 X02 (design table exists?) | ASK/jev_agent | "yes" bound; `jev_agent: already_asked`; DO | **right** (DO) |
| j5 W40 | ASK/jev_agent, somatic question shown | -- | right (asks) |

- **A4 pass:** X22 DECLINE, X02 DO, W40 asks.
- X22's turn-2 reading again typed no doubt (`unknown_facts` empty); the decline comes from part 3 applying the
  answered "400" -- the case that failed in ad1. The reason is the code-verified limit with both numbers.

Seen in passing, not gated: X22's turn 2 also printed "Router output invalid -- using deterministic fallback /
Semantic routing unavailable" and ends "Retry this request when semantic routing is available", although the check
and the decline were complete. A follow-up turn's interpreter failure shown beside a finished answer; a candidate for
a later round.
