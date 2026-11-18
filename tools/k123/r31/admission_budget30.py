"""Defer expensive source admission without admitting or invalidating its input."""
from pathlib import Path
import os,json,time,signal
W=Path(__file__).resolve().parent
class Deferred(ValueError):pass
_cache=None

def run(fn,text,key,seconds=120):
 global _cache
 # The intermediate controller already owns its shorter wall deadline.
 if signal.getitimer(signal.ITIMER_REAL)[0]>0:return fn(text)
 if _cache is None:
  _cache={};p=W/'admission-deferred30.jsonl'
  if p.exists():
   for l in p.read_text().splitlines():
    try:r=json.loads(l);_cache[r['key']]=r
    except (ValueError,KeyError):pass
 load=os.getloadavg()[0]
 if key in _cache and load>min(40,_cache[key]['load']/2):raise Deferred('saved source admission budget; exact record retained')
 def expire(*args):raise Deferred('source admission exceeded wall budget')
 old=signal.getsignal(signal.SIGALRM);signal.signal(signal.SIGALRM,expire);signal.setitimer(signal.ITIMER_REAL,seconds)
 try:return fn(text)
 except Deferred:
  row={'key':key,'time':time.strftime('%FT%TZ',time.gmtime()),'load':load,'seconds':seconds,'record':json.loads(text)};_cache[key]=row
  with (W/'admission-deferred30.jsonl').open('a') as f:f.write(json.dumps(row,separators=(',',':'))+'\n')
  raise
 finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)
