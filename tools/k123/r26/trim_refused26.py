"""Remove queued donor identities that the current source audit refused."""
import pathlib,sys,json,re,hashlib,subprocess,fcntl,time
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
lock=open(W/'trim-refused26.lock','a')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit
state=json.load(open(W/'collect-state.json'));keys=sorted(k for k,r in state.items() if r.get('status')=='source-refused')
signature=hashlib.sha256(json.dumps(keys).encode()).hexdigest();memo=W/'trim-refused26.json'
previous=json.load(open(memo)) if memo.exists() else {}
if previous.get('signature')==signature:raise SystemExit
from source25 import audit
bad=set(previous.get('geometries',[]))
for key in keys:
 parts=key.split('-',2)
 if len(parts)!=3:continue
 pool,tag=parts[1:];match=re.match(r'(\d+)r?-(\d+)r?-j',tag)
 if not match:continue
 path=W/pool/('sources-'+pool+'.json')
 if not path.exists():path=W/('sources-'+pool+'.json')
 if not path.exists():continue
 manifest=json.load(open(path))
 for n in match.groups():
  credit=manifest[n]
  if state[key].get('source_check_file') or audit(credit) is None:bad.add(credit['sha256_geometry'])
refused=json.load(open(W/'refused-inputs26.json')) if (W/'refused-inputs26.json').exists() else {}
for path in W.glob('*/sources-*.json'):
 pool=path.stem.removeprefix('sources-');manifest=json.load(open(path));ns=set(refused.get(pool,[]))
 ns.update(n for n,c in manifest.items() if c.get('sha256_geometry') in bad)
 if ns:refused[pool]=sorted(ns,key=int)
# A useful clean pair must remain eligible when unrelated bad roots are removed.
assert not {'375','986'}&set(refused.get('fresh10440',[])),'clean375/986 control was removed'
target=W/'refused-inputs26.json';target.with_suffix('.tmp').write_text(json.dumps(refused,separators=(',',':')));target.with_suffix('.tmp').replace(target)
control='/tmp/squares-k123-r26-ssh'
subprocess.run(['scp','-q','-o','ControlPath='+control,str(target),'boxE:scratch/squares-k123/refused-inputs26.json.tmp'],check=True)
subprocess.run(['ssh','-S',control,'boxE','mv $SCRATCH/squares-k123/refused-inputs26.json.tmp $SCRATCH/squares-k123/refused-inputs26.json'],check=True)
record={'signature':signature,'geometries':sorted(bad),'pools':len(refused),'donors':sum(map(len,refused.values()))};memo.write_text(json.dumps(record))
print('TRIM CONTROL clean375/986 retained; refused geometries',len(bad),'pools',len(refused),flush=True)
with open(W.parent/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f" boxA FINISH trim_refused26.py: {len(bad)} refused geometry identities excluded from {len(refused)} pools; clean375/986 positive control retained; work/trim-refused26.json; deadline17:15Z.\n")
lock.close()
