"""Light local dispatch, immutable held projections, and certified result intake."""
import csv,json,hashlib,math,os,re,shutil,subprocess,sys,time,tarfile,fcntl
sys.dont_write_bytecode=True
from pathlib import Path
csv.field_size_limit(100000000)
S=Path('$SCRATCH/bounties-squares');T=S/'take-classfill-r31';W=T/'work';ROOT='scratch/squares-classfill-r31';R=Path('.');END=1794788100.0
END=float((W/'stage/deadline').read_text());HOSTS=[('boxE','A'),('boxE','B'),('boxD','C')];COL=['n','held','new','gain','source','licence']
def now():return time.strftime('%FT%TZ',time.gmtime())
def note(x):
 with (T/'STATE.txt').open('a') as f:f.write(now()+' '+x+'\n')
def hand(x):
 with (S/'handoff-r31.log').open('a') as f:f.write(now()+' classfill -> all: '+x+'\n')
def read(p,d=None):
 try:return json.loads(Path(p).read_text())
 except (ValueError,OSError):return d

def atom(p,j):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(j,indent=1)+'\n');q.replace(p)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cmd(a,timeout=60):
 if a[0]=='ssh':a=a[:1]+['-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2']+a[1:]
 if a[0]=='scp':a=a[:1]+['-O','-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2']+a[1:]
 return subprocess.run(a,check=True,capture_output=True,text=True,timeout=timeout).stdout

def rows(p):
 try:return list(csv.DictReader(open(p),delimiter='\t'))
 except OSError:return []
def bars():
 base={int(r['n']):float(r['bar']) for r in rows(S/'round31-briefs/bar31.tsv')};live=dict(base)
 for p in S.glob('take-*-r31/take.tsv'):
  if p.parent==T:continue
  for r in rows(p):
   try:n=int(r['n']);live[n]=min(live[n],float(r['new']))
   except (ValueError,KeyError):pass
 return base,live

def writebar():
 base,live=bars();owned={int(r['n']):float(r['new']) for r in rows(T/'take.tsv')}
 p=W/'stage/bar.csv'
 with p.open('w') as f:
  w=csv.writer(f);w.writerow(['n','L','score','min_gap'])
  for n,v in live.items():v=min(v,owned.get(n,v));w.writerow([n,(1+v)*math.sqrt(n),v,2.2e-11])
 for host in dict(HOSTS):
  cmd(['scp','-q',str(p),host+':'+ROOT+'/bar.csv.new']);cmd(['ssh',host,'mv '+ROOT+'/bar.csv.new '+ROOT+'/bar.csv'])
 return base,live

def claimed(digest):
 cutoff=time.time()-3600
 for l in (S/'handoff-r31.log').read_text().splitlines():
  if digest not in l and digest[:16] not in l and digest[:12] not in l:continue
  if not re.search(r'claim|reserv',l,re.I):continue
  try:t=__import__('datetime').datetime.fromisoformat(l.split()[0].replace('Z','+00:00')).timestamp()
  except ValueError:continue
  if t>cutoff:return l
 return None

def dispatch(n,p,source,licence,kind='held',priority=10,seed=3101,seconds=900,method='midm',proof=None):
 digest=sha(p);tag='x'+digest[:12]+'s'+str(seed);target=W/'jobs'/f'{tag}.json'
 if target.exists():return False
 line=claimed(digest)
 if line and not kind.startswith('own-'):note(f'SKIP n{n} exact recent claim {line[:260]}');return False
 with (S/'handoff-r31.log').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  if claimed(digest) and not kind.startswith('own-'):return False
  if method!='audit':f.write(now()+f' classfill -> all: claims n={n} sha256 {digest}, {kind} {seconds}s seed {seed}; '+str(p)+'\n');f.flush()
 local=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,local)
 if sha(local)!=digest:raise RuntimeError('input changed while copying '+str(p))
 job=dict(tag=tag,n=n,kind=kind,input='data/'+local.name,input_path=str(p),input_sha256=digest,input_snapshot=str(local),source='complete source in '+str(target)+'; input '+str(p),licence='complete inherited terms in '+str(target),source_record=source,licence_record=licence,proof=proof,priority=priority,seed=seed,seconds=seconds,wall=seconds+400,search_method=method,bar_input=True,kicks='0.02,0.04',created_utc=now())
 loads=[]
 for host,slot in HOSTS:
  ls=cmd(['ssh',host,'find '+ROOT+'/queue/'+slot+' -type f \\( -name "*.json" -o -name "*.active" \\)']).splitlines();loads.append((len(ls),host,slot))
 _,host,slot=min(loads);job.update(host=host,slot=slot);atom(target,job)
 cmd(['scp','-q',str(local),host+':'+ROOT+'/data/'+local.name]);cmd(['scp','-q',str(target),host+':'+ROOT+'/queue/'+slot+'/'+tag+'.tmp']);cmd(['ssh',host,'mv '+ROOT+'/queue/'+slot+'/'+tag+'.tmp '+ROOT+'/queue/'+slot+'/'+tag+'.json'])
 note(f'START_QUEUE {host} {slot} {kind} n{n} seed{seed} {seconds}s {tag}; log work/{host}/logs/{tag}.log; common deadline00:15Z')
 return True

def setup():
 held=S/'gather/round30-2026-11-15c.csv';heldsha=sha(held);srcs=read(W/'held-sources.json',{});pool=W/'held';pool.mkdir(exist_ok=True)
 # Extract exact rows with their original fields, recording the complete submitted container identity.
 groups={}
 with held.open() as f:
  cr=csv.DictReader(f);fields=cr.fieldnames
  for r in cr:groups.setdefault(int(r['n']),[]).append(r)
 for n,rs in groups.items():
  p=pool/f'{n}.csv'
  with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rs)
  old=srcs.get(str(n),{});record=old.get('record',{});source=f'held n = {n} of round 30; submitted gather/round30-2026-11-15c.csv sha256 {heldsha}; '+old.get('table','prior held baseline')+' n='+str(n)+': '+record.get('source','held baseline')
  lic='our own submitted packing; inherited terms: '+record.get('licence','held baseline')
  atom(p.with_suffix('.json'),dict(n=n,path=str(held),sha256=heldsha,row_sha256=sha(p),source=source,licence=lic,table=old.get('table'),record=record,policy='held ancestry; no share gate'))
 atom(W/'held-extraction.json',dict(container=str(held),sha256=heldsha,counts=len(groups),time=now()))

def heldqueue():
 order=read(S/'take-border-r30/work/held30/order3.json',{});recent=read(W/'recent-count-jobs.json',{});srcs=read(W/'held-sources.json',{})
 # Include all non-grid held constructors, prioritizing counts without a recent kick and with a measured gap.
 old_hashes=set()
 for rnd in [28,29,30]:old_hashes.update(read(S/('take-classfill-r'+str(rnd))/'work/scanned.json',[]))
 base,_=bars();board={int(r['n']):float(r['board_L']) for r in rows(S/'main-r17/gap-by-n.tsv')}
 ordered=sorted((int(n) for n in srcs if int(n)>40),key=lambda n:(str(n) in recent,-max(float(order.get(str(n),0)),base[n]-(board.get(n,(1+base[n])*math.sqrt(n))/math.sqrt(n)-1)),n))
 items=[]
 for n in ordered:
  p=W/'held'/f'{n}.csv';j=read(p.with_suffix('.json'),{})
  # Directly named excluded source trees remain excluded even when a source notice is inherited.
  txt=j.get('source','')+' '+j.get('licence','')
  if 'squares-verified-best-of-1105' in txt or ('squares-joegun-boxed-certified-union' in txt and n in [639,691,745,858,918]):continue
  # Avoid the measured rigid grid and unchanged original seed campaigns.
  if sha(p) in old_hashes or n in [503,983] or abs((1+base[n])*math.sqrt(n)-math.ceil(math.sqrt(n)))<1e-7:continue
  items.append(dict(n=n,p=str(p),source=j['source'],licence=j['licence'],kind='held-untried' if str(n) not in recent else 'held-revisit',proof=str(p.with_suffix('.json'))))
 atom(W/'held-order.json',items);return items

def collect():
 base,live=bars();take={int(r['n']):r for r in rows(T/'take.tsv')};seen=set(read(W/'collected.json',[]));chain=[]
 for host in dict(HOSTS):
  local=W/host;local.mkdir(exist_ok=True)
  cmd(['rsync','-az','--exclude','tmp/','--exclude','fq-tmp/',host+':'+ROOT+'/out/',str(local/'out')+'/'],timeout=70)
  cmd(['rsync','-az',host+':'+ROOT+'/logs/',str(local/'logs')+'/'],timeout=60)
  for d in (local/'out').glob('*'):
   if not (d/'DONE').exists() or d.name in seen:continue
   tag=d.name.split('-',1)[1];job=read(W/'jobs'/f'{tag}.json',{});
   if not job:continue
   job['source']=job.get('source_record',job['source']);job['licence']=job.get('licence_record',job['licence'])
   if job.get('kind')=='fresh-rectangle':
    proof=read(job.get('proof'),{}).get('source_closure',{})
    notices=json.dumps(dict(held_notices=proof.get('notices',[]),public_roots=proof.get('public_roots',[])),sort_keys=True)
    job['source']+='; inherited source notices '+notices
    job['licence']+='; inherited source notices '+notices
   n=job['n'];p=d/f'{n}.csv';meta=read(p.with_suffix('.json'),{});score=meta.get('finish_score');seen.add(d.name)
   if score is None:continue
   receipt=read(local/'out'/('finish-'+tag)/'quench-receipt.json',{})
   record=dict(job=job,output=str(p),output_sha256=sha(p),score=score,finish=meta,quench_receipt=receipt)
   atom(W/'candidates'/f'{tag}.json',record)
   near=T/'near'/f'{n}-{tag}.csv';shutil.copy2(p,near);atom(near.with_suffix('.json'),dict(source=job['source'],licence=job['licence'],input=job['input_path'],input_sha256=job['input_sha256'],proof=job['proof'],receipt=str(W/'candidates'/f'{tag}.json')))
   margin=live[n]-score;start=meta['finish_start_side'];delta=start-(1+score)*math.sqrt(n)
   note(f'FINISH {host} {tag} n{n} score{score:.17g} delta_side{delta:.9g} live_margin{margin:.9g} quenched{meta.get("finish_quenched")}')
   # A completed certified-file quench and exact bytes are mandatory.
   eligible=score<live[n]-1e-10 and meta.get('finish_quenched') and receipt.get('completed',0)>0
   if eligible and (n not in take or score<float(take[n]['new'])-1e-10):
    shutil.copy2(p,T/f'{n}.csv');source='classfill r31 '+job['kind']+(' family lkick180' if job.get('search_method')=='invent' else ' midm probe120/full900')+' and finesafe 2.2e-11; certified-file fq on '+host+'; '+job['source']+'; immutable receipt '+str(W/'candidates'/f'{tag}.json')
    take[n]=dict(zip(COL,[n,repr(base[n]),repr(score),repr(base[n]-score),source,job['licence']]))
    table(take);hand(f'certified n={n} score={score!r} gain={base[n]-score!r}, {T}/{n}.csv; receipt {W}/candidates/{tag}.json')
   if not (W/'STOP_PREPARED').exists() and n>40 and job['kind']=='held-untried' and delta<=1e-6 and meta.get('finish_quenched') and time.time()<END-360:
    from light29 import load
    from physical30 import key
    a=load(job['input_snapshot'],{n})[n];b=load(p,{n})[n]
    def norm(P):
     hs=[.5*(abs(math.cos(z))+abs(math.sin(z))) for x,y,z in P];dx=min(x-h for (x,y,z),h in zip(P,hs));dy=min(y-h for (x,y,z),h in zip(P,hs));return [(x-dx,y-dy,z%(math.pi/2)) for x,y,z in P]
    aa,bb=norm(a),norm(b)
    movement=max(max(abs(x-u),abs(y-v),min(abs(z-c),math.pi/2-abs(z-c))) for (x,y,z),(u,v,c) in zip(aa,bb))
    record['prepared_max_displacement']=movement;atom(W/'candidates'/f'{tag}.json',record)
    if movement>1e-5 and key(a,decimals=5)!=key(b,decimals=5):
     record['prepared_geometry_changed']=True;atom(W/'candidates'/f'{tag}.json',record)
     dispatch(n,near,job['source']+'; changed certified preparation '+str(near),job['licence'],'own-prepared-follow',5,3203,900,proof=str(W/'candidates'/f'{tag}.json'))
   if n>40 and delta>1e-6 and time.time()<END-360 and meta.get('finish_quenched'):
    chain.append((n,near,job,record,delta))
 # Reprice immutable completed outputs if a lower peer row is later removed.
 for rp in (W/'candidates').glob('*.json'):
  r=read(rp,{});j=r.get('job',{});n=j.get('n',0);score=r.get('score',1.)
  if n<=40 or score>=live[n]-1e-10 or not r.get('finish',{}).get('finish_quenched') or not r.get('quench_receipt',{}).get('completed'):continue
  if n in take and score>=float(take[n]['new'])-1e-10:continue
  pp=Path(r['output'])
  if not pp.is_file() or sha(pp)!=r['output_sha256']:continue
  shutil.copy2(pp,T/f'{n}.csv')
  src='classfill r31 '+j['kind']+'; finesafe 2.2e-11 and completed certified-file fq on '+j['host']+'; '+j['source']+'; immutable receipt '+str(rp)
  take[n]=dict(zip(COL,[n,repr(base[n]),repr(score),repr(base[n]-score),src,j['licence']]))
  table(take);hand(f'certified n={n} score={score!r} gain={base[n]-score!r}, {T}/{n}.csv; repriced completed output {rp}')
 for n,r in list(take.items()):
  if float(r['new'])>=live[n]-1e-10:
   note(f'SUPERSEDED n{n} score{r["new"]} live{live[n]}');(T/f'{n}.csv').unlink(missing_ok=True);del take[n]
 table(take);atom(W/'collected.json',sorted(seen))
 for n,p,job,record,delta in chain:
  proof=str(W/'candidates'/f'{job["tag"]}.json');src='classfill r31 changed certified endpoint '+str(p)+' sha256 '+sha(p)+'; '+job['source']
  dispatch(n,p,src,job['licence'],'own-leg',-5,job['seed']+97,900,proof=proof)
  if record['score']<live[n]-1e-10 and job.get('search_method')!='invent':
   dispatch(n,p,src,job['licence'],'own-family-follow',-6,11,180,method='invent',proof=proof)
  if delta>=1e-5:
   # New seeds are distinct recipes, but are admitted only after the exact-input claim expires.
   dispatch(n,p,src,job['licence'],'own-deep-seed',-4,job['seed']+197,900,proof=proof)
   dispatch(n,p,src,job['licence'],'own-deep-seed',-4,job['seed']+297,900,proof=proof)
 return take

def table(take):
 with (T/'take.tsv.tmp').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=COL,delimiter='\t');w.writeheader();w.writerows(take[n] for n in sorted(take))
 os.replace(T/'take.tsv.tmp',T/'take.tsv')

def bootstrap():
 # Required process count check precedes starting the three strictly serial slots.
 for host in dict(HOSTS):note('REMOTE_PROCESS_CHECK '+host+' '+cmd(['ssh',host,'ps -axo pid,ppid,command | grep "[s]quares-classfill-r31" || true']).strip())
 p=W/'bundle31.tar.gz'
 with tarfile.open(p,'w:gz') as tf:
  for q in (W/'stage').iterdir():tf.add(q,arcname=q.name)
 for host in dict(HOSTS):
  cmd(['ssh',host,'mkdir -p '+ROOT]);cmd(['scp','-q',str(p),host+':'+ROOT+'/bundle.tar.gz']);cmd(['ssh',host,'cd '+ROOT+' && tar xzf bundle.tar.gz && rm bundle.tar.gz'])
 for host,slot in HOSTS:
  py='$SCRATCH/squares-base/venv/bin/python' if host=='boxE' else '$SCRATCH/squares-readers/venv/bin/python'
  out=cmd(['ssh',host,'cd '+ROOT+' && nohup nice -n 5 '+py+' -u worker31.py '+slot+' > logs/worker-'+slot+'.log 2>&1 < /dev/null & echo $!'])
  atom(W/f'owned-{host}-{slot}.json',dict(pid=int(out.strip().splitlines()[-1]),host=host,slot=slot));note('START_WORKER '+host+' '+slot+' pid'+out.strip()+' deadline00:15Z')

if __name__=='__main__':
 if '--resume' not in sys.argv:setup();bootstrap()
 queue=heldqueue();writebar();admitted=set(read(W/'admitted.json',[]));last_handoff=0
 while time.time()<END-300 and not (W/'STOP').exists():
  try:
   take=collect();writebar()
   # Dispatch at most 9 waiting jobs across 3 serial compute slots; claims are made at actual queue admission.
   waiting=sum(len(cmd(['ssh',h,'find '+ROOT+'/queue/'+slot+' -name "*.json"']).splitlines()) for h,slot in HOSTS)
   added=0
   for j in queue:
    n=j['n']
    if n in admitted:continue
    if waiting+added>=6:break
    p=Path(j['p']);admitted.add(n)
    if dispatch(n,p,j['source'],j['licence'],j['kind'],priority=10 if j['kind']=='held-untried' else 20,proof=j['proof']):added+=1
   atom(W/'admitted.json',sorted(admitted))
   # Reading the handoff every pass gives a permanent intake record and supports revival.
   if time.time()-last_handoff>=600:
    data=(S/'handoff-r31.log').read_text();(W/'handoff-latest.txt').write_text(data);note('HANDOFF_READ lines'+str(len(data.splitlines())));last_handoff=time.time()
    if (W/'fresh-source-controls.json').exists() and time.time()<END-420:
     guard_pid=int((W/'freshguard-pid').read_text()) if (W/'freshguard-pid').exists() else 0
     guard_cmd=subprocess.run(['ps','-p',str(guard_pid),'-o','command='],capture_output=True,text=True).stdout if guard_pid else ''
     if str(W/'freshguard31.py') not in guard_cmd:
      guard=subprocess.Popen(['nice','-n','19',sys.executable,'-u',str(W/'freshguard31.py')],stdin=subprocess.DEVNULL,stdout=open(W/'freshguard31.log','a'),stderr=subprocess.STDOUT,start_new_session=True)
      (W/'freshguard-pid').write_text(str(guard.pid));note('START source admission guard pid'+str(guard.pid)+' log work/fresh31.log, wall cap120s, no local search')
   atom(W/'heartbeat.json',dict(time=now(),take=len(take),admitted=len(admitted),queue_added=added,waiting=waiting))
  except Exception as e:note('CONTROLLER_ERROR '+repr(e));print(now(),repr(e),flush=True)
  time.sleep(45)
 note('FINISH_ADMISSION deadline00:10Z; workers stop at00:15Z')
