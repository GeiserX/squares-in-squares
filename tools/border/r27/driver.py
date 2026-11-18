import os,sys,time,csv,json,math,glob,hashlib,subprocess,traceback,shutil,re
from pathlib import Path
from types import SimpleNamespace as NS
S=Path('$SCRATCH/bounties-squares');T=S/'take-border-r27';W=T/'work'
import fcntl
LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)
LANE=Path('.')
sys.path.insert(0,str(LANE))
csv.field_size_limit(16*1024*1024)
import border_sweep as bs
bs.lib()
import floatsafe
END=float((W/'deadline').read_text());POLL_END=END-300
REMOTE='boxC:scratch/squares-border-r27/'
for d in ['q','final','donors','staged']: (W/d).mkdir(exist_ok=True)
(W/'empty.csv').write_text('id,n,square_id,x,y,angle\n')
seen={}; queued=set(); staged=set(); published=set(); known=set(); manifest={};near_staged={}
for p in list((S/'take-border-r24/work/q').glob('*.start.txt'))+list((S/'take-border-r25/work/q').glob('*.start.txt'))+list((S/'take-border-r26/work/q').glob('*.start.txt')):
 rec=p.with_name(p.name.removesuffix('.start.txt')+'.k0.json')
 if rec.exists():known.add(hashlib.md5(p.read_bytes()).hexdigest())
for p in (W/'q').glob('*.start.txt'): queued.add(hashlib.md5(p.read_bytes()).hexdigest())
sys.path.insert(0,str(W));import base27 as base25
SUB,held,BASE_NOTE=base25.base()
CANON={}
base_rows=list(csv.DictReader(open(SUB)))
TEMPLATE=list(base_rows[0]); current={};L={}
def log(msg):
 s=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+msg
 print(s,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(s+'\n')
def takes():return [p for pattern in ['take-*-r27'] for p in S.glob(pattern) if p!=T and (p/'take.tsv').exists()]
def policy_floor(n,policy):
 return clean[n] if n in sp.RELAXED and policy['status']=='none' else float(current[n]['new'])
def qualifies(n,score,policy):
 return sp.eligible(n,score,policy,held,current,clean)
def refresh():
 global current,L,clean,SUB,held,BASE_NOTE
 note0=BASE_NOTE
 SUB,held,BASE_NOTE=base25.base()
 if BASE_NOTE!=note0:log('BASE changed: '+BASE_NOTE)
 current={n:{'new':str(sc),'source':'base bar: '+BASE_NOTE} for n,sc in held.items()}
 clean={n:sp.OLD22[n] for n in sp.RELAXED}
 for t in takes():
  try:
   for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t'):
    n=int(r['n']);new=float(r['new'])
    if new<float(current[n]['new']):current[n]=dict(r,take=str(t/'take.tsv'))
    if n in clean and new<clean[n] and sp.classify(r.get('source',''),r.get('licence',''))['status']=='none':clean[n]=new
  except (OSError,ValueError,KeyError):log('transient take read '+str(t))
 L={n:(float(r['new'])+1)*math.sqrt(n) for n,r in current.items()}
 for n in clean:L[n]=(clean[n]+1)*math.sqrt(n)
 if (T/'take.tsv').exists():
  rr=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));keep=[]
  for r in rr:
   n=int(r['n']);policy=sp.classify(r['source'],r['licence'])
   if not qualifies(n,float(r['new']),policy):
    if (T/f'{n}.csv').exists():
     dst=T/'near'/f'{n}-overtaken-{time.time_ns()}.csv';shutil.move(T/f'{n}.csv',dst)
     dst.with_suffix('.json').write_text(json.dumps({'source':r['source'],'licence':r['licence']}))
    log(f'overtaken or ineligible {n}, source group '+policy['status'])
   else:keep.append(r)
  write_take(keep)
  for r in keep:
   n=int(r['n']);policy=sp.classify(r['source'],r['licence'])
   if n not in clean or policy['status']=='none':L[n]=min(L[n],(float(r['new'])+1)*math.sqrt(n))
 with open(W/'details.csv','w') as f:
  w=csv.writer(f);w.writerow(['n','L','score']);w.writerows((n,L[n],L[n]/math.sqrt(n)-1) for n in sorted(L))
 (W/'bars.json').write_text(json.dumps(L))
def write_take(rows):
 p=T/'take.tsv.tmp'
 with open(p,'w') as f:
  w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(sorted(rows,key=lambda r:int(r['n'])))
 os.replace(p,T/'take.tsv')
def sources(initial=False):
 out=[]
 for t in [p for p in S.glob('take-*-r27') if p.is_dir() and p!=T]:
  rd=t.name.endswith('r27')
  try:rows={int(r['n']):r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
  except (OSError,ValueError,KeyError):rows={}
  for n,r in rows.items():
   p=t/f'{n}.csv'
   if p.exists() and (rd or initial):
    out.append((p,r,rd))
  if rd or initial:
   for p in t.rglob('near/*.csv'):
    if not any(q.startswith(('control','ctl-','broken')) for q in p.relative_to(t).parts):out.append((p,None,rd))
 hand=S/'handoff-r27.log'
 if hand.exists():
  for line in hand.read_text().splitlines():
   if '->' not in line:continue
   dest=line.split('->',1)[1].split(':',1)[0]
   if 'all' not in dest and 'border' not in dest:continue
   for name in re.findall(r'$SCRATCH/bounties-squares/[^\s,;]+\.csv',line):
    p=Path(name)
    if p.exists() and str(T) not in name and '/take-' in name and p.stat().st_size<1000000:
     out.append((p,None,True))
 # r27 item 2: the layouts the r26 gate refused (Samanyu lifted) and the frozen r22-r26 take and near files of
 # other lanes, after the fresh r27 files; 200 per pass so fresh files are never held up.
 import reopen
 out.extend((p,r,False) for p,r in reopen.batch(200))
 ranked=[]
 for p,r,rd in out:
  try:mtime=p.stat().st_mtime
  except OSError:continue
  ranked.append((p,r,rd,mtime))
 return [(p,r,rd) for p,r,rd,_ in sorted(ranked,key=lambda c:(0 if c[2] else 1,-c[3] if c[2] else 0))]
def make(p,r,rd):
 try:
  st=p.stat();key=(str(p),st.st_mtime_ns,st.st_size)
  if key in seen:return
  seen[key]=True
  m,s,A=bs.read_near(str(p))
  picks=[]
  # Plain corner windows are cheap closure checks on each new donor.
  for c in range(4):
   ext=sorted(bs.extents(bs.corner(A,s,c)))
   for target in range(2,m):
    side=float(ext[target-1]);mg=side-L[target]
    if mg < -1e-10*math.sqrt(target)-1e-9:
     picks.append(('rev',target,c,0,side,mg,-2))
  f=math.floor(s)
  for target in range(m+1,min(1000,m+4*f+4)+1):
   if target<=m+2*f+1:kind,side='b1',s+1
   else:kind,side='b2',s+2
   mg=side-L[target]
   if mg < -1e-10*math.sqrt(target)-1e-9:
    for v in range(4):picks.append((kind,target,0,v,side,mg,-2))
  n=m+2*math.floor(s)+1
  if n<=1000 and abs(s-round(s))>=1e-4:
   margin=s+1-L[n]
   if margin<=(.02 if (m==870 or '-r27/' in str(p)) else .012) and (m,n) not in [(868,927),(929,990)]:
    walls=[bs.walls(bs.corner(A,s,c),s) for c in range(4)]
    if m in (870,931):variants=[2];pri=-3 if m==870 else 0
    elif m==859:variants=[67];pri=1
    elif m==794:variants=[7];pri=3
    elif margin < -3e-9:variants=list(range(4));pri=-1
    else:
     v=max(range(4),key=lambda c:(min(walls[c]),max(walls[c]),walls[c][1]))
     variants=[v] if max(walls[v])>=5 else [];pri=4
    picks.extend(('b1',n,0,v,s+1,margin,pri) for v in variants)
  with open(W/'scan.tsv','a') as scan:
   scan.write(f'{time.time()}\t{m}\t{s}\t{len(picks)}\t{p}\n')
  if not picks:return
  # r27: the walk runs only for a donor with picks (boxA at load 100).
  if not audit(p,r):return
  digest=hashlib.sha256(p.read_bytes()).hexdigest()[:16]
  copy=W/'donors'/f'{m}-{digest}.csv'
  if not copy.exists():shutil.copyfile(p,copy)
  src=f'{p}' + (f', from {p.parent}/take.tsv: {r["source"]}' if r else ', '+bs.near_source(str(p),m,s,L[m]))
  lic=r.get('licence','ours') if r else bs.near_metadata(str(p)).get('licence') or 'ours (near layout of another lane)'
  if p.parent.name.endswith('-r23') and p.stem.isdigit() and m in CANON:
   src+='; results/round23-best-2026-11-13.tsv: '+CANON[m]['source']
   lic=CANON[m]['licence']
  md=metadata(p)
  if md:
   src+='; recorded ancestry '+json.dumps(md,sort_keys=True)
   lic=md.get('licence') or lic
  # Pin the complete parent tree while the original still matches its retained copy.
  sp.manifest_policy(dict(donor=m,donor_source=src,donor_licence=lic,near=str(copy)))
  cols=['kind','donor','n','corner','side','margin','dropped','variant','near','near_source','donor_licence']
  with open(W/'pick.tsv','w') as f:
   w=csv.writer(f,delimiter='\t');w.writerow(cols)
   for kind,target,c,v,side,mg,pri in picks:w.writerow([kind,m,target,c,side,mg,0,v,str(copy),src,lic])
  before={p.name for p in (W/'q').glob('*.start.txt')}
  a=NS(held=str(W/'empty.csv'),details=str(W/'details.csv'),pairs=str(W/'pick.tsv'),dir=str(W/'q'),kinds='b1,b2,rev',max=.02,min=-1e9,min_abs=3e-9,no_grid=True,per_n=0,limit=100,vfrom=0,variants=4,gaps='',edge_min=0)
  bs.cmd_starts(a)
  fresh=[]
  for start in (W/'q').glob('*.start.txt'):
   if start.name in before:continue
   md=hashlib.md5(start.read_bytes()).hexdigest()
   if md in known or md in queued:
    start.unlink();continue
   queued.add(md);fresh.append(start)
   ident=start.name.removesuffix('.start.txt')
   manrows={z['id']:z for z in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
   r0=manrows[ident]
   if r0['kind']=='rev' or float(r0['margin_before']) < -1e-8:
    _,fr,sc,e=to_rows(int(r0['n']),start)
    if fr is not None and qualifies(int(r0['n']),sc,sp.manifest_policy(r0)):
     uid=ident+'-plain-'+hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
     csvout(W/'staged'/f'{uid}.csv',fr)
     ss,AA=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
     bs.write_txt(str(W/'final'/f'{uid}.input.txt'),ss,AA)
     meta=dict(input=f'{uid}.input.txt',output=f'{uid}.output.txt',n=int(r0['n']),manifest=r0,certified_before=sc,chain={'mode':'plain '+r0['kind']+', certified directly','s_start':ss,'log':[]})
     (W/'final'/f'{uid}.job.json').write_text(json.dumps(meta))
     log(f'direct window {r0["donor"]}->{r0["n"]} score{sc:.16g} queued certified-file fq')
    if r0['kind']=='rev':continue
   job=start.with_name(ident+'.job.json')
   priority={int(row[1]):row[6] for row in picks}.get(int(start.name.split('-')[0]),4)
   fresh23='-r27/' in str(p)
   if fresh23:priority=-110 if float(r0['margin_before'])<0 else -90
   # r26: a chain whose expected end (margin minus the best give-back measured on its donor/target pair in rounds
   # 24 to 26) is more than 4e-3 above the bar is a measured dead end; it gets no job. Direct windows still run.
   tgt=int(r0['n']);mg=float(r0['built_L'])-L[tgt];expected=mg-pair_giveback(int(r0['donor']),tgt,mg)
   # r27: a measured dead-end pair (3 or more chain records, best end more than 1.5e-3 above the bar) gets no chain;
   # 48 chains of (860,919), (922,983) and (861,920) were queued from re-opened donors before this rule.
   if (int(r0['donor']),tgt) in _pairs.get('dead',set()) and mg>=0:dead_skipped.append((int(r0['donor']),tgt));continue
   if mg>=0 and expected>4e-3:
    # Explore tier (r26): a fresh pair with no record below n=800 and margin under 0.012 runs only when the
    # slots have nothing better, so each new design gets one measured chain (give-back ratio above 0.8 came in
    # 10 to 20 per cent of the n=400-700 records of rounds 24 and 25).
    if not(fresh23 and mg<.012 and tgt<800 and (int(r0['donor']),tgt) not in _pairs['v']):
     dead_skipped.append((int(r0['donor']),tgt));continue
    priority=50+1000*expected
   elif fresh23 and mg>=0:priority=-100+1000*max(0.,expected)
   job.write_text(json.dumps({'start':start.name,'priority':priority,'fresh23':fresh23,'expected':expected}))
  if dead_skipped:
   log(f'skip chains of donor {m} from {p}: expected end above 4e-3 on pairs {sorted(set(dead_skipped))} (measured give-back)');dead_skipped.clear()
  if fresh:
   log(f'queue boxC donor {m} picks {picks} from {p}; deadline 23:45Z, logs boxC worker1.log/worker2.log')
   pass # Batch transfer in sync().
 except Exception:traceback.print_exc()
def sync():
 subprocess.run(['rsync','-a',str(W/'bars.json'),REMOTE],check=True)
 subprocess.run(['rsync','-a','--ignore-existing','--include','*.start.txt','--include','*.job.json','--exclude','*',str(W/'q')+'/',REMOTE+'q/'],check=True)
 subprocess.run(['rsync','-a','--ignore-existing','--include','*.input.txt','--include','*.job.json','--exclude','*',str(W/'final')+'/',REMOTE+'final/'],check=True)
 subprocess.run(['rsync','-a','--exclude','*.claim',REMOTE+'q/',str(W/'q')+'/'],check=True)
 subprocess.run(['rsync','-a','--exclude','*.claim',REMOTE+'final/',str(W/'final')+'/'],check=True)
 # r27: prioritize.py dropped from the loop (adopted chains keep their creation priority)
def to_rows(n,txt):
 _,A=bs.read_txt(str(txt))
 rows=[{'n':str(n),'square_id':str(i),'x':repr(x),'y':repr(y),'angle':repr(math.radians(a))} for i,(x,y,a) in enumerate(A)]
 return floatsafe.work((n,rows))
def csvout(path,rows):
 with open(path,'w') as f:
  w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in rows)
def _save_published():
 tmp=W/'published.tmp';tmp.write_text(json.dumps(sorted(published)));tmp.replace(W/'published.json')
if (W/'published.json').exists():published.update(json.load(open(W/'published.json')))
def collect():
 if not (W/'q/manifest.tsv').exists():return
 manifest={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
 for p in (W/'q').glob('*.k*.json'):
  mm=re.match(r'^(.*)\.k(\d+)\.json$',p.name)
  if not mm:continue
  ident=mm[1];kk=int(mm[2])
  try:j=json.load(open(p))
  except ValueError:continue
  r=manifest.get(ident)
  if not r or not j['log']:continue
  bs.check_start(str(W/'q'),r)
  n=int(r['n']);b=W/'q'/j['best']
  record=(ident,kk,j['s_final'])
  if record in staged or not b.exists():continue
  if j['s_final']>=L[n]-math.sqrt(n)*1e-10:
   continue  # r27: only chain ends below the live bar are staged (near staging cost minutes per restart at load 100, and gave no row in r26)
   complete=(W/'q'/(ident+('.job.done' if kk==0 else f'.kick{kk}.job.done'))).exists()
   if j['s_final']>L[n]+.003 or (j['cut'] and not complete and j['round']<2 and j['s_final']>L[n]+.0005):continue
   if j['s_final']>=near_staged.get((ident,kk),1e100)-1e-4:continue
   if kk and j['s_final']>=near_staged.get((ident,0),1e100)-1e-6:continue
   near_staged[(ident,kk)]=j['s_final']
  staged.add(record)
  _,fr,sc,e=to_rows(n,b)
  if fr is None or (sc+1)*math.sqrt(n)>L[n]+.003:continue
  uid=ident+(f'-k{kk}' if kk else '')+'-'+hashlib.md5(repr(sc).encode()).hexdigest()[:8]
  csvout(W/'staged'/f'{uid}.csv',fr)
  s,A=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
  bs.write_txt(str(W/'final'/f'{uid}.input.txt'),s,A)
  meta={'input':f'{uid}.input.txt','output':f'{uid}.output.txt','n':n,'manifest':r,'certified_before':sc,'chain':j,'k':kk,'kick':(KICKS[(kk-1)%len(KICKS)] if kk else None)}
  (W/'final'/f'{uid}.job.json').write_text(json.dumps(meta))
  pass # Batch transfer in sync().
  log(f'stage {n} score {sc:.15g} for final fq from certified csv on boxC; {uid}')
 for p in (W/'final').glob('*.job.done'):
  uid=p.name.removesuffix('.job.done')
  if uid in published:continue
  done=json.load(open(p));meta=json.load(open(W/'final'/f'{uid}.job.json'))
  if done['side'] is None:log('final fq failed '+uid);published.add(uid);continue
  txt=W/'final'/done['output']
  if not txt.exists():continue
  n=meta['n']
  # r27: a job whose raw fq side and certified input are both above the live bar is closed without floatsafe and
  # without a near file (each floatsafe takes about a minute at load 120; r26 near files of this kind gave no row).
  if min(float(done['side']),(meta['certified_before']+1)*math.sqrt(n))>=L[n]-math.sqrt(n)*1e-10+1e-9:
   published.add(uid);_save_published();continue
  _,fr,sc,e=to_rows(n,txt);published.add(uid);_save_published()
  retained=False
  if fr is not None and sc>meta['certified_before']:
   fr=list(csv.DictReader(open(W/'staged'/f'{uid}.csv')))
   sc=meta['certified_before'];retained=True
   log(f'final fq {n} completed but certified input is smaller; retained input score {sc:.16g}')
  if fr is None:continue
  refresh()
  policy=sp.manifest_policy(meta['manifest'])
  if not qualifies(n,sc,policy):
   near=T/'near'/f'{n}-{uid}.csv'
   if not near.exists():
    csvout(near,fr)
    with open(near.with_suffix('.json'),'w') as f:json.dump(meta,f,indent=2)
    log(f'near {n} above best side by {(sc+1)*math.sqrt(n)-L[n]:.8g}: {near}')
    with open(S/'handoff-r27.log','a') as f:f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+f' border -> all: fresh border near {n}, above bar side by {(sc+1)*math.sqrt(n)-L[n]:.8g}, {near}\n')
   continue
  tt=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t')) if (T/'take.tsv').exists() else []
  old=next((r for r in tt if int(r['n'])==n),None)
  if old:
   op=sp.classify(old['source'],old['licence'])
   if n in sp.RELAXED and op['status']=='none' and policy['status']!='none':continue
   if not(n in sp.RELAXED and policy['status']=='none' and op['status']!='none') and float(old['new'])<=sc:continue
  # Publish the CSV only after all source checks below pass.
  r=dict(meta['manifest'])
  if not audit_manifest(r):
   log('REJECT unclean or unresolved publication '+uid);continue
  original=Path(r['donor_source'].split(', ',1)[0])
  if original.exists() and original.read_bytes()==Path(r['near']).read_bytes():
   ancestry=bs.near_metadata(str(original))
   full=metadata(original)
   if full:
    ancestry['source']=full['source'] if isinstance(full.get('source'),str) else json.dumps(full,sort_keys=True)
    if isinstance(full.get('licence'),str):ancestry['licence']=full['licence']
   if ancestry.get('source') and ancestry['source'] not in r['donor_source']:r['donor_source']+='; from '+ancestry['source']
   if ancestry.get('licence'):r['donor_licence']=ancestry['licence']
  if r['kind']=='direct':src=f're-opened layout (round 27 brief item 2), the pinned copy {r["near"]} (sha256 {r.get("start_sha256","")}) of {r["donor_source"]}; certified-file fq {uid} on boxC'
  elif r['kind']=='lp':src=f'contact LP reclose (methods_lp.py --iters 40 on boxC, lpfeed.py) of the pinned copy {r["near"]} (sha256 {r.get("start_sha256","")}) of {r["donor_source"]}; certified-file fq {uid} on boxC'
  else:src=f'fq quench of {r["kind"]} on n={r["donor"]}, corner {bs.recipe_corner(r)}, variant {r["variant"]}, {r["donor_source"]}; certified-file fq {uid} on boxC (border_sweep.py)'
  if r['kind']=='win':src=f'sub-window [a, a+s] x [b, b+s] with {r["window"]} of n={r["donor"]} (literature_window.scan_one on boxC, wscan.py), {r["donor_source"]}; certified-file fq {uid} on boxC'
  src+=('; retained the smaller certified input after fq' if retained else '')
  if meta.get('island'):src+='; then '+meta['island']
  if meta.get('k'):src+=f"; kicked chain k={meta['k']} (first fq call with --kick {meta['kick']} --seed {meta['k']}, then default and deep rounds)"
  lic='ours, on '+r['donor_licence']
  try:src,lic=enrich_source(src,lic)
  except ValueError as e:
   log('REJECT public ancestry '+uid+': '+str(e));continue
  for notice in sp.root_notices(policy):src+=' | '+notice;lic+='; '+notice
  if policy.get('evidence_file'):src+='; full parent evidence '+policy['evidence_file']
  lic+='; '+sp.label(policy)
  if n in sp.RELAXED and policy['status']=='none':src+='; clean-source reference gate/cand-round22-1113b/details.csv'
  reference=sp.OLD22[n] if n in sp.RELAXED and policy['status']=='none' else held[n]
  row={'n':n,'held':repr(reference),'new':repr(sc),'gain':repr(reference-sc),'source':src,'licence':lic}
  csvout(W/'staged'/f'{uid}.share.csv',fr)
  try:share=prvsiyan_share(n,str(W/'staged'/f'{uid}.share.csv'))
  except Exception as e:
   log(f'REJECT {uid}: share test failed {e}');continue
  if share>=0.4:
   log(f'REJECT {uid}: prvsiyan 1105 share within 1e-3 = {share:.3f} (rule b share test, r27)');continue
  src+=f'; prvsiyan 1105 share within 1e-3 = {share:.3f} (prvsim26.py, rule b share test)'
  row['source']=src
  csvout(T/f'{n}.csv',fr)
  write_take([r for r in tt if int(r['n'])!=n]+[row])
  log(f'certified {n}: score {sc:.16g}, gain vs base {held[n]-sc:.9g}, over other takes {float(current[n]["new"])-sc:.9g}')
  with open(S/'handoff-r27.log','a') as f:f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+f' border -> all: certified fresh border {n}, score {sc:.16g}, donor {r["donor"]}, {T}/{n}.csv\n')
dead_skipped=[];_pairs={'t':0,'v':{}}
def pair_giveback(d,n,mg):
 if time.time()-_pairs['t']>600:
  import initial_queue as iq
  iq.OLD=[S/'take-border-r24/work',S/'take-border-r25/work',W]
  rec=iq.records(L)
  _pairs['v']={k:max(x['giveback'] for x in v) for k,v in rec.items()};_pairs['t']=time.time()
  _pairs['dead']={k for k,v in rec.items() if len(v)>=3 and min(x['end'] for x in v)>1.5e-3}
 return _pairs['v'].get((d,n),.3*max(mg,0))
KICK_GAP=1e-3;KICKS=(0.01,0.04,0.003,0.02);KICK_COUNT=0;kicked=set()
def kicks():
 # r26 change for the stuck near-bar endpoints of r25 (794 at 1.7e-4, fq gave back 2.4e-6): kicked fq chains
 # (fq --kick sigma --seed k on the first call, then the same default+deep rounds), midm's measured kick sigmas.
 # r26 14:50Z: off. 16 of 16 kicked chains (794 x8, 791 x4, 909 x4) came back to the side they started from.
 if KICK_COUNT<=0:return
 if not (W/'q/manifest.tsv').exists():return
 manifest={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
 for p in (W/'q').glob('*.k0.json'):
  ident=p.name.removesuffix('.k0.json')
  if ident in kicked or not (W/'q'/(ident+'.job.done')).exists():continue
  r=manifest.get(ident)
  try:j=json.load(open(p))
  except ValueError:continue
  if not r or (j['cut'] and j['round']<6):continue
  n=int(r['n']);gap=j['s_final']-L[n]
  if not(-math.sqrt(n)*1e-10<gap<KICK_GAP):continue
  if sp.manifest_policy(r)['status']!='none':continue
  kicked.add(ident)
  for k in range(1,KICK_COUNT+1):
   job=W/'q'/f'{ident}.kick{k}.job.json'
   if job.exists() or job.with_suffix('.skip').exists() or job.with_suffix('.done').exists():continue
   job.write_text(json.dumps(dict(start=ident+'.start.txt',k=k,kick=KICKS[(k-1)%len(KICKS)],priority=-125+1e5*gap,kick_of=ident)))
  log(f'QUEUE kick chains {ident}: end {gap:.3e} above the bar after a converged fq chain; {KICK_COUNT} chains, fq --kick {KICKS} --seed 1..{KICK_COUNT}; deadline 23:45Z, boxC worker1/2.log')
sys.path.insert(0,str(W))
from provenance import audit, audit_manifest, metadata, enrich_source, prvsiyan_share
import source_policy as sp
from initial_queue import initialize
initialize(globals())
log('start round27 collector/scanner boxA nice5 (light: scan and collect only). Base '+BASE_NOTE+'. Fresh r26 designs first, then saved r25 chains near the bar, then clean r25 unstarted ranked by measured pair give-back. Search and quench end 23:45Z.')
refresh();write_take([]) if not (T/'take.tsv').exists() else None
initialize(globals(),ready=True)
initial=True;tick=0;last_sync=0
while time.time()<END+300:
 try:
  refresh();sync();
  # r27: export_raw_near.py dropped from the loop (0 exports in r26 and r27; each python start costs minutes at load 100)
  collect();kicks()
  if time.time()<POLL_END:
   for p,r,rd in sources(initial):
    if time.time()>POLL_END:break
    make(p,r,rd)
    if time.time()-last_sync>45:
     sync();collect();last_sync=time.time()
  initial=False;tick+=1
  if tick%4==1:
   lines=(S/'handoff-r27.log').read_text().splitlines() if (S/'handoff-r27.log').exists() else []
   print('HANDOFF',*lines[-12:],sep='\n',flush=True)
   print('STATUS',len(queued),'queued starts',len(staged),'staged',len(published),'final quenches read',flush=True)
 except Exception:traceback.print_exc()
 time.sleep(45)
log('collector/scanner finished by deadline')
