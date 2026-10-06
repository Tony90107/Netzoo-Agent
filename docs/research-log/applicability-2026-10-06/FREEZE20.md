# Log 380 freeze: each listed workflow judged against the request's data (plan item 4)

Frozen before anyone on the implementing side read the twentieth held-out set (`heldout20/`). An isolated
subagent writes that set after this freeze.

**Frozen change:** `ap_frozen.patch`, sha256 `913c84f2acc6`.
- It is the diff of `scripts/` and `tests/` against `161f33d`, new files included. 18 files.
- It is applied in the clean worktree `.worktrees/netzoo-ap-cand`.
- It does not touch the regex session's `interpretation/extraction.py`.

**Reading.** The Log 376 data-facts call, restored, plus a miRNA field.
- `DataFactsProposal` reads `priors` and `mirna`. Each is stated, ruled_out or unstated, with a quote.
- The prompt now lives in `graph/data_facts_call.py`, because `llm.py` reached its size bound.
  - Prompt hash `732e9fb607bd`, schema hash `566ae2e4f927`.
  - The study-purpose prompt and schema are unchanged: `e2af95adf863` / `83461bb34d77`.
- Verification only checks provenance: a reading with an empty quote, or a quote not found in the request, becomes unstated.
- The call is made after routing, only for a guidance decision that lists a workflow needing TF priors or miRNA that the request does not bind as files.
- If the call is unconfigured, blocked or fails, nothing changes.

**Judgement** (`interpretation/applicability.py`, `TaskDecision.data_facts` / `.applicability`, all code-owned):
- Every listed workflow gets a status:
  - applicable: every needed input is stated;
  - not_applicable: a needed input is ruled out;
  - insufficient_information: a needed input is unstated.
- Each status carries its basis: the kind, the state, the quote, and its source.
- For a kind the reading judged, the reading replaces the request's wording. `PresentInputs.judged` and `.absent` carry it into `missing_input_labels`, so no loose word list can overrule it. Log 373's "no transcription factor motifs" no longer counts as having them.
- Event `routing.applicability_assessed`. The judgement is also recorded in `RequestRequirements`.

**Effects** (reply and card only; nothing is selected, ranked or removed, and nothing executes):
- **Exact match.**
  - A workflow judged short of data is not presented as "Selected path"; the reply leads with the condition:
    - "**X** fits the result you describe, but it needs …, which you said you do not have."
    - "**X** fits the result you describe if you have …."
  - The card headline says the same.
- **Log 312's paragraph and card ("What your data allows").** They now run on the reading.
  - They also trigger when no alternative exists, as long as the reading judged the kind.
  - Kinds the request ruled out are stated in its own words and never asked about.
  - Only kinds the reading judged unstated are asked about.
  - A workflow that is already ruled out is not asked about any other input.
  - With no alternative, nothing is claimed about "every registered workflow".
- **Tie.** An advisory recommendation of a workflow the reading rules out is dropped (event field `recommendation_dropped`).

**Seen data only (calibration, not a verdict).**
- `facts_eval.py` on heldout16–19, 96 calls each.
  - Priors: 0 read as stated when not stated. Stated recall 36/36, 33/33, 33/33, 45/45. Ruled-out recall 18/27, 17/27, 27/27, 24/24. This matches Log 376.
  - miRNA: on heldout19, stated 12/12 with 0 false. Unlabelled sets read stated only for T6, whose request does state miRNA targets.
- `ap_dev.py` replays the recorded decisions with the dev readings and re-renders the replies.

  | Set | Priors stated | Priors ruled out | Priors unstated | Changed replies |
  |---|---|---|---|---|
  | s19 | 0 priors questions | — | asks 9/9 (before 6/9) | 3/50 |
  | s18 | 0 priors questions | 0 questions; 21/24 say the user does not have them | asks 23/23 (before 0) | 47/77 |

  - s18 annotation `data_question`:
    - asks when "priors": 20/20;
    - asks when "none": 3 — all T5, where routing chose GIRAFFE for a question BONOBO answers.
  - s18 B1/B2, where routing fell back to PUMA alone: 3 questions about a miRNA list. These are correct: priors are stated, miRNA is not, and PANDA and LIONESS-PANDA are named as the alternatives.
  - 3 s18 sessions could not render under either version, because of the >8-option card bug owned by another session.

**Checks.**
- Clean worktree: 3379 passed / 35 skipped. Base `161f33d` has 3359; 20 tests are new in `test_applicability.py`. Updated tests pin the new data-facts role and the TaskDecision schema digest.
- Fingerprints: legacy `e920bf3b5d57`, claims `743b2dd0d73a`, unchanged.
- One deliberate behaviour change against an existing test's spirit: a workflow that needs priors the request never mentions now draws a question (F3), not only a "Not mentioned" note. The note's old test still passes, because it carries no reading.
