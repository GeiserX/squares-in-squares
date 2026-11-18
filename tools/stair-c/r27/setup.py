"""Round 27: merge the three archived round 26 box libraries with the round 25 libraries
(which still hold the 110 states the round 26 Samanyu gate dropped), refilter them with
the round 27 gate (Samanyu rule lifted, prvsiyan share test added), add fresh donors
(the held 921 and every round 26 take row of bar27 in or near the slice), and stage one
box folder for three serial workers (n % 3)."""
import csv,datetime,hashlib,json,math,os,pickle,re,shutil,sys
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');L=Path('.')
T=S/'take-stair-c-r27';W=T/'work';B=W/'box'
LIBS=[W/'r26arch/n',W/'r26arch/m',W/'r26arch/s',S/'take-stair-c-r26/work/r25n',S/'take-stair-c-r26/work/r25s']
sys.path[:0]=[str(L),str(L/'tools'),str(L/'tools/stair-c/r27')]
from prepare import fingerprint
from provenance import clean,control,audit
import share27
import modules as M
control();share27.control()
HELDFILE=S/'gather/round25-2026-11-14b.csv'
held=M.read_layouts(str(HELDFILE))
SH={}
def share_of(path,n):
    key=(str(path),n)
    if key not in SH:
        try:
            lay=held[n] if path=='held' else M.read_layouts(str(path))[n]
            SH[key]=share27.share(n,M.np.asarray(lay,float)[:,:2])
        except Exception as ex:
            SH[key]=None
    return SH[key]
PATH=re.compile(r'($SCRATCH/bounties-squares/[^\s;<>]+\.csv) immutable sha256')
def origin_ok(q):
    """Rule b by share: the layout a module was cut from must share less than 0.4 with prvsiyan."""
    src=q['src'];m=re.match(r'(\d+)',q['id'])
    p=PATH.search(src)
    if p:
        n=int(os.path.basename(p[1]).split('-')[0].split('.')[0]) if os.path.basename(p[1])[0].isdigit() else (int(m[1]) if m else None)
        if n is None or not os.path.exists(p[1]):return True
        s=share_of(p[1],n);return s is None or s<share27.LIMIT
    if src.startswith('clean held gather/') and m:
        n=int(m[1])
        if n in held:
            s=share_of('held',n);return s is None or s<share27.LIMIT
    return True
EXCL=('verified-best-of-1105','joegun-boxed')
def ok(q):
    if any(t in q['src'] or t in q['licence'] for t in EXCL):return False
    if not clean(q['src'],q['licence']):return False
    return origin_ok(q)
for d in ['libbase','inbox','lane']:(B/d).mkdir(parents=True,exist_ok=True)
mods={};lens={};layouts=[];dropped={};why={}
for w in LIBS:
    a=pickle.load(open(w/'libbase/library.pkl','rb'));e=pickle.load(open(w/'libbase/lens.pkl','rb'))
    if not layouts:layouts=[l for l in a.get('layouts',[]) if l['n']==975 and l['tag']=='tw17']
    for q in a['mods']:
        fp=fingerprint(q)
        if fp in mods or fp in dropped:
            if fp in mods and q['id'] in e and mods[fp]['id']==q['id'] and q['id'] not in lens:lens[q['id']]=e[q['id']]
            continue
        if not ok(q):dropped[fp]=q['id'];continue
        mods[fp]=q
        if q['id'] in e:lens[q['id']]=e[q['id']]
print('SHARE measured',len(SH),'origins; out',sorted(k for k,v in SH.items() if v is not None and v>=share27.LIMIT),flush=True)
fix=pickle.load(open(LIBS[0]/'control-fixture.pkl','rb'))
lib=dict(mods=list(mods.values()),layouts=layouts)
ids={q['id'] for q in lib['mods']}
if not layouts:
    for w in LIBS:
        a=pickle.load(open(w/'libbase/library.pkl','rb'));layouts=[l for l in a.get('layouts',[]) if l['n']==975 and l['tag']=='tw17']
        if layouts:break
    lib['layouts']=layouts
assert layouts and set(layouts[0]['ids_slide'])<=ids|{q['id'] for q in fix['mods']}
missing=[q['id'] for q in lib['mods'] if q['id'] not in lens]
lens={k:v for k,v in lens.items() if k in ids}
pickle.dump(lib,open(B/'libbase/library.pkl','wb'));pickle.dump(lens,open(B/'libbase/lens.pkl','wb'))
shutil.copy2(LIBS[0]/'control-fixture.pkl',B/'control-fixture.pkl')
r26drop=set(json.load(open(S/'take-stair-c-r26/work/base-audit.json'))['dropped'])
back=sorted(ids&r26drop)
print('LIBRARY merged',len(lib['mods']),'states, dropped',len(dropped),'by the r27 gate, tables',len(lens),'missing tables',len(missing),'reopened r26-dropped',len(back),flush=True)
# Fresh donors: the held 921 (Samanyu rule lifted) and the round 26 take rows that bar27 holds.
bar={int(r['n']):r for r in csv.DictReader(open(S/'round27-briefs/bar27.tsv'),delimiter='\t')}
H={int(r['n']):float(r['L']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}
rec={int(r['n']):r for r in csv.DictReader(open(L/'results/round25-best-2026-11-14.tsv'),delimiter='\t')}
seen=set(mods);donors=[];refused={}
def stage(n,lay,src,lic,tag,name):
    cut,why=M.cut(M.np.asarray(lay,float),n)
    if cut is None:return 'unreadable '+str(why)
    fresh=[]
    for q in M.modules_of(cut,src,lic,tag):
        fp=fingerprint(q)
        if fp in seen:continue
        seen.add(fp);fresh.append(dict(q,ours=True))
    if not fresh:return 'no new geometry'
    pickle.dump(dict(mods=fresh,lens={},origin='candidate'),open(B/f'inbox/{name}.pkl','wb'));donors.append(name);return None
for n in [921,415,501]:
    r=rec.get(n)
    if r is None or abs(float(r['L'])-H[n])>2e-7:refused[n]='no matching round 25 record';continue
    src='clean held gather/round25-2026-11-14b.csv; results/round25-best-2026-11-14.tsv: '+r['source'];lic=r['licence']
    if not clean(src,lic):refused[n]='source gate';continue
    s=share_of('held',n)
    if s is None or s>=share27.LIMIT:refused[n]=f'prvsiyan share {s}';continue
    w=stage(n,held[n],src,lic,'r27c'+str(n),f'a-{n}')
    if w:refused[n]=w
for n,r in sorted(bar.items()):
    if 'take-' not in r['source'] or n<700:continue
    m=re.search(r'(take-[a-z0-9-]+-r26)',r['source'])
    if not m:continue
    p=S/m[1]/f'{n}.csv'
    if not p.exists():refused[n]='missing '+str(p);continue
    record=audit(p,n)
    if record is None:refused[n]='untraced '+str(p);continue
    lay=M.read_layouts(str(p))[n]
    s=share_of(p,n)
    if s is None or s>=share27.LIMIT:refused[n]=f'prvsiyan share {s}';continue
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    snap=W/'snap';snap.mkdir(exist_ok=True);shutil.copy2(p,snap/f'{n}-{digest[:12]}.csv')
    w=stage(n,lay,record['source'],record['licence'],'r27t'+digest[:12],f'a-t{n}')
    if w:refused[n]=w
print('DONORS',donors,'refused',refused,flush=True)
# Saved builds: round 26 pending queues of the three boxes, repriced against bar27.
BAR={n:(1+float(r['bar']))*math.sqrt(n) for n,r in bar.items()}
byid={q['id']:q for q in lib['mods']};byid.update({q['id']:q for q in fix['mods']})
recipes=set(pickle.load(open(LIBS[0]/'prior-recipes.pkl','rb')))
keep={}
for w in LIBS:
    st=pickle.load(open(w/'state.pkl','rb'));recipes|=st['recipes']
for w in LIBS:
    st=pickle.load(open(w/'state.pkl','rb'))
    for j in st['build']:
        if not set(j['ids'])<=set(byid):continue
        r=(j['n'],*[fingerprint(byid[k]) for k in j['ids']],*j['stacks'])
        if r in keep or j['n'] in (805,873,997):continue
        j=dict(j,bar=BAR[j['n']],patch='r26-saved '+j['patch'])
        if j['predicted']-BAR[j['n']]<.003:keep[r]=j
recipes-=set(keep)
pickle.dump(recipes,open(B/'prior-recipes.pkl','wb'))
for part in range(3):
    b=sorted((j for j in keep.values() if j['n']%3==part),key=lambda j:j['predicted']-j['bar'])
    pickle.dump(dict(imported=set(),rank=[],build=b,fresh=set(),recipes=set(),fingerprints=set(),built=0),open(B/f'state-{part}.pkl','wb'))
    print('PART',part,'saved builds',len(b),'best',[(j['n'],round(j['predicted']-j['bar'],6)) for j in b[:5]],flush=True)
for p in L.glob('*.py'):shutil.copy2(p,B/'lane'/p.name)
for name in ['prepare.py','worker.py','quench22.py','finish-box.py','exactf.py']:shutil.copy2(L/'tools/stair-c/r27'/name,B/name)
for name in ['guard.py','fq']:shutil.copy2(S/'take-stair-c-r26/work/box'/name,B/name)
# details.csv: the held file's columns, with L and score set to bar27 so ranking, recipes and
# the worker's own bar use the round 27 bar.
rows=list(csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv')))
for r in rows:
    n=int(r['n']);r['score']=repr(float(bar[n]['bar']));r['L']=repr((1+float(bar[n]['bar']))*math.sqrt(n))
with open(B/'details.csv','w') as h:
    w=csv.DictWriter(h,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
shutil.copy2(S/'main-r17/gap-by-n.tsv',B/'gap.tsv')
rr=[r for r in csv.DictReader(open(HELDFILE)) if int(r['n'])==975]
with open(B/'control975.csv','w') as f:w=csv.DictWriter(f,fieldnames=rr[0].keys());w.writeheader();w.writerows(rr)
for file,h,m in [('deadline',23,45),('search-deadline',23,15)]:(B/file).write_text(str(datetime.datetime(2026,11,14,h,m,tzinfo=datetime.timezone.utc).timestamp()))
json.dump(dict(kept=len(lib['mods']),dropped=sorted(dropped.values()),reopened=back,donors=donors,refused={str(k):v for k,v in refused.items()},saved_builds=len(keep),prior_recipes=len(recipes),share={f'{k[0]}:{k[1]}':v for k,v in SH.items()}),open(W/'base-audit.json','w'),indent=1)
