"""Round 26: merge the two round 25 box libraries, refilter them with the round 26
source gate, add the held rows that moved since round 23 b as fresh donors, and
stage one box folder for three serial workers (n % 3)."""
import csv,datetime,hashlib,json,math,os,pickle,shutil,sys
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');L=Path('.')
T=S/'take-stair-c-r26';W=T/'work';B=W/'box';R25=[W/'r25n',W/'r25s']
sys.path[:0]=[str(L),str(L/'tools'),str(L/'tools/stair-c/r26')]
from prepare import fingerprint
from provenance import clean,control
import modules as M
sys.path.insert(0,str(L/'tools/midm'))
import sources25
DROP=('921-29e12ff3','921r25c921','921mo16.F1d','985-r25-ba842328a07b')
# The round 25 skeptic traced take-stair-c-r22/work/boxcopy/n/raw-a/863-0f92c19d.json to our own
# corner, our own taper and malyshevdanil 984 (take-assemble-r25/skeptic.json), and base b holds
# 922 and 985 on it. The midm text gate still lists that alias, so it is normalized first.
def midm_ok(text):return sources25.clean_text(text.replace('take-stair-c-r22 near/863-0f92c19d-n','stair-c-r22-863-traced').replace('take-stair-c-r22/near/863-0f92c19d-n','stair-c-r22-863-traced'))
control()
# Positive and negative controls of the added round 26 gate.
assert not clean('module 921r25c921.F1 of held 921','our own')
assert not sources25.clean_text('parent take-stair-c-r17/near/921-29e12ff3.csv')
assert sources25.clean_text('twoshort_corner.py: staircase corner (own construction) our own')
print('CONTROL r26 gate rejects the bare 921 Samanyu file name and the held 921 module tag; accepts an own construction',flush=True)
def ok(q):
    text=q['src']+' '+q['licence']
    if any(t in text or t in q['id'] or t in q.get('tag','') for t in DROP):return False
    if not midm_ok(text):return False
    independent='held' not in q['src'] and 'take-' not in q['src'] and not q['src'].startswith('stair-c')
    if independent:return clean(q['src'],q['licence'])
    return clean(q['src'],q['licence'])
for d in ['libbase','inbox','lane']:(B/d).mkdir(parents=True,exist_ok=True)
mods={};lens={};layouts=[];dropped={}
for w in R25:
    a=pickle.load(open(w/'libbase/library.pkl','rb'));e=pickle.load(open(w/'libbase/lens.pkl','rb'))
    if not layouts:layouts=[l for l in a.get('layouts',[]) if l['n']==975 and l['tag']=='tw17']
    for q in a['mods']:
        fp=fingerprint(q)
        if fp in mods or fp in dropped:continue
        if not ok(q):dropped[fp]=q['id'];continue
        mods[fp]=q
        if q['id'] in e:lens[q['id']]=e[q['id']]
fix=pickle.load(open(R25[1]/'control-fixture.pkl','rb'))
lib=dict(mods=list(mods.values()),layouts=layouts)
ids={q['id'] for q in lib['mods']}
assert set(layouts[0]['ids_slide'])<=ids|{q['id'] for q in fix['mods']}
lens={k:v for k,v in lens.items() if k in ids}
pickle.dump(lib,open(B/'libbase/library.pkl','wb'));pickle.dump(lens,open(B/'libbase/lens.pkl','wb'))
shutil.copy2(R25[1]/'control-fixture.pkl',B/'control-fixture.pkl')
print('LIBRARY merged',len(lib['mods']),'states, dropped',len(dropped),'by the r26 gate, tables',len(lens),flush=True)
# Held rows that moved since round 23 b are the fresh donors of item 1.
new={int(r['n']):float(r['L']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}
old={int(r['n']):float(r['L']) for r in csv.DictReader(open(S/'gate/cand-round23-1113b/details.csv'))}
rec={int(r['n']):r for r in csv.DictReader(open(L/'results/round25-best-2026-11-14.tsv'),delimiter='\t')}
held=M.read_layouts(str(S/'gather/round25-2026-11-14b.csv'))
seen=set(mods);donors=[];refused={}
for n in sorted(new):
    if n<100 or n in (801,921) or not new[n]<old[n]-1e-12:continue
    r=rec.get(n)
    if r is None or abs(float(r['L'])-new[n])>2e-7:refused[n]='no matching round 25 record';continue
    src='results/round25-best-2026-11-14.tsv: '+r['source'];lic=r['licence']
    if not clean(src,lic) or not midm_ok(src+' '+lic) or any(t in src for t in DROP):refused[n]='source gate';continue
    cut,why=M.cut(M.np.asarray(held[n],float),n)
    if cut is None:refused[n]='unreadable '+str(why);continue
    fresh=[]
    for q in M.modules_of(cut,'clean held gather/round25-2026-11-14b.csv; '+src,lic,'r26c'+str(n)):
        fp=fingerprint(q)
        if fp in seen:continue
        seen.add(fp);fresh.append(dict(q,ours=True))
    if not fresh:refused[n]='no new geometry';continue
    pickle.dump(dict(mods=fresh,lens={},origin='candidate'),open(B/f'inbox/a-{n}.pkl','wb'));donors.append(n)
print('DONORS',donors,'refused',refused,flush=True)
# Saved builds of round 25, repriced against base b.
H={int(r['n']):float(r['L']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}
byid={q['id']:q for q in lib['mods']};byid.update({q['id']:q for q in fix['mods']})
recipes=set(pickle.load(open(R25[1]/'prior-recipes.pkl','rb')))
keep={};pending=[]
for w in R25:
    st=pickle.load(open(w/'state.pkl','rb'));recipes|=st['recipes']
    for j in st['build']:
        if not set(j['ids'])<=set(byid):continue
        r=(j['n'],*[fingerprint(byid[k]) for k in j['ids']],*j['stacks'])
        if r in keep:continue
        j=dict(j,bar=H[j['n']],patch='r25-saved '+j['patch'])
        if j['predicted']-H[j['n']]<.004:keep[r]=j
recipes-=set(keep)
pickle.dump(recipes,open(B/'prior-recipes.pkl','wb'))
for part in range(3):
    b=sorted((j for j in keep.values() if j['n']%3==part),key=lambda j:j['predicted']-j['bar'])
    pickle.dump(dict(imported=set(),rank=[],build=b,fresh=set(),recipes=set(),fingerprints=set(),built=0),open(B/f'state-{part}.pkl','wb'))
    print('PART',part,'saved builds',len(b),'best',[(j['n'],round(j['predicted']-j['bar'],6)) for j in b[:5]],flush=True)
for p in L.glob('*.py'):shutil.copy2(p,B/'lane'/p.name)
for name in ['prepare.py','worker.py','quench22.py','finish-box.py']:shutil.copy2(L/'tools/stair-c/r26'/name,B/name)
for name in ['guard.py','fq']:shutil.copy2(R25[1]/name,B/name)
shutil.copy2(S/'gate/cand-round25-1114b/details.csv',B/'details.csv');shutil.copy2(S/'main-r17/gap-by-n.tsv',B/'gap.tsv')
rr=[r for r in csv.DictReader(open(S/'gather/round25-2026-11-14b.csv')) if int(r['n'])==975]
with open(B/'control975.csv','w') as f:w=csv.DictWriter(f,fieldnames=rr[0].keys());w.writeheader();w.writerows(rr)
for file,h,m in [('deadline',17,15),('search-deadline',16,45)]:(B/file).write_text(str(datetime.datetime(2026,11,14,h,m,tzinfo=datetime.timezone.utc).timestamp()))
json.dump(dict(kept=len(lib['mods']),dropped=sorted(dropped.values()),donors=donors,refused={str(k):v for k,v in refused.items()},saved_builds=len(keep),prior_recipes=len(recipes)),open(W/'base-audit.json','w'),indent=1)
