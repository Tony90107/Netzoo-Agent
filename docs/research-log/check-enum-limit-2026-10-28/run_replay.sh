#!/bin/bash
# Usage: run_replay.sh OUT_NAME on|off   (flags-on = overlap + forms through adapter.py; Jev reads cached in this folder)
set -e
cd "$(dirname "$0")/../../.."
D="docs/research-log/check-enum-limit-2026-10-28"
set -a; . "../../netzoo_agent/.env"; set +a
export NETZOO_JEV_GUARD=off NETZOO_JEV_OVERLAP="$2" NETZOO_JEV_FORMS="$2"
export NETZOO_JEV_FORMS_CACHE="$PWD/$D/jev-forms-cache.json" NETZOO_JEV_OVERLAP_CACHE="$PWD/$D/jev-overlap-cache.json"
python3 docs/research-log/jev-forms-2026-10-27/adapter.py docs/research-log/stability-round13-2026-10-21/harness.py \
  run "$D/$1.json" > "$D/$1.log" 2>&1
tail -2 "$D/$1.log"
