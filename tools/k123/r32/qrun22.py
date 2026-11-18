"""Run one shared join queue, stopping every child at the deadline."""
import os,sys,time,pathlib,subprocess,re,json,math,hashlib
R=pathlib.Path.home()/'scratch/squares-k123';os.chdir(R)
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
sys.path.insert(0,str(R/'lane'))
import methods_lp as mlp, k123_join as kj, family_step as fs
PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(pathlib.Path.home()/'scratch/squares-base/fq')
slot=sys.argv[1];mechanism='loosen1.005-r30' if slot=='j22d' and (R/'enable-wide30').exists() else None;loosen=1.005 if mechanism else 1.001
worker='j22w' if mechanism else slot
if slot=='j22c' and (R/'enable-wide31').exists():
 mechanism='loosen1.010-r31';loosen=1.010;worker='j22v'
if slot=='j22a' and (R/'enable-mid00332').exists():
 mechanism='loosen1.003-r32';loosen=1.003;worker='j22u'
out=R/'out'/worker;out.mkdir(parents=True,exist_ok=True);(R/'claims').mkdir(exist_ok=True)
cache={};jobdeadline=math.inf
history={tuple(z) for z in json.load(open(R/'completed-geometries26.json'))}
def run(args,log):
 left=min(float((R/'deadline').read_text()),jobdeadline)-time.time()
 if left<=0:return -1
 with open(log,'a') as h:
  p=subprocess.Popen(args,stdout=h,stderr=h,start_new_session=True)
  try:return p.wait(timeout=min(left,300))
  except subprocess.TimeoutExpired:
   import signal
   os.killpg(p.pid,signal.SIGKILL);p.wait();return -2
while time.time()<float((R/'search-deadline').read_text()):
 if worker=='j22u':
  ledger=out/'done.jsonl';completed32=[json.loads(l) for l in ledger.read_text().splitlines()] if ledger.exists() else []
  if len(completed32)>=80:
   (R/'mid00332-assessment.json').write_text(json.dumps({'attempts':len(completed32),'raws':sum(bool(r.get('raw')) for r in completed32),'seconds_policy':'one existing slot, 80 attempts maximum'}))
   (R/'enable-mid00332').unlink(missing_ok=True)
   os.execv(PY,[PY,'-I',str(R/'qrun22.py'),slot])
 found=False
 refused=json.load(open(R/'refused-inputs26.json')) if (R/'refused-inputs26.json').exists() else {}
 queue=(R/'queue.tsv').read_text().splitlines()
 queue=[l for l in queue if len(l.split('\t'))>=8]
 hot=set((R/'priority-pools.txt').read_text().split()) if (R/'priority-pools.txt').exists() else set()
 finished=json.load(open(R/'prior-trials.json')) if (R/'prior-trials.json').exists() else {}
 finished={int(n):v for n,v in finished.items()}
 for fp in (R/'out').glob('j22*/done.jsonl'):
  for line in fp.read_text().splitlines():
   try:
    nn=json.loads(line)['n'];finished[nn]=finished.get(nn,0)+1
   except (ValueError,KeyError):pass
 first={}
 for line in queue:
  f=line.split('\t');first.setdefault((f[7],f[0]),f[1])
 def priority(line):
  f=line.split('\t');pool=f[7];fresh=pool.startswith(('fresh','licensed','rebuild'))
  if worker=='j22b':return (not fresh,finished.get(int(f[0]),0),-float(f[6]),-float(f[5]))
  return (not fresh,finished.get(int(f[0]),0),-int(''.join(c for c in pool if c.isdigit()) or '0') if fresh else 0,-float(f[5]))
 for l in sorted(queue,key=priority):
  w=l.split('\t');n=int(w[0]);tag=w[1];pool=w[7];key=f'{pool}-{n}-{tag}'
  mm=re.match(r'(\d+)r?-(\d+)r?-j',tag)
  if mm and set(mm.groups())&set(refused.get(pool,[])):continue
  try:
   meta=json.load(open(R/f'sources-{pool}.json'))
   if any(meta[nn].get('seed_share_gate')!='v6' for nn in mm.groups()):continue
   roots=[(nn,meta[nn]['sha256_geometry'],meta[nn].get('ancestry_sha256','')) for nn in mm.groups()]
   if tuple([tag]+[z[1] for z in roots]+([mechanism] if mechanism else [])) in history:continue
   signature=hashlib.sha256(json.dumps([tag,w[3],roots]+(['reader-fallback25'] if pool.startswith('rebuildfix') else [])+([mechanism] if mechanism else []),sort_keys=True).encode()).hexdigest()
   keyclaim='input-'+signature
  except (OSError,KeyError,ValueError):keyclaim=key
  try:(R/'claims'/keyclaim).mkdir()
  except FileExistsError:continue
  found=True;jobdeadline=time.time()+180;d=out/key;d.mkdir(exist_ok=True)
  record=dict(n=n,tag=tag,pool=pool,worker=worker,bar=float(w[4]),raw=0,**({'mechanism':mechanism,'loosen':loosen} if mechanism else {}))
  try:
   bar={int(x.split('\t')[0]):float(x.split('\t')[1]) for x in (R/'bars.tsv').read_text().splitlines()}[n]
   q=re.fullmatch(r'(\d+)(r?)-(\d+)(r?)-j(\d+)-(\d+)-s(-?\d+)',tag)
   nx,rx,ny,ry,j1,j2,s=q.groups(); nx,ny=int(nx),int(ny)
   if pool not in cache:cache[pool]=mlp.load(str(R/f'{pool}.csv'),None)
   ALL=cache[pool]
   # load() with an empty set may select no rows.
   if nx not in ALL or ny not in ALL:ALL.update(mlp.load(str(R/f'{pool}.csv'),{nx,ny}))
   lays=[]
   for nn,rr in [(nx,rx),(ny,ry)]:
    Q,L=kj.norm(ALL[nn]);lays.append(kj.Lay(nn,kj.rot(Q,L) if rr else Q,L,str(nn)+rr))
   F,L=kj.join(*lays,int(j1),int(j2),int(s),max(0.0,lays[1].f-lays[0].f)+min((0,.01,.02,.04,.07,.1,.13,.16,.2,.25,.3),key=lambda d:abs(d+max(0.0,lays[1].f-lays[0].f)-float(w[3]))))
   record=dict(n=n,tag=tag,pool=pool,bar=bar,worker=worker,time=time.strftime('%H:%M:%SZ',time.gmtime()),base=float(w[5]),start_count=len(F),start_gap=float(mlp.min_gap(F)),**({'mechanism':mechanism,'loosen':loosen} if mechanism else {}))
   if len(F)!=n:
    record['error']='rebuilt count differs'
   else:
    fs.write_rows(str(d/'start.csv'),n,F)
    code=run([PY,'-I','lane/k123_turn.py',str(d/'start.csv'),str(n),str(d),FQ,'--turns=0','--modes','self','--loosen',str(loosen),'--bar',str(bar),'--keep'],d/'turn.log')
    record['code']=code
    tsv=d/f'turn-{n}.tsv'
    rows=[x for x in tsv.read_text().splitlines() if not x.startswith('#')] if tsv.exists() else []
    if rows:
     try:record['side']=float(rows[-1].split('\t')[3])
     except ValueError:pass
    side=record.get('side',math.inf);dv=side-bar
    if code==0 and dv<.008 and (dv< -1e-7 or dv>2e-6):
     record['fq2code']=run([PY,'-I','fq2.py',str(d/f'turn/{n}-self-+0.000-{loosen:.3f}.csv'),str(n),str(d),FQ,str(bar)],d/'fq2.log')
    record['raw']=len(list((d/'raw').glob('*.csv')))
  except Exception as e:
   record['error']=type(e).__name__+': '+str(e)
   record['raw']=len(list((d/'raw').glob('*.csv')))
  with open(out/'done.jsonl','a') as h:h.write(json.dumps(record)+'\n')
  if time.time()>=float((R/'deadline').read_text()):break
  break  # Refresh the queue after each candidate so fresh scans run first.
 if '--once' in sys.argv:break
 if not found:time.sleep(10)
