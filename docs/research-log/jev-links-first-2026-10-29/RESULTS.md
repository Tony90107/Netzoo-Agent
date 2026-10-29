# jev-links-first phase C -- offline results (2026-10-29)

| Gate | Result |
|---|---|
| P1 unit tests (`tests/test_jev_links_first.py`, 4) | pass: rule (>= 0.7 replaces, 0.69 keeps, none -> [], error keeps); off makes no Jev call; shadow records `core.jev_links_first` and returns the reading unchanged; on applies; a Jev error keeps the reading. |
| P2 flags-off replay | 1388 readings, right 609, byte-identical to main's replay. |
| P2 clean-env tests | 5175 passed; the 2 known unrelated failures only; module size passes (router_invocation.py 991 lines). |
| P3 parity (`parity.py`) | the built `linked`, fed phase A's cached reads: 433 of 433 readings credit exactly what phase A's arm H credited. |

Recording note: `routing.capability_checked` keeps mini's own proposal; the applied links are in `core.jev_links_first`
(so a flag-on turn replays without Jev unless its reads are injected).

Offline all gates pass. P4 (fresh j7, live, paired off/on) not run yet.
