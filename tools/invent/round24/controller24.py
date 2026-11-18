import io, itertools, csv, glob, hashlib, json, math, os, pathlib, re, shutil, subprocess, sys, time, traceback
import numpy as np
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from invent_shape22 import fingerprint
from enrich23 import lookup
from ancestry24 import clean, expand
from policy24 import classify, annotate, RELAXED, save_cache
S=pathlib.Path('$SCRATCH/bounties-squares');T=S/'take-invent-r24';W=T/'work'
R=pathlib.Path('.')
PY=str(S/'venv/bin/python'); REM='boxE:scratch/squares-invent-r24/'
TRACK={'readers','family','stair-c','corners','modules','twoshort','k123','classfill','rigidsoft','forensics','harvest','border','soft','midm'}

def now():return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a') as h:h.write(now()+' boxA '+s+'\n')
def atomic(p,x):
 p=pathlib.Path(p); q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(x));q.replace(p)
def command(a):
 r=subprocess.run(a,capture_output=True,text=True,timeout=120)
 if r.returncode:raise RuntimeError(str(a)+' code='+str(r.returncode)+' '+r.stderr[-2000:])
 return r.stdout

_shape_bytes={};_shape_mtime={}
def shape(p):
 p=pathlib.Path(p);before=p.stat().st_mtime_ns;data=p.read_bytes();after=p.stat().st_mtime_ns
 _shape_bytes[str(p)]=data;_shape_mtime[str(p)]=before if before==after else None
 rows=list(csv.DictReader(io.StringIO(data.decode())));n=len(rows)
 a=np.array([[float(r['x']),float(r['y']),float(r['angle'])]for r in rows])
 h=.5*(np.abs(np.cos(a[:,2]))+np.abs(np.sin(a[:,2])))
 L=float(np.max((a[:,:2]+h[:,None]).max(0)-(a[:,:2]-h[:,None]).min(0)))
 fp=fingerprint(a)
 return n,L,fp

def provenance(p,n):
 lane=next((v for v in p.parts if v.startswith('take-')),'unknown')
 jp=p.with_suffix('.json');src='';lic=''
 if not jp.exists():jp=pathlib.Path(str(p)+'.json')
 nt=p.parent/'near.tsv'
 if nt.exists():
  for r in csv.DictReader(open(nt),delimiter='\t'):
   if r.get('file')==p.name:src=r['source'];lic=r['licence'];break
 if jp.exists() and not src:
  try:
   j=json.load(open(jp));mods=j.get('modules',[])
   if mods:
    src='modules build: '+', '.join(m['id']+' <'+m['source']+'>'for m in mods)
    lic='; '.join(m['licence']for m in mods)
    src+='; squeezed '+str(j.get('squeeze','methods_lp, fq'))
   elif 'manifest' in j:
    m=j['manifest'];src=f"border {m.get('kind')} from n={m.get('donor')}, corner {m.get('corner')}, variant {m.get('variant')}: {m.get('donor_source')}; exact near record {jp}";lic=m.get('donor_licence','')
   elif 'parts' in j:
    src='rectangle windows '+json.dumps(j['parts'],separators=(',',':'))
    lic='; '.join(j['parts'][k].get('licence','see donor ledger') for k in ('A','B'))
   else:src=j.get('source')or j.get('source_override','');lic=j.get('licence')or j.get('licence_override','')
  except Exception:pass
 if not src and lane in ('take-k123-r22','take-k123-r23'):
  cf=S/lane/'work/collect-state.json'
  if cf.exists():
   for key,record in json.load(open(cf)).items():
    pair=p.stem.replace(str(n)+'-initial-','')
    if record.get('n')==n and pair in key and record.get('source'):
     src=record['source'];lic=record['licence'];break
 if not src:
  resolved=lookup(p,n)
  if resolved:src,lic=resolved
 if not src:
  # Readers and family near names retain their donor n and lane. Keep the named source table as the provenance reference.
  src='near build recorded by '+lane+'/STATE.txt and work logs'
  lic='see '+lane+' source records; held ancestry: results/round23-best-2026-11-13.tsv'
 return f'{lane}/near/{p.name}: {src}',lic

def turn():
 _shape_bytes.clear();_shape_mtime.clear()
 remote=W/'boxE-raw';remote.mkdir(exist_ok=True)
 command(['rsync','-a','--exclude=lane/','--exclude=starts/','--exclude=locks/','--exclude=*.py','--exclude=logs/','--exclude=tmp/','--exclude=*.tmp',REM,str(remote)+'/'])
 receipts_path=remote/'certified-receipts.json'
 if receipts_path.exists():
  try:cf=json.load(open(W/'fs-cache-policy.json'))
  except (OSError,ValueError):cf={}
  for rel,receipt in json.load(open(receipts_path)).items():
   p=remote/rel
   if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==receipt['sha256']:
    cf[str(p)]=[p.stat().st_mtime,receipt['score'],receipt['sha256'],True]
  atomic(W/'fs-cache-policy.json',cf)
 try: jobs=json.load(open(W/'jobs.json'))
 except Exception:jobs=[]
 jobs=[j for j in jobs if not j.get('skipped_duplicate')]
 ids={j['id']for j in jobs}
 for j in jobs:
  if False:
   p=S/j['source'].split(': near build recorded by ')[0]
   if p.exists():j['source'],j['licence']=provenance(p,j['n'])
 locks=set(command(['ssh','-o','ConnectTimeout=10','boxE','ls $SCRATCH/squares-invent-r24/locks']).split())
 done={}
 for p in remote.glob('*/done.json'):
  try:done[p.parent.name]=json.load(open(p))
  except Exception:pass
 recorded=json.load(open(W/'recorded-runs.json')) if (W/'recorded-runs.json').exists() else {'start':[],'finish':[]}
 for j in jobs:
  ident=j['id']
  if ident in locks and ident not in recorded['start']:
   state(f'ADOPT RUN {ident} boxE invent_rest.py n={j["n"]} start={j["start"]} seconds={j["seconds"]} seed={j["seed"]} fq={j["fq"]}, log work/boxE-raw/{ident}/run.log, deadline22:15Z')
   recorded['start'].append(ident)
  if ident in done and ident not in recorded['finish']:
   state(f'FINISH RUN {ident} boxE invent_rest.py, log work/boxE-raw/{ident}/run.log, deadline22:15Z; {json.dumps(done[ident],sort_keys=True)}')
   recorded['finish'].append(ident)
 atomic(W/'recorded-runs.json',recorded)
 held={int(r['n']):float(r['score'])for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))}
 bar=dict(held);owners={};sources={}
 for p in sorted(list(S.glob('take-*-r24/take.tsv'))):
  if p.parent==T:continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   try:n=int(r['n']);v=float(r['new'])
   except Exception:continue
   if n in bar and v<bar[n]:bar[n]=v;owners[n]=p.parent.name;sources[n]=r
 with open(W/'bar24.csv.tmp','w',newline='')as h:
  w=csv.writer(h);w.writerow(['n','L','score','who'])
  for n,s in sorted(bar.items()):w.writerow([n,(s+1)*math.sqrt(n),s,owners.get(n,'round23')])
 os.replace(W/'bar24.csv.tmp',W/'bar24.csv')
 for j in jobs:
  if j['id'] not in locks and j['n'] in bar:
   j['bar']=(bar[j['n']]+1)*math.sqrt(j['n'])
   if j.get('backlog') and not j.get('rebar_recorded'):
    state(f"DECIDE saved start {j['id']} n={j['n']} side={j['side']:.12f} current bar={j['bar']:.12f} delta={j['side']-j['bar']:+.6g}; run once on slot3 as assigned, log work/boxE-raw/{j['id']}/run.log deadline22:15Z")
    j['rebar_recorded']=True
 atomic(W/'jobs.json',jobs)
 # Publish only runs whose certified input has had its remote fq quench.
 specs=[]
 for j in jobs:
  if j['kind']=='control' or j['id'] not in done or not done[j['id']].get('quench_from_certified'):continue
  if not clean(j['source'],j['licence'])[0]:continue
  specs.append(str(remote/j['id']/'final')+'|invent_rest.py lkick, family squeeze'+(' and fq'if j['fq']else'')+', then floatsafe and one fq quench from the certified file, from '+j['source']+'|'+j['licence'])
 before={r['n']:r['new']for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')}if (T/'take.tsv').exists()else{}
 atomic(W/'cert-specs.json',specs)
 proc=subprocess.run([PY,'-I',str(W/'certrest24.py'),str(T),'@'+str(W/'cert-specs.json')],capture_output=True,text=True,timeout=180)
 (W/'certrest.log').write_text(proc.stdout+proc.stderr)
 if proc.returncode:raise RuntimeError('certrest failed '+proc.stderr[-1000:])
 for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
  if before.get(r['n'])==r['new']:continue
  msg=f"certified n={r['n']} score={r['new']}, {T}/{r['n']}.csv"
  with open(S/'handoff-r24.log','a')as h:h.write(now()+' invent -> all: '+msg+'\n')
  state('CERT '+msg)
 # Hand off each new layout as soon as its run finishes, including useful near misses.
 handed=set(json.load(open(W/'handed.json')))if (W/'handed.json').exists()else set()
 for j in jobs:
  if j['id']in handed or j['kind']=='control' or j['id']not in done:continue
  d=done[j['id']];handed.add(j['id'])
  if not d.get('quench_from_certified'):continue
  n=j['n'];L=(d['new']+1)*math.sqrt(n)
  if L>(bar[n]+1)*math.sqrt(n)+0.015:continue
  p=T/'near'/f'{n}-{j["id"]}.csv';shutil.copy(remote/j['id']/'final'/f'{n}.csv',p)
  atomic(p.with_suffix('.json'),{'n':n,'source':j['source'],'licence':j['licence'],'side':L,'kick':'invent_rest.py lkick then certified-input fq'})
  with open(S/'handoff-r24.log','a')as h:h.write(now()+f' invent -> all: finished kick n={n}, side={L:.12f}, delta to bar {L-(bar[n]+1)*math.sqrt(n):+.3e}; {p}\n')
 atomic(W/'handed.json',sorted(handed))
 # Rank search against our retained row too. Publication still uses the external bar in certrest.
 for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
  n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
 for j in jobs:
  if j['id']not in locks and j['kind']!='control':
   j['bar']=(bar[j['n']]+1)*math.sqrt(j['n'])
   if j['kind']=='near':j['order']=j['side']-j['bar']
 fallback={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round22-1113b/details.csv'))}
 for n in RELAXED:bar[n]=max(bar[n],fallback[n])
 # No production search before the positive control has printed a side under its stop.
 ctl=remote/'ctl907b'
 green=False
 for p in ctl.glob('slide-*.tsv'):
  for l in open(p):
   a=l.split('\t')
   if len(a)>4 and a[0].isdigit():
    try:green|=float(a[4])<30.6195806
    except Exception:pass
 if not green:
  print(now(),'control not green yet',flush=True);return
 if not(W/'CONTROL_GREEN').exists():
  (W/'CONTROL_GREEN').write_text('907 passed side 30.6195806\n');state('CONTROL GREEN ctl907b: local kick from stopped block passed side 30.6195806; production enabled')
 command(['rsync','-a',str(W/'CONTROL_GREEN'),REM])
 if time.time()>=float((W/'deadline').read_text())-300:return
 seen=set(json.load(open(W/'seen-r23-v2.json')))if(W/'seen-r23-v2.json').exists()else set()
 # Seed from r21 history so old kicks are not repeated on the same start.
 if not(W/'history-r23-v2-loaded').exists():
  for p in list((S/'take-invent-r21/work/starts').glob('*.csv'))+list((S/'take-invent-r22/work/starts').glob('*.csv'))+list((S/'take-invent-r23/work/starts').glob('*.csv')):
   try:seen.add(shape(p)[2])
   except Exception:pass
  (W/'history-r23-v2-loaded').touch()
 for j in jobs:
  if j['kind']=='control':continue
  try:seen.add(shape(W/j['start'])[2])
  except Exception:pass
 candidates=[]
 # Each builder take is a fresh design even if a kick lane already lowered its n.
 for table in sorted(list(S.glob('take-*-r24/take.tsv'))):
  who=table.parent.name;lane=who[len('take-'):-4];table_mtime=table.stat().st_mtime_ns
  if lane not in TRACK:continue
  for row in csv.DictReader(open(table),delimiter='\t'):
   try:n=int(row['n'])
   except Exception:continue
   p=table.parent/f'{n}.csv'
   if not p.exists() or p.stat().st_mtime_ns>table_mtime:continue
   src,lic=row['source'],row['licence']
   if src.startswith(('fq kick','one fq quench','fq quench of invent_rest','fq quench of fq kick and quench','midm_scan.py','invent_rest.py','$SCRATCH/bounties-squares/take-')):continue
   try:nn,L,fp=shape(p)
   except Exception:continue
   if nn!=n or fp in seen or L>(bar[n]+1)*math.sqrt(n)+0.015 or _shape_mtime[str(p)] is None or _shape_mtime[str(p)]>table_mtime:continue
   src,lic=expand(row['source'],row['licence'])
   src,lic=annotate(src,lic)
   if not clean(src,lic)[0]:continue
   candidates.append(((-0.4 if lane in ('family','readers','k123') else -0.3) if who.endswith('-r24') else 2,-(held[n]-bar[n]),str(p),n,L,fp,f'{who}/take.tsv: {src}',lic,'fresh',src.startswith('rectangle windows')))
 # Read exact public starts from handoffs even when another kick lane now owns their count.
 public={}
 for line in (S/'handoff-r24.log').read_text().splitlines():
  if 'new certified public n=' not in line:continue
  paths=re.findall(r'$SCRATCH/bounties-squares/take-harvest-r24/work/public/starts/\d+\.csv',line)
  for path in paths:public[path]=line
 for path,line in public.items():
  p=pathlib.Path(path)
  if not p.exists() or 'licence=' not in line:continue
  try:n,L,fp=shape(p)
  except Exception:continue
  if fp in seen or L>(bar[n]+1)*math.sqrt(n)+0.015:continue
  src='exact public start handoff: '+line
  lic=line.split('licence=',1)[1].rsplit(', /Volumes/',1)[0]
  src,lic=expand(src,lic);src,lic=annotate(src,lic)
  if not clean(src,lic)[0] or classify(src,lic)['status']=='unknown':continue
  candidates.append((-0.5,L-(bar[n]+1)*math.sqrt(n),str(p),n,L,fp,src,lic,'fresh',False))
 # New r22 near layouts first, with r21 leftovers within 2e-4 as a reserve.
 cache=json.load(open(W/'near-cache-r23-v2.json'))if(W/'near-cache-r23-v2.json').exists()else{}
 for rd in(24,):
  for p in S.glob(f'take-*-r{rd}/near/**/*.csv'):
   if p.is_relative_to(T):continue
   lane=p.parts[len(S.parts)]
   if lane.split('-r')[0][5:]not in TRACK:continue
   try:
    mt=p.stat().st_mtime;c=cache.get(str(p))
    if c and c[0]==mt:n,L,fp=c[1:]
    else:n,L,fp=shape(p);cache[str(p)]=[mt,n,L,fp]
    if fp in seen or n not in bar:continue
    n,L,fp=shape(p)
    if fp in seen or _shape_mtime[str(p)] is None:continue
    delta=L-(bar[n]+1)*math.sqrt(n)
    if delta>0.015 or delta<-0.02:continue
    src,lic=provenance(p,n)
    src,lic=expand(src,lic)
    src,lic=annotate(src,lic)
    if not clean(src,lic)[0] or p.stat().st_mtime_ns!=_shape_mtime[str(p)]:continue
    fq=('squeezed methods_lp' in src or 'squeezed (methods_lp' in src or 'fq' in p.name or lane.startswith('take-forensics-'))
    candidates.append((-0.2 if rd==24 else 3,delta,str(p),n,L,fp,src,lic,'near',fq))
   except Exception:continue
 atomic(W/'near-cache-r23-v2.json',cache)
 # Give every substantive find one leg. No leg of a leg.
 for j in jobs:
  d=done.get(j['id'],{})
  if j['kind']in('leg','control')or not d.get('quench_from_certified')or 'leg:'+j['id']in seen:continue
  n=j['n'];L=(d['new']+1)*math.sqrt(n)
  if j['side']-L<5e-8 or L-(bar[n]+1)*math.sqrt(n)>max(2e-5,j['side']-L):continue
  p=remote/j['id']/'final'/f'{n}.csv'
  candidates.append((-1 if j['side']-L>1e-5 else 0.25,-(j['side']-L),str(p),n,L,'leg:'+j['id'],'leg of '+j['id']+' from '+j['source'],j['licence'],'leg',j['fq']))
 pending=[j for j in jobs if j['id']not in locks and j['kind']!='control']
 room=max(0,12-sum(not j.get('backlog') for j in pending))
 if any(c[8]=='fresh' for c in candidates):room=max(room,3-sum(j['kind']=='fresh' and not j.get('backlog') for j in pending))
 if any(c[8]=='near' and c[0]<0 for c in candidates):room=max(room,2)
 added=[];pern={}
 for rank,delta,ps,n,L,fp,src,lic,kind,fq in sorted(candidates):
  if room<=0:break
  if fp in seen or pern.get(n,0)>=2:continue
  if kind=='near' and rank==3 and sum(j['kind']=='near' and j.get('priority')==3 for j in pending+added)>=3:continue
  # Keep only one waiting fresh line, leaving room for near starts.
  if kind=='fresh'and sum(j['kind']=='fresh' and not j.get('backlog') for j in pending+added)>=3:continue
  ident=f'{kind[0]}{time.strftime("%H%M%S",time.gmtime())}x{n}x{len(jobs)+len(added)}'
  start='starts/'+ident+'.csv';snapshot=_shape_bytes.get(ps)
  if snapshot is None:snapshot=pathlib.Path(ps).read_bytes()
  (W/start).write_bytes(snapshot)
  new={'id':ident,'n':n,'start':start,'seconds':300 if fq else 420,'seed':123 if kind!='leg'else 172,'kind':kind,'fq':fq,'bar':(bar[n]+1)*math.sqrt(n),'side':L,'source':src,'licence':lic,'priority':rank,'order':delta,'input_sha256':hashlib.sha256(snapshot).hexdigest()}
  added.append(new);seen.add(fp);pern[n]=pern.get(n,0)+1;room-=1
  state(f'QUEUE {ident} n={n} kind={kind} side={L:.12f} delta={L-new["bar"]:+.3e} fq={fq} from {ps}; boxE worker24.py, deadline22:15Z')
 jobs+=added
 atomic(W/'seen-r23-v2.json',sorted(seen));atomic(W/'jobs.json',jobs)
 fresh_started=sum(j['kind']=='fresh' and j['id'] in locks for j in jobs)
 near_started=sum(j['kind']=='near' and j['id'] in locks for j in jobs)
 reserve_near=fresh_started>=2*max(1,near_started)
 queue=sorted([j for j in jobs if j['id']not in locks and clean(j['source'],j['licence'])[0] and (j['kind']=='control' or classify(j['source'],j['licence'])['status']!='unknown')],key=lambda j:(-1 if reserve_near and j['kind']=='near' else j.get('priority',-2),j.get('order',0),j['id']))
 atomic(W/'queue.json',queue)
 # Slot1 reserves fresh handoffs. Slot2/3 drain clean snapshots and saved near starts.
 fresh=[j for j in queue if not j.get('backlog') and j['kind'] in ('control','fresh','near')]
 # A new count gets a first pass before another version of a count already scanned.
 counts_started={j['n'] for j in jobs if j['id'] in locks and j['kind']!='control'}
 fresh.sort(key=lambda j:(-1 if j['kind']=='control' else int(j['n'] in counts_started),0 if classify(j['source'],j['licence'])['status']=='none' else 1,j.get('priority',0),j.get('order',0),j['id']))
 rest=[j for j in queue if j not in fresh]
 # A measured short-probe control must finish before any budget is shortened.
 probe=done.get('ctl907probe',{})
 short_green=probe.get('quench_from_certified',False) and (probe['new']+1)*math.sqrt(907)<30.6195806
 if short_green:
  if not (W/'SHORT_GREEN').exists():
   (W/'SHORT_GREEN').write_text(json.dumps(probe));state('CONTROL short180 probe907 passed stop and certified-input quench; shorter first probes enabled for new non-join starts')
  for j in queue:
   if not j.get('backlog') and j['kind'] in ('fresh','near') and not j['fq'] and 'k123_join.py' not in j['source']:j['seconds']=180
  atomic(W/'jobs.json',jobs)
 atomic(W/'queue1.json',fresh+[j for j in rest if j.get('backlog') and j['kind']=='fresh'])
 atomic(W/'queue2.json',[j for j in rest if j['kind']=='rescue']+[j for j in fresh if j['kind']=='fresh'][:1]+rest+fresh)
 atomic(W/'queue3.json',rest+fresh)
 command(['rsync','-a',str(W/'starts'),REM])
 command(['rsync','-a',str(W/'queue.json'),str(W/'queue1.json'),str(W/'queue2.json'),str(W/'queue3.json'),REM])
 # Record handoff observations every pass. It is read-only and never messages another agent.
 hp=S/'handoff-r24.log'
 if hp.exists():
  count=sum(1 for _ in open(hp));old=int((W/'handoff-lines').read_text())if(W/'handoff-lines').exists()else 0
  if count>old:
   for l in open(hp).readlines()[old:]:
    if ' -> invent:'in l or 'main -> all:'in l:state('HANDOFF READ '+l.strip())
   (W/'handoff-lines').write_text(str(count))
 save_cache()
 print(now(),'done',len(done),'jobs',len(jobs),'added',len(added),'cert',proc.stdout.strip().splitlines()[-1],flush=True)

if __name__=='__main__':
 while time.time()<float((W/'deadline').read_text())+480 and not(W/'STOPCONTROLLER').exists():
  try:turn()
  except Exception:traceback.print_exc();state('CONTROLLER ERROR see work/controller.log')
  if '--once'in sys.argv:break
  time.sleep(60)
