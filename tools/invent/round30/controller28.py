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
SOURCE_GENERATION=hashlib.sha256(b''.join((W/name).read_bytes()for name in ('ancestry28.py','source_gate28.py','public_archive28.py','archived_credit28.py','archive28.py','aliases29.py','historical756.py','gather29.py','public_roots29.py','implicit_public29.py','scoped30.py','owned30.py','public_branch30.py','exact_root30.py','extend30.py','controller28.py'))).hexdigest()
from invent_shape22 import fingerprint
REM='boxE:scratch/squares-invent-r30/'
TRACK={'readers','family','stair-c','corners','modules','twoshort','k123','classfill','forensics','harvest','border','soft','midm','gap','backlog','rebuild','quench'}
FRESH_BUILD={'family','readers','k123','rebuild','gap','modules','twoshort','stair-c','corners','forensics','classfill','border'}

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a')as h:h.write(now()+' boxA '+s+'\n')
def atomic(p,x):
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if not j.get('reallocated')and j.get('id')not in load(W/'reallocated-jobs.json',[])]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')not in('invent_barentry30.py','invent_barentry30b.py')or j['kind']=='control'or(W/'BAR_ENTRY_GREEN').exists()]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')!='invent_barentry30c.py'or j['kind']=='control'or(W/'FINE_ENTRY_GREEN').exists()]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')!='invent_barretain30.py'or j['kind']=='control'or(W/'RETAIN_GREEN').exists()]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')!='invent_barretain_budget30.py'or j['kind']=='control'or(W/'RETAIN_BUDGET_GREEN').exists()]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')!='invent_null30.py'or j['kind']=='control'or(W/'NULL_CONTROL_GREEN').exists()]
 if p.name.startswith('queue')and isinstance(x,list):x=[j for j in x if j.get('program')!='invent_bar30.py'or j['kind']=='control'or(W/'BAR_CONTROL_GREEN').exists()]
 q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x,separators=(',',':')));q.replace(p)
def load(p,default):
 try:return json.load(open(p))
 except (OSError,ValueError):return default
def method_name(job):
 if job.get('seconds')==0 and job['kind']!='recovered':return 'finish saved own endpoint with certificate and certified-input fq'
 if job['kind']=='recovered':return 'recovered own r29 '+job['previous_program']+' endpoint and certified-file fq'
 program=load(W/'boxE-raw'/job['id']/'done.json',{}).get('program',job.get('program','lane/invent_rest.py'))
 if program=='invent_barretain_budget30.py':return 'bar-entry kick with bounded coarse search and finer saved candidates'
 if program=='invent_barretain30.py':return 'bar-entry local kick with coarse search and finer saved candidates'
 if program=='invent_barentry30c.py':return 'bar-entry local kick with legal baseline and finer above-bar steps'
 if program in('invent_barentry30.py','invent_barentry30b.py'):return 'bar-entry local kick with legal input baseline and family squeeze'
 if program=='invent_null30.py':return 'invent_null30.py fixed-side random contact LP and family squeeze'
 if program=='invent_bar30.py':return 'invent_bar30.py compressed bar-side local kick and family squeeze'
 if program=='globalfit29.py':return 'globalfit29.py whole-packing rigid rotation'
 if program=='invent_domain29.py':return 'invent_domain29.py rigid domain kick and family squeeze'
 return 'invent_rest.py local kick and family squeeze'

def credit(job):
 src,lic=A.published(dict(proof=job['ancestry']))
 checked=load(W/'independent-results'/f'{job["id"]}.json',{})
 audit=checked.get('public_sources')or{}
 if audit.get('receipt'):src+='; first-public source audit '+audit['receipt']+' sha256 '+audit['receipt_sha256']
 for row in((checked.get('public_sources')or{}).get('public_roots',[])+(checked.get('public_sources')or{}).get('source_notices',[])):
  item=row.get('captured_public_archive')
  if not item:continue
  src+='; captured first-public archive '+item['source']+' sha256 '+item['sha256']
  for upstream in item.get('upstream',[]):
   ref=upstream.get('source_ref')or upstream.get('source')
   if ref:src+='; upstream '+str(ref)+' named in notebook own source table';lic+='; upstream '+str(ref)+' via notebook own source table'
 return src,lic

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
 if job['kind']in ('fresh','near','saved','seed'):
  job['order']=job['side']-side
  job['outside_margin']=job['order']>.015
 elif job['kind']in('repair','wide','seam','rescue','walk','domain','domainwalk','largedomain','joinlong'):
  job['order']=job['side']-side;job['outside_margin']=job['order']>(1e-4 if job['kind']=='repair'else .002)
 elif job['kind']=='leg':
  job['outside_margin']=job['side']-side>max(2e-5,-job.get('order',0))
 return job


def priority(j):
 if j['kind']=='control':return -10
 overrides=load(W/'priority-overrides.json',{})
 if j['id']in overrides:return float(overrides[j['id']])
 if j['kind']in('leg','rescue'):return -3
 if j['kind']=='fresh':return -4
 if j['kind']=='joinlong':return -2.2
 if j['kind']=='walk':return -1.75
 if j['kind']=='domainwalk':return min(-1.6,j.get('priority',-1.6))
 if j['kind']=='near'and j.get('order',0)<=1e-4:return -1.5
 if j['kind']=='saved':return 1
 return j.get('priority',2)

def claimed_input(n,digest,lines):
 for line in lines:
  if 'invent ->'in line or 'claim'not in line.lower():continue
  counts=re.findall(r'\bn\s*=\s*(\d+)',line)
  hashes=re.findall(r'inputsha256[=: ]+([0-9a-f]{12,64})',line)
  if str(n)in counts and any(digest.startswith(prefix)for prefix in hashes):return True
  for count,prefix in re.findall(r'(?:follow:take-[a-z0-9-]+-r30-|reopen:reopen-|near:near-)(\d+)-([0-9a-f]{8,64})',line):
   if int(count)==n and digest.startswith(prefix):return True
 return False

def handoff(msg):
 with open(S/'handoff-r30.log','a')as h:h.write(now()+' invent -> all: '+msg+'\n')
def base():
 details=S/'round30-briefs/bar30.tsv'
 bar={int(r['n']):float(r['bar'])for r in csv.DictReader(open(details),delimiter='\t')}
 atomic(W/'base.json',dict(details=str(details),posted=True,scores=bar))
 return bar

def bars():
 bar=base();peer=dict(bar)
 for table in S.glob('take-*-r30/take.tsv'):
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
 out=sync();jobs=load(W/'jobs.json',[]);extras=load(W/'extra-ready.json',[]);jobs.extend(v for v in extras if not any(j['id']==v['id'] for j in jobs));atomic(W/'jobs.json',jobs);done={p.parent.name:load(p,{})for p in out.glob('*/done.json')}
 for j in jobs:
  if j.get('rescue_parent')and any(v['id']==j['rescue_parent']and v.get('seconds')==0 for v in jobs):j['reallocated']=True
 # Publish the source graph captured at intake, never a later rewrite at the same path.
 for job in jobs:
  if job['id']in load(W/'reallocated-jobs.json',[]):job['reallocated']=True
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

 locks=set(call(['ssh','boxE','ls $SCRATCH/squares-invent-r30/locks']).split()); active_locks=locks-set(done)
 profiles={}
 for job in sorted(jobs,key=lambda j:0 if j['id']in locks else 1):
  if job['kind']not in('fresh','near')or job.get('reallocated'):continue
  key=(job.get('input_sha256'),job.get('program'),job.get('seed'),job.get('fq'),job.get('seconds'),json.dumps(job.get('options',[])))
  if key in profiles and job['id']not in locks:
   job['reallocated']=True;state('SKIP duplicate unstarted numerical profile '+job['id']+'; existing '+profiles[key])
  else:profiles[key]=job['id']
 atomic(W/'jobs.json',jobs)
 rec=load(W/'recorded.json',dict(start=[],end=[]))
 for j in jobs:
  if j['id']in locks and j['id']not in rec['start']:
   state(f"START boxE {j['id']} n={j['n']} kind={j['kind']} seconds={j['seconds']} seed={j['seed']}; log work/boxE-raw/{j['id']}/run.log deadline17:45Z");rec['start'].append(j['id'])
  if j['id']in done and j['id']not in rec['end']:
   state('FINISH boxE '+j['id']+' '+json.dumps(done[j['id']],sort_keys=True));rec['end'].append(j['id'])
 atomic(W/'recorded.json',rec)
 # Recheck every captured source when public policy or explicit withdrawals change.
 epoch=G.review_epoch()+(':'+str(int(time.time()//300))if any(j.get('source_hold')and j['id']not in done for j in jobs)else '')
 if load(W/'source-review-epoch.json','')!=epoch:
  controls=[j for j in jobs if j['kind']=='control'and j['id']not in locks]
  for slot in (1,2,3):atomic(W/f'queue{slot}.json',controls)
  call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
  rejected=[];approved=list(controls);review_lines=(S/'handoff-r30.log').read_text().splitlines();review_bar,review_peer=bars()
  # Check active and next-to-run jobs before historical ends. Refill each slot
  # as soon as a complete current source check accepts its next input.
  for j in sorted(jobs,key=lambda v:(0 if v['id']in active_locks else 1 if v['id']not in locks else 2,priority(v),v.get('order',0))):
   if j['kind']=='control'or not j.get('ancestry')or not j.get('evidence'):continue
   if j['id']in done and not done[j['id']].get('quench_from_certified'):continue
   checked=G.check(j,W/j['start']);j['source_hold']=not checked['clean']
   if checked['clean']and len({v['n']for v in approved})<3 and j['id']not in locks and not j.get('refused')and not j.get('reallocated')and not j.get('claimed_elsewhere')and not claimed_input(j['n'],j.get('input_sha256',''),review_lines)and not globals().get('COLLECT_ONLY')and time.time()<float((W/'search-deadline').read_text()):
    proof=load(pathlib.Path(j['ancestry']),{});rebar(j,(review_peer[j['n']]+1)*math.sqrt(j['n']))
    if not j.get('outside_margin')and proof.get('ok')and all(A.rejected(v['source'],v['licence'],terminal=not v.get('parents'))is None for v in proof.get('nodes',{}).values())and hashlib.sha256((W/j['start']).read_bytes()).hexdigest()==j.get('input_sha256'):
     approved.append(j);call(['rsync','-a',str(W/j['start']),REM+'starts/'])
     for slot in(1,2,3):atomic(W/f'queue{slot}.json',approved)
     call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM]);state('SOURCE REVIEW early checked dispatch '+j['id']+'; complete current source gate passed before archive rechecks finish')
   if not checked['clean']:
    j['source_refusal']=checked['hits'];rejected.append(j['id'])
    if j['id']in active_locks:
     call(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python','-I','$SCRATCH/squares-invent-r30/cleanup28.py','cancel',j['id']])
    near=T/'near'/f'{j["n"]}-{j["id"]}.csv'
    if near.is_file():
     digest=hashlib.sha256(near.read_bytes()).hexdigest();dest=W/'withheld-source'/near.name;dest.parent.mkdir(exist_ok=True);shutil.move(near,dest)
     side=near.with_suffix('.json')
     if side.exists():shutil.move(side,dest.with_suffix('.json'))
     handoff('WITHDRAW near n='+str(j['n'])+' exact sha256 '+digest+', '+str(near)+'; recorded first-public source or exact parent withdrawal failed; evidence '+j['evidence'])
  atomic(W/'jobs.json',jobs);atomic(W/'source-review-epoch.json',epoch);state('SOURCE REVIEW '+str(len(jobs))+' captured jobs, held '+str(rejected)+'; public origins only, own layouts unmeasured')

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
  if j.get('refused')or j.get('source_hold') or j['kind']=='control' or not d.get('quench_from_certified')or not p.exists():continue
  if (W/'branch-audit-pending').exists()and j['kind']!='recovered':continue
  if hashlib.sha256(p.read_bytes()).hexdigest()!=d['sha256']:raise RuntimeError('receipt hash mismatch '+j['id'])
  proof=A.audit(W/j['start'],n,**dict(src=j.get('source',''),lic=j.get('licence',''))) if not j.get('ancestry') else load(pathlib.Path(j['ancestry']),{})
  if not proof.get('ok'):continue
  sc=d['new'];eligible.append((j,d,p))
  if sc<bar[n]-1e-10 and sc<peer[n]:choices.setdefault(n,[]).append((j,d,p))
 for n,options in choices.items():
  chosen,refused=first_clean(options,G.check)
  for j,checked in refused:state('WITHHOLD independent source n='+str(n)+' id='+j['id']+' '+str(checked['hits'])[:1200])
  if chosen:best[n]=chosen
 old={int(r['n']):r for r in A.rows(T/'take.tsv')};rs=[]
 for n,(j,d,p)in sorted(best.items()):
  dest=T/f'{n}.csv';tmp=dest.with_suffix('.csv.tmp');shutil.copyfile(p,tmp);tmp.replace(dest)
  ap=load(pathlib.Path(j['ancestry']),{});src,lic=credit(j)
  src+='; frozen full source walk '+j.get('evidence','')+' sha256 '+j.get('evidence_sha256','')
  row=dict(n=n,held=bar[n],new=d['new'],gain=bar[n]-d['new'],source=method_name(j)+', finesafe, completed certified-file fq; '+src,licence=lic)
  rs.append(row)
 q=T/'take.tsv.tmp'
 with q.open('w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(rs)
 q.replace(T/'take.tsv')
 for n in old:
  if n not in best:
   state(f'SUPERSEDED live n={n}: peer or base is lower; preserve bytes through final freeze')
   p=T/f'{n}.csv'
   if p.exists():
    folder=W/'superseded';folder.mkdir(exist_ok=True);digest=hashlib.sha256(p.read_bytes()).hexdigest();shutil.copyfile(p,folder/f'{n}-{digest}.csv');atomic(folder/f'{n}-{digest}.json',old[n])
 for row in rs:
  if str(row['new'])!=old.get(row['n'],{}).get('new'):
   state(f"CERT n={row['n']} score={row['new']} basegain={row['gain']}; completed boxE certified-file fq and receipt proof")
   handoff(f"certified n={row['n']} score={row['new']}, {T}/{row['n']}.csv; exact ancestry {best[row['n']][0]['ancestry']}")
 deferred=set(load(W/'deferred.json',[]))
 for j in jobs:
  if j['id']in deferred or j.get('refused')or j.get('source_hold')or j['kind']=='control':continue
  d=done.get(j['id'],{});n=j['n'];p=out/j['id']/'certin'/f'{n}.csv'
  if not d.get('error')or not p.exists()or 'midm_fqonce'not in d['error']:continue
  nn,L,_,b=shape(p)
  if nn!=n or L/math.sqrt(n)-1>=bar[n]-1e-10:continue
  folder=W/'deferred'/j['id'];folder.mkdir(parents=True,exist_ok=True)
  dest=folder/f'{n}.csv';dest.write_bytes(b)
  src,lic=credit(j);atomic(dest.with_suffix('.json'),dict(n=n,source=src,licence=lic,side=L,needs_certified_input_quench=True))
  with open(S/'handoff-r30.log','a')as h:h.write(now()+f' invent -> quench: unfinished certified-input quench n={n}, side={L:.12f}; source proof {j["ancestry"]}; {dest}\n')
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
  src,lic=credit(j);atomic(dest.with_suffix('.json'),dict(n=n,source=method_name(j)+', finesafe and completed certified-file fq; '+src,licence=lic,side=L,sha256=d['sha256'],receipt=str(p.parent.parent/'done.json')))
  tmp.replace(dest)
  handoff(f'finished local kick n={n}, side={L:.12f}; {dest}')
 atomic(W/'handed.json',sorted(handed))
 # Record main and addressed handoffs on every short collector pass.
 lines=(S/'handoff-r30.log').read_text().splitlines();count=load(W/'handoff-count.json',0)
 for l in lines[count:]:
  if 'main -> all:'in l or ' -> invent:'in l:state('HANDOFF READ '+l.split(': ',1)[0]+'; sha256 '+hashlib.sha256(l.encode()).hexdigest()+'; handoff-r30.log')
 atomic(W/'handoff-count.json',len(lines))
 # Control must pass in its current completed trace and complete the required quench.
 green=False
 ctl=done.get('ctl907retry',{}) or done.get('ctl907',{})
 if ctl.get('quench_from_certified')and (ctl['new']+1)*math.sqrt(907)<30.6195806:green=True
 if green and not(W/'CONTROL_GREEN').exists():
  (W/'CONTROL_GREEN').write_text(json.dumps(ctl));call(['rsync','-a',str(W/'CONTROL_GREEN'),REM]);state('CONTROL GREEN stopped907 local kick and certified-input fq passed: '+json.dumps(ctl))
 barctl=done.get('ctlbar907',{})
 bargreen=barctl.get('quench_from_certified')and(barctl.get('new',99)+1)*math.sqrt(907)<30.6195806 and barctl.get('clearance',0)>=2.2e-11
 if bargreen and not(W/'BAR_CONTROL_GREEN').exists():
  atomic(W/'BAR_CONTROL_GREEN',barctl);state('CONTROL GREEN compressed bar-side907 completed certified-input fq: '+json.dumps(barctl))
 nullctl=done.get('ctlnull907',{})
 nullgreen=nullctl.get('quench_from_certified')and(nullctl.get('new',99)+1)*math.sqrt(907)<30.6195806 and nullctl.get('clearance',0)>=2.2e-11
 if nullgreen and not(W/'NULL_CONTROL_GREEN').exists():
  atomic(W/'NULL_CONTROL_GREEN',nullctl);state('CONTROL GREEN random contact LP907 completed certified-input fq: '+json.dumps(nullctl))
 entry2=done.get('ctlentry2b',{});entry907=done.get('ctlentry907b',{})
 entry_green=entry2.get('quench_from_certified')and 1.99<(entry2.get('new',99)+1)*math.sqrt(2)<2.01 and entry907.get('quench_from_certified')and(entry907.get('new',99)+1)*math.sqrt(907)<30.6195806
 if entry_green and not(W/'BAR_ENTRY_GREEN').exists():
  atomic(W/'BAR_ENTRY_GREEN',dict(pair=entry2,packing=entry907));state('CONTROL GREEN bar-entry v2 pair and907 with above-bar step1e-7, both completed certified-input fq')
 if entry_green and not globals().get('COLLECT_ONLY')and time.time()<float((W/'search-deadline').read_text()):
  entry_seen=set(load(W/'entry-seen.json',[]))
  for parent in jobs.copy():
   if parent['kind']!='barretry'or parent['n']not in(539,598)or parent['n']in entry_seen:continue
   if parent.get('refused')or parent.get('source_hold')or parent['id']not in done:continue
   n=parent['n'];digest=parent['input_sha256']
   if claimed_input(n,digest,lines):entry_seen.add(n);state('SKIP changed entry profile exact claimed input n='+str(n));continue
   original=W/parent['start'];assert hashlib.sha256(original.read_bytes()).hexdigest()==digest
   if not G.check(parent,original)['clean']:continue
   ident='entry30x'+str(n);start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
   job=dict(parent,id=ident,start=start,kind='entryretry',program='invent_barentry30b.py',seconds=900,seed=123,priority=-1.4,options=['--plateau-stop','0'],entry_parent=parent['id'])
   checked=G.check(job,W/start)
   if not checked['clean']:continue
   jobs.append(job);entry_seen.add(n);atomic(W/'jobs.json',jobs);atomic(W/'entry-seen.json',sorted(entry_seen))
   call(['rsync','-a',str(W/start),REM+'starts/'])
   ready=[v for v in jobs if v['id']not in locks and not v.get('refused')and not v.get('reallocated')and not v.get('source_hold')and not v.get('claimed_elsewhere')and not claimed_input(v['n'],v.get('input_sha256',''),lines)]
   ready.sort(key=lambda v:(priority(v),v.get('order',0)))
   for slot in(1,2,3):atomic(W/f'queue{slot}.json',ready)
   call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
   state('QUEUE '+ident+' changed legal-baseline acceptor from same bar start; old logged masked movement '+str(2.6620782826114464e-5 if n==539 else 2.4105999330004124e-7)+'; source rechecked,900s and certified-input fq, cap2 counts; common17:45Z')
 fine2=done.get('ctlentry2c',{});fine907=done.get('ctlentry907c',{})
 fine_green=all(d.get('quench_from_certified')and d.get('program')=='invent_barentry30c.py'and d.get('clearance',0)>=2.2e-11 for d in(fine2,fine907))and 1.99<(fine2.get('new',99)+1)*math.sqrt(2)<2.01 and(fine907.get('new',99)+1)*math.sqrt(907)<30.6183
 if fine_green and not(W/'FINE_ENTRY_GREEN').exists():
  atomic(W/'FINE_ENTRY_GREEN',dict(pair=fine2,packing=fine907));state('CONTROL GREEN finer above-bar step1e-8 pair and deep907 both completed certified-input fq; padding6.1e-9 still refused')
 keep2=done.get('ctlretain2',{});keep907=done.get('ctlretain907',{})
 keep_green=all(d.get('quench_from_certified')and d.get('program')=='invent_barretain30.py'and d.get('clearance',0)>=2.2e-11 for d in(keep2,keep907))and 1.99<(keep2.get('new',99)+1)*math.sqrt(2)<2.01 and(keep907.get('new',99)+1)*math.sqrt(907)<30.6183
 if keep_green and not(W/'RETAIN_GREEN').exists():
  atomic(W/'RETAIN_GREEN',dict(pair=keep2,packing=keep907));state('CONTROL GREEN separate retention pair and deep907 completed certified-input fq; coarse search state preserved')
 bounded2=done.get('ctlretainlimit2',{});bounded907=done.get('ctlretainlimit907',{})
 bounded_green=all(d.get('quench_from_certified')and d.get('program')=='invent_barretain_budget30.py'and d.get('clearance',0)>=2.2e-11 for d in(bounded2,bounded907))and 1.99<(bounded2.get('new',99)+1)*math.sqrt(2)<2.01 and(bounded907.get('new',99)+1)*math.sqrt(907)<30.6183
 if bounded_green and not(W/'RETAIN_BUDGET_GREEN').exists():
  atomic(W/'RETAIN_BUDGET_GREEN',dict(pair=bounded2,packing=bounded907));state('CONTROL GREEN bounded separate retention pair and deep907 completed certified-input fq; per-try LP/fq budget90s')
 # Preserve strict fresh priority while draining saved starts on quiet slots.
 if (W/'admission-paused').exists()or globals().get('COLLECT_ONLY')or time.time()>float((W/'search-deadline').read_text()):return
 for n,(j,d,p)in best.items():peer[n]=min(peer[n],d['new'])
 audited=load(W/'audit-ready.json',[])
 if audited:
  atomic(W/'saved-pending.json',load(W/'saved-pending.json',[])+audited);(W/'saved-loaded').unlink(missing_ok=True)
  (W/'audit-ready.json').replace(W/'audit-adopted.json');state('ADOPT independent source-audited saved inputs '+str([v['id']for v in audited]))
 seen=set(load(W/'seen.json',[]));seen.update(load(W/'historical-fingerprints.json',[]));filecache=load(W/'filecache.json',{})
 version=SOURCE_GENERATION+':'+hashlib.sha256((R/'quench_walk.py').read_bytes()).hexdigest()
 if load(W/'source-version.json','')!=version:
  filecache={};source_backoff={};atomic(W/'source-backoff.json',source_backoff);atomic(W/'source-version.json',version)
 candidates=[]
 completed_hashes=set(load(W/'completed-hashes.json',[]))
 if not(W/'saved-loaded').exists():
  pending=load(W/'saved-pending.json',[]);remaining=pending[1:];pending=pending[:1];drops=[]
  for j in pending:
   p=pathlib.Path(j['start']) if pathlib.Path(j['start']).is_absolute() else S/'take-invent-r24/work'/j['start']
   if not p.exists():drops.append(dict(id=j['id'],reason='snapshot missing'));continue
   n,L,fp,b=shape(p)
   if (('walk:'+fp) if j.get('method')=='walk' else fp) in seen or (j.get('method')!='walk' and hashlib.sha256(b).hexdigest()in completed_hashes):drops.append(dict(id=j['id'],reason='exact completed input'));continue
   proof=A.audit(p,n,j['source'],j['licence'])
   if not proof['ok']:drops.append(dict(id=j['id'],n=n,reason=proof['reason']));continue
   if L>(peer[n]+1)*math.sqrt(n)+.015:drops.append(dict(id=j['id'],n=n,reason='above side margin',side=L,bar=(peer[n]+1)*math.sqrt(n)));continue
   
   if j.get('method')=='walk':
    from seam_boxes28 import box
    plan=box(p,n)
    if not plan:continue
    proof['options']=['--cbox',plan['cbox'],'--walk','0.000001','--plateau-stop','0']
    fp='walk:'+fp
   candidates.append((-.7 if j.get('method')=='walk' else 2,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'walk' if j.get('method')=='walk' else 'saved',j['fq'],j['seconds'],j['seed'],j['id']))
  if drops:
   with (W/'saved-drops.jsonl').open('a')as h:
    for drop in drops:h.write(json.dumps(dict(time=now(),**drop))+'\n')
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
 source_backoff=load(W/'source-backoff.json',{})
 def delayed(path,data):
  old=source_backoff.get(str(path),{})
  return old.get('sha256')==hashlib.sha256(data).hexdigest()and old.get('until',0)>time.time()
 for table in sorted(S.glob('take-*-r30/take.tsv'),key=lambda p:p.stat().st_mtime_ns,reverse=True):
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
   if claimed_input(n,hashlib.sha256(b).hexdigest(),lines):filecache[str(p)]=token;continue
   if delayed(p,b):continue
   intake_count+=1
   proof=A.audit(p,n,row['source'],row['licence'],record=str(table))
   if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if not proof['ok']:
    with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token;continue
   candidates.append((-.8 if lane in ('readers','family','k123','rebuild','gap')else -.5,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',lane=='forensics',900 if lane=='forensics' else (420 if lane=='k123' or 'k123_join' in row['source'][:1600] else 180),123,''));filecache[str(p)]=token
 # Handoff paths may precede a producer's public take publication.
 for line in lines:
  if intake_count>=1:break
  if 'invent ->' in line:continue
  for ref in re.findall(r'$SCRATCH/bounties-squares/take-[a-z0-9-]+-r30/[^\s,;]+\.csv',line):
   p=pathlib.Path(ref)
   if not p.exists() or '/near/' in ref or re.fullmatch(r'\d+\.csv',p.name) and p.parent.name.startswith('take-'):continue
   token=str(p.stat().st_mtime_ns)
   if filecache.get(str(p))==token:continue
   try:
    n,L,fp,b=shape(p)
    if n not in peer or fp in seen or L>(peer[n]+1)*math.sqrt(n)+.015:continue
    src,lic,record=A.metadata(p,n)
    if not src and 'licence=' in line:
     src='exact public handoff '+line;lic=line.split('licence=',1)[1].split(', /Volumes/',1)[0]
    if intake_count>=1:break
    if claimed_input(n,hashlib.sha256(b).hexdigest(),lines):filecache[str(p)]=token;continue
    if delayed(p,b):continue
    intake_count+=1
    proof=A.audit(p,n,src,lic,record=record)
    if proof['ok']:
     candidates.append((-.9,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',False,420 if 'k123' in src else 180,123,''))
    else:
     with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token
   except Exception:continue
 # New near geometry receives a single run. Repeated old geometry stays in history.
 def near_order(path):
  try:
   n,L,fp,data=shape(path);delta=L-(peer[n]+1)*math.sqrt(n)
   return (0 if '/take-forensics-r30/'in str(path)else 1,0 if delta<=1e-4 else 1 if delta<=.002 else 2,delta,-path.stat().st_mtime_ns)
  except(Exception):return (9,9,0,0)
 for p in sorted(S.glob('take-*-r30/near/**/*.csv'),key=near_order):
  if intake_count>=2:break
  lane=p.parts[len(S.parts)][5:-4]
  if lane not in TRACK:continue
  token=hashlib.sha256(p.read_bytes()+b'|'.join(q.read_bytes()for q in (p.with_suffix('.json'),pathlib.Path(str(p)+'.json'),p.parent/'near.tsv')if q.exists())).hexdigest()
  if filecache.get(str(p))==token:continue
  try:
   n,L,fp,b=shape(p)
   if n not in peer or fp in seen or abs(L-(peer[n]+1)*math.sqrt(n))>.015:filecache[str(p)]=token;continue
   if claimed_input(n,hashlib.sha256(b).hexdigest(),lines):filecache[str(p)]=token;continue
   if delayed(p,b):continue
   intake_count+=1
   proof=A.audit(p,n)
   if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if not proof['ok']:
    with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token;continue
   fq=lane=='forensics';candidates.append((-.6 if lane in FRESH_BUILD else -.3,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'near',fq,900 if fq else (420 if lane=='k123' or 'k123_join' in proof.get('source','')[:1600]else 180),123,''));filecache[str(p)]=token
  except Exception:continue
 # Follow a useful end while its completed step gains at least1e-9 of side.
 for j,d,p in eligible:
  if j['kind']=='control'or 'leg:'+j['id']in seen:continue
  n=j['n'];L=(d['new']+1)*math.sqrt(n);move=j['side']-L
  if move<1e-9 or L-(peer[n]+1)*math.sqrt(n)>max(2e-5,move):continue
  _,_,fp,b=shape(p);proof=dict(ok=True,proof=j['ancestry'],inherited_evidence=j.get('evidence'),inherited_parent=j['id'])
  candidates.append((-1 if move>1e-5 else -.1,-move,p,n,L,'leg:'+j['id'],b,proof,'leg',j['fq'],420,172,''))
 claims=[l for l in lines if 'backlog ->'in l and ('CLAIM'in l.upper()or 'claim'in l)]
 for rank,delta,p,n,L,fp,b,proof,kind,fq,seconds,seed,oldid in sorted(candidates,key=lambda c:c[:2]):
  if fp in seen or (kind!='walk' and hashlib.sha256(b).hexdigest()in completed_hashes):continue
  if claimed_input(n,hashlib.sha256(b).hexdigest(),lines):
   state(f'SKIP exact n={n} sha='+hashlib.sha256(b).hexdigest()[:12]+', claimed by backlog');continue
  if kind=='saved'and any(oldid in l or str(p)in l for l in claims):state(f'SKIP saved {oldid}, claimed by backlog');continue
  ident=f'{kind[0]}{time.strftime("%H%M%S",time.gmtime())}x{n}x{len(jobs)}'
  start='starts/'+ident+'.csv';(W/start).write_bytes(b)
  ap=proof['proof']
  if kind=='leg'and proof.get('inherited_parent'):
   from extend30 import extend
   parent=next(v for v in jobs if v['id']==proof['inherited_parent'])
   evidence=extend(parent,p,n,ap);ap=evidence.get('ancestry',ap)
  else:evidence=G.freeze(p,n,ap)
  if hashlib.sha256(p.read_bytes()).hexdigest()!=hashlib.sha256(b).hexdigest():
   state('DEFER start changed during full source audit '+str(p));continue
  if not evidence['clean']:
   source_backoff[str(p)]=dict(sha256=hashlib.sha256(b).hexdigest(),until=time.time()+300,hits=evidence.get('hits'));atomic(W/'source-backoff.json',source_backoff)
   state('REFUSE frozen evidence '+str(p)+' '+str(evidence.get('hits'))[:600]);continue
  jobs.append(dict(id=ident,n=n,start=start,program='invent_barentry30b.py'if kind in('fresh','near','leg')and(W/'BAR_ENTRY_GREEN').exists()else'invent_bar30.py'if kind in('fresh','near')and(W/'BAR_CONTROL_GREEN').exists()else'lane/invent_rest.py',seconds=max(seconds,900)if kind in('fresh','near')else seconds,seed=seed,kind=kind,fq=fq,bar=(peer[n]+1)*math.sqrt(n),side=L,ancestry=ap,priority=rank,order=delta,input_sha256=hashlib.sha256(b).hexdigest(),old_id=oldid,evidence=evidence['path'],evidence_sha256=evidence['sha256'],options=proof.get('options',[]),end_walk_parent=proof.get('end_walk_parent')))
  seen.add(fp)
  # Checkpoint an admitted job before the next source walk can delay the queue.
  atomic(W/'jobs.json',jobs);atomic(W/'seen.json',sorted(seen))
  active=[v for v in jobs if v['id']not in locks and not v.get('refused')and not v.get('claimed_elsewhere')and not v.get('reallocated')and not v.get('source_hold')and not claimed_input(v['n'],v.get('input_sha256',''),lines)and not(v.get('old_id')and any(v['old_id']in l for l in claims))]
  active.sort(key=lambda v:(priority(v),v.get('order',0)))
  call(['rsync','-a',str(W/start),REM+'starts/'])
  for slot in (1,2,3):atomic(W/f'queue{slot}.json',active)
  call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
  state(f'QUEUE {ident} n={n} {kind} delta={delta:+.8g} from {p}; source proof {ap}; boxE deadline17:45Z')
  if kind in('fresh','near'):handoff(f'CLAIM first900s {kind} n={n}, inputsha256={hashlib.sha256(b).hexdigest()}, pinned start {W/start}; queued {ident}')
  if kind=='saved':handoff(f'CLAIM saved invent-r24 {oldid}; immutable input {p}, queued {ident}')
 # Polished starts can stall above fq's floor under the plain squeeze (invent.md 15.4).
 # Try the documented per-try fq repair once on an already admitted exact input.
 repair_marks=set(load(W/'repair-fq-seen.json',[]));new_repairs=[]
 prior_fq={v[0]for v in load(S/'take-invent-r27/work/completed-inputs.json',[])if v[2]}
 for parent in list(jobs):
  if len(repair_marks)>=12:break
  if parent['kind']not in('fresh','near')or parent.get('fq')or parent.get('refused')or parent.get('source_hold'):continue
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
  state('QUEUE changed repair '+ident+' n='+str(job['n'])+' per-try fq after squeeze, exact input '+digest+'; prior plain-squeeze parent '+parent['id']+'; common17:45Z')
 jobs.extend(new_repairs);atomic(W/'repair-fq-seen.json',sorted(repair_marks))
 # Certify a competitive admitted input directly, even when its search returned no raw find.
 rescued=set(load(W/'rescue-seen.json',[]));rescues=[]
 for parent in list(jobs):
  if len(rescued)>=24:break
  if parent['kind']in('control','rescue')or parent.get('seconds')==0 or parent.get('refused')or not parent.get('evidence'):continue
  n=parent['n'];digest=parent.get('input_sha256','');floor=min(bar[n],peer[n],best[n][1]['new']if n in best else 99)
  if not digest or digest in rescued or parent['side']/math.sqrt(n)-1>=floor-2e-10:continue
  if claimed_input(n,digest,lines):continue
  original=W/parent['start']
  if hashlib.sha256(original.read_bytes()).hexdigest()!=digest:raise RuntimeError('changed rescue input')
  if not G.check(parent,original)['clean']:continue
  ident='z'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(rescues));start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
  rescues.append(dict(parent,id=ident,start=start,kind='rescue',seconds=0,fq=False,options=[],seed=0,priority=-2.5,order=parent['side']-(peer[n]+1)*math.sqrt(n),rescue_parent=parent['id']))
  rescued.add(digest);state('QUEUE finish-only source-cleared competitive input '+ident+' from '+parent['id']+'; exact input '+digest+'; common17:45Z')
 jobs.extend(rescues);atomic(W/'rescue-seen.json',sorted(rescued))
 # A harvested join can hide the current producer name behind a compact source reference.
 # A bounded search can save a winning raw file before its final try times out.
 # Finish that file with the already controlled zero-search certificate/quench path.
 salvaged=set(load(W/'salvaged.json',[]));salvages=[]
 for parent in jobs:
  if parent['kind']in('control','salvage')or parent['id']in salvaged or parent['id']in deferred:continue
  receipt=done.get(parent['id'],{})
  if not receipt.get('error')or 'timed out'not in receipt['error']or parent.get('source_hold')or parent.get('refused'):continue
  raw=sorted((out/parent['id']/'raw').glob('*.csv'),key=lambda p:int(p.stem.split('-')[-1]))
  if not raw:continue
  path=raw[-1];n,L,fp,data=shape(path);floor=min(bar[n],peer[n]);digest=hashlib.sha256(data).hexdigest()
  if L/math.sqrt(n)-1>=floor-1e-10:continue
  if claimed_input(n,digest,lines)or not G.check(parent,path)['clean']:continue
  evidence=G.freeze(path,n,parent['ancestry'])
  if not evidence['clean']:continue
  ident='v'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(salvages));start='starts/'+ident+'.csv';(W/start).write_bytes(data)
  salvages.append(dict(id=ident,n=n,start=start,kind='salvage',seconds=0,seed=0,fq=False,priority=-3.2,options=[],bar=(peer[n]+1)*math.sqrt(n),side=L,order=L-(peer[n]+1)*math.sqrt(n),input_sha256=digest,ancestry=parent['ancestry'],evidence=evidence['path'],evidence_sha256=evidence['sha256'],salvage_parent=parent['id']))
  salvaged.add(parent['id']);state('QUEUE saved winning raw after bounded timeout '+ident+' from '+parent['id']+'; certify then fq from certified input, no repeated numerical search; common17:45Z')
 jobs.extend(salvages);atomic(W/'salvaged.json',sorted(salvaged))
 extended=set(load(W/'joinlong-seen.json',[]));longjoins=[]
 for parent in jobs:
  if len(extended)>=2:break
  if parent['kind']!='fresh'or parent.get('refused')or parent['seconds']>=420:continue
  receipt=done.get(parent['id'],{})
  if receipt.get('raw')!=0 or receipt.get('error'):continue
  digest=parent.get('input_sha256','');n=parent['n']
  proof=load(pathlib.Path(parent.get('ancestry','')), {})if parent.get('ancestry')else{}
  if not any('k123'in v.get('source','').lower()for v in proof.get('nodes',{}).values()):continue
  if not digest or digest in extended or claimed_input(n,digest,lines):continue
  if parent['side']-(peer[n]+1)*math.sqrt(n)>1e-4:continue
  original=W/parent['start']
  if not G.check(parent,original)['clean']:continue
  ident='j'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(longjoins));start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
  longjoins.append(dict(parent,id=ident,start=start,kind='joinlong',seconds=420,priority=-2.2,order=parent['side']-(peer[n]+1)*math.sqrt(n),joinlong_parent=parent['id']))
  extended.add(digest);state('QUEUE join-duration correction '+ident+' 180->420s, current join hidden by harvest wrapper; historical join first move337.7s, exact input '+digest+'; common17:45Z')
 jobs.extend(longjoins);atomic(W/'joinlong-seen.json',sorted(extended))
 # A rigid domain must reproduce the numerical 907 control before production.
 domain=done.get('ctldomain907',{})
 domain_green=domain.get('quench_from_certified')and domain.get('program')=='invent_domain29.py'and(domain.get('new',99)+1)*math.sqrt(907)<30.6195806 and domain.get('clearance',0)>=2.2e-11
 if domain and not(W/'DOMAIN_CONTROL_RESULT').exists():atomic(W/'DOMAIN_CONTROL_RESULT',dict(green=bool(domain_green),result=domain));state('CONTROL rigid-domain907 green='+str(bool(domain_green)))
 domains=set(load(W/'domain-seen.json',[]));more=[]
 if False and domain_green:
  for parent in sorted(jobs,key=lambda j:j.get('order',0)):
   if len(domains)>=8:break
   if parent['kind']not in('fresh','near','saved')or parent.get('refused')or not parent.get('evidence'):continue
   digest=parent.get('input_sha256','');n=parent['n']
   if not digest or digest in domains or parent['side']-(peer[n]+1)*math.sqrt(n)>.002:continue
   if claimed_input(n,digest,lines):continue
   original=W/parent['start']
   if not G.check(parent,original)['clean']:continue
   ident='d'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(more));start='starts/'+ident+'.csv';shutil.copyfile(original,W/start)
   more.append(dict(parent,id=ident,start=start,kind='domain',program='invent_domain29.py',seconds=300,seed=2991,fq=False,priority=3,options=['--plateau-stop','0'],order=parent['side']-(peer[n]+1)*math.sqrt(n),domain_parent=parent['id']))
   domains.add(digest);state('QUEUE rigid-domain '+ident+' changed internal-contact-preserving motion; source pins inherited from '+parent['id']+'; common17:45Z')
 jobs.extend(more);atomic(W/'domain-seen.json',sorted(domains))
 # Combine the measured tight-walk acceptor with contact-preserving rigid motion.
 dw=done.get('ctldomainwalk907',{});dwfile=out/'ctldomainwalk907/final/907.csv'
 dwgreen=dw.get('quench_from_certified')and dw.get('program')=='invent_domain29.py'and(dw.get('new',99)+1)*math.sqrt(907)<30.6195806 and dw.get('clearance',0)>=2.2e-11 and dwfile.is_file()and hashlib.sha256(dwfile.read_bytes()).hexdigest()==dw.get('sha256')
 if dw and not(W/'DOMAINWALK_CONTROL_RESULT').exists():atomic(W/'DOMAINWALK_CONTROL_RESULT',dict(green=bool(dwgreen),result=dw));state('CONTROL rigid-domain tight-walk907 green='+str(bool(dwgreen)))
 dwmarks=set(load(W/'domainwalk-seen.json',[]));dwm=[];dwdeferred=set(load(W/'domainwalk-deferred.json',[]))
 if False and dwgreen:
  for parent,receipt,path in eligible:
   n=parent['n']
   if parent['kind']!='leg'or n in dwmarks or n in dwdeferred:continue
   L=(receipt['new']+1)*math.sqrt(n)
   if parent['side']-L<1e-8 or receipt['new']>=bar[n]-1e-10:continue
   victims=[j for j in jobs if j['kind']=='domainwalk'and j['id']not in locks and j['id']not in done and not j.get('reallocated')and j['side']/math.sqrt(j['n'])-1>=bar[j['n']]-1e-10]
   if len(dwmarks)>=6 and victims:
    victim=max(victims,key=lambda j:j['side']-(bar[j['n']]+1)*math.sqrt(j['n']));victim['reallocated']=True;dwmarks.discard(victim['n']);dwdeferred.add(victim['n'])
    state('REALLOCATE unstarted domainwalk '+victim['id']+' to fresh winning moved leg n='+str(n)+'; same six-count budget, no numerical child interrupted')
 if False and dwgreen:
  for parent,receipt,path in sorted(eligible,key=lambda v:v[1]['new']-peer[v[0]['n']]):
   if len(dwmarks)>=6:break
   n=parent['n']
   if n in dwmarks or n in dwdeferred or parent['kind']in('control','domainwalk')or parent.get('refused'):continue
   if parent['kind']=='leg'and receipt['new']>=bar[n]-1e-10:continue
   L=(receipt['new']+1)*math.sqrt(n)
   if parent['side']-L<1e-8 or L-(peer[n]+1)*math.sqrt(n)>.002:continue
   if claimed_input(n,receipt['sha256'],lines):continue
   nn,L,fp,data=shape(path)
   evidence=G.freeze(path,n,parent['ancestry'])
   if not evidence['clean']:continue
   ident='u'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(dwm));start='starts/'+ident+'.csv';(W/start).write_bytes(data)
   dwm.append(dict(id=ident,n=n,start=start,kind='domainwalk',program='invent_domain29.py',seconds=420,seed=2971,fq=False,priority=-2.5 if parent['kind']=='leg'else -1.6,options=['--walk','0.000001','--plateau-stop','0'],bar=(peer[n]+1)*math.sqrt(n),side=L,order=L-(peer[n]+1)*math.sqrt(n),input_sha256=hashlib.sha256(data).hexdigest(),ancestry=parent['ancestry'],evidence=evidence['path'],evidence_sha256=evidence['sha256'],domainwalk_parent=parent['id']))
   dwmarks.add(n);state('QUEUE rigid-domain tight walk '+ident+' from moved certified end '+parent['id']+'; changed acceptor1e-6, one end per count, cap6; common17:45Z')
 jobs.extend(dwm);atomic(W/'domainwalk-seen.json',sorted(dwmarks));atomic(W/'domainwalk-deferred.json',sorted(dwdeferred))
 # The small coherent patches mostly returned to the starting basin. Enlarge
 # the coupled region while reducing angular noise; retain the tight acceptor.
 large=done.get('ctllargedomain907',{});largefile=out/'ctllargedomain907/final/907.csv'
 largegreen=large.get('quench_from_certified')and large.get('program')=='invent_domain29.py'and(large.get('new',99)+1)*math.sqrt(907)<30.6195806 and large.get('clearance',0)>=2.2e-11 and largefile.is_file()and hashlib.sha256(largefile.read_bytes()).hexdigest()==large.get('sha256')
 if large and not(W/'LARGE_CONTROL_RESULT').exists():atomic(W/'LARGE_CONTROL_RESULT',dict(green=bool(largegreen),result=large));state('CONTROL large-domain tight-walk907 green='+str(bool(largegreen)))
 lgmarks=set(load(W/'largedomain-seen.json',[]));lgm=[]
 if False and largegreen:
  for parent,receipt,path in sorted(eligible,key=lambda v:v[1]['new']-peer[v[0]['n']]):
   if len(lgmarks)>=4:break
   n=parent['n'];L=(receipt['new']+1)*math.sqrt(n)
   if n in lgmarks or parent['kind']in('control','largedomain')or parent.get('source_hold')or parent.get('refused'):continue
   if parent['side']-L<1e-8 or L-(peer[n]+1)*math.sqrt(n)>.002:continue
   if claimed_input(n,receipt['sha256'],lines):continue
   if not G.check(parent,path)['clean']:continue
   nn,L,fp,data=shape(path);evidence=G.freeze(path,n,parent['ancestry'])
   if not evidence['clean']:continue
   ident='g'+time.strftime('%H%M%S',time.gmtime())+'x'+str(n)+'x'+str(len(jobs)+len(lgm));start='starts/'+ident+'.csv';(W/start).write_bytes(data)
   lgm.append(dict(id=ident,n=n,start=start,kind='largedomain',program='invent_domain29.py',seconds=420,seed=2953,fq=False,priority=-1.7,options=['--walk','0.000001','--plateau-stop','0','--rmax','8','--tfac','0.15','--sigs','0.006,0.012,0.02','--apart','0.08'],bar=(peer[n]+1)*math.sqrt(n),side=L,order=L-(peer[n]+1)*math.sqrt(n),input_sha256=hashlib.sha256(data).hexdigest(),ancestry=parent['ancestry'],evidence=evidence['path'],evidence_sha256=evidence['sha256'],largedomain_parent=parent['id']))
   lgmarks.add(n);state('QUEUE large-domain tight walk '+ident+' from '+parent['id']+'; changed patch radius8 and angular noise0.15, cap4 source-valid counts; common17:45Z')
 jobs.extend(lgm);atomic(W/'largedomain-seen.json',sorted(lgmarks))
 # Whole-packing rotation tests a remaining explanation for the owned808 gap.
 rg=done.get('ctlrigid2',{});rgraw=out/'ctlrigid2/raw/2-rigid-1.csv'
 rgreen=rg.get('quench_from_certified')and rg.get('program')=='globalfit29.py'and rg.get('clearance',0)>=2.2e-11 and rgraw.exists()and shape(rgraw)[1]<2.001
 if rg and not(W/'RIGID_CONTROL_RESULT').exists():atomic(W/'RIGID_CONTROL_RESULT',dict(green=bool(rgreen),result=rg));state('CONTROL whole-packing rigid rotation green='+str(bool(rgreen)))
 if False and rgreen and not(W/'rigidfit-queued.json').exists():
  for parent,receipt,path in eligible:
   if parent['id']!='v102514x808xown':continue
   if not G.check(parent,path)['clean']:continue
   n,L,fp,data=shape(path);ev=G.freeze(path,n,parent['ancestry'])
   if not ev['clean']:continue
   ident='r'+time.strftime('%H%M%S',time.gmtime())+'x808xfit';start='starts/'+ident+'.csv';(W/start).write_bytes(data)
   item=dict(id=ident,n=n,start=start,kind='rigidfit',program='globalfit29.py',seconds=10,seed=0,fq=False,priority=-3.1,options=[],bar=(peer[n]+1)*math.sqrt(n),side=L,order=L-(peer[n]+1)*math.sqrt(n),input_sha256=hashlib.sha256(data).hexdigest(),ancestry=parent['ancestry'],evidence=ev['path'],evidence_sha256=ev['sha256'],rigidfit_parent=parent['id'])
   jobs.append(item);atomic(W/'rigidfit-queued.json',item);state('QUEUE one whole-packing rotation '+ident+' from actual owned808 end. All internal geometry fixed; changed transformation, one test only; common17:45Z');break
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
 pending=[j for j in jobs if j['id']not in locks and not j.get('refused') and not j.get('claimed_elsewhere')and not j.get('reallocated')and not j.get('source_hold')]
 for j in pending:
  if j['kind']!='control':rebar(j,(peer[j['n']]+1)*math.sqrt(j['n']))
  if j['kind']in('fresh','near'):j['seconds']=max(j['seconds'],900)
  if j['kind']in('fresh','near')and j.get('ancestry'):
   proof=load(pathlib.Path(j['ancestry']),{});node=proof.get('nodes',{}).get(proof.get('root'),{})
   if any('k123'in v.get('source','').lower()for v in proof.get('nodes',{}).values()):j['seconds']=max(j['seconds'],420)
 pending=[j for j in pending if not j.get('outside_margin')]
 started_counts={j['n']for j in jobs if j['id']in active_locks and j['kind']!='control'}

 pending.sort(key=lambda j:(priority(j),j.get('order',0),j['id']))
 fresh=[j for j in pending if j['kind']in ('fresh','near','control')];rest=[j for j in pending if j not in fresh]
 old_kind={j['id']:j['kind']for j in load(W/'saved-pending.json',[])}
 for j in jobs:
  if j.get('old_id'):j['original_kind']=old_kind.get(j['old_id'])
 atomic(W/'jobs.json',jobs);atomic(W/'seen.json',sorted(seen));atomic(W/'filecache.json',filecache)
 for slot in (1,2,3):atomic(W/f'queue{slot}.json',pending)
 call(['rsync','-a',str(W/'starts'),REM]);call(['rsync','-a',str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
 print(now(),'done',len(done),'jobs',len(jobs),'retained',len(rs),'gain',sum(r['gain']for r in rs),'control',green,flush=True)

if __name__=='__main__':
 while time.time()<float((W/'deadline').read_text())+480 and not(W/'STOP').exists():
  try:turn()
  except Exception:traceback.print_exc();state('CONTROLLER ERROR work/controller.log')
  if '--once'in sys.argv:break
  time.sleep(35)
