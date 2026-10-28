# The tie question's default line names only workflows the check credited (2026-10-28, user: "先修預設建議")

## Trace

gu1 W01 ("... rather than any per-sample networks"): the reply's separating question ends "If none of these applies:
PANDA, LIONESS-PANDA." The condition recommender writes that line in routing, before the capability check runs
(`invoke_router`: `_route_request` -> check), from the routing candidates; with the granularity left unknown they
include the per-sample LIONESS-PANDA. The check credited PANDA, PUMA, OTTER, GIRAFFE only.

All recorded replies with the line (55; 35 distinct requests, `survey.py` below): it names workflows the check did
not credit in requests of both scales -- PANDA beside LIONESS-PANDA for "a network for each of our 25 patients"
(credited LIONESS-PANDA only), LIONESS-PANDA for "an aggregate PANDA network" (credited PANDA only), and PANDA where
the user named OTTER, CONDOR or PUMA (credited only that).

## Change

After the check is attached (end of `invoke_router`'s checked path), the default line keeps only the workflows the
check credited for a result; the line is dropped when none remain; nothing changes when the check credited no result
(full gap, unavailable) or the question has no such line. The options and their questions are unchanged.

## Gates (declared before the code)

- **D1** recorded replies (`survey.py`): every changed line keeps only credited names; lines whose check credited
  nothing are unchanged; per-sample requests keep LIONESS-PANDA, aggregate ones drop it (listed per request).
- **D2** unit tests: filter, drop when empty, unchanged without credited results or without the line.
- **D3** clean-env tests: no new failures; flags-off replay 0 of 1388.
- Live only after the user agrees: W01 turn 1 (the line no longer names LIONESS-PANDA) plus one per-sample request
  from the survey (keeps LIONESS-PANDA); about US$0.02.

Stop rule: a failed gate -> withdraw; no gate is changed afterwards.
