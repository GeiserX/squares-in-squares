#!/bin/zsh
# one line per job of the rebuild boxes: done jobs (last 8) and running jobs with their raw finds and best side so far
date -u +%T
for b in boxB boxE; do echo "== $b"; ssh $b 'cd $SCRATCH/squares-rebuild 2>/dev/null || cd $SCRATCH/squares-rebuild; tail -8 done.jsonl 2>/dev/null | python3 -c "
import sys,json
for l in sys.stdin:
  r=json.loads(l); print(\"done\",r[\"key\"],r[\"n\"],\"start %.10f\"%r.get(\"start_side\",0),\"side\",r.get(\"side\"),\"room %s\"%r.get(\"room\"),\"probe_stop\",r.get(\"probe_stop\"),r.get(\"t0\"),r.get(\"t1\"),r.get(\"error\",\"\"))
"; for d in out/*/; do k=$(basename $d); [ -f $d/done.json ] && continue; echo "run $k $(ls $d/raw 2>/dev/null | wc -l | tr -d " ") raw; tries $(cat $d/scan-*.tsv 2>/dev/null | grep -vc "^#"); min side $(grep -hv "^#" $d/scan-*.tsv 2>/dev/null | cut -f5 | sort -g | head -1); $(ls $d/raw 2>/dev/null | tail -1)"; done; echo "queue: $(cut -f1 queue.tsv | while read k; do [ -d claims/$k ] || echo -n "$k "; done)"'; done
