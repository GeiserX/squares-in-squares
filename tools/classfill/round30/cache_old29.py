from common29 import *
import signal
class SourceTimeout(BaseException):pass
def expired(a,b):raise SourceTimeout('cache source budget180s')
signal.signal(signal.SIGALRM,expired)
paths=[q['path'] for q in read(W/'reopen-ranked.json',{}).get('candidates',[]) if q['n'] in [503,700,758]]
seen=set()
for text in paths:
 n=int(Path(text).name.split('-')[0])
 if n in seen:continue
 seen.add(n);p=Path(text);sha=hashlib.sha256(p.read_bytes()).hexdigest();j={}
 for q in [p.with_suffix('.json'),Path(str(p)+'.json')]:
  if q.is_file():j.update(read(q,{}))
 src=j.get('source_override') or j.get('source','');lic=j.get('licence_override') or j.get('licence','')
 if j.get('modules'):
  src='modules.py: '+', '.join(q['id']+' <'+q['source']+'>' for q in j['modules']);lic='; '.join(sorted({q['licence'] for q in j['modules']}))
 if not src:note('CACHE_OLD_SKIP missing source '+text);continue
 note('CACHE_OLD_BEGIN '+text);start=time.time();signal.alarm(180)
 try:a,reason=audit(src,lic,j,n)
 except SourceTimeout as e:a={};reason=str(e)
 except Exception as e:a={};reason=repr(e)
 finally:signal.alarm(0)
 atomic(W/'cached-old'/f'{sha}.json',dict(input=text,sha256=sha,n=n,source=src,licence=lic,metadata=j,audit=a,reason=reason,seconds=time.time()-start))
 note(f'CACHE_OLD_END n{n} seconds{time.time()-start:.3f} reason{reason} issues'+json.dumps(a.get('history',{}).get('issues',[]))[:300]);print(n,time.time()-start,reason,flush=True)
