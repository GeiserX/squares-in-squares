"""Restore byte-pinned round 29 libraries and reprice only unmeasured recipes."""
import csv,datetime,hashlib,json,math,pickle,shutil,signal,sys,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('$SCRATCH/bounties-squares')
LANE=Path('.')
WORK=ROOT/'take-stair-c-r33/work';B=WORK/'box'
sys.path[:0]=[str(HERE),str(LANE)]
from prepare import fingerprint
from provenance import clean,control
from ancestors import audit
from public_roots import audit as public_audit,warm
from saved_all import gather,control as saved_control
control();saved_control();warm()
for d in ['libbase','inbox','lane','requests','cert-in','donors']:(B/d).mkdir(parents=True,exist_ok=True)
archives=[];mods={};lens={};checked={};dropped={}
class SourceTimeout(BaseException):pass
def timeout(*a):raise SourceTimeout('source admission exceeded 8 seconds')
signal.signal(signal.SIGALRM,timeout)
for key in ['n','m','s']:
    archive=ROOT/f'take-stair-c-r32/work/archive/{key}/final-copy.tar.gz'
    with tarfile.open(archive) as tf:
        read=lambda name:pickle.loads(tf.extractfile(name).read())
        lib=read('libbase/library.pkl');tables=read('libbase/lens.pkl');st=read('state.pkl');history=read('prior-recipes.pkl')
        records=[json.loads(tf.extractfile(m).read())for m in tf.getmembers()if m.name.startswith('raw-a/')and m.name.endswith('.json')]
        archives.append((lib,st,history,records))
        if key=='n':
            fixture=read('control-fixture.pkl')
            for name in ['control975.csv','corner-guard-control.json','corner-stacks-control.json','bar-probe-control.json','closed-corners.json','two-stacks-control.json']:
                (B/name).write_bytes(tf.extractfile(name).read())
        for q in lib['mods']:
            fp=fingerprint(q)
            if fp in mods or fp in dropped:continue
            group=hashlib.sha256((q['src']+'\0'+q['licence']).encode()).hexdigest()
            if group not in checked:
                try:
                    signal.setitimer(signal.ITIMER_REAL,8)
                    if not clean(q['src'],q['licence']):raise ValueError('source proof refused')
                    audit(q['src'],q['licence'],q.get('n'))
                    public_audit(dict(source=q['src'],licence=q['licence']));checked[group]=None
                except (OSError,ValueError,KeyError,RecursionError,TimeoutError,SourceTimeout)as ex:checked[group]=str(ex)
                finally:signal.setitimer(signal.ITIMER_REAL,0)
            if len(checked)%20==0:print('SOURCE PROGRESS',key,len(checked),'states',len(mods),'deferred',len(dropped),flush=True)
            if checked[group]:dropped[fp]=dict(id=q['id'],reason=checked[group]);continue
            mods[fp]=q
            if q['id']in tables:lens[q['id']]=tables[q['id']]
    print('RESTORE',key,'states',len(mods),'deferred',len(dropped),flush=True)
data=gather(archives,fingerprint)
bar={int(r['n']):float(r['bar'])for r in csv.DictReader(open(ROOT/'round33-briefs/bar33.tsv'),delimiter='\t')}
by={q['id']:q for q in mods.values()}
pending=[]
for j in data['jobs']:
    if not set(j['ids'])<=set(by):continue
    side=(1+bar[j['n']])*math.sqrt(j['n'])
    if j['predicted']>side+.003:continue
    pending.append(dict(j,bar=side,name=j['name'].replace('-r32-','-r33-').replace('-r29-','-r33-'),patch='saved-r29 '+j['patch']))
pickle.dump(dict(mods=list(mods.values()),layouts=archives[0][0]['layouts']),open(B/'libbase/library.pkl','wb'))
pickle.dump(lens,open(B/'libbase/lens.pkl','wb'));pickle.dump(fixture,open(B/'control-fixture.pkl','wb'))
pickle.dump(data['completed'],open(B/'prior-recipes.pkl','wb'))
pickle.dump(data,open(B/'saved-jobs.pkl','wb'))
for part in range(3):
    jobs=sorted((j for j in pending if j['n']%3==part),key=lambda j:j['predicted']-j['bar'])
    pickle.dump(dict(imported=set(),rank=[],build=jobs,fresh=set(),recipes=set(),fingerprints=set(),built=0),open(B/f'state-{part}.pkl','wb'))
for p in LANE.glob('*.py'):shutil.copy2(p,B/'lane'/p.name)
for p in HERE.glob('*.py'):shutil.copy2(p,B/p.name)
shutil.copy2(LANE/'tools/border/r28/finesafe.py',B/'lane/stair_finesafe.py')
for name in ['guard.py','fq']:shutil.copy2(ROOT/'take-stair-c-r31/work/box'/name,B/name)
rr=list(csv.DictReader(open(ROOT/'gate/cand-round28-1115b/details.csv')))
for r in rr:r.update(score=repr(bar[int(r['n'])]),L=repr((1+bar[int(r['n'])])*math.sqrt(int(r['n']))))
with open(B/'details.csv','w')as f:w=csv.DictWriter(f,rr[0].keys());w.writeheader();w.writerows(rr)
shutil.copy2(ROOT/'main-r17/gap-by-n.tsv',B/'gap.tsv')
for name,day,h,m in [('deadline',17,0,15),('search-deadline',16,23,55),('kick-deadline',17,0,10),('pack-deadline',17,0,22)]:
    (B/name).write_text(str(datetime.datetime(2026,11,day,h,m,tzinfo=datetime.timezone.utc).timestamp()))
# Reopen frozen changed layouts, with fresh r30 handoffs retaining priority.
reopen=sorted(str(p)for p in ROOT.glob('take-*-r32/*.csv'))
(WORK/'reopen.txt').write_text('\n'.join(reopen)+'\n')
(WORK/'base-audit.json').write_text(json.dumps(dict(kept=len(mods),dropped=list(dropped.values()),source_groups=len(checked),pending=len(pending),completed=len(data['completed']),all_unrun=len(data['jobs'])),indent=2))
print('READY',len(mods),'states',len(pending),'priced jobs',len(data['jobs']),'all unrun',flush=True)
