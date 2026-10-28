#!/bin/bash
# Usage: run_measure.sh OUT_NAME   (overlap + forms on; Jev reads cached in this folder)
set -e
cd "$(dirname "$0")/../../.."
D="docs/research-log/jev-permissive-2026-10-28"
set -a; . "../../netzoo_agent/.env"; set +a
export NETZOO_JEV_GUARD=off NETZOO_JEV_OVERLAP=on NETZOO_JEV_FORMS=on
export NETZOO_JEV_FORMS_CACHE="$PWD/$D/jev-forms-cache.json" NETZOO_JEV_OVERLAP_CACHE="$PWD/$D/jev-overlap-cache.json"
python3 "$D/measure.py" "$D/$1.json" > "$D/$1.log" 2>&1
cat "$D/$1.log"
