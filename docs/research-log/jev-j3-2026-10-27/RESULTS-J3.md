# j3 two-arm run (PLAN-J3.md) — ALL GATES PASS

Frozen code 00c14271 (jev-overlap tip, contains jev-guard 62bade52); j3 sealed (items.json 7a6f7fc7…). Arm F (both
flags off) and arm G (NETZOO_JEV_GUARD=on, NETZOO_JEV_OVERLAP=on), gpt-4o-mini, up to 3 turns, 48 conversations
each; spent US$0.53 (cap 1.30). Raw: RESULTS-J3.txt, gates-j3.json.

| | final right | FA | FR | MA | UNCHECKED |
|---|---|---|---|---|---|
| F | 31/48 | 5 | 7 | 4 | 1 |
| G | **35/48** | **4** | **4** | **3** | 2 |

By group F → G: GT 3→7, GO 6→6, GL 3→3, T 3→4, TC 6→5, U 4→4, N 3→3, V 3→3.
Per item: 5 improved (R05 R12 R18 R31 R34), 1 regressed (R21, check_unconfirmed); exact sign test p = 0.22.
Wrong overlap reasons on non-overlap finals: F 5 (R12 R18 R31 R34 R39) → G 1 (R39).

Gates: O1 35 >= 31+4 PASS; O2 FA 5→4, FR 7→4, MA 4→3 PASS; O3 no wrong Jev decline PASS; O4 overlap reason G 1 <= F 5
PASS; OV1 6/6 overlap requests kept DECLINE + reason, never asked PASS; OV2 4/5 GT refused by F end DO PASS; S0 0 J-ask
false alarms PASS; S1 3/3 T DO calls confirmed, TC 0 PASS; S4 0 V links PASS.

Notes: R02 (T): the confirm answer was read `meets` → DO (wrong, as in j2 Q46/Q48); R28 `fails` below 0.7. R13 (U):
after the Jev question the system re-read and declined (gold DO); arm F was MA on it. R39 (GT): credited to no
workflow and Jev not consulted, so the wrong overlap reason stays.
