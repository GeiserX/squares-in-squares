"""Collect boxE receipts, admit owned starts, and publish live winners."""
import pathlib,sys,os,csv,json,math,time,hashlib,subprocess,shutil,re,traceback
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.')
sys.path.insert(0,str(W));sys.path.insert(0,str(R));os.environ['QUENCH_LIVE_ROUND']='31'
import ancestry28 as A,source_gate28 as G,public_branch30 as B
import methods_lp as mlp,quench_walk as Q
REMOTE='boxE:scratch/squares-invent-r31/';FIELDS=['n','held','new','gain','source','licence']
BASE={int(r['n']):float(r['bar'])for r in csv.DictReader(open(S/'round31-briefs/bar31.tsv'),delimiter='\t')}
HARD=float((W/'deadline').read_text());ADMIT=float((W/'search-deadline').read_text())
def now():return time.strftime('%FT%TZ',time.gmtime())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(p,default):
 try:return json.load(open(p))
 except (FileNotFoundError,ValueError):return default

def atomic(p,v):
 p=pathlib.Path(p);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(v));q.replace(p)
def state(t):
 with (T/'STATE.txt').open('a')as f:f.write(now()+' boxA '+t+'\n')
def hand(t):
 with (S/'handoff-r31.log').open('a')as f:f.write(now()+' invent -> all: '+t+'\n')
def cmd(args):return subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=45).stdout

def peers():
 best=dict(BASE)
 for p in S.glob('take-*-r31/take.tsv'):
  if p.parent==T:continue
  try:
   for r in csv.DictReader(open(p),delimiter='\t'):
    n=int(r['n']);v=float(r['new']);best[n]=min(best[n],v)
  except (ValueError,KeyError,OSError):continue
 return best

def claimed(digest,lines):
 for l in lines:
  if 'claim'not in l.lower() or ' invent ->'in l:continue
  if not any(digest.startswith(v)for v in re.findall(r'(?<![0-9a-f])[0-9a-f]{16,64}(?![0-9a-f])',l)):continue
  try:ts=time.mktime(time.strptime(l[:19],'%Y-%m-%dT%H:%M:%S'))-time.timezone
  except ValueError:continue
  if time.time()-ts<3600:return True
 return False

def ownsource(p,n,source=None,lic=None,record=None):
 a=A.audit(p,n,source,lic,record)
 if not a.get('ok'):return dict(ok=False,reason=a.get('reason'))
 evidence=G.freeze(p,n,a['proof'])
 if not evidence['clean']:return dict(ok=False,reason=str(evidence['hits']))
 try:b=B.audit(evidence['path'],a['proof'])
 except Exception as e:return dict(ok=False,reason=str(e))
 # Public-first transport is outside this campaign. Fresh own layouts and held ancestry need no share gate.
 if not b['clean']or b.get('public_roots'):return dict(ok=False,reason='direct public branch or source refusal '+str(b.get('hits',[])))
 return dict(ok=True,ancestry=a['proof'],evidence=evidence['path'],evidence_sha256=evidence['sha256'],source=a['source'],licence=a['licence'])

def produce_input(p,n,kind,seed,peer,proof=None,origin=None):
 data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();P=mlp.load(str(p),{n})[n];L=float(mlp.side(P))
 if proof is not None and proof.get('parent_job'):
  from extend30 import extend
  parent=proof['parent_job'];e=extend(parent,p,n,parent['ancestry'])
  if not e.get('clean'):return None,str(e.get('hits'))
  proof=dict(ok=True,ancestry=e['ancestry'],evidence=e['path'],evidence_sha256=e['sha256'],source='own continuation of '+parent['source'],licence=parent['licence'])
 if proof is None:proof=ownsource(p,n)
 if not proof['ok']:return None,proof.get('reason','source refused')
 ident=kind+str(n)+'-'+digest[:10]+'-s'+str(seed);rel='starts/'+ident+'.csv';(W/rel).write_bytes(data)
 j=dict(id=ident,n=n,start=rel,kind=kind,program='midm'if kind in('held','deep')else'invent_barretain_budget30.py',seconds=900,seed=seed,probe=120,side=L,bar=(peer[n]+1)*math.sqrt(n),input_sha256=digest,origin=str(origin or p),**{k:v for k,v in proof.items()if k!='ok'})
 return j,None

def init_held():
 if (W/'held-order.json').exists():return
 inputfile=S/'gather/round30-2026-11-15c.csv';groups={};
 for r in csv.DictReader(open(inputfile)):groups.setdefault(int(r['n']),[]).append(r)
 cmdline=[]
 logs='\n'.join((S/f'handoff-r{k}.log').read_text(errors='replace')for k in (28,29,30)if(S/f'handoff-r{k}.log').exists())
 used={int(v)for v in re.findall(r'\bn\s*=\s*(\d+)\b',logs)}
 gaps={int(r['n']):(float(r['board_L']),float(r['score_gap']))for r in csv.DictReader(open(S/'main-r17/gap-by-n.tsv'),delimiter='\t')}
 order=[];(W/'held31').mkdir(exist_ok=True)
 for n,rows in groups.items():
  if n<100 or n not in gaps:continue
  gap=BASE[n]-(gaps[n][0]/math.sqrt(n)-1)
  if gap<=1e-7:continue
  src=Q.held(n,30)
  # Plain public-file starts were a measured zero in r30. Own seeds and constructed held rows go first.
  constructed=bool(re.search(r'Samanyu-dev|own |modules\.py|family_|invent_|rectangle windows|k123|stair-c|twoshort|kick',src,re.I))
  if not constructed:continue
  p=W/'held31'/f'{n}.csv'
  with p.open('w',newline='')as h:
   writer=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);writer.writeheader();writer.writerows([{k:r[k]for k in writer.fieldnames}for r in rows])
  meta=dict(n=n,source=f'held n = {n} of round 30 (gather/round30-2026-11-15c.csv, sha256 {sha(inputfile)}); its recorded source: '+src,licence='own held layout; recorded terms: '+src.split(' || ')[-1],sha256=sha(p))
  pathlib.Path(str(p)+'.json').write_text(json.dumps(meta));order.append(dict(n=n,path=str(p),gap=gap,recent=n in used,source=meta['source'],licence=meta['licence']))
 order.sort(key=lambda v:(v['recent'],-v['gap']));atomic(W/'held-order.json',order);state(f'HELD queue {len(order)} constructed held rows, {sum(not r["recent"]for r in order)} without last-three-round n claim; rank gap then recent coverage. Plain public starts omitted after r30 measured zero.')

def collect():
 out=W/'boxE-raw';out.mkdir(exist_ok=True)
 cmd(['rsync','-a','--exclude','tmp/','--exclude','lane/','--exclude','starts/',REMOTE,str(out)+'/'])
 js=load(W/'jobs.json',[])
 for control in load(W/'extra-controls.json',[]):
  if not any(v['id']==control['id']for v in js):js.insert(0,control);atomic(W/'jobs.json',js)
 done={j['id']:load(out/j['id']/'done.json',{})for j in js};peer=peers();best={};seen=set(load(W/'finished-seen.json',[]))
 c2=done.get('control2',{});c907=done.get('control907',{})
 if c2.get('quench_from_certified')and c907.get('quench_from_certified')and(c907['new']+1)*math.sqrt(907)<30.6183 and c907.get('clearance',0)>=2.2e-11:
  if not(W/'CONTROL_GREEN').exists():(W/'CONTROL_GREEN').write_text(now());state('CONTROL GREEN pair and deep907 reached side '+str((c907['new']+1)*math.sqrt(907))+'; certified-input fq and native/pandas clearance passed.');cmd(['rsync','-a',str(W/'CONTROL_GREEN'),REMOTE])
 allctl=done.get('all-finish-control',{})
 if allctl.get('quench_from_certified')and len(allctl.get('candidate_quenches',[]))==allctl.get('unique_certified_candidates',-1)and len(allctl.get('candidate_quenches',[]))>=3 and all(v.get('quench_from_certified')for v in allctl.get('candidate_quenches',[])) and(allctl['new']+1)*math.sqrt(2)<2.000001:
  if not(W/'ALL_FINISH_GREEN').exists():(W/'ALL_FINISH_GREEN').write_text(now());cmd(['rsync','-a',str(W/'ALL_FINISH_GREEN'),REMOTE]);state('CONTROL GREEN every unique certified candidate quenched separately before comparison; canonical winning input/marker verified.')
 for j in js:
  d=done[j['id']]
  if not d:continue
  if j['id']not in seen:state('FINISH '+j['id']+' '+json.dumps(d));seen.add(j['id'])
  if j['kind']=='control'or not d.get('quench_from_certified')or 'error'in d:continue
  p=out/j['id']/'final'/f'{j["n"]}.csv'
  if not p.exists()or sha(p)!=d['sha256']:continue
  n=j['n'];v=d['new']
  if v>=BASE[n]-1e-10 and j['side']-(v+1)*math.sqrt(n)<=1e-8:continue
  if not G.check(j,p)['clean']:continue
  near=T/'near'/f'{n}-{j["id"]}.csv'
  if j['side']-(v+1)*math.sqrt(n)>1e-8 and not near.exists():
   from extend30 import extend
   e=extend(j,p,n,j['ancestry'])
   if e.get('clean'):
    shutil.copyfile(p,near)
    pathlib.Path(str(near)+'.json').write_text(json.dumps(dict(n=n,source='source metadata '+e['ancestry'],licence=j['licence'],ancestry_file=e['ancestry'],evidence=e['path'],sha256=d['sha256'])))
    hand('NEAR owned endpoint n='+str(n)+' side='+str((v+1)*math.sqrt(n))+'; '+str(near)+'; source='+e['ancestry'])
  if v<BASE[n]-1e-10 and v<peer[n]and(n not in best or v<best[n][1]['new']):best[n]=(j,d,p)
 current={}
 for n,(j,d,p)in sorted(best.items()):
  dest=T/f'{n}.csv';fresh=not dest.exists()or sha(dest)!=sha(p)
  if fresh:shutil.copyfile(p,dest)
  source='invent round31: '+j['program']+' '+j['kind']+' '+j['id']+'; immutable start '+str(W/j['start'])+' sha256 '+j['input_sha256']+'; full recorded source '+j['ancestry']+'; parent: '+j['source']+'; border finesafe 2.2e-11, fq from certified file; receipt '+str(out/j['id']/'done.json')
  current[n]=dict(n=n,held=BASE[n],new=d['new'],gain=BASE[n]-d['new'],source=source,licence=j['licence'])
  pathlib.Path(str(p)+'.origin.json').write_text(json.dumps(dict(n=n,source=source,licence=j['licence'],sha256=d['sha256'])))
  if fresh:hand(f'CERTIFIED n={n} score={d["new"]:.17g} gain={BASE[n]-d["new"]:.12g}; {dest}; sha256={d["sha256"]}; source={j["ancestry"]}')
 old={int(r['n'])for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')}if(T/'take.tsv').exists()else set()
 for n in old-current.keys():
  p=T/f'{n}.csv'
  if p.exists():shutil.move(p,T/'near'/f'{n}-superseded.csv')
 tmp=T/'work/take.tmp'
 with tmp.open('w',newline='')as h:
  writer=csv.DictWriter(h,fieldnames=FIELDS,delimiter='\t');writer.writeheader();writer.writerows(current.values())
 tmp.replace(T/'take.tsv');atomic(W/'finished-seen.json',sorted(seen))
 atomic(W/'comparison.json',dict(time=now(),improved_n=len(current),gain=dict(against_base_bar=sum(r['gain']for r in current.values()),beyond_other_live_r31=sum(peer[n]-r['new']for n,r in current.items()))))
 return js,done,peer

def dispatch_key(v):
 kind=v['kind'];score=v['side']/math.sqrt(v['n'])-1
 rank=v.get('priority',{'control':-9,'leg':-5,'deep':-4.5,'held':-4,'fresh':-2}.get(kind,2))
 if kind in('leg','deep')and score<BASE[v['n']]-1e-10:rank=-7 if kind=='leg'else -6.5
 return rank,v['side']-v['bar'],v.get('order',0)


def turn():
 js,done,peer=collect()
 if time.time()>=ADMIT:return
 lines=(S/'handoff-r31.log').read_text(errors='replace').splitlines();atomic(W/'last-handoff-read.json',dict(time=now(),lines=len(lines)))
 if not(W/'CONTROL_GREEN').exists():return
 locks={p.name for p in (W/'boxE-raw/locks').glob('*')};pending=[j for j in js if j['id']not in locks and j['id']not in done or not done.get(j['id'])and j['id']not in locks]
 room=max(0,6-len([j for j in pending if j['kind']!='control'and not j.get('retired_profile')]))
 tried=set(load(W/'tried-inputs.json',[]));deferred=load(W/'deferred31.json',{})
 candidates=[]
 # Measured round31 held starts supplied both retained rows. Keep at least one third of recent admissions on held coverage.
 recent=[j for j in js if j['kind']in('held','fresh')][-9:]
 promote_held=sum(j['kind']=='held'for j in recent)<3
 # Preserve useful own endpoints and frozen source trees, without rereading live producer paths.
 followed=set(load(W/'followed.json',[]))
 for j in js:
  d=done.get(j['id'],{});n=j['n']
  if j['kind']=='control'or j['id']in followed or not d.get('quench_from_certified')or 'error'in d:continue
  L=(d['new']+1)*math.sqrt(n);movement=j['side']-L
  if movement>(1e-9 if j['kind']in('leg','deep')else 1e-6):
   p=W/'boxE-raw'/j['id']/'final'/f'{n}.csv'
   proof=dict(parent_job=j)
   candidates.append((-5,-movement,p,n,'leg',j['seed']+97,proof,j['id']))
 # A large first gain earns two additional seeds even when its first leg is dry.
 for j in js:
  d=done.get(j['id'],{});n=j['n']
  if j['kind']not in ('held','fresh')or not d.get('quench_from_certified')or 'error'in d:continue
  movement=j['side']-(d['new']+1)*math.sqrt(n)
  if movement<1e-5:continue
  p=W/'boxE-raw'/j['id']/'final'/f'{n}.csv'
  for offset in (197,397):
   seed=j['seed']+offset;ident='deep'+str(n)+'-'+d['sha256'][:10]+'-s'+str(seed)
   if any(v['id']==ident for v in js):continue
   candidates.append((-4.5,-movement,p,n,'deep',seed,dict(parent_job=j),None))
 # Fresh own geometry from changed rectangles and joins; skip exact queued inputs and wait ten minutes for backlog takes.
 shape_cache=load(W/'shape-cache31.json',{})
 for t in sorted(S.glob('take-*-r31')):
  if t==T:continue
  paths=list((t/'near').glob('*.csv'))+list(t.glob('*.csv'))
  for p in paths:
   if 'threeway'in p.name.lower():continue
   if p.parent==t and time.time()-p.stat().st_mtime<600:continue
   if time.time()-p.stat().st_mtime>7200:continue
   st=p.stat();key=(str(p),st.st_mtime_ns,st.st_size);cached=shape_cache.get(str(p))
   if cached and cached['mtime_ns']==st.st_mtime_ns and cached['size']==st.st_size:
    digest=cached['sha256'];n=cached['n'];L=cached['side']
   else:
    digest=sha(p)
    if digest in tried or digest in deferred:continue
    try:n=int(p.stem.split('-')[0]);P=mlp.load(str(p),{n})[n];L=float(mlp.side(P))
    except Exception:continue
    shape_cache[str(p)]=dict(mtime_ns=st.st_mtime_ns,size=st.st_size,sha256=digest,n=n,side=L)
   if digest in tried or digest in deferred:continue
   delta=L-(peer[n]+1)*math.sqrt(n)
   if delta>.003 or delta<-.02:continue
   candidates.append((-2,delta,p,n,'fresh',3131,None,None))
 atomic(W/'shape-cache31.json',shape_cache)
 # New held coverage comes before fresh geometry while untouched held starts remain.
 for r in load(W/'held-order.json',[]):
  p=pathlib.Path(r['path']);digest=sha(p)
  if digest in tried or digest in deferred:continue
  candidates.append((-4 if not r['recent']else (-3 if promote_held else 1),-r['gap'],p,r['n'],'held',3103,None,None))
 candidates.sort(key=lambda v:(v[0],v[1]));new=[];admission_end=time.time()+100
 for _,__,p,n,kind,seed,proof,parent in candidates:
  if len(new)>=room or time.time()>=admission_end:break
  digest=sha(p)
  if claimed(digest,lines)or(digest in tried and kind!='deep'):continue
  if any(j['n']==n and not done.get(j['id'])for j in js+new):continue
  try:j,why=produce_input(p,n,kind,seed,peer,proof)
  except Exception as error:
   deferred[digest]=dict(path=str(p),reason='source adapter error: '+repr(error));atomic(W/'deferred31.json',deferred);state('DEFER source adapter '+str(p)+' '+repr(error));continue
  if j is None:deferred[digest]=dict(path=str(p),reason=why);atomic(W/'deferred31.json',deferred);state('DEFER '+str(p)+' '+str(why)[:400]);continue
  j['priority']=_;j['order']=__
  if parent:followed.add(parent);j['parent_job']=parent
  # Own continuations keep the parent evidence's original input hash for source checks separately.
  if parent:j['source_input_sha256']=next(v['input_sha256']for v in js if v['id']==parent)
  if claimed(digest,(S/'handoff-r31.log').read_text(errors='replace').splitlines()):continue
  hand(f'CLAIM {kind} n={n} sha256={digest}, 900s probe120 seed={seed}; pinned {W/j["start"]}; job={j["id"]}')
  state('QUEUE boxE '+j['id']+' from '+str(p)+'; source '+j['ancestry']+'; log work/boxE-raw/'+j['id']+'/run.log; common00:15Z')
  new.append(j);tried.add(digest)
  atomic(W/'jobs.json',js+new);atomic(W/'tried-inputs.json',sorted(tried))
  early=[v for v in js+new if not done.get(v['id'])and v['id']not in locks and not v.get('retired_profile')]
  for v in early:
   if v['kind']!='control':v['bar']=(peer[v['n']]+1)*math.sqrt(v['n'])
  early.sort(key=dispatch_key)
  atomic(W/'queue.json',early);cmd(['rsync','-a',str(W/j['start']),REMOTE+'starts/']);cmd(['rsync','-a',str(W/'queue.json'),REMOTE])
 js.extend(new);atomic(W/'jobs.json',js);atomic(W/'tried-inputs.json',sorted(tried));atomic(W/'deferred31.json',deferred);atomic(W/'followed.json',sorted(followed))
 pending=[j for j in js if not done.get(j['id'])and j['id']not in locks]
 pending=[j for j in pending if not claimed(j['input_sha256'],lines)and not j.get('retired_profile')]
 for v in pending:
  if v['kind']!='control':v['bar']=(peer[v['n']]+1)*math.sqrt(v['n'])
 pending.sort(key=dispatch_key)
 # All admissions are source-frozen, and the remote locks make each queue entry run once.
 atomic(W/'queue.json',pending);cmd(['rsync','-a',str(W/'starts'),REMOTE]);cmd(['rsync','-a',str(W/'queue.json'),REMOTE])
 print(now(),'jobs',len(js),'done',sum(bool(d)for d in done.values()),'pending',len(pending),'deferred',len(deferred),flush=True)

if __name__=='__main__':
 init_held()
 while time.time()<HARD and not(W/'STOP').exists():
  try:turn()
  except Exception:traceback.print_exc();state('CONTROLLER ERROR work/campaign.log')
  if '--once'in sys.argv:break
  time.sleep(25)
