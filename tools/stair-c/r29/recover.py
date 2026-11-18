"""Retry deferred source groups after fixing donor-count and optional-sidecar handling."""
import csv,datetime,hashlib,json,math,pickle,signal,subprocess,sys,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('$SCRATCH/bounties-squares');W=ROOT/'take-stair-c-r29/work';L=Path('.')
sys.path[:0]=[str(HERE),str(L)]
from provenance import clean
from ancestors import audit
from prepare import fingerprint
base=json.loads((W/'base-audit.json').read_text());wanted={r['id'] for r in base['dropped'] if r['reason'].startswith(('missing complete ancestor','missing ancestor record','bounded source','excluded complete ancestor','source text or reference','changed pinned ancestor'))}
groups={};completed=set();jobs={}
for key in ['n','m','s']:
 with tarfile.open(ROOT/'take-stair-c-r28/work/archive'/key/'final-copy.tar.gz')as tf:
  lib=pickle.loads(tf.extractfile('libbase/library.pkl').read());lens=pickle.loads(tf.extractfile('libbase/lens.pkl').read())
  for q in lib['mods']:
   if q['id'] in wanted:
    group=hashlib.sha256((q['src']+'\0'+q['licence']).encode()).hexdigest();groups.setdefault(group,{})[fingerprint(q)]=(q,lens.get(q['id']))
seen=set();receipts=[]
# Reuse exact module packets already staged by the first pass.
for packet in (W/'recovery').glob('r29-reopen-rule-*.pkl'):
 try:
  old=pickle.load(open(packet,'rb'));seen.update(fingerprint(q)for q in old['mods'])
 except (OSError,ValueError,KeyError):pass
def timeout(*a):raise TimeoutError('retry source budget8s')
signal.signal(signal.SIGALRM,timeout)
for group,values in groups.items():
 if all(fp in seen for fp in values):continue
 if time.time()>__import__('datetime').datetime(2026,11,15,11,25,tzinfo=__import__('datetime').timezone.utc).timestamp():break
 q=next(iter(values.values()))[0]
 try:
  signal.setitimer(signal.ITIMER_REAL,8)
  if not clean(q['src'],q['licence']):raise ValueError('source gate')
  checks=audit(q['src'],q['licence'],q.get('n'))
 except (OSError,ValueError,KeyError,RecursionError,TimeoutError)as ex:
  signal.setitimer(signal.ITIMER_REAL,0);receipts.append(dict(group=group,accepted=False,reason=str(ex)));continue
 signal.setitimer(signal.ITIMER_REAL,0)
 pairs=[(fp,q,t)for fp,(q,t)in values.items()if fp not in seen]
 for offset in range(0,len(pairs),3):
  batch=pairs[offset:offset+3];mods=[q for fp,q,t in batch];tables={q['id']:t for fp,q,t in batch if t is not None}
  dest=W/'recovery'/f'r29-reopen-rule-{group[:12]}-{offset}.pkl';dest.parent.mkdir(exist_ok=True)
  pickle.dump(dict(mods=mods,lens=tables,origin='recovered source group'),open(dest,'wb'))
  for host in ['boxC','boxD','boxE']:
   try:r=subprocess.run(['rsync','-a',str(dest),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40);assert r.returncode==0
   except Exception as ex:print('COPYFAIL',host,str(ex),flush=True)
  seen.update(fp for fp,q,t in batch)
 receipts.append(dict(group=group,accepted=True,states=len(pairs),checks=checks));print('RECOVERED',group[:12],len(pairs),flush=True)
(W/'recovery-audit.json').write_text(json.dumps(dict(groups=receipts,states=len(seen)),indent=2))
with (W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA FINISH recovery '+str(len(seen))+' states from fixed count inference/optional metadata; full source and complete ancestor tests retained. Log work/recovery.log; deadline11:45Z.\n')
