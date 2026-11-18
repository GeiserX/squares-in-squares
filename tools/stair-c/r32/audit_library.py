"""Recheck cached module sources against the public-first root rule."""
import datetime,hashlib,json,pickle,signal,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import public_roots as P
W=P.ROOT
class SourceTimeout(BaseException):pass
def timeout(*a):raise SourceTimeout('library public-root proof exceeded 20 seconds')
signal.signal(signal.SIGALRM,timeout)
lib=pickle.load(open(W/'box/libbase/library.pkl','rb'));groups={}
for path in (W/'donors').glob('*.pkl'):
    data=pickle.load(open(path,'rb'));lib['mods'].extend(data.get('mods',[]))
for q in lib['mods']:groups.setdefault((q['src'],q['licence']),[]).append(q['id'])
results=[];excluded=[]
prior=json.load(open(W/'library-public-exclusions.json'))if(W/'library-public-exclusions.json').exists()else[]
for index,((source,licence),ids)in enumerate(groups.items()):
    if time.time()>float((W/'box/search-deadline').read_text()):break
    try:
        signal.setitimer(signal.ITIMER_REAL,20)
        record=P.audit(dict(source=source,licence=licence));signal.setitimer(signal.ITIMER_REAL,0)
        result=dict(ids=ids,allowed=True,record=record)
    except (OSError,ValueError,KeyError,RecursionError,TimeoutError,SourceTimeout)as ex:
        signal.setitimer(signal.ITIMER_REAL,0);result=dict(ids=ids,allowed=False,reason=str(ex));excluded.append(source)
        with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA DEFER cached source group '+','.join(ids)+' after public-root audit: '+str(ex)[:240]+'; bytes remain in frozen archive.\n')
    results.append(result)
    temp=W/'library-public-exclusions.json.tmp';temp.write_text(json.dumps(sorted(set(prior+excluded))));temp.replace(W/'library-public-exclusions.json')
    if index%20==0:print('AUDIT',index+1,'of',len(groups),'deferred',len(excluded),flush=True)
temp=W/'library-public-exclusions.json.tmp';temp.write_text(json.dumps(excluded));temp.replace(W/'library-public-exclusions.json')
out=W/'library-public-audit.json';out.write_text(json.dumps(dict(groups=len(groups),modules=len(lib['mods']),deferred_groups=len(excluded),results=results),indent=2))
print('LIBRARY PUBLIC AUDIT',len(groups),'groups',len(excluded),'deferred',flush=True)
