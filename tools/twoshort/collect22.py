"""Copy boxE artifacts, refresh the shared bar, and publish certified results."""
import csv,hashlib,json,math,os,pathlib,pickle,re,shlex,shutil,subprocess,sys,time
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r22';W=T/'work';R=W/'boxE22';R.mkdir(exist_ok=True);PY=str(B/'venv/bin/python');remote='boxE:scratch/squares-twoshort/'
seenpath=W/'collect-seen.json';seen=set(json.load(open(seenpath))) if seenpath.exists() else set()
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+s+'\n')
def rsync(src,dst,*opts):subprocess.run(['rsync','-az',*opts,str(src),str(dst)],check=True)
def once():
 rsync(remote,R,'--exclude=lane','--exclude=lib-z4','--exclude=tmp','--exclude=lib')

 for line in (R/'worker.log').read_text().splitlines():
  key='worker:'+hashlib.sha256(line.encode()).hexdigest()
  if key not in seen:
   state('boxE queue '+line+'; logs work/boxE22/runs or designs; deadline 15:20 UTC');seen.add(key)
 same974=None
 dry974=0
 for dp in R.glob('done/*.json'):
  dd=json.load(open(dp))
  if dd.get('n')==974 and 'start_side' in dd and dd['start_side']-dd['best']<1e-8:dry974+=1
 if dry974>=3:
  from shape974 import guard
  same974,control=guard(R);(W/'shape974-control.json').write_text(json.dumps(control,indent=2))
  cancel=[]
  for jp in R.glob('jobs/*.json'):
   if (R/'locks'/jp.name).exists():continue
   jj=json.load(open(jp))
   if jj.get('n')!=974:continue
   start=jj['start'];prefix='$SCRATCH/squares-twoshort/'
   local=R/start[len(prefix):] if start.startswith(prefix) else R/start
   if local.exists() and same974(local):
    live=json.load(open(W/'bar.json'))['974']
    if (T/'take.tsv').exists():
     for rr in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
      if rr['n']=='974':live=min(live,(1+float(rr['new']))*math.sqrt(974))
    if shape_load(local)[1]>=live-1e-10*math.sqrt(974):cancel.append(jp.name)
  if cancel:
   code='from pathlib import Path;import json,time;r=Path.home()/"scratch/squares-twoshort";names='+repr(cancel)+'\nfor name in names:\n try:(r/"locks"/name).mkdir()\n except FileExistsError:continue\n j=json.load(open(r/"jobs"/name));j["cancelled"]="same 974 geometry after three dry scans";json.dump(j,open(r/"done"/name,"w"));print(name)'
   result=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(code)],check=True,capture_output=True,text=True)
   if result.stdout.strip():state('CANCEL shared974 floor after '+str(dry974)+' dry scans: '+result.stdout.strip().replace('\n',', '))
 # Treat a numerical copy of an already queued start as the same handoff.
 from shape974 import load as shape_load,distance as shape_distance
 shape_pool={};shape_cache={}
 prefix='$SCRATCH/squares-twoshort/'
 for jp in R.glob('jobs/*.json'):
  jj=json.load(open(jp))
  if 'n' not in jj or 'start' not in jj:continue
  st=jj['start'];lp=R/st[len(prefix):] if st.startswith(prefix) else R/st
  if lp.exists():shape_pool.setdefault(jj['n'],set()).add(lp)
 def same_queued(n,path):
  if n not in shape_pool:return None
  arr,side=shape_load(path)
  for ref in shape_pool[n]:
   if ref not in shape_cache:shape_cache[ref]=shape_load(ref)
   rr,ss=shape_cache[ref]
   if len(rr)!=len(arr) or abs(side-ss)>=2e-8:continue
   gap=shape_distance(arr,side,rr)
   if gap<2e-8:return ref,gap
  return None
 held=list(csv.DictReader(open(B/'gate/cand-round20-1113a/details.csv')));bar={int(r['n']):float(r['score']) for r in held}
 for p in list(B.glob('take-*-r21/take.tsv'))+list(B.glob('take-*-r22/take.tsv')):
  if p.parent==T:continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   try:n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
   except:pass
 with open(W/'details-bar.csv','w',newline='') as f:
  out=csv.writer(f);out.writerow(['n','L','score','min_gap'])
  for r in held:
   n=int(r['n']);out.writerow([n,(1+bar[n])*math.sqrt(n),bar[n],r['min_gap']])
 json.dump({str(n):(1+s)*math.sqrt(n) for n,s in bar.items()},open(W/'bar.json','w'))
 rsync(W/'bar.json',remote+'bar.json');rsync(W/'details-bar.csv',remote+'details-bar.csv')
 stage=W/'stage';stage.mkdir(exist_ok=True)
 for p in R.glob('q/*/meta.json'):
  key='q:'+str(p)
  j=json.load(open(p))
  if key in seen and j['quench_rc']==0:continue
  src=p.parent/pathlib.Path(j['quenched_file']).name
  if j['quench_rc']!=0 or not src.exists():continue
  if j['licence'].startswith(('see ','unresolved')) and (T/'take.tsv').exists():
   current={int(rr['n']):float(rr['new']) for rr in csv.DictReader(open(T/'take.tsv'),delimiter='\t')}
   if j['n'] in current:
    sys.path.insert(0,'.');import floatsafe
    rows=[{kk:rr[kk] for kk in ('n','square_id','x','y','angle')} for rr in csv.DictReader(open(src))]
    _,fr,score,err=floatsafe.work((j['n'],rows))
    if fr is not None and score>=current[j['n']]:
     seen.add(key);state('DROP indirect candidate n='+str(j['n'])+' score='+str(score)+' is above our own '+str(current[j['n']])+'; no source claim or publication needed');continue
  if j['licence'].startswith(('see ','unresolved')):
   initial=R/'starts'/(j['tag']+'.csv')
   if initial.exists():
    digest=hashlib.sha256(initial.read_bytes()).digest()
    for donor in list(B.glob('take-*-r21/'+str(j['n'])+'.csv'))+list(B.glob('take-*-r22/'+str(j['n'])+'.csv')):
     if donor.parent==T or hashlib.sha256(donor.read_bytes()).digest()!=digest:continue
     for rr in csv.DictReader(open(donor.parent/'take.tsv'),delimiter='\t'):
      if rr['n']==str(j['n']):
       j['source']=str(donor)+'; exact copy as '+str(initial)+'; '+rr['source']+'; '+str(donor.parent/'take.tsv')+'; results/round20-best-2026-11-13.tsv';j['licence']=rr['licence']
     break
  if j['licence'].startswith(('see ','unresolved')):
   uk='unresolved:'+str(p)
   if uk not in seen:state('SOURCE TRACE needed for candidate '+str(src));seen.add(uk)
   continue
  name=str(j['n'])+'-'+p.parent.name;shutil.copy2(src,stage/(name+'.csv'));json.dump(dict(source=j['source']+'; raw chain start '+str(R/pathlib.Path(j['start']).relative_to('$SCRATCH/squares-twoshort') if j['start'].startswith('$SCRATCH/squares-twoshort/') else R/j['start'])+'; lkick seed '+str(j['seed'])+'; boxE fq from certified file',licence=j['licence']),open(stage/(name+'.json'),'w'))
  # Near files retain both forms so follow lanes can choose their squeeze.
  if j['best']<j['bar']+.00015:
   near=T/'near'/(name+'.csv');shutil.copy2(src,near)
   raw=R/pathlib.Path(j['best_file']).relative_to('$SCRATCH/squares-twoshort') if j['best_file'].startswith('$SCRATCH/squares-twoshort/') else R/j['best_file']
   if raw.exists():shutil.copy2(raw,T/'near'/(name+'-raw.csv'))
   with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: near local-kick chain '+name+', side '+str(j['best'])+'; raw and quenched copies '+str(near)+'\n')
  with open(W/'certify.log','a') as f:subprocess.run([PY,str(W/'certify22.py'),str(stage)],stdout=f,stderr=subprocess.STDOUT,check=True)
  seen.add(key)
 # Relay raw near finds before their chain or fq quench ends.
 job_runs={}
 for jp in R.glob('jobs/*.json'):
  jj=json.load(open(jp))
  if 'tag' in jj and 'seed' in jj:job_runs[(jj['tag'],jj['seed'])]=jj
 published={hashlib.sha256(pp.read_bytes()).digest() for pp in (T/'near').glob('*.csv')}
 for log in R.glob('runs/*/slide-*.tsv'):
  run=log.parent.name
  try:tag,seedtext=run.rsplit('-s',1);seed=int(seedtext);jj=job_runs[(tag,seed)]
  except (ValueError,KeyError):continue
  if tag.startswith('control'):continue
  text=log.read_text();head=re.search(r'start=([0-9.]+)',text)
  if not head:continue
  start=float(head[1]);n=jj['n'];barL=(1+bar[n])*math.sqrt(n)
  for line in text.splitlines():
   parts=line.split('\t')
   if len(parts)!=7 or parts[-1]!='BEST':continue
   side=float(parts[3]);gain=start-side;gap=side-barL
   if gain<1e-9 or not (gap<.001 or gain>=1e-5 and gap<.015):continue
   raw=log.parent/'raw'/('%d-sl%d-%s.csv'%(n,seed,parts[0]))
   if not raw.exists():continue
   digest=hashlib.sha256(raw.read_bytes()).digest()
   if digest in published:continue
   published.add(digest);dst=T/'near'/('%d-%s-s%d-t%s-raw.csv'%(n,tag,seed,parts[0]));tmp=dst.with_suffix('.tmp');shutil.copy2(raw,tmp);tmp.replace(dst)
   nsrc=jj['source'];nlic=jj['licence']
   if nlic.startswith(('see ','unresolved')):nsrc=nsrc.split('; ancestry ')[0]+'; held source register results/round20-best-2026-11-13.tsv';nlic='unresolved (raw near input, not a certified take)'
   dst.with_suffix('.json').write_text(json.dumps(dict(n=n,built=side,start=start,bar=barL,source=nsrc,licence=nlic,seed=seed,trial=parts[0],certified=False),indent=2))
   with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: raw local-kick near n='+str(n)+' side='+str(side)+' gap='+str(gap)+' from '+tag+', '+str(dst)+'\n')
 # Publish each new corner base and raw family build as soon as it arrives.
 for p in R.glob('designs/*/base.pkl'):
  if p.parent.name.startswith('import-'):continue
  key='base:'+str(p)+':'+str(p.stat().st_mtime_ns)
  if key not in seen:
   seen.add(key)
   with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: new 9x9 staircase base (possibly partial), '+str(p)+'\n')
 for p in R.glob('designs/*/builds/*.json'):
  key='build:'+str(p)
  if key in seen:continue
  seen.add(key);d=json.load(open(p));n=d['n']
  if d.get('built') is None or d['built']>(1+bar[n])*math.sqrt(n)+.001:continue
  dst=T/'near'/(str(n)+'-'+p.parent.parent.name+'-'+p.stem+'-family.csv');shutil.copy2(p.with_suffix('.csv'),dst);shutil.copy2(p,dst.with_suffix('.json'))
  with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: fresh family-only build '+str(n)+' side '+str(d['built'])+', '+str(dst)+'\n')
 for pat in ['designs/*/runs/corner*.pkl','designs/*/runs-weak/corner*.pkl']:
  for p in R.glob(pat):
   if p.parent.parent.name.startswith('import-'):continue
   key='corner-run:'+str(p)+':'+str(p.stat().st_mtime_ns)
   if key not in seen:
    seen.add(key)
    with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: fresh kept corner state (zone_corner table reads this runs folder), '+str(p.parent)+'\n')
 for p in R.glob('designs/*/zones/corners.pkl'):
  if p.parent.parent.name.startswith('import-') and not p.parent.parent.name.startswith('import-rescreen-'):continue
  key='zones:'+str(p)+':'+str(p.stat().st_mtime_ns)
  if key not in seen:
   seen.add(key)
   with open(B/'handoff-r22.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: fresh staircase/hopped 9x9 corners, '+str(p.parent)+'\n')
 # Read every new handoff line. New designs in the lane slice take priority.
 known_digests={hashlib.sha256(pp.read_bytes()).digest() for pat in ['*.csv','near/*.csv'] for pp in T.glob(pat)}
 live_sides={n:(1+score)*math.sqrt(n) for n,score in bar.items()}
 if (T/'take.tsv').exists():
  for rr in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
   nn=int(rr['n']);live_sides[nn]=min(live_sides[nn],(1+float(rr['new']))*math.sqrt(nn))
 known_bases={hashlib.sha256(pp.read_bytes()).hexdigest() for pp in R.glob('designs/*/base.pkl') if not pp.parent.name.startswith('import-')}
 hp=B/'handoff-r22.log'
 if hp.exists():
  for line in hp.read_text().splitlines():
   key='h:'+hashlib.sha256(line.encode()).hexdigest()
   if key in seen:continue
   seen.add(key)
   if 'twoshort ->' in line or ' -> ' not in line:continue
   lane=line.split(' -> ')[0].split()[-1]
   for src in re.findall(r'$DATA/[^\s,;]+\.pkl',line):
    p=pathlib.Path(src)
    if not p.exists():continue
    try:
     base=pickle.load(open(p,'rb'))
     if not isinstance(base,list) or not base:continue
     if not any(q.get('c1') in [8,9,10] and q.get('c2') in [8,9,10] for q in base):continue
     f0=float(base[0]['f'])
    except Exception:continue
    digest=hashlib.sha256(p.read_bytes()).hexdigest();dk='pkl:'+digest
    if dk in seen or digest in known_bases:continue
    seen.add(dk);tag='import-'+lane+'-'+dk[-8:];d=W/'designs'/tag;d.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d/'base.pkl')
    j=dict(kind='design',f=f0,tag=tag);q=W/'jobs'/('000-00-'+tag+'.json');json.dump(j,open(q,'w'))
    rsync(d,remote+'designs/');rsync(q,remote+'jobs/'+q.name)
    state('QUEUE corner import '+src+' as '+tag+'; command boxE design22.py '+str(f0)+' '+tag+'; logs designs/'+tag+'; deadline15:20 UTC')
   paths=re.findall(r'$DATA/[^\s,;]+\.csv',line)
   for src in paths:
    p=pathlib.Path(src)
    if not p.exists():continue
    try:
     first=next(csv.DictReader(open(p)));n=int(first['n']);m=math.isqrt(n-1)
    except:continue
    if m not in range(28,32) or n-m*m not in range(5,17):continue
    lane=line.split(' -> ')[0].split()[-1]
    if lane in ['midm','polish','harvest','soft','classfill','invent']:continue
    data=p.read_bytes()
    if hashlib.sha256(data).digest() in known_digests:continue
    if n==974 and same974 is not None and same974(p) and shape_load(p)[1]>=live_sides[n]-1e-10*math.sqrt(n):continue
    duplicate=same_queued(n,p)
    if duplicate and shape_load(p)[1]>=live_sides[n]-1e-10*math.sqrt(n):
     state('DROP numeric handoff copy n='+str(n)+' maxgeom='+str(duplicate[1])+' from '+str(p)+'; queued start '+str(duplicate[0]));continue
    dk='file:'+hashlib.sha256(data).hexdigest()
    if dk in seen:continue
    seen.add(dk);tag='h-'+lane+'-'+str(n)+'-'+dk[-8:];dst=W/'starts'/(tag+'.csv');shutil.copy2(p,dst)
    licence='unresolved (raw near input: '+str(p)+')';source=str(p)+'; held source register results/round20-best-2026-11-13.tsv'
    if (p.parent/'take.tsv').exists():source+='; ancestry '+str(p.parent/'take.tsv')
    if (p.parent/'take.tsv').exists():
     for r in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t'):
      if r['n']==str(n):source+='; '+r['source'];licence=r.get('licence',licence)
    input_side=shape_load(p)[1];gap=input_side-(1+bar[n])*math.sqrt(n);priority=6 if gap>.001 else 0
    j=dict(tag=tag,n=n,start='starts/'+dst.name,seed=322,remaining=1 if priority==6 else 4,seconds=300,miss=0,priority=priority,source=source,licence=licence)
    q=W/'jobs'/('%03d-'%priority+tag+'-322.json');json.dump(j,open(q,'w'));shape_pool.setdefault(n,set()).add(dst);rsync(dst,remote+'starts/'+dst.name);rsync(q,remote+'jobs/'+q.name)
    state('QUEUE fresh handoff '+tag+' from '+str(p)+'; logs boxE runs/'+tag+'-s322; deadline 15:20 UTC')
 # Archive completed libraries before removing their remote copies to keep the box below 3 GB.
 for summary in R.glob('designs/*/summary.json'):
  tag=summary.parent.name;key='lib-copy:'+tag
  if key in seen or not re.fullmatch(r'[A-Za-z0-9_-]+',tag):continue
  if json.load(open(summary)).get('skipped'):seen.add(key);continue
  dst=summary.parent/'lib';dst.mkdir(exist_ok=True)
  try:
   rsync(remote+'designs/'+tag+'/lib/',str(dst)+'/')
   hashes={name:hashlib.sha256((dst/name).read_bytes()).hexdigest() for name in ['library.pkl','lens.pkl']}
   code='from pathlib import Path;import hashlib,json,shutil;r=Path.home()/"scratch/squares-twoshort/designs"/'+repr(tag)+'/"lib";want='+repr(hashes)+';got={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in want};assert got==want,(got,want);shutil.rmtree(r);print(json.dumps(got))'
   reply=subprocess.run(['ssh','boxE',str(pathlib.Path('$SCRATCH/squares-base/venv/bin/python'))+' -c '+shlex.quote(code)],check=True,capture_output=True,text=True)
   (dst/'copy-check.json').write_text(reply.stdout);seen.add(key);state('ARCHIVE verified library '+tag+' to '+str(dst)+'; removed only remote designs/'+tag+'/lib');break
  except subprocess.CalledProcessError as e:
   state('ARCHIVE retry '+tag+' rc='+str(e.returncode))
 seenpath.write_text(json.dumps(sorted(seen)))
 print(time.strftime('%FT%TZ',time.gmtime()),'collected',len(list(R.glob('done/*.json'))),'runs',flush=True)
if '--loop' in sys.argv:
 while time.time()<1794583500 and not (W/'STOP-COLLECT').exists():
  try:subprocess.run([PY,__file__,'--once'],check=True)
  except Exception as e:state('COLLECT ERROR '+repr(e));print(repr(e),flush=True)
  time.sleep(25)
else:once()
