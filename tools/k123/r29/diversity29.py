"""Run in the existing fourth boxE slot. Keep source pins and exact recipe tags."""
from pathlib import Path
import json,subprocess,sys,re,shutil
R=Path.home()/'scratch/squares-k123';j=json.load(open(sys.argv[1]));tag=j['tag'];meta=json.load(open(R/f'sources-{tag}.json'))
assert all(c.get('seed_share_gate')=='v6' for c in meta.values())
PY=str(Path.home()/'scratch/squares-base/venv/bin/python');pairs=(R/f'pairs-{tag}.txt').read_text().split()
args=[f'{tag}.csv',f'bars-{tag}.tsv',f'scan{tag}',*pairs,'--rmax','.3','--pmax','.3','--room','-.1','--mmin','10']
log=R/f'out/scan{tag}.log'
with log.open('w') as f:subprocess.run([PY,'-I','lane/k123_join_diverse29.py','scan',*args],stdout=f,stderr=f,check=True,cwd=R)
if j.get('control'):
 reference=R/'out/diversity29-control-reference.log'
 with reference.open('w') as f:subprocess.run([PY,'-I','lane/k123_join.py','scan',*args],stdout=f,stderr=f,check=True,cwd=R)
 def rows(p):
  out=set()
  for l in p.read_text().splitlines():
   m=re.search(r'n (\d+) m (\d+).*start ([\d.]+).*  (\S+) (?:WRITTEN)?$',l)
   if m:out.add(m.groups())
  return out
 old=rows(reference);new=rows(log);assert old and old<=new,(len(old),len(new),old-new)
 (R/'diversity29-control.json').write_text(json.dumps({'baseline':len(old),'diverse':len(new),'baseline_retained':True}))
 print('DIVERSITY_CONTROL',len(old),len(new),'baseline retained',flush=True)
subprocess.run([PY,'-I','divsel29.py',f'q{tag}.txt','4',str(log)],check=True,cwd=R)
lines=[]
for line in (R/f'q{tag}.txt').read_text().splitlines():
 w=line.split('\t')
 if float(w[3])>.09 or float(w[5])>.05:continue
 w.append(tag);lines.append('\t'.join(w)+'\n')
with (R/'queue.tsv').open('a') as f:f.writelines(lines)
print('DIVERSITY_QUEUED',len(lines),flush=True);shutil.rmtree(R/f'scan{tag}',ignore_errors=True)
