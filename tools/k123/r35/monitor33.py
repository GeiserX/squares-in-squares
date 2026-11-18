"""Print a compact heartbeat while the restartable numerical drivers run."""
from pathlib import Path
import json,csv,time,collections,os
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;csv.field_size_limit(1<<28);last_handoff=0.;last_note=0.;prior='';seen=set()
while not (W/'finalize26.done').exists():
 now=time.time();records=[]
 try:
  for line in (W/'records.jsonl').read_text().splitlines():
   try:records.append(json.loads(line))
   except ValueError:pass
  rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'))
  tasks=list((W/'taskdone').glob('*.json'));fresh=len(list(W.glob('fresh[0-9]*')))
  print(time.strftime('%FT%TZ',time.gmtime())+f' k123: {len(records)} numerical attempts, {len({r["n"] for r in records})} counts, {sum(bool(r.get("raw")) for r in records)} raw crossings, {fresh} fresh pools, {len(tasks)} completed scan/cert tasks, take {[int(r["n"]) for r in rows]}.',flush=True)
  if now-last_handoff>=600:
   p=S/'handoff-r35.log';lines=p.read_text().splitlines() if p.exists() else []
   addressed=[l for l in lines if '-> k123:' in l or '-> all:' in l and any(q in l for q in ['WITHDRAW','main -> all:'])]
   for line in addressed:
    if line not in seen:print('HANDOFF '+line[:1500],flush=True);seen.add(line)
   last_handoff=now
  if now-last_note>=600:
   with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA MONITOR joins={len(records)}, fresh_pools={fresh}, take={[int(r["n"]) for r in rows]}; restartable4 boxE slots; log work/monitor33.log; common hard16:25Z, finalizer16:05Z.\n')
   last_note=now
 except (ValueError,FileNotFoundError,OSError) as e:print('TRANSIENT '+str(e)[:180],flush=True)
 if (W/'finalize26.error').exists():print('ALERT FINALIZER '+(W/'finalize26.error').read_text(),flush=True);break
 time.sleep(50)
