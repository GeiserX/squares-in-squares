import pathlib,json,sys,signal,time,os
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A,source_gate28 as G
manifest=json.load(open(W/'saved-shortlist.json'))
j=next(v for v in manifest if v['id']=='r24-n202134x985x139')
result=dict(id=j['id'],path=j['start'])
def expired(*unused):raise TimeoutError('600-second source-only audit bound reached')
signal.signal(signal.SIGALRM,expired);signal.alarm(min(600,max(1,int(float((W/'deadline').read_text())-time.time()))))
try:
 p=pathlib.Path(j['start']);a=A.audit(p,j['n'],j['source'],j['licence'])
 result['graph']=a
 if a.get('ok'):
  signal.alarm(min(600,max(1,int(float((W/'deadline').read_text())-time.time()))))
  e=G.freeze_unbounded(p,j['n'],a['proof']);result['evidence']=e
  if e['clean']:
   checked=G.check(dict(id='independent985',n=j['n'],evidence=e['path'],evidence_sha256=e['sha256']),p);result['check']=checked
   if checked['clean']:
    ready=W/'audit-ready.json';tmp=ready.with_suffix('.tmp');tmp.write_text(json.dumps([j]));tmp.replace(ready)
except Exception as e:result['error']=repr(e)
signal.alarm(0);(W/'audit985-result.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
with (W.parent/'STATE.txt').open('a')as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' FINISH independent985 source-only audit; work/audit985-result.json; common05:45Z.\n')
