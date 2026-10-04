# Path (b) freeze (Log 355 preparation)

The study-purpose call's instruction, proposal contract and verification rules were
frozen before anyone on the implementing side read the fifth held-out set
(`heldout5/`), which an isolated subagent wrote while the call was implemented.

Frozen copies in `b_frozen/` (sha256):
- `495f7e19b0611bf833d9b990d4f448cf880c34bfdc6ab015d1ce2f2add09a800` study_purpose_verify.py
- `cb2c1fcdde6e056c27d06a153ebae8130c89b4e11b45ab10d19e00dd05be2de8` study_purpose.py
- `e2af95adf863ba89dff8108f6f1254e7f1f41f74ebd4d582d000177820fd491b` study_purpose_system.txt

- `study_purpose_system.txt` is `netzoo_agent_core.llm.STUDY_PURPOSE_SYSTEM`, word for word Log 354's prototype prompt.
- `study_purpose_verify.py` reproduces Log 354's `b_prototype/verify.py` S2 exactly: on the 387 recorded
  proposals the implemented and prototype verifications differ in 0 rows (design 254/297, 0 false;
  conclusions 237/264, 0 false; 0 false causal/prediction).
- Model: openai/gpt-4o-mini, temperature 0, strict function calling, as in Log 354.

Any change to these after this commit must be declared and reported separately
from the fifth held-out results.
