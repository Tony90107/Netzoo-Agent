#!/bin/bash
# usage: grids.sh <repo> <outdir>   -- five grids + diff against base
set -e
R="$1"; O="$2"; B=/private/tmp/claude-501/-Users-chenzhonghan-Documents-LLM-AGENT/cbd53668-e381-48a0-b25e-c6c49743fe66/scratchpad/base
mkdir -p "$O"; cd "$R"
python docs/research-log/log136_outcome_grid.py "$O/g.json" >/dev/null
python docs/research-log/log148_evidence_grid.py "$R" "$O/eg.json" >/dev/null
python docs/research-log/log170_guidance_grid.py "$R" "$O/gg.json" >/dev/null
python docs/research-log/log174_tag_grid.py "$R" "$O/tg.json" >/dev/null
python docs/research-log/log150_pair_grid.py "$R" "$O/pg.json" >/dev/null
for g in g eg gg tg pg; do if cmp -s "$B/$g.json" "$O/$g.json"; then echo "$g identical"; else echo "$g DIFFERS"; fi; done
