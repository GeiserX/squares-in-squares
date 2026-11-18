#!/usr/bin/env python3
"""Advance saved border chains that have closed most of a small margin.

Run with python -I prioritize_progress.py TAKE_DIR/work.
Jobs retain their inputs and flags. Only the priority changes.
The round 23 queue lives on boxC in scratch/squares-border-r23.
"""
from pathlib import Path
import json,csv,math,subprocess,datetime,sys
W=Path(sys.argv[1]).resolve();bars=json.load(open(W/'bars.json'));changed=[]
for p in (W/'q').glob('*.job.json'):
 j=json.load(open(p));rec=W/'q'/j['start'].replace('.start.txt','.k0.json')
 if not rec.exists() or p.with_suffix('.done').exists():continue
 try:r=json.load(open(rec))
 except ValueError:continue
 n=int(j['start'].split('-')[0]);bar=bars[str(n)];margin=r['s_final']-bar;giveback=r['s_start']-r['s_final'];initial=r['s_start']-bar
 if r.get('cut') and r['round']<6 and 0<margin<.001 and giveback>.001 and initial>0 and giveback/initial>.7:
  if j['priority']>-75:
   j['priority']=-75;j['progress_boost']=True;p.write_text(json.dumps(j));changed.append(p.name)
   line=f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} boxC ADOPT promising continuation {p.name}, round{r['round']}, margin{margin:.9g}, giveback{giveback:.9g}, closure{giveback/initial:.4f}. work/prioritize_progress.py, worker1/2-new.log, deadline18:30Z."
   print(line,flush=True)
   with open(W.parent/'STATE.txt','a') as f:f.write(line+'\n')
if changed:
 f=W/'progress-jobs.txt';f.write_text('\n'.join(changed)+'\n')
 subprocess.run(['rsync','-a','--files-from='+str(f),str(W/'q')+'/','boxC:scratch/squares-border-r23/q/'],check=True)
else:print('no new promising continuations',flush=True)
