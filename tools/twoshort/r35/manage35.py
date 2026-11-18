"""Round 35 twoshort collector (manage34 with the round 35 paths, 3 boxE workers, load guard 16, last start 15:30Z,
sel35 lists A (second seeds) then B (two seeds), a walk of every start before its claim, no legs). Round 34 text:
Round 34 twoshort collector on boxA (light python only). Override 8: deep kicks of class n mod 4 = 1.
Plan from sel35.json: list A (rows changed in round 34 a with only probed 900 s kicks since), then list B (fewer than
two unprobed 900 s kicks since the current geometry, board gap 1e-6 or more, largest first), then list C (the rest of
B, kept so no slot idles). Each row gets its missing seeds (two at most) as unprobed 900 s midm_scan lkick,kick jobs on
boxE (worker35.py, 2 workers). Before a row starts: one claim line naming its seeds, wait 5 s, re-read
handoff-r35.log and start only if no earlier claim or kick line of another lane names that n this round; skip a row
when a live r35 take of another lane holds n below the held bar (kick only the lowest live row). No new job while the
boxE 5-minute load is 13 or more. A running job stops (stopn/<n>) when another lane posts a row more than 1e-6
below the bar at n. Each loop checks both workers (pid file), restarts a dead one and frees its job. Finds: the
worker runs the full fq loop (zone_corner.py quench); here finesafe certifies, the take is written, and the find is
handed to backlog at once. No share gate: every start is a held row (override 2)."""
import csv, json, math, os, re, shutil, subprocess, sys, time, hashlib, glob, calendar
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r35';W=T/'work';LOG=B/'handoff-r35.log'
sys.path.insert(0,str(W))
import finesafe
HOST='boxE';RD='scratch/squares-twoshort';PYR='$SCRATCH/squares-base/venv/bin/python'
DL=int((W/'deadline').read_text());SDL=int((W/'search-deadline').read_text())
LAST_START=calendar.timegm(time.strptime('2026-11-17T15:30:00','%Y-%m-%dT%H:%M:%S'))
NWORK=3;SEEDS=(3541,7541);LOADMAX=16.0
HELD=B/'gather/round34-2026-11-17a.csv';DET=B/'gate/cand-round34-1117a/details.csv'
def now():return time.strftime('%FT%TZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(now()+' boxA '+s+'\n')
def handoff(s,to='all'):
 with open(LOG,'a') as f:f.write(now()+' twoshort -> %s: '%to+s+'\n')
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
def ssh(cmd,t=60):return subprocess.run(['ssh',HOST,cmd],capture_output=True,text=True,timeout=t)
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round35-briefs/bar35.tsv'),delimiter='\t')}
L0={int(r['n']):float(r['L']) for r in csv.DictReader(open(DET))}
RES=Path('results')
def held_src():
 src={}
 def k(f):return int(re.match(r'round(\d+)',Path(f).name)[1])
 for f in sorted(glob.glob(str(RES/'round*-best-*.tsv')),key=k):
  for r in csv.DictReader(open(f),delimiter='\t'):
   try:src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
   except (ValueError,TypeError):pass
 return src
SRC=held_src()
def takes():
 out={}
 for p in B.glob('take-*-r35/take.tsv'):
  if p.parent==T:continue
  lane=p.parent.name[5:-4]
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   out[(lane,n)]=dict(lane=lane,n=n,new=s)
 return out
def live():
 lv={}
 for (lane,n),r in takes().items():
  if r['new']<lv.get(n,(9,''))[0]:lv[n]=(r['new'],lane)
 return lv
def tsec(s):
 try:return calendar.timegm(time.strptime(s[:19],'%Y-%m-%dT%H:%M:%S'))
 except ValueError:return 0
def other_claims(n,before=None):
 """claim, kick or follow lines of other lanes in handoff-r35.log naming n (before a time if given)"""
 hits=[]
 if not LOG.exists():return hits
 for line in open(LOG,errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or not re.search(r'claim|kick|follow',line,re.I):continue
  if before and m[1][:19]>before[:19]:continue
  ns=set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line))|set(int(x) for x in re.findall(r'(?:held\w*|starts|take-[\w-]+-r3\d)/(\d+)[-.]',line))
  if n in ns:hits.append(line[:240].strip())
 return hits
def plan():
 d=json.load(open(W/'sel35.json'))
 # round 35 (lesson 6c): rows with one unprobed 900 s kick since their geometry first (their second seed), then rows
 # with none (two seeds), each by board gap; rows within 1e-7 of the board are left
 A=[o for o in d['A'] if o['gap']>=1e-7];Bl=[o for o in d['B'] if o['gap']>=1e-7]
 extra=[o for o in d.get('handed',[])]
 return [('A',o) for o in A]+[('B',o) for o in Bl]+[('F',o) for o in fresh_rows()]+[('H',o) for o in extra]+[('N',o) for o in near_rows()]
def fresh_rows():
 """Round 35, after lists A and B: class n mod 4 = 1 rows whose lowest live r35 row (any lane, ours included) is a fresh
 geometry, 1e-8 or more below bar35, certified 10 minutes ago or more, with fewer than two unprobed 900 s kicks claimed
 in handoff-r35 after it was written (lesson 6a: fresh geometry pays; 6c: two seeds per geometry)."""
 best={}
 for p in B.glob('take-*-r35/take.tsv'):
  lane=p.parent.name[5:-4]
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   f=p.parent/('%d.csv'%n)
   if s>=bar[n]-1e-8 or not f.exists():continue
   if s<best.get(n,(9,))[0]:best[n]=(s,lane,f)
 out=[]
 for n,(s,lane,f) in sorted(best.items(),key=lambda x:x[1][0]-bar[x[0]]):
  age=time.time()-f.stat().st_mtime
  if age<600:continue
  t0=time.strftime('%Y-%m-%dT%H:%M:%S',time.gmtime(f.stat().st_mtime))
  k=0
  for line in open(LOG,errors='replace'):
   m=re.match(r'(\S+) (\S+) ->',line)
   if not m or m[1][:19]<t0 or m[2]=='twoshort':continue
   if not re.search(r'claim',line,re.I) or not re.search(r'\b900\s*-?s\b|900s|seconds=900',line):continue
   if re.search(r'probe\s*=?\s*[1-9]|[1-9]\d*\s*s probe',line):continue
   if n not in set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line)):continue
   mm=re.search(r'seeds\s*\[([\d,\s]+)\]',line);k+=len(mm[1].split(',')) if mm else 1
  sh=sha(f)
  out.append(dict(n=n,gap=bar[n]-s,side=(s+1)*math.sqrt(n),score=s,lane=lane,take=str(f),sha=sh,key='F%d-%s'%(n,sh[:12]),
   unprobed=k,probed=0,since='%s %s'%(lane,t0),seeds_left=max(0,2-k)))
 return [o for o in out if o['seeds_left']>0]
def side_of(f):
 xs=[];ys=[];hs=[]
 for r in csv.DictReader(open(f)):
  a=float(r['angle']);h=(abs(math.cos(a))+abs(math.sin(a)))/2;x=float(r['x']);y=float(r['y'])
  xs+=[x-h,x+h];ys+=[y-h,y+h]
 return max(max(xs)-min(xs),max(ys)-min(ys)),len(xs)//2
_SIDE={}
def near_rows():
 """Round 35 list N (main's 12:54:03Z line to quench, the same pool): k123 near/ donors of any class, fresh geometry,
 side gap to bar35 under 2e-5, closest first, two unprobed 900 s seeds, skipped when any other lane's claim line
 names the donor sha (12 hex) or its file name."""
 logt=open(LOG,errors='replace').read() if LOG.exists() else ''
 global LVALL
 LVALL={n:v[0] for n,v in live().items()}
 if (T/'take.tsv').exists():
  for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):LVALL[int(r['n'])]=min(LVALL.get(int(r['n']),9),float(r['new']))
 out=[]
 for f in sorted((B/'take-k123-r35/near').glob('*.csv')):
  try:n=int(f.name.split('-')[0])
  except ValueError:continue
  if n not in bar:continue
  st=f.stat();k=(str(f),st.st_mtime)
  if k not in _SIDE:
   try:_SIDE[k]=side_of(f)
   except Exception:_SIDE[k]=(None,0)
  L,cnt=_SIDE[k]
  if L is None or cnt!=n:continue
  g=L-(bar[n]+1)*math.sqrt(n)
  if g>=2e-5:continue
  # main 13:24:46Z (rule 6e): kick only the lowest live row; skip a donor when any live r35 take (ours too) holds n lower
  if LVALL.get(n,9)<L/math.sqrt(n)-1:continue
  sh=sha(f)
  if re.search(r'(?m)^\S+ (?!twoshort )\S+ ->.*claim.*(%s|%s)'%(sh[:12],re.escape(f.name)),logt,re.I):continue
  out.append(dict(n=n,gap=-g/math.sqrt(n),side=L,score=L/math.sqrt(n)-1,lane='k123near',take=str(f),sha=sh,key='N%d-%s'%(n,sh[:12]),
   unprobed=0,probed=0,since='k123near 0000',seeds_left=2,near=True))
 out.sort(key=lambda o:o['side']-(bar[o['n']]+1)*math.sqrt(o['n']))
 return out
def pdb():
 p=W/'plan35.json'
 return json.load(open(p)) if p.exists() else {}
def save_pdb(d):(W/'plan35.json.tmp').write_text(json.dumps(d,indent=1));(W/'plan35.json.tmp').replace(W/'plan35.json')
def remote_status():
 r=ssh('cd %s && echo LOAD $(sysctl -n vm.loadavg); for f in jobs/*.json; do b=$(basename $f); if [ -d locks/$b ]; then [ -f done/$b ] || echo RUN $b; else echo PEND $b; fi; done; for w in w1 w2 w3; do p=$(cat pid-$w 2>/dev/null); if [ -n "$p" ] && kill -0 $p 2>/dev/null; then echo ALIVE $w $p; else echo DEAD $w; fi; echo CUR $w $(cat cur-$w 2>/dev/null); done'%RD)
 st=dict(load=None,run=[],pend=[],alive={},cur={})
 for l in r.stdout.splitlines():
  q=l.split()
  if not q:continue
  if q[0]=='LOAD':
   try:st['load']=float(q[3])
   except (IndexError,ValueError):pass
  elif q[0]=='RUN':st['run'].append(q[1])
  elif q[0]=='PEND':st['pend'].append(q[1])
  elif q[0]=='ALIVE':st['alive'][q[1]]=q[2]
  elif q[0]=='DEAD':st['alive'][q[1]]=None
  elif q[0]=='CUR':st['cur'][q[1]]=q[2] if len(q)>2 else ''
 return st
def liveness(st):
 if time.time()+120>SDL:return
 for w,pid in st['alive'].items():
  if pid:continue
  job=st['cur'].get(w,'')
  fix=''
  if job:
   r=ssh('cd %s && [ -f done/%s ] || { rm -rf locks/%s; echo freed; }'%(RD,job,job));fix=' freed job %s (%s)'%(job,r.stdout.strip() or 'done')
  ssh('cd %s && echo "" > cur-%s && (nohup nice -n 5 %s -I worker35.py %s > out-%s.txt 2>&1 &)'%(RD,w,PYR,w,w))
  state('RESTART worker %s on boxE (pid file dead)%s'%(w,fix))
def supersede(st):
 lv=live()
 for w,job in st['cur'].items():
  m=re.match(r'\d+-(?:deep35|control)-(\d+)',job or '')
  if not m:continue
  n=int(m[1]);ref=pdb().get('_score',{}).get(str(n),bar[n])
  if n in lv and lv[n][0]<ref-1e-6:
   r=ssh('cd %s && [ -f stopn/%d ] || { touch stopn/%d; echo new; }'%(RD,n,n))
   if 'new' in r.stdout:state('STOPN n=%d: %s posted %.13f, more than 1e-6 below the start score %.13f; job %s stopped (lesson 6e)'%(n,lv[n][1],lv[n][0],ref,job))
def make_start(n):
 rows=[r for r in csv.DictReader(open(HELD)) if r['n']==str(n)]
 f=W/'starts'/('%d-held34a.csv'%n)
 with open(f,'w',newline='') as g:
  cw=csv.writer(g);cw.writerow(['n','square_id','x','y','angle'])
  for r in rows:cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
 hh=(W/'held-sha.txt').read_text().strip()
 json.dump(dict(source='held n = %d of round 34 a (gather/round34-2026-11-17a.csv, sha256 %s)'%(n,hh),licence='own layout (held row)',n=n,sha256=sha(f),held_file=str(HELD),held_sha256=hh),open(str(f)+'.json','w'))
 return f,sha(f)
WALKER=Path('quench_walk.py')
def walk(f):
 """lesson 6i: walk every row before its kick (quench_walk.py, the held sidecar names the held row)"""
 r=subprocess.run([str(B/'venv/bin/python'),'-I',str(WALKER),str(f)],capture_output=True,text=True,timeout=600,cwd=str(WALKER.parent))
 try:d=json.loads(r.stdout.strip().splitlines()[-1])
 except (ValueError,IndexError):return False,'walker gave no verdict: '+(r.stderr or r.stdout)[-300:]
 return bool(d.get('clean')),'clean %s, hits %s, helds %s, files %s'%(d.get('clean'),d.get('hits'),d.get('helds'),d.get('files'))
def queue_next(st):
 if time.time()>LAST_START:return 0
 if st['load'] is not None and st['load']>=LOADMAX:state('WAIT boxE 5-minute load %.2f (no new kick at %.0f or more)'%(st['load'],LOADMAX));return 0
 db=pdb();lv=live();mine=set(int(r['n']) for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')) if (T/'take.tsv').exists() else set()
 for lst,o in plan():
  n=o['n'];K=o.get('key',str(n));e=db.get(K,dict(status='new',sent=[]))
  if e['status'] in ('skip','done'):continue
  seeds=list(SEEDS[:o['seeds_left']])
  left=[s for s in seeds if s not in e['sent']]
  if not left:e['status']='done';db[K]=e;save_pdb(db);continue
  def skip(why):
   e['status']='skip';e['why']=why;db[K]=e;save_pdb(db);state('SKIP deep n=%d (list %s): %s'%(n,lst,why[:300]))
  if lst in ('F','N'):
   if queue_fresh(o,e,K,db,seeds,left):return 1
   continue
  if n in lv and lv[n][0]<bar[n]-1e-12:skip('a live r35 row of %s holds n below the held bar (%.13f); kick only the lowest live row'%(lv[n][1],lv[n][0]));continue
  if n in mine:skip('our own r35 row holds n');continue
  if e['status']=='new':
   cl=other_claims(n)
   if cl:skip('claimed in handoff-r35: '+cl[0]);continue
   f,h=make_start(n)
   ok,wtxt=walk(f)
   state('WALK n=%d %s: %s'%(n,f.name,wtxt[:400]))
   if not ok:skip('the walk refused the start: '+wtxt);continue
   if abs(L0[n]-o['side'])>1e-9:state('NOTE n=%d details L %.12f vs sel side %.12f'%(n,L0[n],o['side']))
   hs=SRC.get(n,('','',''))
   if re.search(r'prvsiyan/squares-verified-best-of-1105|joegun-boxed',hs[1]+hs[2]) and 'own' not in hs[1]:skip('source names an out file');continue
   t=now()
   handoff('claim: 900 s midm_scan lkick,kick (seeds %s, probe 0 s, boxE; full fq loop on each find; finds go to backlog at once, no legs) of n=%d, start bytes sha256 %s, the held round 34 a row (deep-kick class n mod 4 = 1, list %s: board gap %.2e of score, %d unprobed and %d probed 900 s kicks since its current geometry (%s)), %s'%(' and '.join(map(str,seeds)),n,h,lst,o['gap'],o['unprobed'],o['probed'],o['since'],f))
   time.sleep(5)
   cl=other_claims(n,before=now())
   if cl:skip('an earlier or same-time claim in handoff-r35 after our claim at %s: %s'%(t,cl[0]));handoff('releases its claim of n=%d (another lane claimed it first)'%n);continue
   e.update(status='claimed',claim=t,start=str(f),sha=h,list=lst,gap=o['gap']);db[K]=e;save_pdb(db)
   subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  seed=left[0];f=Path(e['start']);h=e['sha']
  tag='deep35-%d-%s'%(n,h[:8]);hs=SRC.get(n,('','',''))
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=900,probe=0,leg_seconds=150,leg_probe=120,bar=bar[n],root_side=L0[n],legs=0,noleg=True,priority=10,chain=[str(f)],held=True,kind_text='900 s midm_scan lkick,kick (no probe)',
         follow=dict(lane='held round 34 a',csv=str(HELD),score=bar[n],source='results/%s row n=%d: %s'%(hs[0],n,hs[1][:1200]),licence=(hs[2] or 'ours')+'; the held round 34 a row (a row of a file we submitted)'))
  jf=W/'jobsent'/('030-%s-%d.json'%(tag,seed));jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  e['sent'].append(seed);e['status']='claimed' if len(e['sent'])<len(seeds) else 'done';db[K]=e;db.setdefault('_score',{})[str(n)]=bar[n];save_pdb(db)
  state('QUEUE %s seed %d n=%d (list %s, seed %d of %d) held round 34 a side %.12f gap %.2e; boxE midm_scan lkick,kick 900 s no probe; log %s/runs/%s-s%d; search deadline 16:05Z, deadline 16:25Z'%(tag,seed,n,lst,len(e['sent']),len(seeds),L0[n],o['gap'],RD,tag,seed))
  return 1
 return 0
def queue_fresh(o,e,K,db,seeds,left):
 n=o['n']
 def skip(why):
  e['status']='skip';e['why']=why;db[K]=e;save_pdb(db);state('SKIP fresh n=%d %s: %s'%(n,K,why[:300]))
 if e['status']=='new':
  if o.get('near'):cl=[l for l in other_claims(n) if o['sha'][:12] in l or Path(o['take']).name in l]
  else:cl=[l for l in other_claims(n) if l[:19]>=o['since'].split(' ')[1][:19] and re.search(r'\b900\s*-?s\b|900s',l)]
  if cl:skip('a claim in handoff-r35 names this start: '+cl[0]);return 0
  ok,wtxt=walk(Path(o['take']))
  state('WALK fresh n=%d %s: %s'%(n,o['take'],wtxt[:400]))
  ruled=[l.split('\t') for l in (W/'ruled.txt').read_text().splitlines() if l.strip()] if (W/'ruled.txt').exists() else []
  rr=[r for r in ruled if r[0]==o['take'] and r[1]==o['sha']]
  if not ok and rr:state('WALK OVERRULED n=%d %s: %s'%(n,o['take'],rr[0][2][:300]));ok=True
  if not ok:skip('the walk refused the fresh row: '+wtxt);return 0
  f=W/'starts'/('%d-fresh-%s-%s.csv'%(n,o['lane'],o['sha'][:12]));shutil.copy2(o['take'],f)
  if sha(f)!=o['sha']:skip('the take file changed while it was copied');return 0
  json.dump(dict(source='byte copy of %s (sha256 %s), the lowest live r35 row of n = %d (lane %s), walked clean with quench_walk.py'%(o['take'],o['sha'],n,o['lane']),licence='see the take.tsv row of that file',n=n,sha256=o['sha'],copy_of=o['take']),open(str(f)+'.json','w'))
  t=now()
  handoff('claim: 900 s midm_scan lkick,kick (seeds %s, probe 0 s, boxE; full fq loop on each find; finds go to backlog at once, no legs) of n=%d, start bytes sha256 %s = %s, %s, %s'%(' and '.join(map(str,seeds)),n,o['sha'],o['take'],('an uncounted k123 near/ donor (fresh geometry, side %.3e above bar35; the pool of main 12:54:03Z)'%(-o['gap']*math.sqrt(n))) if o.get('near') else ('the lowest live r35 row of n (fresh geometry, %.3e below bar35, %d unprobed 900 s kicks claimed since it was written)'%(o['gap'],o['unprobed'])),f))
  time.sleep(5)
  if o.get('near'):cl=[l for l in other_claims(n,before=now()) if o['sha'][:12] in l or Path(o['take']).name in l]
  else:cl=[l for l in other_claims(n,before=now()) if l[:19]>=o['since'].split(' ')[1][:19] and re.search(r'\b900\s*-?s\b|900s',l)]
  if cl:skip('an earlier or same-time 900 s claim: '+cl[0]);handoff('releases its claim of n=%d (another lane claimed it first)'%n);return 0
  e.update(status='claimed',claim=t,start=str(f),sha=o['sha'],list='N' if o.get('near') else 'F',gap=o['gap'],take=o['take'],score=o['score'],near=bool(o.get('near')));db[K]=e;save_pdb(db)
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  ssh('cd %s && rm -f stopn/%d'%(RD,n))
 seed=left[0];f=Path(e['start']);h=e['sha']
 tag='deep35-%d-%s'%(n,h[:8])
 if e.get('near'):
  try:sc=json.load(open(e['take']+'.json'))
  except (OSError,ValueError):sc={}
  tk=dict(source='k123 near/ sidecar %s.json: %s'%(e['take'],sc.get('source','')),licence=sc.get('licence','see the sidecar of the donor'))
 else:tk={int(r['n']):r for r in csv.DictReader(open(Path(e['take']).parent/'take.tsv'),delimiter='\t')}.get(n,{})
 j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=900,probe=0,leg_seconds=150,leg_probe=120,bar=bar[n],root_side=(e['score']+1)*math.sqrt(n),legs=0,noleg=True,priority=10,chain=[e['take'],str(f)],held=False,kind_text='900 s midm_scan lkick,kick (no probe) of '+('a k123 near/ donor' if o.get('near') else 'a fresh r35 row'),
        follow=dict(lane=Path(e['take']).parent.name,csv=e['take'],score=e['score'],source=('%s'%tk.get('source','')[:1500]) if e.get('near') else '%s row n=%d: %s'%(str(Path(e['take']).parent/'take.tsv'),n,tk.get('source','')[:1200]),licence=tk.get('licence','')))
 jf=W/'jobsent'/('030-%s-%d.json'%(tag,seed));jf.write_text(json.dumps(j,indent=1))
 subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
 e['sent'].append(seed);e['status']='claimed' if len(e['sent'])<len(seeds) else 'done';db[K]=e;db.setdefault('_score',{})[str(n)]=min(e['score'],bar[n],live().get(n,(9,''))[0]);save_pdb(db)
 state('QUEUE %s seed %d n=%d (list F, seed %d of %d) fresh row %s score %.13f (%.3e below bar35); boxE midm_scan lkick,kick 900 s no probe; log %s/runs/%s-s%d'%(tag,seed,n,len(e['sent']),len(seeds),e['take'],e['score'],e['gap'],RD,tag,seed))
 return 1
def mirror():
 subprocess.run(['rsync','-a','--exclude','tmp','--exclude','lane','--exclude','ext','%s:%s/'%(HOST,RD),str(W/'boxE35')+'/'],timeout=300)
def certify_all():
 seen=json.load(open(W/'cert-seen.json')) if (W/'cert-seen.json').exists() else {}
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')} if (T/'take.tsv').exists() else {}
 changed=False;lv=live()
 for p in sorted((W/'boxE35/done').glob('*.json')):
  j=json.load(open(p));q=j.get('quench')
  if p.name in seen:continue
  if j.get('control'):
   seen[p.name]=dict(control=True);json.dump(seen,open(W/'cert-seen.json','w'))
   state('CONTROL %s n=%d start %s best %s moved %s tries %s %s'%(j['tag'],j['n'],j.get('start_side'),j.get('best'),(j['start_side']-j['best']) if j.get('best') is not None and j.get('start_side') is not None else None,j.get('tries'),j.get('why')));continue
  if not q:
   seen[p.name]=dict(moved=(j.get('start_side') or 0)-(j.get('best') or 0));json.dump(seen,open(W/'cert-seen.json','w'))
   state('DONE %s seed %s n=%d moved %.3e of side in %s tries (%s, %s s), no find near the bar'%(j['tag'],j['seed'],j['n'],(j.get('start_side') or 0)-(j.get('best') or 0),j.get('tries'),j.get('why'),j.get('seconds_used')));continue
  if q.get('rc')!=0:
   seen[p.name]=dict(qrc=q.get('rc'));json.dump(seen,open(W/'cert-seen.json','w'));state('QUENCH FAIL %s rc %s'%(p.name,q.get('rc')));continue
  n=j['n'];qf=W/'boxE35/q'/('%s-s%d'%(j['tag'],j['seed']))/('%d-best.csv'%n)
  if not qf.exists():continue
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qf))]
  _,fr,s,e=finesafe.work((n,rows))
  seen[p.name]=dict(score=s,e=e,bar=bar[n]);json.dump(seen,open(W/'cert-seen.json','w'))
  lvn=min(lv.get(n,(9,''))[0],bar[n])
  state('CERTCHECK %s n=%d finesafe %.13f bar %.13f (%+.3e) live %.13f'%(p.name,n,s if fr else float('nan'),bar[n],(s-bar[n]) if fr else 0,lvn))
  if fr is None or len(rows)!=n:continue
  if s>=bar[n]-1e-10 or s>=lvn-1e-10:
   if s<bar[n]+5e-7:
    nf=T/'near'/('%d-twoshort35-%s-s%d.csv'%(n,j['tag'].split('-')[-1],j['seed']))
    with open(nf,'w',newline='') as g:
     cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
   continue
  if n in cur and s>=float(cur[n]['new'])-1e-13:continue   # 02:05: a second seed at the same point re-posted 753
  dst=T/('%d.csv'%n);tmp=T/('%d.csv.tmp'%n)
  with open(tmp,'w',newline='') as g:
   cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  tmp.replace(dst)
  loc=lambda x:str(W/'boxE35'/x.replace(str(Path.home())+'/'+RD+'/','')) if not x.startswith('/Volumes') else x
  chain=' -> '.join('%s (sha256 %s)'%(loc(c),sha(loc(c)) if os.path.exists(loc(c)) else '?') for c in j.get('chain',[j['start']]))
  bf=loc(j.get('best_file') or '');bfs=sha(bf) if os.path.exists(bf) else '?'
  fo=j.get('follow',{})
  tooltxt='midm_scan.py --modes lkick,kick (%d s, %s, seed %d, leg %d)'%(j['seconds'],'no probe' if not j.get('probe') else 'probe %s s'%j.get('probe'),j['seed'],j.get('legs',0))
  source=('twoshort round 35: '+tooltxt+' on boxE, the held round 34 a row of n=%d (gather/round34-2026-11-17a.csv; score %.13f, start snapshot sha256 %s): %s; raw best %s (sha256 %s); '
   'the full fq loop (zone_corner.py quench: default then polish flags, up to 3 passes) from its floatsafe-certified copy; finesafe (pinned sha256 e35eac45cc52); held-row descendant, override 2, no share gate. '
   'Start row source: %s')%(n,fo.get('score',0),j['start_sha256'],chain,bf,bfs,fo.get('source','')[:1200])
  if j.get('held') is False:
   source=('twoshort round 35: '+tooltxt+' on boxE, the fresh r35 row %s of n=%d (score %.13f, start byte copy sha256 %s, walked clean with quench_walk.py before the claim): %s; raw best %s (sha256 %s); '
    'the full fq loop (zone_corner.py quench: default then polish flags, up to 3 passes) from its floatsafe-certified copy; finesafe (pinned sha256 e35eac45cc52). '
    'Start row source: %s')%(fo.get('csv'),n,fo.get('score',0),j['start_sha256'],chain,bf,bfs,fo.get('source','')[:1200])
  lic=(fo.get('licence') or 'own layout (held row)')
  cur[n]=dict(n=n,held=bar[n],new=s,gain=bar[n]-s,source=source,licence=lic)
  changed=True;writetake(cur)
  handoff('certified n=%d gain=%.4e on bar35 (score %.13f, %.3e below the live r35 rows), %s of %s (seed %d, leg %d), full fq loop from the certified file, %s, %s'%(n,bar[n]-s,s,lvn-s,j.get('kind_text'),'the held round 34 a row' if j.get('held') is not False else fo.get('csv'),j['seed'],j.get('legs',0),'held-row descendant (no share gate)' if j.get('held') is not False else 'start walked clean before the claim',dst))
  handoff('hands off take-twoshort-r35/%d.csv (sha256 %s, score %.13f) for your follow at once (override 8); our worker queues no legs'%(n,sha(dst),s),to='backlog')
  state('CERT n=%d gain %.4g against bar35, %.4g below the live r35 rows, %s; handed to backlog'%(n,bar[n]-s,lvn-s,dst))
def writetake(cur):
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
 (T/'take.tsv.tmp').replace(T/'take.tsv')
def prune():
 if not (T/'take.tsv').exists():return
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')};lv=live();drop=[n for n in cur if lv.get(n,(9,''))[0]<=float(cur[n]['new'])]
 if not drop:return
 for n in drop:
  shutil.copy2(T/('%d.csv'%n),T/'near'/('%d-overtaken-twoshort35.csv'%n));state('PRUNE n=%d: live r35 row of %s %.13f at or below ours %.13f (csv kept in place)'%(n,lv[n][1],lv[n][0],float(cur[n]['new'])));cur.pop(n)
 writetake(cur)
def inbox():
 seen=set((W/'inbox-seen.txt').read_text().splitlines()) if (W/'inbox-seen.txt').exists() else set();new=[]
 if not LOG.exists():return
 for line in open(LOG,errors='replace'):
  if re.search(r'-> [\w, -]*twoshort|take-twoshort-r35|main -> all|WITHDRAW',line) and not re.match(r'\S+ twoshort ->',line) and line.strip() not in seen:new.append(line.strip())
 for l in new:state('INBOX '+l[:400])
 if new:
  with open(W/'inbox-seen.txt','a') as f:f.write(''.join(l+'\n' for l in new))
if __name__=='__main__':
 if sys.argv[1:]==['once']:
  mirror();certify_all();sys.exit()
 (W/'collector-pid').write_text(str(os.getpid()))
 state('COLLECTOR manage35 start PID %d'%os.getpid())
 while time.time()<DL+300 and not (W/'STOP-COLLECT').exists():
  try:
   st=remote_status()
   liveness(st);supersede(st)
   if time.time()<SDL-900:
    # keep one job pending so no worker idles
    free=NWORK-len([x for x in st['run'] if not x.startswith('000-')])
    want=max(0,free+1-len(st['pend']))
    for _ in range(min(want,2)):
     if not queue_next(st):break
   mirror();certify_all();prune();inbox()
  except Exception as ex:state('COLLECTOR ERROR '+repr(ex)[:300])
  time.sleep(60)
 state('COLLECTOR exit')
