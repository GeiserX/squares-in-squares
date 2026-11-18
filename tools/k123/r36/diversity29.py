"""Run in the existing fourth boxE slot. Keep source pins and exact recipe tags."""
from pathlib import Path
import json,subprocess,sys,re,shutil
R=Path.home()/'scratch/squares-k123';j=json.load(open(sys.argv[1]));tag=j['tag'];meta=json.load(open(R/f'sources-{tag}.json'))
assert all(c.get('seed_share_gate')=='v6' for c in meta.values())
PY=str(Path.home()/'scratch/squares-base/venv/bin/python');pairs=(R/f'pairs-{tag}.txt').read_text().split()
args=[f'{tag}.csv',f'bars-{tag}.tsv',f'scan{tag}',*pairs,'--rmax','.3','--pmax','.3','--room','-.1','--mmin','10']
args.extend(['--seam-bins',str(j.get('seam_bins',3))])
log=R/f'out/scan{tag}.log'
with log.open('w') as f:subprocess.run([PY,'-I','lane/k123_join_diverse29.py','scan',*args],stdout=f,stderr=f,check=True,cwd=R)
if j.get('control'):
 reference=R/'out/diversity29-control-reference.log'
 with reference.open('w') as f:subprocess.run([PY,'-I','lane/k123_join.py','scan',*args[:-2]],stdout=f,stderr=f,check=True,cwd=R)
 def rows(p):
  out=set()
  for l in p.read_text().splitlines():
   m=re.search(r'n (\d+) m (\d+).*start ([\d.]+).*  (\S+) (?:WRITTEN)?$',l)
   if m:out.add(m.groups())
  return out
 old=rows(reference);new=rows(log);assert old and old<=new,(len(old),len(new),old-new)
 (R/'diversity29-control.json').write_text(json.dumps({'baseline':len(old),'diverse':len(new),'baseline_retained':True,'seam_bins':j.get('seam_bins',3)}))
 print('DIVERSITY_CONTROL',len(old),len(new),'baseline retained',flush=True)
import os
selector='divsel30.py' if j.get('board_targets') else 'divsel29.py'
env=dict(os.environ);env['K123_ALLOW_BOARD_COUNTS']=','.join(map(str,j.get('board_targets',[])))
subprocess.run([PY,'-I',selector,f'q{tag}.txt',str(j.get('starts_per_count',4)),str(log)],check=True,cwd=R,env=env)
if j.get('board_control'):
 baseline=R/f'q{tag}-baseline.txt'
 subprocess.run([PY,'-I','divsel29.py',str(baseline),str(j.get('starts_per_count',4)),str(log)],check=True,cwd=R)
 a=set(baseline.read_text().splitlines());b=set((R/f'q{tag}.txt').read_text().splitlines());assert a<=b,(a-b)
 added=[l for l in b-a if int(l.split('\t')[0]) in j['board_targets']];assert added,'target override produced no added starts'
 result={'baseline_retained':len(a),'total':len(b),'added_target_starts':len(added),'targets':j['board_targets']};(R/'board-selector-control30.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)

lines=[]
for line in (R/f'q{tag}.txt').read_text().splitlines():
 w=line.split('\t')
 if float(w[3])>.09 or float(w[5])>.05:continue
 w.append(tag);lines.append('\t'.join(w)+'\n')
with (R/'queue.tsv').open('a') as f:f.writelines(lines)
print('DIVERSITY_QUEUED',len(lines),flush=True);shutil.rmtree(R/f'scan{tag}',ignore_errors=True)
