"""Feed three remote slots from fresh geometry and certified immutable snapshots."""
import csv,hashlib,io,json,math,os,pathlib,re,shutil,subprocess,sys,time,traceback
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
import numpy as np
import faulthandler
faulthandler.dump_traceback_later(120,repeat=True)
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.')
sys.path.insert(0,str(W));import ancestry28 as A
import source_gate28 as G
from selection28 import first_clean
SOURCE_GENERATION=hashlib.sha256(b''.join((W/name).read_bytes()for name in ('ancestry28.py','source_gate28.py','public_archive28.py','archived_credit28.py','archive28.py'))).hexdigest()
from invent_shape22 import fingerprint
REM='boxE:scratch/squares-invent-r28/'
TRACK={'readers','family','stair-c','corners','modules','twoshort','k123','classfill','forensics','harvest','border','soft','midm','gap','backlog','rebuild','quench'}
FRESH_BUILD={'family','readers','k123','rebuild','gap','modules','twoshort','stair-c','corners','forensics','classfill','border'}

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a')as h:h.write(now()+' boxA '+s+'\n')
def atomic(p,x):
 q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,separators=(',',':')));q.replace(p)
def load(p,default):
 try:return json.load(open(p))
 except (OSError,ValueError):return default
def call(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError(str(cmd)+': '+p.stderr[-1200:])
 return p.stdout
def shape(p):
 before=(p.stat().st_mtime_ns,p.stat().st_size);b=p.read_bytes();after=(p.stat().st_mtime_ns,p.stat().st_size)
 if before!=after:raise ValueError('producer changed CSV during snapshot')
 rs=list(csv.DictReader(io.StringIO(b.decode())));n=len(rs)
 a=np.array([[float(r['x']),float(r['y']),float(r['angle'])]for r in rs]);h=.5*(abs(np.cos(a[:,2]))+abs(np.sin(a[:,2])))
 side=float(((a[:,:2]+h[:,None]).max(0)-(a[:,:2]-h[:,None]).min(0)).max())
 return n,side,fingerprint(a),b

def rebar(job, side):
 job['bar']=side
 if job['kind']in ('fresh','near','saved'):
  job['order']=job['side']-side
  job['outside_margin']=job['order']>.015
 elif job['kind']in('repair','wide','seam','rescue','walk'):
  job['order']=job['side']-side;job['outside_margin']=job['order']>(1e-4 if job['kind']=='repair'else .002)
 elif job['kind']=='leg':
  job['outside_margin']=job['side']-side>max(2e-5,-job.get('order',0))
 return job

def claimed_input(n,digest,lines):
 for line in lines:
  if 'backlog ->'not in line or 'claim'not in line.lower():continue
  for count,prefix in re.findall(r'(?:follow:take-[a-z0-9-]+-r28-|reopen:reopen-|near:near-)(\d+)-([0-9a-f]{8,64})',line):
   if int(count)==n and digest.startswith(prefix):return True
 return False

def handoff(msg):
 with open(S/'handoff-r28.log','a')as h:h.write(now()+' invent -> all: '+msg+'\n')
def base():
 details=S/'round28-briefs/bar28.tsv'
 bar={int(r['n']):float(r['bar'])for r in csv.DictReader(open(details),delimiter='\t')}
 atomic(W/'base.json',dict(details=str(details),posted=True,scores=bar))
 return bar

def bars():
 bar=base();peer=dict(bar)
 for table in S.glob('take-*-r28/take.tsv'):
  if table.parent==T:continue
  for row in A.rows(table):
   try:n=int(row['n']);sc=float(row['new'])
   except (KeyError,ValueError):continue
   if sc<peer[n]:
    peer[n]=sc
 return bar,peer

def sync():
 out=W/'boxE-raw';out.mkdir(exist_ok=True)
 call(['rsync','-a','--exclude=lane/','--exclude=starts/','--exclude=locks/','--exclude=*.py','--exclude=tmp/','--exclude=*.tmp',REM,str(out)+'/'])
 return out

def turn():
 out=sync();jobs=load(W/'jobs.json',[]);done={p.parent.name:load(p,{})for p in out.glob('*/done.json')}
 # Publish the source graph captured at intake, never a later rewrite at the same path.
 pinned_change=False
 for job in jobs:
  if not job.get('ancestry')or not job.get('evidence'):continue
  ep=pathlib.Path(job['evidence'])
  if not ep.is_file()or hashlib.sha256(ep.read_bytes()).hexdigest()!=job.get('evidence_sha256'):continue
  ev=load(ep,{});snap=next((v for v in ev.get('snapshots',[])if v.get('sha256')==ev.get('ancestry_sha256')),None)
  ok=False
  if snap:
   gp=pathlib.Path(snap['path'])
   if gp.is_file()and gp.parent==W/'pins'and hashlib.sha256(gp.read_bytes()).hexdigest()==snap['sha256']:
    graph=load(gp,{})
    if graph.get('policy')=='strict28v1'and graph.get('n')==job['n']:
     ok=True
     if job['ancestry']!=str(gp):job['ancestry_original']=job['ancestry'];job['ancestry']=str(gp);pinned_change=True
  if job.get('graph_pin_ok')!=ok:job['graph_pin_ok']=ok;pinned_change=True
  if not ok:job['refused']=True
 if pinned_change:atomic(W/'jobs.json',jobs)

 locks=set(call(['ssh','boxE','ls $SCRATCH/squares-invent-r28/locks']).split()); active_locks=locks-set(done)
 rec=load(W/'recorded.json',dict(start=[],end=[]))
 for j in jobs:
  if j['id']in locks and j['id']not in rec['start']:
   state(f"START boxE {j['id']} n={j['n']} kind={j['kind']} seconds={j['seconds']} seed={j['seed']}; log work/boxE-raw/{j['id']}/run.log deadline05:45Z");rec['start'].append(j['id'])
  if j['id']in done and j['id']not in rec['end']:
   state('FINISH boxE '+j['id']+' '+json.dumps(done[j['id']],sort_keys=True));rec['end'].append(j['id'])
 atomic(W/'recorded.json',rec)
 bar,peer=bars();best={};choices={};eligible=[]
 for j in jobs:
  if not j.get('ancestry'):continue
  if j.get('graph_pin_ok')is False:j['refused']=True;continue
  proof=load(pathlib.Path(j['ancestry']),{})
  known=proof.get('policy')=='strict28v1'
  node_clean=all(A.rejected(v['source'],v['licence'],terminal=not v.get('parents'))is None for v in proof.get('nodes',{}).values())
  if known and ((proof.get('ok')and node_clean)or(not proof.get('ok')and proof.get('policy')=='strict28v1')):
   j['refused']=not proof.get('ok')
   continue
  node=proof.get('nodes',{}).get(proof.get('root'),{})
  fresh=A.audit(W/j['start'],j['n'],node.get('source',''),node.get('licence',''),record=node.get('record'))
  j['ancestry']=fresh.get('proof',j['ancestry']);j['refused']=not fresh.get('ok')
  if j['refused']:state('DROP queue '+j['id']+' '+fresh['reason'])
 
 for j in jobs:
  d=done.get(j['id'],{});n=j['n'];p=out/j['id']/'final'/f'{n}.csv'
  if j.get('refused') or j['kind']=='control' or not d.get('quench_from_certified')or not p.exists():continue
  if hashlib.sha256(p.read_bytes()).hexdigest()!=d['sha256']:raise RuntimeError('receipt hash mismatch '+j['id'])
  proof=A.audit(W/j['start'],n,**dict(src=j.get('source',''),lic=j.get('licence',''))) if not j.get('ancestry') else load(pathlib.Path(j['ancestry']),{})
  if not proof.get('ok'):continue
  sc=d['new'];eligible.append((j,d,p))
  if sc<bar[n]-1e-10 and sc<peer[n]-1e-12:choices.setdefault(n,[]).append((j,d,p))
 for n,options in choices.items():
  chosen,refused=first_clean(options,G.check)
  for j,checked in refused:state('WITHHOLD independent source n='+str(n)+' id='+j['id']+' '+str(checked['hits'])[:1200])
  if chosen:best[n]=chosen
 old={int(r['n']):r for r in A.rows(T/'take.tsv')};rs=[]
 for n,(j,d,p)in sorted(best.items()):
  dest=T/f'{n}.csv';tmp=dest.with_suffix('.csv.tmp');shutil.copyfile(p,tmp);tmp.replace(dest)
  ap=load(pathlib.Path(j['ancestry']),{});src,lic=A.published(dict(proof=j['ancestry']))
  src+='; frozen full source walk '+j.get('evidence','')+' sha256 '+j.get('evidence_sha256','')
  row=dict(n=n,held=bar[n],new=d['new'],gain=bar[n]-d['new'],source='invent_rest.py local kick and family squeeze, floatsafe, completed certified-file fq; '+src,licence=lic)
  rs.append(row)
 q=T/'take.tsv.tmp'
 with q.open('w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(rs)
 q.replace(T/'take.tsv')
 for n in old:
  if n not in best:
   state(f'DROP live take n={n}: external peer or changed base is lower');(T/f'{n}.csv').unlink(missing_ok=True)
 for row in rs:
  if str(row['new'])!=old.get(row['n'],{}).get('new'):
   state(f"CERT n={row['n']} score={row['new']} basegain={row['gain']}; completed boxE certified-file fq and receipt proof")
   handoff(f"certified n={row['n']} score={row['new']}, {T}/{row['n']}.csv; exact ancestry {best[row['n']][0]['ancestry']}")
 deferred=set(load(W/'deferred.json',[]))
 for j in jobs:
  if j['id']in deferred or j.get('refused')or j['kind']=='control':continue
  d=done.get(j['id'],{});n=j['n'];p=out/j['id']/'certin'/f'{n}.csv'
  if not d.get('error')or not p.exists()or 'midm_fqonce'not in d['error']:continue
  nn,L,_,b=shape(p)
  if nn!=n or L/math.sqrt(n)-1>=bar[n]-1e-10:continue
  folder=W/'deferred'/j['id'];folder.mkdir(parents=True,exist_ok=True)
  dest=folder/f'{n}.csv';dest.write_bytes(b)
  src,lic=A.published(dict(proof=j['ancestry']));atomic(dest.with_suffix('.json'),dict(n=n,source=src,licence=lic,side=L,needs_certified_input_quench=True))
  with open(S/'handoff-r28.log','a')as h:h.write(now()+f' invent -> quench: unfinished certified-input quench n={n}, side={L:.12f}; source proof {j["ancestry"]}; {dest}\n')
  deferred.add(j['id']);state(f'DEFER certified input n={n} to quench; {dest}')
 atomic(W/'deferred.json',sorted(deferred))
 # End files with ancestry sidecars are available to followers even above the bar.
 handed=set(load(W/'handed.json',[]))
 for j,d,p in eligible:
  final_side=(d['new']+1)*math.sqrt(j['n'])
  if j['side']-final_side<=1e-8 and (j['n']not in best or best[j['n']][0]['id']!=j['id']):continue
  if j['id']in handed:continue
  n=j['n'];L=(d['new']+1)*math.sqrt(n)
  if L>(bar[n]+1)*math.sqrt(n)+.015:continue
  if not G.check(j,p)['clean']:continue
  handed.add(j['id'])
  dest=T/'near'/f'{n}-{j["id"]}.csv';tmp=dest.with_suffix('.csv.tmp');shutil.copyfile(p,tmp)
  src,lic=A.published(dict(proof=j['ancestry']));atomic(dest.with_suffix('.json'),dict(n=n,source='invent_rest.py local kick, family squeeze, floatsafe and completed certified-file fq; '+src,licence=lic,side=L,sha256=d['sha256'],receipt=str(p.parent.parent/'done.json')))
  tmp.replace(dest)
  handoff(f'finished local kick n={n}, side={L:.12f}; {dest}')
 atomic(W/'handed.json',sorted(handed))
 # Record main and addressed handoffs on every short collector pass.
 lines=(S/'handoff-r28.log').read_text().splitlines();count=load(W/'handoff-count.json',0)
 for l in lines[count:]:
  if 'main -> all:'in l or ' -> invent:'in l:state('HANDOFF READ '+l.split(': ',1)[0]+'; sha256 '+hashlib.sha256(l.encode()).hexdigest()+'; handoff-r28.log')
 atomic(W/'handoff-count.json',len(lines))
 # Control must pass in its current completed trace and complete the required quench.
 green=False
 ctl=done.get('ctl907',{})
 if ctl.get('quench_from_certified')and (ctl['new']+1)*math.sqrt(907)<30.6195806:green=True
 if green and not(W/'CONTROL_GREEN').exists():
  (W/'CONTROL_GREEN').write_text(json.dumps(ctl));call(['rsync','-a',str(W/'CONTROL_GREEN'),REM]);state('CONTROL GREEN stopped907 local kick and certified-input fq passed: '+json.dumps(ctl))
 # Preserve strict fresh priority while draining saved starts on quiet slots.
 if globals().get('COLLECT_ONLY')or time.time()>float((W/'search-deadline').read_text()):return
 for n,(j,d,p)in best.items():peer[n]=min(peer[n],d['new'])
 audited=load(W/'audit-ready.json',[])
 if audited:
  atomic(W/'saved-pending.json',audited+load(W/'saved-pending.json',[]));(W/'saved-loaded').unlink(missing_ok=True)
  (W/'audit-ready.json').replace(W/'audit-adopted.json');state('ADOPT independent source-audited saved inputs '+str([v['id']for v in audited]))
 seen=set(load(W/'seen.json',[]));seen.update(load(W/'historical-fingerprints.json',[]));filecache=load(W/'filecache.json',{})
 version=SOURCE_GENERATION+':'+hashlib.sha256((R/'quench_walk.py').read_bytes()).hexdigest()
 if load(W/'source-version.json','')!=version:
  filecache={};atomic(W/'source-version.json',version)
 candidates=[]
 completed_hashes=set(load(W/'completed-hashes.json',[]))
 if not(W/'saved-loaded').exists():
  pending=load(W/'saved-pending.json',[]);remaining=pending[1:];pending=pending[:1];drops=[]
  for j in pending:
   p=pathlib.Path(j['start']) if pathlib.Path(j['start']).is_absolute() else S/'take-invent-r24/work'/j['start']
   if not p.exists():drops.append(dict(id=j['id'],reason='snapshot missing'));continue
   n,L,fp,b=shape(p)
   if fp in seen or hashlib.sha256(b).hexdigest()in completed_hashes:drops.append(dict(id=j['id'],reason='exact completed input'));continue
   proof=A.audit(p,n,j['source'],j['licence'])
   if not proof['ok']:drops.append(dict(id=j['id'],n=n,reason=proof['reason']));continue
   if L>(peer[n]+1)*math.sqrt(n)+.015:drops.append(dict(id=j['id'],n=n,reason='above side margin',side=L,bar=(peer[n]+1)*math.sqrt(n)));continue
   candidates.append((2,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'saved',j['fq'],j['seconds'],j['seed'],j['id']))
  atomic(W/'saved-drops.json',drops);atomic(W/'saved-rerank.json',[dict(id=c[-1],n=c[3],delta=c[1],proof=c[7]['proof'])for c in sorted(candidates,key=lambda c:c[:2])]);state(f'RERANK saved starts: {len(pending)} assessed, {len(candidates)} eligible, {len(drops)} refused; work/saved-rerank.json and saved-drops.json')
  atomic(W/'saved-pending.json',remaining)
  if not remaining:(W/'saved-loaded').touch()
 # Seed only completed historical geometry; all pending immutable starts remain eligible.
 if not(W/'history-loaded').exists():
  for rd in (21,22,23,24,25,26):
   wd=S/f'take-invent-r{rd}/work';oldjobs=load(wd/'jobs.json',[])
   complete={p.parent.name for p in (wd/'boxE-raw').glob('*/done.json')}
   for j in oldjobs:
    if j['id']not in complete or j['kind']=='control':continue
    try:seen.add(shape(wd/j['start'])[2])
    except Exception:pass
  (W/'history-loaded').touch()
 intake_count=0
 for table in sorted(S.glob('take-*-r28/take.tsv'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
  if intake_count>=1:break
  lane=table.parent.name[5:-4]
  if lane not in TRACK:continue
  for row in A.rows(table):
   if intake_count>=1:break
   try:n=int(row['n']);p=table.parent/f'{n}.csv'
   except (KeyError,ValueError):continue
   if not p.exists()or p.stat().st_mtime_ns>table.stat().st_mtime_ns:continue
   token=hashlib.sha256(p.read_bytes()+(row['source']+'\0'+row['licence']).encode()).hexdigest()
   if filecache.get(str(p))==token:continue
   nn,L,fp,b=shape(p)
   if nn!=n or p.stat().st_mtime_ns>table.stat().st_mtime_ns or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if fp in seen or L>(peer[n]+1)*math.sqrt(n)+.015:filecache[str(p)]=token;continue
   intake_count+=1
   proof=A.audit(p,n,row['source'],row['licence'])
   if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if not proof['ok']:
    with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token;continue
   candidates.append((-.8 if lane in ('readers','family','k123','rebuild','gap')else -.5,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',lane=='forensics',420 if lane=='k123' or 'k123_join' in row['source'][:1600] else 180,123,''));filecache[str(p)]=token
 # Handoff paths may precede a producer's public take publication.
 for line in lines:
  if intake_count>=1:break
  if 'invent ->' in line:continue
  for ref in re.findall(r'$SCRATCH/bounties-squares/take-[a-z0-9-]+-r28/[^\s,;]+\.csv',line):
   p=pathlib.Path(ref)
   if not p.exists() or '/near/' in ref or re.fullmatch(r'\d+\.csv',p.name) and p.parent.name.startswith('take-'):continue
   token=str(p.stat().st_mtime_ns)
   if filecache.get(str(p))==token:continue
   try:
    n,L,fp,b=shape(p)
    if n not in peer or fp in seen or L>(peer[n]+1)*math.sqrt(n)+.015:continue
    src,lic,_=A.metadata(p,n)
    if not src and 'licence=' in line:
     src='exact public handoff '+line;lic=line.split('licence=',1)[1].split(', /Volumes/',1)[0]
    if intake_count>=1:break
    intake_count+=1
    proof=A.audit(p,n,src,lic)
    if proof['ok']:
     candidates.append((-.9,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',False,420 if 'k123' in src else 180,123,''))
    else:
     with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token
   except Exception:continue
 # New near geometry receives a single run. Repeated old geometry stays in history.
 for p in sorted(S.glob('take-*-r28/near/**/*.csv'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
  if intake_count>=2:break
  lane=p.parts[len(S.parts)][5:-4]
  if lane not in TRACK:continue
  token=hashlib.sha256(p.read_bytes()+b'|'.join(q.read_bytes()for q in (p.with_suffix('.json'),pathlib.Path(str(p)+'.json'),p.parent/'near.tsv')if q.exists())).hexdigest()
  if filecache.get(str(p))==token:continue
  try:
   n,L,fp,b=shape(p)
   if n not in peer or fp in seen or abs(L-(peer[n]+1)*math.sqrt(n))>.015:filecache[str(p)]=token;continue
   intake_count+=1
   proof=A.audit(p,n)
   if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if not proof['ok']:
    with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token;continue
   fq=lane=='forensics';candidates.append((-.6 if lane in FRESH_BUILD else -.3,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'near',fq,420 if lane=='k123' or 'k123_join' in proof.get('source','')[:1600]else(300 if fq else 180),123,''));filecache[str(p)]=token
  except Exception:continue
 # One continuation per useful new find. Never repeat the leg's geometry.
 for j,d,p in eligible:
  if j['kind']in ('leg','control')or j.get('original_kind')=='leg'or 'leg:'+j['id']in seen:continue
  n=j['n'];L=(d['new']+1)*math.sqrt(n);move=j['side']-L
  if move<5e-8 or L-(peer[n]+1)*math.sqrt(n)>max(2e-5,move):continue
  _,_,fp,b=shape(p);proof=dict(ok=True,proof=j['ancestry'],inherited_evidence=j.get('evidence'))
  candidates.append((-1 if move>1e-5 else -.1,-move,p,n,L,'leg:'+j['id'],b,proof,'leg',j['fq'],420,172,''))
 # A successful plain continuation can expose another junction. Change its mechanism once on two ends.
 end_walk_marks=set(load(W/'end-walk-seen.json',[]))
 if load(W/'WALK_CONTROL_RESULT',{}).get('green'):
  for parent,d,p in sorted(eligible,key=lambda v:v[1]['new']-peer[v[0]['n']]):
   if len(end_walk_marks)>=2:break
   if parent['kind']!='leg'or parent['id']in end_walk_marks:continue
   n=parent['n'];L=(d['new']+1)*math.sqrt(n)
   if parent['side']-L<5e-8 or L-(peer[n]+1)*math.sqrt(n)>2e-5:continue
   from seam_boxes28 import box
   plan=box(p,n)
   if not plan:continue
   nn,LL,fp,b=shape(p)
   proof=dict(ok=True,proof=parent['ancestry'],options=['--cbox',plan['cbox'],'--walk','0.000001','--plateau-stop','0'],end_walk_parent=parent['id'])
   candidates.append((-.2,L-(peer[n]+1)*math.sqrt(n),p,n,L,'end-walk:'+parent['id'],b,proof,'walk',False,420,2861,''))
   end_walk_marks.add(parent['id']);state('PLAN controlled tight walk after material plain leg '+parent['id']+'; changed mechanism, cap2 distinct ends; common05:45Z')
 atomic(W/'end-walk-seen.json',sorted(end_walk_marks))
 claims=[l for l in lines if 'backlog ->'in l and ('CLAIM'in l.upper()or 'claim'in l)]
 for rank,delta,p,n,L,fp,b,proof,kind,fq,seconds,seed,oldid in sorted(candidates,key=lambda c:c[:2]):
  if fp in seen or hashlib.sha256(b).hexdigest()in completed_hashes:continue
  if claimed_input(n,hashlib.sha256(b).hexdigest(),lines):
   state(f'SKIP exact n={n} sha='+hashlib.sha256(b).hexdigest()[:12]+', claimed by backlog');continue
  if kind=='saved'and any(oldid in l or str(p)in l for l in claims):state(f'SKIP saved {oldid}, claimed by backlog');continue
  ident=f'{kind[0]}{time.strftime("%H%M%S",time.gmtime())}x{n}x{len(jobs)}'
  start='starts/'+ident+'.csv';(W/start).write_bytes(b)
  ap=proof['proof']
  evidence=G.freeze(p,n,ap)
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashlib.sha256(b).hexdigest():
   state('DEFER start changed during full source audit '+str(p));continue
  if not evidence['clean']:
   state('REFUSE frozen evidence '+str(p)+' '+str(evidence.get('hits'))[:600]);continue
  jobs.append(dict(id=ident,n=n,start=start,seconds=seconds,seed=seed,kind=kind,fq=fq,bar=(peer[n]+1)*math.sqrt(n),side=L,ancestry=ap,priority=rank,order=delta,input_sha256=hashlib.sha256(b).hexdigest(),old_id=oldid,evidence=evidence['path'],evidence_sha256=evidence['sha256'],options=proof.get('options',[]),end_walk_parent=proof.get('end_walk_parent')))
  seen.add(fp)
  # Checkpoint an admitted job before the next source walk can delay the queue.
  atomic(W/'jobs.json',jobs);atomic(W/'seen.json',sorted(seen))
  active=[v for v in jobs if v['id']not in locks and not v.get('refused')]
  active.sort(key=lambda v:(v.get('priority',0),v.get('order',0)))
  call(['rsync','-a',str(W/start),REM+'starts/'])
  for slot in (1,2,3):atomic(W/f'queue{slot}.json',active)
  call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
  state(f'QUEUE {ident} n={n} {kind} delta={delta:+.8g} from {p}; source proof {ap}; boxE deadline05:45Z')
  if kind=='saved':handoff(f'CLAIM saved invent-r24 {oldid}; immutable input {p}, queued {ident}')
 # Polished starts can stall above fq's floor under the plain squeeze (invent.md 15.4).
 # Try the documented per-try fq repair once on an already admitted exact input.
 repair_marks=set(load(W/'repair-fq-seen.json',[]));new_repairs=[]
 prior_fq={v[0]for v in load(S/'take-invent-r27/work/completed-inputs.json',[])if v[2]}
 for parent in list(jobs):
  if len(repair_marks)>=12:break
  if parent['kind']not in('fresh','near')or parent.get('fq')or parent.get('refused'):continue
  d=done.get(parent['id'],{});digest=parent.get('input_sha256','')
  if not d or 'error'in d or not digest or digest in repair_marks or digest in prior_fq:continue
  if parent['side']-(peer[parent['n']]+1)*math.sqrt(parent['n'])>1e-4:continue
  if claimed_input(parent['n'],digest,lines):continue
  original=W/parent['start']
  if hashlib.sha256(original.read_bytes()).hexdigest()!=digest:raise RuntimeError('changed immutable repair input')
  checked=G.check(parent,original)
  if not checked['clean']:continue
  ident='q'+time.strftime('%H%M%S',time.gmtime())+'x'+str(parent['n'])+'x'+str(len(jobs)+len(new_repairs))
  start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
  job=dict(parent,id=ident,start=start,kind='repair',fq=True,seconds=420 if parent['seconds']>=420 else 240,seed=2811,priority=2,order=parent['side']-(peer[parent['n']]+1)*math.sqrt(parent['n']),repair_parent=parent['id'])
  new_repairs.append(job);repair_marks.add(digest)
  state('QUEUE changed repair '+ident+' n='+str(job['n'])+' per-try fq after squeeze, exact input '+digest+'; prior plain-squeeze parent '+parent['id']+'; common05:45Z')
 jobs.extend(new_repairs);atomic(W/'repair-fq-seen.json',sorted(repair_marks))
 # Wider kicks have their own completed numeric control and a separate eight-geometry cap.
 wide=load(out/'WIDE_CONTROL_GREEN',{});wide_options=['--rmax','5.0','--sigs','0.01,0.02,0.04','--apart','0.08']
 control_csv=out/'wide907-control/final/907.csv';control_in=out/'wide907-control/certin/907.csv';control_done=out/'wide907-control/quench/907.done'
 wide_green=wide.get('quench_from_certified')and wide.get('side',99)<30.6195806 and wide.get('clearance',0)>=2.2e-11 and wide.get('options')==wide_options and control_csv.is_file()and control_in.is_file()and control_done.is_file()
 if wide_green:
  wide_green=hashlib.sha256(control_csv.read_bytes()).hexdigest()==wide['sha256']and hashlib.sha256(control_in.read_bytes()).hexdigest()==wide['quench_input_sha256']==control_done.read_text().strip()
 if wide_green and not(W/'WIDE_CONTROL_ADOPTED').exists():
  atomic(W/'WIDE_CONTROL_ADOPTED',wide);state('CONTROL GREEN wider kick certified-input fq side='+str(wide['side'])+' clearance='+str(wide['clearance']))
 wide_marks=set(load(W/'wide-seen.json',[]));new_wide=[]
 if wide_green:
  for parent in list(jobs):
   if len(wide_marks)>=8:break
   if parent['kind']not in('fresh','near','saved')or parent.get('refused'):continue
   d=done.get(parent['id'],{});digest=parent.get('input_sha256','')
   if not d or 'error'in d or not digest:continue
   if parent['side']-(peer[parent['n']]+1)*math.sqrt(parent['n'])>.002:continue
   if claimed_input(parent['n'],digest,lines):continue
   original=W/parent['start'];n,L,fp,b=shape(original)
   if fp in wide_marks:continue
   if hashlib.sha256(b).hexdigest()!=digest:raise RuntimeError('changed immutable wider-kick input')
   if not G.check(parent,original)['clean']:continue
   ident='w'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(new_wide));start='starts/'+ident+'.csv';(W/start).write_bytes(b)
   job=dict(parent,id=ident,start=start,kind='wide',fq=False,seconds=300,seed=2829,priority=3,options=wide_options,order=L-(peer[n]+1)*math.sqrt(n),wide_parent=parent['id'])
   new_wide.append(job);wide_marks.add(fp);state('QUEUE wider kick '+ident+' n='+str(n)+' changed radius/sigma/repair, exact input '+digest+'; control907 green; common05:45Z')
 jobs.extend(new_wide);atomic(W/'wide-seen.json',sorted(wide_marks))
 # Certify a competitive admitted input directly, even when its search returned no raw find.
 rescued=set(load(W/'rescue-seen.json',[]));rescues=[]
 for parent in list(jobs):
  if len(rescued)>=24:break
  if parent['kind']in('control','rescue')or parent.get('refused')or not parent.get('evidence'):continue
  n=parent['n'];digest=parent.get('input_sha256','');floor=min(bar[n],peer[n],best[n][1]['new']if n in best else 99)
  if not digest or digest in rescued or parent['side']/math.sqrt(n)-1>=floor-2e-10:continue
  if claimed_input(n,digest,lines):continue
  original=W/parent['start']
  if hashlib.sha256(original.read_bytes()).hexdigest()!=digest:raise RuntimeError('changed rescue input')
  if not G.check(parent,original)['clean']:continue
  ident='z'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(rescues));start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
  rescues.append(dict(parent,id=ident,start=start,kind='rescue',seconds=0,fq=False,options=[],seed=0,priority=-2.5,order=parent['side']-(peer[n]+1)*math.sqrt(n),rescue_parent=parent['id']))
  rescued.add(digest);state('QUEUE finish-only source-cleared competitive input '+ident+' from '+parent['id']+'; exact input '+digest+'; common05:45Z')
 jobs.extend(rescues);atomic(W/'rescue-seen.json',sorted(rescued))
 # The next selector targets orientation junctions and must pass its own real 907 control.
 seam_plan=load(W/'seam-plan.json',{});seam_ctl=seam_plan.get('control');seam_id='ctl-seam907'
 if seam_ctl and not any(j['id']==seam_id for j in jobs):
  opts=['--cbox',seam_ctl['cbox']]
  jobs.append(dict(id=seam_id,n=907,start='starts/control907.csv',seconds=300,seed=2,kind='control',fq=False,bar=30.6195806,side=30.61958067887703,priority=-10,order=0,options=opts,input_sha256=seam_ctl['input_sha256']))
  state('START queued orientation-junction control907, cbox='+seam_ctl['cbox']+'; requires completed certified-input fq and side<30.6195806')
 sd=done.get(seam_id,{});sp=out/seam_id/'final/907.csv'
 seam_green=sd.get('quench_from_certified')and (sd.get('new',99)+1)*math.sqrt(907)<30.6195806 and sd.get('clearance',0)>=2.2e-11 and sp.is_file()and hashlib.sha256(sp.read_bytes()).hexdigest()==sd.get('sha256')
 if sd and not(W/'SEAM_CONTROL_RESULT').exists():
  atomic(W/'SEAM_CONTROL_RESULT',dict(green=bool(seam_green),result=sd));state('CONTROL junction907 green='+str(bool(seam_green))+' '+str(sd))
 seam_marks=set(load(W/'seam-seen.json',[]));seam_jobs=[]
 if seam_green:
  for parent in list(jobs):
   if len(seam_marks)>=8:break
   if parent['kind']not in('fresh','near','saved')or parent.get('refused')or parent['id']not in done:continue
   n=parent['n'];digest=parent.get('input_sha256','');plan=seam_plan.get('inputs',{}).get(digest)
   if not plan or parent['side']-(peer[n]+1)*math.sqrt(n)>.002 or claimed_input(n,digest,lines):continue
   original=W/parent['start'];nn,L,fp,b=shape(original)
   if fp in seam_marks:continue
   if hashlib.sha256(b).hexdigest()!=digest:raise RuntimeError('changed junction input')
   if not G.check(parent,original)['clean']:continue
   ident='c'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(seam_jobs));start='starts/'+ident+'.csv';(W/start).write_bytes(b)
   seam_jobs.append(dict(parent,id=ident,start=start,kind='seam',seconds=300,seed=2841,fq=False,priority=3,options=['--cbox',plan['cbox']],order=L-(peer[n]+1)*math.sqrt(n),seam_parent=parent['id']))
   seam_marks.add(fp);state('QUEUE orientation-junction kick '+ident+' cbox='+plan['cbox']+'; exact input '+digest+'; common05:45Z')
 jobs.extend(seam_jobs);atomic(W/'seam-seen.json',sorted(seam_marks))


 # Round20's global walk at1e-4 returned to an older basin. Test a hundredfold smaller tolerance at a junction.
 walk_id='ctl-walk907';walk_options=['--walk','0.000001','--plateau-stop','0']
 if seam_ctl and not any(j['id']==walk_id for j in jobs):
  jobs.append(dict(id=walk_id,n=907,start='starts/control907.csv',seconds=300,seed=2,kind='control',fq=False,bar=30.6195806,side=30.61958067887703,priority=-10,order=0,options=['--cbox',seam_ctl['cbox']]+walk_options,input_sha256=seam_ctl['input_sha256']))
  state('QUEUE tight-walk junction control907, tolerance1e-6 instead of round20 failed1e-4; requires completed certified-file fq')
 wd=done.get(walk_id,{});wp=out/walk_id/'final/907.csv'
 walk_green=wd.get('quench_from_certified')and(wd.get('new',99)+1)*math.sqrt(907)<30.6195806 and wd.get('clearance',0)>=2.2e-11 and wp.is_file()and hashlib.sha256(wp.read_bytes()).hexdigest()==wd.get('sha256')
 if wd and not(W/'WALK_CONTROL_RESULT').exists():atomic(W/'WALK_CONTROL_RESULT',dict(green=bool(walk_green),result=wd));state('CONTROL tight-walk907 green='+str(bool(walk_green)))
 walk_marks=set(load(W/'walk-seen.json',[]));walk_jobs=[]
 if walk_green:
  parents=sorted(jobs,key=lambda j:j['id'],reverse=True)
  for parent in parents:
   if len(walk_marks)>=8:break
   if parent['kind']not in('fresh','near','saved')or parent.get('refused'):continue
   d=done.get(parent['id'],{});digest=parent.get('input_sha256','');n=parent['n'];plan=seam_plan.get('inputs',{}).get(digest)
   if not plan or not d.get('quench_from_certified')or not digest:continue
   if parent['side']-(d['new']+1)*math.sqrt(n)<1e-8:continue
   if parent['side']-(peer[n]+1)*math.sqrt(n)>.002 or claimed_input(n,digest,lines):continue
   original=W/parent['start'];nn,L,fp,b=shape(original)
   if fp in walk_marks:continue
   if hashlib.sha256(b).hexdigest()!=digest:raise RuntimeError('changed tight-walk input')
   if not G.check(parent,original)['clean']:continue
   ident='t'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(walk_jobs));start='starts/'+ident+'.csv';(W/start).write_bytes(b)
   walk_jobs.append(dict(parent,id=ident,start=start,kind='walk',seconds=420,seed=2861,fq=False,priority=3,options=['--cbox',plan['cbox']]+walk_options,order=L-(peer[n]+1)*math.sqrt(n),walk_parent=parent['id']))
   walk_marks.add(fp);state('QUEUE tight-walk junction '+ident+' n='+str(n)+' tolerance1e-6, prior same-input plain kick moved; exact input '+digest+'; common05:45Z')
 jobs.extend(walk_jobs);atomic(W/'walk-seen.json',sorted(walk_marks))


 claims=[l for l in lines if 'backlog ->'in l and 'claim'in l.lower()]
 for j in jobs:
  if j['id']not in locks and claimed_input(j['n'],j.get('input_sha256',''),lines):j['claimed_elsewhere']=True
  if j['id']not in locks and j.get('old_id')and any(j['old_id']in l for l in claims):
   j['claimed_elsewhere']=True
   if not j.get('claim_recorded'):state('SKIP queue '+j['id']+' claimed by backlog');j['claim_recorded']=True
 for j in jobs:
  if j.get('ancestry'):
   why=G.banned(pathlib.Path(j['ancestry']).read_text())
   if why:j['refused']=True;j['independent_refusal']=why
 pending=[j for j in jobs if j['id']not in locks and not j.get('refused') and not j.get('claimed_elsewhere')]
 for j in pending:
  if j['kind']!='control':rebar(j,(peer[j['n']]+1)*math.sqrt(j['n']))
  if j['kind']in('fresh','near')and j.get('ancestry'):
   proof=load(pathlib.Path(j['ancestry']),{});node=proof.get('nodes',{}).get(proof.get('root'),{})
   if 'k123_join'in node.get('source','')[:1600]:j['seconds']=420
 pending=[j for j in pending if not j.get('outside_margin')]
 started_counts={j['n']for j in jobs if j['id']in active_locks and j['kind']!='control'}
 pending.sort(key=lambda j:(-10 if j['kind']=='control'else (-3 if j['kind']=='leg'else(-2 if j['kind']=='fresh'else(-1.5 if j['kind']=='saved' else(-1 if j['kind']=='near'and j['n']not in started_counts else j.get('priority',2))))),j.get('order',0),j['id']))
 fresh=[j for j in pending if j['kind']in ('fresh','near','control')];rest=[j for j in pending if j not in fresh]
 old_kind={j['id']:j['kind']for j in load(W/'saved-pending.json',[])}
 for j in jobs:
  if j.get('old_id'):j['original_kind']=old_kind.get(j['old_id'])
 atomic(W/'jobs.json',jobs);atomic(W/'seen.json',sorted(seen));atomic(W/'filecache.json',filecache)
 atomic(W/'queue1.json',fresh+rest);atomic(W/'queue2.json',pending);atomic(W/'queue3.json',pending)
 call(['rsync','-a',str(W/'starts'),REM]);call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
 print(now(),'done',len(done),'jobs',len(jobs),'retained',len(rs),'gain',sum(r['gain']for r in rs),'control',green,flush=True)

if __name__=='__main__':
 while time.time()<float((W/'deadline').read_text())+480 and not(W/'STOP').exists():
  try:turn()
  except Exception:traceback.print_exc();state('CONTROLLER ERROR work/controller.log')
  if '--once'in sys.argv:break
  time.sleep(35)
