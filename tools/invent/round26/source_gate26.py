"""Use the independent full walker and current withdrawal records before publication."""
import csv,hashlib,importlib,json,pathlib,re,sys,time,shutil
W=pathlib.Path(__file__).resolve().parent;S=W.parents[1];R=pathlib.Path('.')
sys.path.insert(0,str(R));import quench_walk as Q
CACHE=W/'independent-cache.json';cache=json.load(open(CACHE))if CACHE.exists()else{}

def banned(text):
 pairs={'harvest':(416,499,646,654,695,814),'k123':(546,695,932,922),'forensics':(416,654,694,695,748,850,932)}
 for lane,counts in pairs.items():
  for n in counts:
   if re.search(r'take-'+lane+r'-r26/'+str(n)+r'\.csv\b',text):return 'withdrawn current donor '+lane+'/'+str(n)
 for purge in (S/'take-forensics-r26/work/withdrawal-purge.json',S/'take-forensics-r26/work/withdrawal-purge-final.json'):
  if purge.exists():
   for p in json.load(open(purge)).get('withdrawn_near',[]):
    if p in text:return 'withdrawn rectangle '+p
 if '/take-twoshort-r26/work/withdrawn/'in text:return 'producer-quarantined twoshort input'
 return None

def token(p):
 try:s=pathlib.Path(p).stat();return [s.st_mtime_ns,s.st_size]
 except OSError:return None

def notices():
 return hashlib.sha256((str([(str(p),token(p))for p in (R/'quench_walk.py',R/'quench_audit.py',R/'forensics_policy.py')])+'\n'+'\n'.join(l for l in (S/'handoff-r26.log').read_text().splitlines()if any(v in l.lower()for v in ('withdr','withhold','purge','source correction','stop using')))).encode()).hexdigest()

def check(job,path):
 path=pathlib.Path(path);proof=pathlib.Path(job['ancestry']);text=proof.read_text();why=banned(text)
 if why:return dict(clean=False,hits=[why],files=0)
 key='private-v2:'+job['id']+':'+hashlib.sha256(path.read_bytes()+text.encode()).hexdigest();old=cache.get(key);sig=notices()
 if old and old['notices']==sig and time.time()<old['expires'] and all(token(p)==stamp for p,stamp in old['paths'].items()):return old['result']
 # Attach the exact recorded source to this immutable end, without changing its CSV bytes.
 a=json.loads(text);lic='; '.join(dict.fromkeys(v['licence']for v in a['nodes'].values()))
 audit=W/'source-audit'/job['id']/path.name;audit.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,audit)
 side=pathlib.Path(str(audit)+'.json');side.write_text(json.dumps(dict(n=job['n'],source='invent_rest.py local kick, floatsafe and completed certified-file fq; source metadata '+str(proof),licence=lic)))
 importlib.reload(Q.quench_audit);importlib.reload(Q.forensics_policy);importlib.reload(Q)
 walked={};original=Q.walk
 def capture(*args,**kwargs):
  result=original(*args,**kwargs);walked['seen']=result[2];return result
 Q.walk=capture
 try:result=Q.check(str(audit))
 finally:Q.walk=original
 paths={p:token(p)for p in walked.get('seen',[])if isinstance(p,str)and p.startswith('/')}
 cache[key]=dict(result=result,paths=paths,expires=time.time()+300,notices=sig)
 temp=CACHE.with_suffix('.tmp');temp.write_text(json.dumps(cache));temp.replace(CACHE)
 (W/'independent-results').mkdir(exist_ok=True);(W/'independent-results'/f'{job["id"]}.json').write_text(json.dumps(result,indent=2))
 return result
