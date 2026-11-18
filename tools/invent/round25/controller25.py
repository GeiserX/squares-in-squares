"""Feed three remote slots from fresh geometry and certified immutable snapshots."""
import csv,hashlib,io,json,math,os,pathlib,re,shutil,subprocess,sys,time,traceback
import numpy as np
import faulthandler
# stack sampling is manual
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;R=pathlib.Path('.')
sys.path.insert(0,str(W));import ancestry25 as A
from invent_shape22 import fingerprint
REM='boxE:scratch/squares-invent-r25/'
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
 elif job['kind']=='leg':
  job['outside_margin']=job['side']-side>max(2e-5,-job.get('order',0))
 return job

def handoff(msg):
 with open(S/'handoff-r25.log','a')as h:h.write(now()+' invent -> all: '+msg+'\n')
def base():
 details=S/'gate/cand-round23-1113b/details.csv';posted=False
 for line in (S/'handoff-r25.log').read_text().splitlines():
  if 'main -> all: BASE 'not in line:continue
  paths=re.findall(r'(?:$SCRATCH/bounties-squares/)?gate/[^\s,;]+',line)
  if paths:
   p=pathlib.Path(paths[-1]);p=p if p.is_absolute() else S/p
   if p.suffix!='.csv':p=p/'details.csv'
   if p.exists():details=p;posted=True
 bar={int(r['n']):float(r['score'])for r in csv.DictReader(open(details))}
 if not posted:
  for table in S.glob('take-*-r24/take.tsv'):
   for row in A.rows(table):
    try:n=int(row['n']);sc=float(row['new'])
    except (KeyError,ValueError):continue
    if sc>=bar[n]:continue
    proof=A.audit(table.parent/f'{n}.csv',n,row['source'],row['licence'])
    if proof['ok']:bar[n]=sc
 atomic(W/'base.json',dict(details=str(details),posted=posted,scores=bar))
 return bar

def bars():
 bar=base();peer=dict(bar)
 for table in S.glob('take-*-r25/take.tsv'):
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
 locks=set(call(['ssh','boxE','ls $SCRATCH/squares-invent-r25/locks']).split())
 rec=load(W/'recorded.json',dict(start=[],end=[]))
 for j in jobs:
  if j['id']in locks and j['id']not in rec['start']:
   state(f"START boxE {j['id']} n={j['n']} kind={j['kind']} seconds={j['seconds']} seed={j['seed']}; log work/boxE-raw/{j['id']}/run.log deadline02:45Z");rec['start'].append(j['id'])
  if j['id']in done and j['id']not in rec['end']:
   state('FINISH boxE '+j['id']+' '+json.dumps(done[j['id']],sort_keys=True));rec['end'].append(j['id'])
 atomic(W/'recorded.json',rec)
 bar,peer=bars();best={};eligible=[]
 for j in jobs:
  if not j.get('ancestry'):continue
  proof=load(pathlib.Path(j['ancestry']),{})
  known=proof.get('policy')=='strict25v6'
  node_clean=all(A.rejected(v['source'],v['licence'],terminal=not v.get('parents'))is None for v in proof.get('nodes',{}).values())
  if known and ((proof.get('ok')and node_clean)or(not proof.get('ok')and proof.get('policy')=='strict25v6')):
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
  if sc<bar[n]-1e-10 and sc<peer[n]-1e-12 and (n not in best or sc<best[n][1]['new']):best[n]=(j,d,p)
 old={int(r['n']):r for r in A.rows(T/'take.tsv')};rs=[]
 for n,(j,d,p)in sorted(best.items()):
  dest=T/f'{n}.csv';tmp=dest.with_suffix('.csv.tmp');shutil.copyfile(p,tmp);tmp.replace(dest)
  ap=load(pathlib.Path(j['ancestry']),{});src,lic=A.published(dict(proof=j['ancestry']))
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
  with open(S/'handoff-r25.log','a')as h:h.write(now()+f' invent -> quench: unfinished certified-input quench n={n}, side={L:.12f}; source proof {j["ancestry"]}; {dest}\n')
  deferred.add(j['id']);state(f'DEFER certified input n={n} to quench; {dest}')
 atomic(W/'deferred.json',sorted(deferred))
 # End files with ancestry sidecars are available to followers even above the bar.
 handed=set(load(W/'handed.json',[]))
 for j,d,p in eligible:
  if j['id']in handed:continue
  handed.add(j['id']);n=j['n'];L=(d['new']+1)*math.sqrt(n)
  if L>(bar[n]+1)*math.sqrt(n)+.015:continue
  dest=T/'near'/f'{n}-{j["id"]}.csv';tmp=dest.with_suffix('.csv.tmp');shutil.copyfile(p,tmp)
  src,lic=A.published(dict(proof=j['ancestry']));atomic(dest.with_suffix('.json'),dict(n=n,source='invent_rest.py local kick, family squeeze, floatsafe and completed certified-file fq; '+src,licence=lic,side=L,sha256=d['sha256'],receipt=str(p.parent.parent/'done.json')))
  tmp.replace(dest)
  handoff(f'finished local kick n={n}, side={L:.12f}; {dest}')
 atomic(W/'handed.json',sorted(handed))
 # Record main and addressed handoffs on every short collector pass.
 lines=(S/'handoff-r25.log').read_text().splitlines();count=load(W/'handoff-count.json',0)
 for l in lines[count:]:
  if 'main -> all:'in l or ' -> invent:'in l:state('HANDOFF READ '+l)
 atomic(W/'handoff-count.json',len(lines))
 # Control must pass in its current completed trace and complete the required quench.
 green=False
 ctl=done.get('ctl907',{})
 if ctl.get('quench_from_certified')and (ctl['new']+1)*math.sqrt(907)<30.6195806:green=True
 if green and not(W/'CONTROL_GREEN').exists():
  (W/'CONTROL_GREEN').write_text(json.dumps(ctl));call(['rsync','-a',str(W/'CONTROL_GREEN'),REM]);state('CONTROL GREEN stopped907 local kick and certified-input fq passed: '+json.dumps(ctl))
 # Preserve strict fresh priority while draining saved starts on quiet slots.
 if time.time()>float((W/'search-deadline').read_text()):return
 for n,(j,d,p)in best.items():peer[n]=min(peer[n],d['new'])
 seen=set(load(W/'seen.json',[]));filecache=load(W/'filecache.json',{})
 version=hashlib.sha256((W/'ancestry25.py').read_bytes()).hexdigest()
 if load(W/'source-version.json','')!=version:
  filecache={};atomic(W/'source-version.json',version)
 candidates=[]
 if not(W/'saved-loaded').exists():
  pending=json.load(open(S/'take-invent-r24/work/pending-final.json'));drops=[]
  for j in pending:
   p=S/'take-invent-r24/work'/j['start']
   if not p.exists():drops.append(dict(id=j['id'],reason='snapshot missing'));continue
   n,L,fp,b=shape(p);proof=A.audit(p,n,j['source'],j['licence'])
   if not proof['ok']:drops.append(dict(id=j['id'],n=n,reason=proof['reason']));continue
   if L>(peer[n]+1)*math.sqrt(n)+.015:drops.append(dict(id=j['id'],n=n,reason='above side margin',side=L,bar=(peer[n]+1)*math.sqrt(n)));continue
   candidates.append((2,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'saved',j['fq'],j['seconds'],j['seed'],j['id']))
  atomic(W/'saved-drops.json',drops);atomic(W/'saved-rerank.json',[dict(id=c[-1],n=c[3],delta=c[1],proof=c[7]['proof'])for c in sorted(candidates,key=lambda c:c[:2])]);state(f'RERANK saved starts: {len(pending)} assessed, {len(candidates)} eligible, {len(drops)} refused; work/saved-rerank.json and saved-drops.json')
  (W/'saved-loaded').touch()
 # Seed only completed historical geometry; all pending immutable starts remain eligible.
 if not(W/'history-loaded').exists():
  for rd in (21,22,23,24):
   wd=S/f'take-invent-r{rd}/work';oldjobs=load(wd/'jobs.json',[])
   complete={p.parent.name for p in (wd/'boxE-raw').glob('*/done.json')}
   for j in oldjobs:
    if j['id']not in complete or j['kind']=='control':continue
    try:seen.add(shape(wd/j['start'])[2])
    except Exception:pass
  (W/'history-loaded').touch()
 for table in S.glob('take-*-r25/take.tsv'):
  lane=table.parent.name[5:-4]
  if lane not in TRACK:continue
  for row in A.rows(table):
   try:n=int(row['n']);p=table.parent/f'{n}.csv'
   except (KeyError,ValueError):continue
   if not p.exists()or p.stat().st_mtime_ns>table.stat().st_mtime_ns:continue
   token=str(p.stat().st_mtime_ns)+hashlib.sha256((row['source']+row['licence']).encode()).hexdigest()
   if filecache.get(str(p))==token:continue
   nn,L,fp,b=shape(p)
   if nn!=n or p.stat().st_mtime_ns>table.stat().st_mtime_ns or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if fp in seen or L>(peer[n]+1)*math.sqrt(n)+.015:filecache[str(p)]=token;continue
   proof=A.audit(p,n,row['source'],row['licence'])
   if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(b).digest():continue
   if not proof['ok']:
    with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token;continue
   candidates.append((-.8 if lane in ('readers','family','k123','rebuild','gap')else -.5,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',lane=='forensics',420 if lane=='k123' or 'k123_join' in row['source'][:1600] else 180,123,''));filecache[str(p)]=token
 # Handoff paths may precede a producer's public take publication.
 for line in lines:
  if 'invent ->' in line:continue
  for ref in re.findall(r'$SCRATCH/bounties-squares/take-[a-z0-9-]+-r25/[^\s,;]+\.csv',line):
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
    proof=A.audit(p,n,src,lic)
    if proof['ok']:
     candidates.append((-.9,L-(peer[n]+1)*math.sqrt(n),p,n,L,fp,b,proof,'fresh',False,420 if 'k123' in src else 180,123,''))
    else:
     with (W/'admission.jsonl').open('a')as h:h.write(json.dumps(dict(time=now(),path=str(p),ok=False,reason=proof['reason']))+'\n')
    filecache[str(p)]=token
   except Exception:continue
 # New near geometry receives a single run. Repeated old geometry stays in history.
 for p in S.glob('take-*-r25/near/**/*.csv'):
  lane=p.parts[len(S.parts)][5:-4]
  if lane not in TRACK:continue
  token=str(p.stat().st_mtime_ns)+str([(str(q),q.stat().st_mtime_ns)for q in (p.with_suffix('.json'),pathlib.Path(str(p)+'.json'),p.parent/'near.tsv')if q.exists()])
  if filecache.get(str(p))==token:continue
  try:
   n,L,fp,b=shape(p)
   if n not in peer or fp in seen or abs(L-(peer[n]+1)*math.sqrt(n))>.015:filecache[str(p)]=token;continue
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
  _,_,fp,b=shape(p);proof=dict(ok=True,proof=j['ancestry'])
  candidates.append((-1 if move>1e-5 else -.1,-move,p,n,L,'leg:'+j['id'],b,proof,'leg',j['fq'],420,172,''))
 claims=[l for l in lines if 'backlog ->'in l and ('CLAIM'in l.upper()or 'claim'in l)]
 for rank,delta,p,n,L,fp,b,proof,kind,fq,seconds,seed,oldid in sorted(candidates,key=lambda c:c[:2]):
  if fp in seen:continue
  if kind=='saved'and any(oldid in l or str(p)in l for l in claims):state(f'SKIP saved {oldid}, claimed by backlog');continue
  ident=f'{kind[0]}{time.strftime("%H%M%S",time.gmtime())}x{n}x{len(jobs)}'
  start='starts/'+ident+'.csv';(W/start).write_bytes(b)
  ap=proof['proof']
  jobs.append(dict(id=ident,n=n,start=start,seconds=seconds,seed=seed,kind=kind,fq=fq,bar=(peer[n]+1)*math.sqrt(n),side=L,ancestry=ap,priority=rank,order=delta,input_sha256=hashlib.sha256(b).hexdigest(),old_id=oldid))
  seen.add(fp)
  state(f'QUEUE {ident} n={n} {kind} delta={delta:+.8g} from {p}; source proof {ap}; boxE deadline02:45Z')
  if kind=='saved':handoff(f'CLAIM saved invent-r24 {oldid}; immutable input {p}, queued {ident}')
 claims=[l for l in lines if 'backlog ->'in l and 'claim'in l.lower()]
 for j in jobs:
  if j['id']not in locks and j.get('old_id')and any(j['old_id']in l for l in claims):
   j['claimed_elsewhere']=True
   if not j.get('claim_recorded'):state('SKIP queue '+j['id']+' claimed by backlog');j['claim_recorded']=True
 pending=[j for j in jobs if j['id']not in locks and not j.get('refused') and not j.get('claimed_elsewhere')]
 for j in pending:
  if j['kind']!='control':rebar(j,(peer[j['n']]+1)*math.sqrt(j['n']))
  if j['kind']in('fresh','near')and j.get('ancestry'):
   proof=load(pathlib.Path(j['ancestry']),{});node=proof.get('nodes',{}).get(proof.get('root'),{})
   if 'k123_join'in node.get('source','')[:1600]:j['seconds']=420
 pending=[j for j in pending if not j.get('outside_margin')]
 started_counts={j['n']for j in jobs if j['id']in locks and j['kind']!='control'}
 pending.sort(key=lambda j:(-10 if j['kind']=='control'else (-3 if j['kind']=='leg'else(-2 if j['kind']=='fresh'else(-1 if j['kind']=='near'and j['n']not in started_counts else j.get('priority',2)))),j.get('order',0),j['id']))
 fresh=[j for j in pending if j['kind']in ('fresh','near','control')];rest=[j for j in pending if j not in fresh]
 old_kind={j['id']:j['kind']for j in load(S/'take-invent-r24/work/pending-final.json',[])}
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
  time.sleep(45)
