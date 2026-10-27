#!/bin/bash
# Merge plan M2: flag-on replays with a fixed Jev cache. $1 = base (jev-combined, pre-refactor) | cand (jev-merge).
set -u
D="$(cd "$(dirname "$0")" && pwd)"
if [ "$1" = base ]; then TREE="$D/../../../../../netzoo-jev-combined"; RUN=(python3); else TREE="$D/../../../.."; RUN=(python3 "$D/m2_adapter.py"); fi
TREE="$(cd "$TREE" && pwd)"; cd "$TREE"
ENV=(env -i "HOME=$HOME" "PATH=$PATH" NETZOO_JEV_OVERLAP=on "NETZOO_JEV_OVERLAP_CACHE=$D/jev-cache-$1.json")
"${ENV[@]}" "${RUN[@]}" docs/research-log/stability-round13-2026-10-21/harness.py run "$D/$1-on.json" > "$D/$1-on.log" 2>&1
"${ENV[@]}" "${RUN[@]}" docs/research-log/jev-overlap-2026-10-27/replay_jsets.py "$D/$1-jsets.json" > "$D/$1-jsets.log" 2>&1
"${ENV[@]}" "${RUN[@]}" docs/research-log/jev-overlap-2026-10-27/measure_reasons.py "$D/$1-reasons.json" > "$D/$1-reasons.log" 2>&1
echo "$1 tree $TREE done; cache size $(python3 -c "import json;print(len(json.load(open('$D/jev-cache-$1.json'))))")"
