# App check settings aligned with the tested settings (2026-10-28)

User decision (2026-10-28, "照改"): pass the tested check settings through `docker-compose.yml`, following
app-config-gap-2026-10-28 (108 of 778 recorded turns lose a call or a check on the app's settings).

## Change (config only, no code)

| variable | before | after |
|---|---|---|
| `OPENROUTER_CAPABILITY_MODEL` | not passed (check runs on the router LLM, 1,200 cap) | `${OPENROUTER_CAPABILITY_MODEL:-}` (empty = unset, same as before) |
| `NETZOO_MAX_TASK_TOKENS` default | 20000 | 30000 |

`OPENROUTER_CAPABILITY_EXTRA_TOKENS` (30,000) and `capability_max_tokens` (4,000 for gpt-4o) are code defaults; not
added. The project `.env` already sets the check model and lists it in `NETZOO_ROUTER_MODEL_ALLOWLIST`.

## Gates (declared before the edit)

- G1 `docker compose config` resolves both services (`netzoo`, `netzoo-daemon` via `extends`) with
  `OPENROUTER_CAPABILITY_MODEL=openai/gpt-4o-mini-2024-07-18` and `NETZOO_MAX_TASK_TOKENS=30000` from the app `.env`.
- G2 With `OPENROUTER_CAPABILITY_MODEL` unset, compose passes an empty value and the code treats it as unset (no
  behaviour change for a project without it).
- G3 Offline replay of the 778 turns (simulate.py rules) on the aligned settings (30,000 turn, 4,000 own reserve, no
  1,200 cut on the check): turns losing a call <= the runners' 78, check cuts = 0.
- G4 Test suite in a clean env: no new failures beyond the two known ones.

Cost estimate (replay, gpt-4o-mini $0.15/$0.60 per M): mean US$0.0057 -> 0.0058 per turn (+~700 tokens); a lower
bound, since refused calls that now run can change what follows.

Stop rule: any gate failing -> revert the compose edit, report; no gate is relaxed after the fact.
Live re-measurement on the app's settings is listed with its cost and run only after the user agrees.
