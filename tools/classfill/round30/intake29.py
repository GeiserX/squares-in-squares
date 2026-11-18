from common29 import *
import signal
class SourceTimeout(BaseException):pass
def source_timeout(signum,frame):raise SourceTimeout('source audit exceeded 45 seconds')
signal.signal(signal.SIGALRM,source_timeout)
import light29 as M
from light29 import key as geometry_key
assert (W/"source-controls.json").exists(), "source controls must pass before admission"
if time.time()>=SEARCH_END:raise SystemExit()
geometries=read(W/'geometry-scanned.json',{})
base,bar=writebar();seen=read(W/'intake-seen.json',{});seen={k:v for k,v in seen.items() if not ('list indices' in v.get('reason','') or 'has no attribute' in v.get('reason',''))};scanned=set(read(W/'scanned.json',[]))
# Earlier rounds' dispatched inputs stay closed: a repeated first scan of the same geometry measured nothing new.
for p in (S/'take-classfill-r24/work/inputs').glob('*-proof.json'):
 j=read(p,{})
 if j.get('input_sha256'):scanned.add(j['input_sha256'])
for p in (S/'take-classfill-r23/work').glob('x*-source-proof.json'):
 j=read(p,{})
 if j.get('input_sha256'):scanned.add(j['input_sha256'])
scanned|=set(read(S/'take-classfill-r25/work/scanned.json',[]))
scanned|=set(read(S/'take-classfill-r26/work/scanned.json',[]))
scanned|=set(read(S/'take-classfill-r27/work/scanned.json',[]))
for rnd in [25,26,27,28,29]:
 for gk,gv in read(S/f'take-classfill-r{rnd}/work/geometry-scanned.json',{}).items():geometries.setdefault(gk,gv)
visited_n={int(p.name.split('-')[0]) for p in (W/'inputs').glob('[0-9]*-x*.csv')}
generation_started=time.time()
def sha_short(q):return hashlib.sha256(q.read_bytes()).hexdigest()[:12]
# Round 26: three or more scans of one n from one producer lane this round, none retained, sends the rest of that family behind the r25 pile.
from collections import Counter
tried=Counter();won={int(r['n']) for r in rows(T/'take.tsv')}
for jp in (W/'jobs').glob('x*.json'):
 jj=read(jp,{});m=re.search(r'/(take-[a-z0-9-]+-r\d+)/(?:near/)?(\d+)[-.]',jj.get('source',''))
 if m:tried[(m[1],int(m[2]))]+=1
candidates=[];handoff=(S/'handoff-r30.log').read_text()
reopened_paths=set(read(W/'reopen-paths.json',[]))
frozen_paths={str(p) for name in ['take-harvest-r29','take-classfill-r29','take-forensics-r29','take-k123-r29'] for p in (S/name).glob('[0-9]*.csv')}
scanned|=set(read(S/'take-classfill-r29/work/scanned.json',[]))
old_pass=True
frozen_probe=(W/'FROZEN_ONCE').exists()
best_paths=read(W/'REOPEN_BEST.json',[]);best_probe=bool(best_paths)
if best_probe:note(f'START bounded reopened-source pass: {len(best_paths)} unscanned paths ranked against the live bar')
if frozen_probe:
 (W/'FROZEN_ONCE').unlink();note('START one frozen-only generation pass: fresh slots thinned, unscanned source-only refusals now eligible under RULE001903')
# Loading the job history must not spend the candidate-generation budget.
note(f'GENERATION_PREP seconds{time.time()-generation_started:.3f}; candidate phase gets its own 25 seconds')
generation_started=time.time()
for rnd in [30,29,28,27,26,25,24,23]:
 for d in sorted(S.glob(f'take-*-r{rnd}'),key=lambda d:({T.name:-1,'take-harvest-r30':0,'take-forensics-r30':1,'take-k123-r30':2,'take-rebuild-r30':3}.get(d.name,4),-(d/'near').stat().st_mtime if (d/'near').exists() else 0)):
  if time.time()-generation_started>25:break
  if 'assemble' in d.name or ('classfill' in d.name and not best_probe and d!=T):continue
  ledger={r.get('n'):r for r in rows(d/'take.tsv')};donor_tables=[q for q in [d/'work/sources-all.tsv',d/'work/sources.tsv'] if q.exists()];donors={r.get('donor'):r for q in donor_tables for r in rows(q)}
  near_tables=[q for q in [d/'near/near.tsv',d/'near.tsv',d/'work/near.tsv'] if q.exists()]
  near_rows={r.get('file') or r.get('path'):r for q in near_tables for r in rows(q)}
  source_paths=(list(d.glob('[0-9]*.csv'))+list((d/'near').glob('[0-9]*.csv'))) if rnd==30 else [Path(q) for q in frozen_paths|reopened_paths if str(Path(q)).startswith(str(d)+'/') and Path(q).exists()]
  if d.name=='take-harvest-r26':source_paths += [Path(q) for q in reopened_paths if '/work/reopened-public/' in q and Path(q).exists()]
  if best_probe:source_paths += [Path(q) for q in best_paths if str(q).startswith(str(d)+'/') and Path(q).is_file()]
  for p in sorted(set(source_paths),key=lambda p:-p.stat().st_mtime):
   if time.time()-generation_started>25:break
   key=str(p)
   if 'classfill' in d.name and str(p) not in best_paths and str(p) not in reopened_paths and not read(str(p)+'.json',{}).get('prepared_geometry_changed'):continue
   if str(p) not in reopened_paths and re.search(r'-(?:raw-(?:l?kick)|(?:l?kick)-\d+|s\d+-t\d+-raw)(?:[-.]|$)',p.name):continue
   if rnd<30 and key not in frozen_paths and key not in reopened_paths and key not in best_paths:continue
   try:
    n=int(re.match(r'\d+',p.name)[0]);stat=p.stat();sides=[q for q in [p.with_suffix('.json'),Path(str(p)+'.json')] if q.exists()]
    near_row=near_rows.get(p.name) or near_rows.get(str(p)) or {}
    parent_match=re.search(r'-(?:up|down)\d+(?:c\d+)?from(.+)\.csv$',p.name)
    donor_row=donors.get(parent_match[1],{}) if parent_match else {}
    version='source-v17-archive-receipts:'+str((stat.st_mtime_ns,stat.st_size,[(q.stat().st_mtime_ns,q.stat().st_size) for q in sides]))+hashlib.sha256(json.dumps([near_row,donor_row],sort_keys=True).encode()).hexdigest()
    if seen.get(key,{}).get('reason')=='side allowance':version+=':bar='+repr(bar[n])
    if seen.get(key,{}).get('reason')=='public terminal review incomplete or excluded':version+=':pinned-root-v4'
    if seen.get(key,{}).get('version')==version and seen.get(key,{}).get('reason')!='small n outside lane':continue
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    if any(sha[:12] in line for line in handoff.splitlines() if re.search(r'backlog ->[^:]*: claims ',line)):
     seen[key]=dict(version=version,reason='backlog claimed exact byte snapshot');continue
    if sha in scanned:seen[key]=dict(version=version,reason='already dispatched geometry');continue
    if n<5:seen[key]=dict(version=version,reason='closed small grid');continue
    packing=M.load(str(p),{n})[n];gkey=geometry_key(packing,decimals=8)+(':prequench-first' if '/work/preq-seeds/' in str(p) else '')
    if gkey in geometries:seen[key]=dict(version=version,reason='geometry already dispatched',witness=geometries[gkey]);continue
    side=M.side(packing);excess=side-(1+bar[n])*math.sqrt(n)
    if excess>0.0005:seen[key]=dict(version=version,reason='side allowance',excess=excess);continue
    j={};snapshot=[];queue_pins=[]
    for q in sides:
     if q.stat().st_size>50000000:raise ValueError('sidecar exceeds 50MB')
     pin=blob(q);queue_pins.append(pin);o=read(pin['snapshot'],{})
     if isinstance(o,dict):j.update(o)
     snapshot.append(str(q))
    lr=ledger.get(str(n),{}) if p.parent==d else near_row
    if near_row:
     j['near_ledger_record']=near_row
     for q in near_tables:snapshot.append(str(q))
    src=j.get('source_override') or j.get('source') or lr.get('source','');lic=j.get('licence_override') or j.get('licence') or lr.get('licence','')
    if not isinstance(src,str):src=json.dumps(src)
    if not src and donors:
     m=re.search(r'-(up|down)(\d+)(?:c\d+)?from(.+)\.csv$',p.name)
     if m and m[3] in donors:
      parent=donors[m[3]];j['family_parent_record']=parent;src='family shell '+m[1]+m[2]+' from '+parent['source'];lic=parent['licence'];snapshot.extend(str(q) for q in donor_tables)
    if j.get('modules'):
     src='modules.py: '+', '.join(q['id']+' <'+q['source']+'>' for q in j['modules']);lic='; '.join(sorted({q['licence'] for q in j['modules']}))
    if j.get('parts') and isinstance(j['parts'],dict):
     parts=[q for q in j['parts'].values() if isinstance(q,dict) and q.get('source')]
     if parts and all(q.get('licence') for q in parts):
      src='forensics rectangle windows '+json.dumps(j['parts']);lic='; '.join(q['licence'] for q in parts)
    a=None
    priority=(0 if rnd==30 else 5)+(0 if p.parent.name=='near' else 1)
    if rnd==30 and n not in visited_n:priority-=0.5
    # Round 26 measured: six first scans of certified r26 take rows (489, 911, 805, 580, 365, 328) tied or lost to backlog, invent and twoshort kicks
    # of the same rows, all within 1e-9. Take rows and k123 pending copies of them go after fresh near layouts; unseen r25 near counts go first among r25.
    if rnd==30 and (p.parent==d or '-pending-' in p.name):priority=3
    if rnd==25 and n not in visited_n:priority-=0.5
    if rnd==30 and j.get('parts'):priority-=0.25
    if rnd==30 and ('take-k123-r30' in str(p) or 'take-rebuild-r30' in str(p)):priority-=0.75
    # Round 26: fresh public layouts certified by harvest this round go first unless backlog claimed that exact file (midm r25: two public scans gained 6.8e-05).
    if d.name=='take-harvest-r30' and p.parent==d and not re.search(r'claims follow:take-harvest-r26-'+str(n)+'-'+sha_short(p),handoff):priority=-1
    if tried[(d.name,n)]>=3 and n not in won:priority=6
    if rnd==30:priority=-3 if p.parent.name=='near' else -2.5
    if key in reopened_paths:priority=-2
    if key in best_paths:priority=(2+best_paths.index(key)/100 if j.get('prequench') else -8+best_paths.index(key)/100)
    if rnd==30 and j.get('parts'):priority=-4
    if d.name=='take-harvest-r30' and p.parent==d:priority=-5
    if tried[(d.name,n)]>=3 and n not in won:priority=6
    if j.get('prepared_geometry_changed'):priority=-5.75
    j['queue_metadata_pins']=queue_pins
    candidates.append((priority,-stat.st_mtime,n,p,sha,src,lic,j,version,excess,a,snapshot))
   except Exception as e:seen[key]=dict(version=locals().get('version',''),reason='read error '+repr(e))
loads=[]
for host,slots in [('boxE',['A','B']),('boxD',['C'])]:
 for slot in slots:
  out=cmd(['ssh',host,'find '+REMOTE+'/queue/'+slot+' -type f \\( -name "*.json" -o -name "*.active" \\)'])
  loads.append([len(out.splitlines()),host,slot])
# Round 26: one more leg on own certified rows whose last scan moved more than 1e-5 of side (850 moved 1.4e-3 in 4 tries), at most 3 legs.
own={int(r['n']):r for r in rows(T/'take.tsv')}
for acc in sorted((W/'accepted-candidates').glob('*.json')):
 if time.time()>=SEARCH_END:break
 r=read(acc,{});n=r.get('n');f=r.get('finish',{});tagp=acc.stem.split('-',1)[1]
 if not n or not f or n not in own or abs(float(own[n]['new'])-r['score'])>1e-15:continue
 p=T/f'{n}.csv'
 if not p.exists():continue
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 if sha in scanned:continue
 if any(sha[:12] in line for line in handoff.splitlines() if re.search(r'backlog ->[^:]*: claims ',line)):
  scanned.add(sha);note(f'LEG_SKIP n{n} exact byte input already claimed by backlog');continue
 own_gkey=geometry_key(M.load(str(p),{n})[n],decimals=8)
 if own_gkey in geometries:
  scanned.add(sha);note(f'LEG_SKIP n{n} endpoint geometry already scanned, witness '+str(geometries[own_gkey]));continue
 parent=read(W/'audited'/f'{tagp}.json',{});leg=int(parent.get('leg',1))+1
 move=f.get('finish_start_side',0)-(1+r['score'])*math.sqrt(n)
 fresh_public_second=(leg==2 and '/take-harvest-r30/' in parent.get('source','') and move>1e-8)
 if (move<=1e-9 and not fresh_public_second) or leg>20 or not parent.get('accepted'):continue
 load,host,slot=min(loads)
 if load>=3:break
 tag='x'+sha[:12];copy=W/'inputs'/f'{n}-{tag}.csv';copy.parent.mkdir(exist_ok=True);shutil.copy2(p,copy)
 rec=dict(parent);rec.update(tag=tag,leg=leg,parent_tag=tagp,input=str(p),input_sha256=sha,certified_output_sha256=None,quench_receipt='finish log of '+tag,source=f'classfill sigma0.02 leg {leg} scan of own certified row {tagp} (that leg moved {move:.3g} of side); before it: '+parent['source'],time_utc=now())
 atomic(W/'audited'/f'{tag}.json',rec)
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source=str(p)+f'; leg {leg} from {tagp}; ancestry '+str(W/'audited'/f'{tagp}.json'),licence='Own sigma0.02 scan. Notices '+str(W/'audited'/f'{tagp}.json'),priority=-6,seed=int(sha[:6],16),seconds=300,wall=900,kicks='0.02,0.04')
 publish_job(job,copy,host,slot);scanned.add(sha);geometries[own_gkey]=str(copy);atomic(W/'geometry-scanned.json',geometries);atomic(W/'scanned.json',sorted(scanned))
 note(f'LEG n{n} {tag} leg{leg} from {tagp}, previous move {move:.3g} of side')
 for q in loads:
  if q[1:]==[host,slot]:q[0]+=1
for priority,mtime,n,p,sha,src,lic,j,version,excess,a,snapshot in sorted(candidates,key=lambda x:((-7+x[0]/100 if x[7].get('prequench') else x[0]),x[1])):
 if time.time()>=SEARCH_END or sha in scanned:continue
 if time.time()-generation_started>240:note('INTAKE_PAUSE dispatch phase reached 240 s; seen saved, next pass resumes');break
 choices=[q for q in loads if not j.get('prequench') or q[1]=='boxE']
 load,host,slot=min(choices)
 if load>=2:
  if j.get('prequench'):continue
  break
 from prvsim29 import check
 from share_policy29 import public_start
 measure=check(str(p),n) if public_start(str(p),src) else dict(share=0.0,excluded=False,policy='own-layout exempt')
 from share_policy29 import public_start
 if public_start(str(p),src) and measure['share']>=0.4:
  seen[str(p)]=dict(version=version,reason='prvsiyan share >=0.4',prvsiyan=measure);note(f'DROP {p}: prvsiyan share {measure["share"]}');atomic(W/'intake-seen.json',seen);continue
 note(f'AUDIT_BEGIN n{n} {p}')
 signal.alarm(45)
 try:a,refused=audit(src,lic,j,n)
 except SourceTimeout as e:a=dict(records=[],unresolved_csv=[],history={});refused=str(e)
 finally:signal.alarm(0)
 note(f'AUDIT_END n{n} refused={refused}')
 if refused:
  atomic(W/'rejected'/(sha+'.json'),dict(input=str(p),input_sha256=sha,reason=refused,source=src,licence=lic,history=a.get('history'),records=[{k:v for k,v in r.items() if k!='metadata'} for r in a.get('records',[])]))
  seen[str(p)]=dict(version=version,reason=refused,trace='t26c');note(f'DROP {p}: {refused}');atomic(W/'intake-seen.json',seen);continue
 tag='x'+sha[:12];copy=W/'inputs'/f'{n}-{tag}.csv';copy.parent.mkdir(exist_ok=True);shutil.copy2(p,copy)
 if hashlib.sha256(copy.read_bytes()).hexdigest()!=sha:
  note('DEFER mutable input changed before snapshot '+str(p));continue
 if (p.parent/'take.tsv').exists():snapshot.append(str(p.parent/'take.tsv'))
 for r in a['records']:
  if Path(r['path']).is_file():snapshot.append(r['path'])
 for donor_table in [p.parent.parent/'work/sources.tsv',p.parent.parent/'work/sources-all.tsv']:
  if donor_table.is_file():snapshot.append(str(donor_table))
 for cp in re.findall(r'$DATA/[^\s<>\";,()]+?\.csv',a['text']):
  if Path(cp).is_file():snapshot.append(cp)
 snapshot=[blob(q) for q in sorted(set(snapshot))]+j.get('queue_metadata_pins',[])
 if any(Path(q['path']).is_file() and hashlib.sha256(Path(q['path']).read_bytes()).hexdigest()!=q['sha256'] for q in j.get('queue_metadata_pins',[])):
  note('DEFER changed metadata during audit '+str(p));continue
 j['prvsiyan_share_check']=measure
 a.pop('text',None)
 a['records']=[{k:v for k,v in r.items() if k!='metadata'} for r in a['records']]
 # Store ancestry once by hash. Queue messages only carry its immutable path.
 closure=W/'ancestry'/(sha+'.json');atomic(closure,dict(n=n,input=str(p),input_sha256=sha,source=src,licence=lic,metadata=j,expanded=a,snapshots=snapshot))
 from ancestor_share29 import inspect as ancestor_check
 anc=ancestor_check(closure)
 if anc['excluded'] or anc['errors']:
  seen[str(p)]=dict(version=version,reason='pinned ancestor share exclusion or unresolved geometry',ancestor_check=anc)
  atomic(W/'intake-seen.json',seen);note('DROP ancestor guard '+str(p)+' '+json.dumps(dict(excluded=anc['excluded'],errors=anc['errors']))[:1000]);continue
 from public_review30 import review as public_review
 try:
  signal.alarm(60);public_result=public_review(closure)
 except SourceTimeout:
  public_result=dict(complete=False,reason='public review budget60s')
 finally:signal.alarm(0)
 if not public_result.get('complete'):
  seen[str(p)]=dict(version=version,reason='public terminal review incomplete or excluded',review=str(W/'public-root-reviews'/(hashlib.sha256(closure.read_bytes()).hexdigest()+'.json')));atomic(W/'intake-seen.json',seen);note('PUBLIC_PREFLIGHT_DEFER '+str(p));continue
 if time.time()>=SEARCH_END:note('DEFER admission cutoff after source audit '+str(p));break
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source=str(p)+'; immutable ancestry '+str(closure),licence='Own sigma0.02 scan. Full notices '+str(closure),priority=priority,seed=int(sha[:6],16),seconds=(900 if abs(excess)<1e-7 else 180),wall=(1200 if abs(excess)<1e-7 else 900),kicks='0.02,0.04')
 if ('take-forensics-r30/' in str(p) or str(p) in best_paths) and read(W/'bar-control-result.json',{}).get('passed'):job.update(bar_input=True,seconds=900,wall=1200)
 if j.get('prepared_geometry_changed'):job.update(prepared_follow=True,bar_input=True,seconds=900,wall=1200)
 if j.get('prequench') and read(W/'preq-control-result.json',{}).get('passed'):job.update(prequench=True,bar_input=True,seconds=300,wall=1200)
 publish_job(job,copy,host,slot);scanned.add(sha)
 geometries[geometry_key(M.load(str(copy),{n})[n],decimals=8)+(':prequench-first' if j.get('prequench') else '')]=str(copy)
 atomic(W/'geometry-scanned.json',geometries)
 atomic(W/'scanned.json',sorted(scanned))
 seen[str(p)]=dict(version=version,reason='queued',tag=tag,host=host,slot=slot,sha256=sha,excess=excess,closure=str(closure))
 atomic(W/'intake-seen.json',seen)
 note(f'FIRST_SCAN side slack0.0005 {p} n{n} excess{excess:.9g} source{closure}')
 for q in loads:
  if q[1:]==[host,slot]:q[0]+=1
atomic(W/'intake-seen.json',seen);atomic(W/'scanned.json',sorted(scanned));atomic(W/'pending-current.json',[dict(n=x[2],path=str(x[3]),sha256=x[4],priority=x[0],side_excess=x[9]) for x in candidates if x[4] not in scanned]);print('INTAKE',len(candidates),'eligible',loads,flush=True)
if best_probe and read(W/'REOPEN_BEST.json',[])==best_paths:
 left=[p for p in best_paths if p not in seen]
 if left:atomic(W/'REOPEN_BEST.json',left)
 else:(W/'REOPEN_BEST.json').unlink(missing_ok=True);note('FINISH bounded reopened-source pass; every selected path now has a recorded disposition')
