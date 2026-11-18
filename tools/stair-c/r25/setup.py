"""Stage only clean exact tables, new donors and lane code for two serial boxes."""
import csv,datetime,glob,hashlib,json,os,pickle,shutil,sys
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');L=Path('.');W=S/'take-stair-c-r25/work';B=W/'box'
sys.path[:0]=[str(L),str(L/'tools/stair-c/r25')]
from prepare import fingerprint
from provenance import clean,held_record,control
import modules as M
control()
for d in ['libbase','inbox','lane']: (B/d).mkdir(parents=True,exist_ok=True)
a=pickle.load(open(S/'take-stair-c-r24/work/box/libbase/library.pkl','rb'));e=pickle.load(open(S/'take-stair-c-r24/work/box/libbase/lens.pkl','rb'))
mods=[];rejected=[]
for q in a['mods']:
 text=q['src'];pure=q['licence']=='our own' and ('twoshort_corner.py: staircase corner' in text or 'zone_search.py: taper enumeration' in text) and not any(t in text for t in ('held','stair-c_design.py','sc22zip','upright wall column'))
 if pure and clean(text,q['licence']):mods.append(dict(q,ours=True))
 else:rejected.append(q['id'])
ids={q['id'] for q in mods};control_layout=next(l for l in a['layouts'] if l['n']==975 and l['tag']=='tw17')
assert set(control_layout['ids_slide'])<=ids
lib=dict(mods=mods,layouts=[control_layout]);lens={k:v for k,v in e.items() if k in ids}
pickle.dump(lib,open(B/'libbase/library.pkl','wb'));pickle.dump(lens,open(B/'libbase/lens.pkl','wb'))
by={q['id']:q for q in mods};cs=[by[k] for k in control_layout['ids_slide']]
pickle.dump(dict(mods=cs,lens={q['id']:lens[q['id']] for q in cs}),open(B/'control-fixture.pkl','wb'))
seen={fingerprint(q) for q in mods};donors=[]
# The current held file is an allowed pool. Attach its matching source record.
held=M.read_layouts(str(S/'gather/round23-2026-11-13b.csv'))
for n in sorted(held):
 if n<100:continue
 record=held_record(n)
 if not record:continue
 cut,why=M.cut(M.np.asarray(held[n],float),n)
 if cut is None:continue
 fresh=[]
 for q in M.modules_of(cut,'clean held gather/round23-2026-11-13b.csv; results/round23-best-2026-11-13.tsv; '+record['source'],record['licence'],'r25c'+str(n)):
  fp=fingerprint(q)
  if fp in seen:continue
  seen.add(fp);fresh.append(dict(q,ours=True))
 if not fresh:continue
 pickle.dump(dict(mods=fresh,lens={},origin='candidate'),open(B/f'inbox/a-{n}.pkl','wb'));donors.append(n)
for p in L.glob('*.py'):shutil.copy2(p,B/'lane'/p.name)
for name in ['prepare.py','worker.py']:shutil.copy2(L/'tools/stair-c/r25'/name,B/name)
for name in ['guard.py','fq','py-n','py-s']:shutil.copy2(S/'take-stair-c-r24/work/box'/name,B/name)
(B/'py-n').write_text('#!/bin/sh\nexec /Users/boxC/scratch/squares-stair-c/venv/bin/python \"$@\"\n')
os.chmod(B/'py-n',0o755)
shutil.copy2(L/'tools/stair-c/r25/quench22.py',B/'quench22.py')
json.dump(held_record(975),open(B/'control975.source.json','w'))
shutil.copy2(S/'gate/cand-round23-1113b/details.csv',B/'details.csv');shutil.copy2(S/'main-r17/gap-by-n.tsv',B/'gap.tsv')
rr=[r for r in csv.DictReader(open(S/'gather/round23-2026-11-13b.csv')) if int(r['n'])==975]
with open(B/'control975.csv','w') as f:w=csv.DictWriter(f,fieldnames=rr[0].keys());w.writeheader();w.writerows(rr)
for file,h,m in [('deadline',2,45),('search-deadline',2,15)]: (B/file).write_text(str(datetime.datetime(2026,11,14,h,m,tzinfo=datetime.timezone.utc).timestamp()))
shutil.copy2(S/'take-stair-c-r24/work/prior-recipes.pkl',B/'prior-recipes.pkl')
json.dump(dict(kept=len(mods),dropped=len(rejected),candidate_donors=donors),open(W/'base-audit.json','w'),indent=2)
print('PREP',len(mods),'independent modules;',len(rejected),'excluded inherited states;',len(donors),'readable traced held designs',donors,flush=True)
