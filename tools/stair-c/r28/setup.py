"""Restore measured libraries and unrun recipes without replaying completed builds."""
import signal,time,csv,datetime,hashlib,json,math,pickle,shutil,sys,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('$SCRATCH/bounties-squares');LANE=Path('.');WORK=ROOT/'take-stair-c-r28/work';B=WORK/'box'
sys.path[:0]=[str(HERE),str(LANE)]
from prepare import fingerprint
from provenance import clean,control
from ancestors import audit
import share27
control();share27.control()
for d in ['libbase','inbox','lane','requests']:(B/d).mkdir(parents=True,exist_ok=True)
archives=[]
for key in ['n','m','s']:
    with tarfile.open(ROOT/'take-stair-c-r27/work/archive'/key/'final-copy.tar.gz') as tf:
        def read(name):return pickle.loads(tf.extractfile(name).read())
        archives.append((read('libbase/library.pkl'),read('libbase/lens.pkl'),read('state.pkl'),read('prior-recipes.pkl')))
        if key=='n':fixture=read('control-fixture.pkl')
mods={};lens={};dropped={};audited={};refused={}
def timeout(*a):raise TimeoutError('bounded source admission exceeded4s')
signal.signal(signal.SIGALRM,timeout)
seen_count=0
for lib,tables,st,history in archives:
    for q in lib['mods']:
        seen_count+=1
        if seen_count%100==0:print('PROGRESS',seen_count,'kept',len(mods),'dropped',len(dropped),'source groups',len(audited),flush=True)
        fp=fingerprint(q)
        if fp in mods or fp in dropped:continue
        k=hashlib.sha256((q['src']+'\0'+q['licence']).encode()).hexdigest()
        if k in refused:dropped[fp]=dict(id=q['id'],reason=refused[k]);continue
        try:
            signal.setitimer(signal.ITIMER_REAL,4)
            if not clean(q['src'],q['licence']):raise ValueError('source text or reference')
            k=hashlib.sha256((q['src']+'\0'+q['licence']).encode()).hexdigest()
            if k not in audited:audited[k]=audit(q['src'],q['licence'],q.get('n'))
        except (OSError,ValueError,KeyError,RecursionError,TimeoutError) as ex:
            signal.setitimer(signal.ITIMER_REAL,0);refused[k]=str(ex)
            dropped[fp]=dict(id=q['id'],reason=str(ex));continue
        signal.setitimer(signal.ITIMER_REAL,0)
        mods[fp]=q
        if q['id'] in tables:lens[q['id']]=tables[q['id']]
lib=dict(mods=list(mods.values()),layouts=archives[0][0]['layouts'])
pickle.dump(lib,open(B/'libbase/library.pkl','wb'));pickle.dump(lens,open(B/'libbase/lens.pkl','wb'));pickle.dump(fixture,open(B/'control-fixture.pkl','wb'))
by={q['id']:q for q in lib['mods']};completed=set();pending={}
for _,_,st,history in archives:completed.update(history);completed.update(st['recipes'])
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(ROOT/'round28-briefs/bar28.tsv'),delimiter='\t')}
for _,_,st,history in archives:
    for j in st['build']:
        if not set(j['ids'])<=set(by):continue
        recipe=(j['n'],*[fingerprint(by[k]) for k in j['ids']],*j['stacks'])
        side=(1+bar[j['n']])*math.sqrt(j['n'])
        if j['predicted']>side+.003:continue
        pending[recipe]=dict(j,bar=side,name=j['name'].replace('-r27-','-r28-'),patch='saved-r27 '+j['patch'])
completed.difference_update(pending)
pickle.dump(completed,open(B/'prior-recipes.pkl','wb'))
for part in range(3):
    jobs=sorted((j for j in pending.values() if j['n']%3==part),key=lambda j:j['predicted']-j['bar'])
    pickle.dump(dict(imported=set(),rank=[],build=jobs,fresh=set(),recipes=set(),fingerprints=set(),built=0),open(B/f'state-{part}.pkl','wb'))
    print('PART',part,'pending',len(jobs),'closest',[(j['n'],j['predicted']-j['bar']) for j in jobs[:5]],flush=True)
for p in LANE.glob('*.py'):shutil.copy2(p,B/'lane'/p.name)
for name in ['prepare.py','worker.py','quench22.py','finish-box.py']:shutil.copy2(HERE/name,B/name)
for name in ['guard.py','fq']:shutil.copy2(ROOT/'take-stair-c-r27/work/box'/name,B/name)
rr=list(csv.DictReader(open(ROOT/'gate/cand-round26-1114b/details.csv')))
for r in rr:r.update(score=repr(bar[int(r['n'])]),L=repr((1+bar[int(r['n'])])*math.sqrt(int(r['n']))))
with open(B/'details.csv','w') as f:w=csv.DictWriter(f,rr[0].keys());w.writeheader();w.writerows(rr)
shutil.copy2(ROOT/'main-r17/gap-by-n.tsv',B/'gap.tsv');shutil.copy2(ROOT/'take-stair-c-r27/work/box/control975.csv',B/'control975.csv')
for name,h,m in [('deadline',5,45),('search-deadline',5,25)]: (B/name).write_text(str(datetime.datetime(2026,11,15,h,m,tzinfo=datetime.timezone.utc).timestamp()))
(WORK/'base-audit.json').write_text(json.dumps(dict(kept=len(mods),dropped=list(dropped.values()),source_groups=len(audited),pending=len(pending),completed=len(completed)),indent=2))
# Frozen r27 changes are fresh geometry for this round, ahead of the saved queue.
reopen=sorted(str(p) for p in ROOT.glob('take-*-r27/*.csv'))
(WORK/'reopen.txt').write_text('\n'.join(reopen)+'\n')
print('LIBRARY',len(mods),'dropped',len(dropped),'source groups',len(audited),'pending',len(pending),'completed',len(completed),flush=True)
