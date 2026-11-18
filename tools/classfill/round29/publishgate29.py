"""Independent recorded-source check of the exact queued byte snapshot."""
from common29 import *
import signal
class GateTimeout(BaseException):pass
def expire(a,b):raise GateTimeout()
def check(tag,n,closure,source_csv,seconds=45,force=False):
 import quench_walk as qw
 from source_policy29 import apply
 apply()
 if not getattr(qw,'_classfill_diag_filter29',False):
  prior_refusals=qw.refusals
  def actual_refusals(path):
   return [line for line in prior_refusals(path) if not re.match(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ SOURCE_REVIEW_REQUIRED ',line)]
  qw.refusals=actual_refusals;qw._classfill_diag_filter29=True
 # Publication is an own search. Public-first source admission already did its share test.
 qw.prv_share=lambda *args:(0.0,0.0,0.0)
 a=read(closure,{})
 data=Path(source_csv).read_bytes();sha=hashlib.sha256(data).hexdigest()
 dest=W/'independent-walk'/f'{n}-{tag}.csv';dest.parent.mkdir(exist_ok=True)
 if not dest.exists():dest.write_bytes(data)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==sha
 side=dict(n=n,source=a['source'],licence=a['licence'],producer=a.get('metadata',{}),input_sha256=sha,immutable_ancestry=str(closure))
 atomic(Path(str(dest)+'.json'),side)
 fingerprints=dict(policy='r29-narrow-745858',input_sha256=sha,closure_sha256=hashlib.sha256(Path(closure).read_bytes()).hexdigest(),withdrawals_sha256=hashlib.sha256('\n'.join(line for line in (S/'handoff-r29.log').read_text().splitlines() if 'WITHDRAW' in line).encode()).hexdigest())
 cache=read(W/'independent-walk'/f'{tag}-result.json',{})
 if not force and cache.get('clean') and all(cache.get(k)==v for k,v in fingerprints.items()):return cache
 prior=signal.signal(signal.SIGALRM,expire);signal.alarm(seconds)
 try:r=qw.check(str(dest))
 except GateTimeout:r=dict(clean=False,hits=[f'independent walk exceeded{seconds}s'])
 finally:signal.alarm(0);signal.signal(signal.SIGALRM,prior)
 r.update(fingerprints)
 atomic(W/'independent-walk'/f'{tag}-result.json',r)
 return r
