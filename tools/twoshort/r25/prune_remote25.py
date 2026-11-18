from pathlib import Path
import pickle,json,time
R=Path.home()/'scratch/squares-twoshort';bad=[]
for p in (R/'jobs').glob('*.json'):
 if p.name in json.load(open(R/'retire-remote.json')):
  (R/'retired-jobs').mkdir(exist_ok=True);p.replace(R/'retired-jobs'/p.name);bad.append(p.name)
rows=[]
for p in (R/'designs').glob('*/lib/library.pkl'):
 ids={m['id'] for m in pickle.load(open(p,'rb'))['mods']}
 for q in [p.parent.parent/'unstarted.json',p.parent.parent/'specifications.json']:
  if q.exists():
   r=json.load(open(q));good=[x for x in r if all(x[k] in ids for k in ['corner','far1','far2'])];q.write_text(json.dumps(good,indent=2));rows.append((str(q.relative_to(R)),len(r),len(good)))
(R/'prune-full-tree.json').write_text(json.dumps(dict(retired=bad,specifications=rows),indent=2));print('retired',len(bad),'tables',len(rows))
