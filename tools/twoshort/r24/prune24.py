from pathlib import Path
import sys,json,math
R=Path.home()/'scratch/squares-twoshort';sys.path.insert(0,str(R));from shape974 import load,distance
refs=json.load(open(R/'reference/index.json'));pool={};cache={};bar=json.load(open(R/'bar.json'));dropped=[]
for r in refs:pool.setdefault(r['n'],[]).append(R/r['file'])
for p in sorted((R/'jobs').glob('*.json')):
 if (R/'locks'/p.name).exists():continue
 j=json.load(open(p))
 if not j.get('start') or j.get('tag','').startswith('control'):continue
 n=j['n'];q=Path(j['start']);q=q if q.is_absolute() else R/q
 if not q.exists():continue
 a,side=load(q);duplicate=None
 if side>=bar[str(n)]-1e-10*math.sqrt(n):
  for ref in pool.get(n,[]):
   if ref not in cache:cache[ref]=load(ref)
   b,bs=cache[ref]
   if abs(side-bs)<2e-8 and distance(a,side,b)<2e-8:duplicate=str(ref);break
 if duplicate:
  dropped.append(dict(job=p.name,reference=duplicate));(R/'locks'/p.name).mkdir();(R/'done'/p.name).write_text(json.dumps(dict(j,skipped='geometry copy',reference=duplicate),indent=2))
 else:pool.setdefault(n,[]).append(q)
(R/'pruned-geometry.json').write_text(json.dumps(dropped,indent=2));print('pruned geometry copies',len(dropped))
