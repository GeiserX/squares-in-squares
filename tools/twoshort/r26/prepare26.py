"""Re-admit the round 25 saved module specifications with the round 26 bare-name walk and stage them as specs jobs."""
from pathlib import Path
import pickle,json,sys,math,time,shutil
W=Path(__file__).parent;B=W.parent.parent;O=B/'take-twoshort-r25/work/boxE25/designs'
sys.path.insert(0,str(W));from admit26 import module_allowed;from bar26 import bars
_,_,_,live=bars();bar={n:(s+1)*math.sqrt(n) for n,s in live.items()}
claims=(B/'handoff-r26.log').read_text()
stats=[];queue=[]
for name in ['library-original-union25','saved25-library-modules-227fa9ea-acfbf39b']:
 d=O/name;rows=json.load(open(d/'unstarted.json'))
 if any('backlog ->' in l and name in l and 'claim' in l.lower() for l in claims.splitlines()):stats.append(dict(origin=str(d),skipped='backlog claim'));continue
 lib=pickle.load(open(d/'lib/library.pkl','rb'));lens=pickle.load(open(d/'lib/lens.pkl','rb'));want={r[k] for r in rows for k in ['corner','far1','far2']}
 verdict={m['id']:module_allowed(m) for m in lib['mods'] if m['id'] in want}
 good={i for i,v in verdict.items() if v}
 clean=[r for r in rows if all(r[k] in good for k in ['corner','far1','far2'])]
 for r in clean:r['predicted_side']=float(r.get('predicted_side',r.get('predicted',float(r.get('held_side',bar[int(r['n'])]))+float(r.get('predicted_minus_held',0)))))
 clean.sort(key=lambda r:r['predicted_side']-bar[int(r['n'])])
 stats.append(dict(origin=str(d),total=len(rows),clean=len(clean),dropped=len(rows)-len(clean),refused_modules=sorted(i for i,v in verdict.items() if not v),best_fit=[(r['n'],r['predicted_side']-bar[int(r['n'])]) for r in clean[:8]]))
 if not clean:continue
 tag='saved26-'+name;dd=W/'designs'/tag;(dd/'lib').mkdir(parents=True,exist_ok=True)
 want={r[k] for r in clean for k in ['corner','far1','far2']};lib['mods']=[m for m in lib['mods'] if m['id'] in want];lib['layouts']=[]
 pickle.dump(lib,open(dd/'lib/library.pkl','wb'));pickle.dump({k:v for k,v in lens.items() if k in want},open(dd/'lib/lens.pkl','wb'))
 (dd/'specifications.json').write_text(json.dumps(clean,indent=2));(dd/'intake.json').write_text(json.dumps(stats[-1],indent=2))
 queue.append(tag)
(W/'pending-admission.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=1));print('queue',queue)
