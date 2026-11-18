"""Stage fresh and deferred joins with immutable input and ancestry records."""
import pathlib,sys,json,csv,re,collections,hashlib,subprocess,os,time,tarfile,io
from provenance24 import W,S,R,mlp,credit,key,banned
from eligible24 import SPECIAL,BARS
from source25 import audit as runtime_audit
assert 'r28-full-tree-v5-pin:' in runtime_audit.__code__.co_consts,'stale source admission module'
sys.path.insert(0,str(W/'lane'));import k123_join as kj
import importlib
importlib.reload(kj)
os.chdir(W)
remote_bytes=1024*int(subprocess.check_output(['ssh','-S','/tmp/squares-k123-r28-ssh','boxE','du -sk $SCRATCH/squares-k123'],text=True).split()[0])
if remote_bytes>2800000000:raise RuntimeError('boxE scratch budget: staging paused above 2.8GB')
from thin23 import select as thin_select
def journal(msg):
 with open(W.parent/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+msg+'\n')
from producer_guard28 import same_producer_records

def _stage(tag,P,origins,pairs,kind,source):
 # Bound admission before walking every partner on the paging collector.
 if len(pairs)>16:
  common=collections.Counter(nn for pair in pairs for nn in pair).most_common(1)[0][0]
  needed={nn for pair in pairs for nn in pair};levels={nn:int(mlp.side(P[nn])) for nn in needed};frac={nn:float(mlp.side(P[nn]))-levels[nn] for nn in needed}
  selected=set(thin_select(sorted(needed-{common}),frac,levels,frac[common],levels[common],limit=12))|{common}
  deferred={'tag':tag,'source':source,'planned_pairs':pairs,'selected':sorted(selected),'reason':'pre-admission cap: local paging delayed the prior full donor walk by over20 minutes'}
  with open(W/'pre-admission-deferred27.jsonl','a') as h:h.write(json.dumps(deferred)+'\n')
  pairs=[(a,b) for a,b in pairs if a in selected and b in selected]
 need={nn for pair in pairs for nn in pair};P={n:A for n,A in P.items() if n in need}
 D=W/tag;D.mkdir(exist_ok=True);manifest={}
 for n,A in P.items():
  op=pathlib.Path(origins.get(n,''));initial_raw=op.read_bytes() if op.is_file() else None
  producer_paths=[pathlib.Path(str(op)+'.json'),op.with_suffix('.json'),op.parent/'take.tsv'] if initial_raw is not None else []
  initial_records={str(ep):ep.read_bytes() for ep in producer_paths if ep.is_file()}
  ledger_body=initial_records.get(str(op.parent/'take.tsv'))
  if ledger_body and op.stem.isdigit():
   producer_row=next((z for z in csv.DictReader(io.StringIO(ledger_body.decode('utf-8-sig')),delimiter='\t') if z.get('n')==str(n)),None)
   if not producer_row or abs(float(producer_row['new'])-(mlp.side(A)/n**.5-1))>1e-12:
    journal('DEFER producer score differs from numeric input '+str(op));continue
  c=credit(n,A,origins.get(n))
  if c:
   snap=W/'input-snapshots';snap.mkdir(exist_ok=True)
   op=pathlib.Path(origins.get(n,''))
   if initial_raw is not None:
    if not op.is_file() or op.read_bytes()!=initial_raw or not same_producer_records(initial_records,{str(ep):ep.read_bytes() for ep in producer_paths if ep.is_file()},n):
     journal('DEFER changed input or producer record during admission '+str(op));continue
    raw=initial_raw;sha=hashlib.sha256(raw).hexdigest();dest=snap/(str(n)+'-'+sha+'.csv')
    if not dest.exists():dest.write_bytes(raw)
    if key(n,mlp.load(str(dest),{n})[n])!=key(n,A):
     journal('DEFER queue byte snapshot differs from numeric array '+str(op));continue
    c={**c,'input_file_snapshot':str(dest),'input_file_sha256':sha}
    records={}
    for name,rr in initial_records.items():
     ep=pathlib.Path(name)
     hh=hashlib.sha256(rr).hexdigest();dd=snap/(hh+ep.suffix)
     if not dd.exists():dd.write_bytes(rr)
     records[str(ep)]={'snapshot':str(dd),'sha256':hh}
    c['input_record_snapshots']=records
   manifest[str(n)]=c
 pairs=[(a,b) for a,b in pairs if str(a) in manifest and str(b) in manifest]
 if not pairs:return False
 need={n for pair in pairs for n in pair}
 with open(D/(tag+'.csv'),'w') as f:
  w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
  for n in sorted(need):w.writerows((n,i,*r) for i,r in enumerate(P[n]))
 (D/('sources-'+tag+'.json')).write_text(json.dumps(manifest))
 (D/'pool-sha256.txt').write_text(hashlib.sha256((D/(tag+'.csv')).read_bytes()).hexdigest())
 (D/('bars-'+tag+'.tsv')).write_text((W/'bars.tsv').read_text())
 remote_csv=D/(tag+'.csv');remote_manifest=D/('sources-'+tag+'.json')
 if remote_bytes>1700000000 and len(need)>16:
  common=collections.Counter(nn for a,b in pairs for nn in (a,b)).most_common(1)[0][0]
  others=sorted(need-{common});levels={nn:int(mlp.side(P[nn])) for nn in need};frac={nn:float(mlp.side(P[nn]))-levels[nn] for nn in need}
  keep=set(thin_select(others,frac,levels,frac[common],levels[common],limit=15))|{common}
  plan=dict(tag=tag,source=source,full_input=str(D/(tag+'.csv')),planned_pairs=pairs,selected=sorted(keep),reason='1.7GB watermark; productive ends retained, including928')
  (D/'cap-deferred24.json').write_text(json.dumps(plan))
  with open(W/'cap-deferred24.jsonl','a') as h:h.write(json.dumps(plan)+'\n')
  pairs=[(a,b) for a,b in pairs if a in keep and b in keep]
  remote_csv=D/('remote-'+tag+'.csv');remote_manifest=D/('remote-sources-'+tag+'.json')
  with open(remote_csv,'w') as f:
   wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
   for nn in sorted(keep):wr.writerows((nn,i,*r) for i,r in enumerate(P[nn]))
  remote_manifest.write_text(json.dumps({nn:c for nn,c in manifest.items() if int(nn) in keep}))
 (D/('pairs-'+tag+'.txt')).write_text(' '.join(f'{min(a,b)},{max(a,b)}' for a,b in pairs))
 task=dict(kind='scan',tag=tag,source=source,origin_kind=kind,pairs=len(pairs));(D/(tag+'.json')).write_text(json.dumps(task))
 with tarfile.open(D/'send.tgz','w:gz',compresslevel=1) as t:
  t.add(remote_csv,arcname=tag+'.csv');t.add(remote_manifest,arcname='sources-'+tag+'.json')
  for name in ['bars-'+tag+'.tsv','pairs-'+tag+'.txt']:t.add(D/name,arcname=name)
  t.add(D/(tag+'.json'),arcname='incoming/'+tag+'.json')
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r28-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(D/'send.tgz'),f'boxE:scratch/squares-k123/send-{tag}.tgz'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r28-ssh','boxE',f'cd $SCRATCH/squares-k123 && tar xzf send-{tag}.tgz && mv incoming/*.json tasks/ && rm send-{tag}.tgz'],check=True)
 journal(f'START boxE {kind} scan {tag}, pairs={len(pairs)}, source={source}, log out/scan{tag}.log, deadline05:45Z')
 print('staged',tag,kind,len(pairs),source,flush=True);return True

def stage(*args,**kwargs):
 import fcntl
 with open(W/'transfer.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  return _stage(*args,**kwargs)

def current():
 from base25 import current as cc
 return cc()

def fresh():
 P,origins=current()
 import numpy as np
 from source25 import audit
 gp=W/'fresh-geometry25.npz';gm=W/'fresh-geometry25.json';geometry={}
 if gp.exists() and gm.exists():
  with np.load(gp,allow_pickle=False) as z:
   geometry={k:(z[k].copy(),v) for k,v in json.load(open(gm)).items() if k in z}
 seenfile=W/'fresh-seen.json';seen=json.load(open(seenfile)) if seenfile.exists() else {};classes={}
 version=W/'fresh-version28'
 if not version.exists() or version.read_text()!='r28-public-slug-v6':
  seen={};version.write_text('r28-public-slug-v6')
 eventfile=W/'event-pending28.json';events=set(json.load(open(eventfile))) if eventfile.exists() else set()
 eventoffset=W/'event-offset28';offset=int(eventoffset.read_text()) if eventoffset.exists() else 0
 logtext=(S/'handoff-r28.log').read_text()
 if offset>len(logtext):offset=0
 events.update(re.findall(r'($DATA/[^\s,;]+\.csv)',logtext[offset:]));processed=set()
 forced=W/'force-fresh28.json'
 if forced.exists():
  events.update(json.load(forced.open()));forced.unlink()
 eventoffset.write_text(str(len(logtext)))
 for n,A in P.items():
  if n<100:continue
  from classes26 import read
  types=read(n,A,kj)
  if types:classes[n]=types
 candidates=[]
 for t in [*S.glob('take-*-r28'),*S.glob('take-*-r27')]:
  candidates+=list(t.glob('*.csv'))
  if t.name.endswith('-r28'):candidates+=list((t/'near').glob('*.csv'))
 log=S/'handoff-r28.log'
 if log.exists():
  candidates.extend(pathlib.Path(p) for p in re.findall(r'($DATA/[^\s,;]+\.csv)',log.read_text()) if any(r in p for r in ['-r27/','-r28/']) and pathlib.Path(p).exists())
 reopened=W/'reopened-inputs27.txt'
 if reopened.exists():candidates=[*map(pathlib.Path,reopened.read_text().splitlines()),*candidates]
 candidates=list(dict.fromkeys(candidates))
 # Hash-named near files are immutable between explicit handoffs. Mutable per-n
 # outputs and common rectangle names remain checked on every pass.
 candidates=[p for p in candidates if str(p) not in seen or p.stem.isdigit() or p.name.endswith('-rect.csv') or p.parent==W/'reopened' or str(p) in events]
 def order(p):
  try:return ('/near/' in str(p),-p.stat().st_mtime)
  except OSError:return (True,0)
 candidates.sort(key=lambda p:(0 if '/reopened/' in str(p) else 1 if '-r27/' in str(p) else 2,*order(p)))
 seq=int((W/'seq').read_text()) if (W/'seq').exists() else 10000;staged=0;refused=[]
 pass_started=time.time()
 for p in candidates:
  if time.time()-pass_started>25:break
  try:sig=hashlib.sha256(b'r28-full-tree-v5-pin:'+p.read_bytes()+b''.join(z.read_bytes() for z in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json'),p.parent/'take.tsv'] if z.exists())).hexdigest()
  except OSError:continue
  if seen.get(str(p))==sig and str(p) not in events:
   processed.add(str(p));continue
  try:
   d=mlp.load(str(p))
   if len(d)!=1:seen[str(p)]=sig;processed.add(str(p));continue
   n,A=next(iter(d.items()))
   if str(p) in events:
    from source25 import retry_origin
    retry_origin(str(p))
   c=credit(n,A,str(p))
   if not c:
    refused.append(str(p));seen[str(p)]=sig;processed.add(str(p))
    journal('DROP source-refused fresh input '+str(p)+'; ancestry unresolved or excluded; deadline05:45Z')
    continue
   duplicate=next((k for k,(B,cc) in geometry.items() if k.startswith(str(n)+'-') and B.shape==A.shape and np.max(np.abs(B-A))<1e-10 and audit(cc)),None)
   if duplicate:
    seen[str(p)]=sig;processed.add(str(p))
    with open(W/'fresh-geometry-skipped25.jsonl','a') as h:h.write(json.dumps({'path':str(p),'duplicate':duplicate,'reason':'same admitted geometry within1e-10'})+'\n')
    continue
   X=kj.Lay(n,*kj.norm(A),str(n))
   if len(X.G)<10:seen[str(p)]=sig;processed.add(str(p));continue
   types={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};types|={(b,a) for a,b in list(types)}
   partners=[nn for nn in classes if types&classes[nn]];ns=set(partners)|{n};donors={nn:A if nn==n else P[nn] for nn in ns};oo={**origins,n:str(p)}
   seq+=1;(W/'seq').write_text(str(seq));tag=f'fresh{seq}';npairs=[(n,nn) for nn in partners]+([(n,n)] if n not in partners else [])
   if stage(tag,donors,oo,npairs,'fresh',str(p)):
    geometry[str(n)+'-'+sig[:16]]=(A.copy(),c)
    staged+=1;seen[str(p)]=sig;processed.add(str(p));seenfile.write_text(json.dumps(seen));(W/'seq').write_text(str(seq))
   if staged>=6:break
  except Exception as e:
   if isinstance(e,KeyError):seen[str(p)]=sig;processed.add(str(p))
   print('stage error',str(p),type(e).__name__,str(e),flush=True)
 if geometry:
  np.savez_compressed(gp,**{k:v[0] for k,v in geometry.items()});gm.write_text(json.dumps({k:v[1] for k,v in geometry.items()}))
 eventfile.write_text(json.dumps(sorted(events-processed)));(W/'seq').write_text(str(seq));seenfile.write_text(json.dumps(seen));(W/'fresh-refused.json').write_text(json.dumps(refused,indent=2));print('fresh staged',staged,'refused',len(refused),flush=True)

def deferred(limit=6):
 if (W/'deferred-batch-size').exists():limit=int((W/'deferred-batch-size').read_text())
 if not (W/'bars.tsv').exists():current()
 P_current,orig_current=current();batch_started=time.time()
 O=S/'take-k123-r24/work';seenfile=W/'deferred-seen.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set();seq=int((W/'deferred-seq').read_text()) if (W/'deferred-seq').exists() else 0;catalogs={};count=0
 for line in (O/'cap-deferred24.jsonl').read_text().splitlines():
  if time.time()-batch_started>20:break
  j=json.loads(line)
  if j['tag'] in seen:continue
  seen.add(j['tag']);catalog=j['full_input'];source=j['source']
  chosen=set(j['selected']);pairs=[(a,b) for a,b in j['planned_pairs'] if a not in chosen or b not in chosen]
  P,orig=P_current,orig_current;pairs=[(a,b) for a,b in pairs if a in P and b in P]
  if not pairs:continue
  n=pairs[0][0];orig.update({nn:orig.get(nn,'held') for a,b in pairs for nn in (a,b)})
  seq+=1;(W/'deferred-seq').write_text(str(seq));tag=f'defer{seq:05d}'
  if stage(tag,P,orig,pairs,'deferred',source):
   count+=1;seenfile.write_text(json.dumps(sorted(seen)))
  if count>=limit:break
 seenfile.write_text(json.dumps(sorted(seen)));(W/'deferred-seq').write_text(str(seq));print('deferred staged',count,'visited',len(seen),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='deferred':deferred(int(sys.argv[2]) if len(sys.argv)>2 else 6)
 else:fresh()
