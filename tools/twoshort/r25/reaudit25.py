from pathlib import Path
import json,pickle,sys,time
W=Path(__file__).parent;sys.path.insert(0,str(W));from admit25 import module_allowed,store
bad=[];jobs=[];changed=[]
for p in (W/'designs').glob('*/lib/library.pkl'):
 lib=pickle.load(open(p,'rb'));good=[m for m in lib['mods'] if module_allowed(m)];bads={m['id'] for m in lib['mods']} - {m['id'] for m in good}
 if not bads:continue
 bad.append(dict(library=str(p),ids=sorted(bads)));lib['mods']=good;pickle.dump(lib,open(p,'wb'));lp=p.parent/'lens.pkl';lens=pickle.load(open(lp,'rb'));pickle.dump({k:v for k,v in lens.items() if k not in bads},open(lp,'wb'));changed.append(str(p.parent.parent))
 for rp in [p.parent.parent/'specifications.json',p.parent.parent/'unstarted.json']:
  if rp.exists():
   rows=json.load(open(rp));rows=[r for r in rows if not any(r[k] in bads for k in ['corner','far1','far2'])];rp.write_text(json.dumps(rows,indent=2))
for p in (W/'jobs').glob('*.json'):
 j=json.load(open(p))
 if not j.get('source') or j.get('tag','').startswith('control'):continue
 if not store(dict(source=j['source'],licence=j['licence']))[0]:
  jobs.append(p.name);(W/'retired-jobs').mkdir(exist_ok=True);p.replace(W/'retired-jobs'/p.name)
out=dict(bad_libraries=bad,retired_jobs=jobs,changed_designs=changed);(W/'reaudit25.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
