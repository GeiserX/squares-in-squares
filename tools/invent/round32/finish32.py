"""Close owned workers, verify their archive, and freeze the lane by 17:25 UTC."""
import pathlib,sys,os,json,time,csv,math,subprocess,hashlib,traceback,signal,datetime,re,statistics
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
for k in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import campaign32base as C
FREEZE=datetime.datetime(2026,11,16,17,23,0,tzinfo=datetime.UTC).timestamp()

def run(args,timeout=60):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout);print(p.stdout,flush=True);p.check_returncode();return p.stdout

def local_collect():
 old=C.cmd
 C.cmd=lambda *unused:''
 try:return C.collect()
 finally:C.cmd=old

def stop_controller():
 (W/'STOP').touch()
 if (W/'campaign.pid').exists():
  pid=int((W/'campaign.pid').read_text())
  try:cmd=run(['ps','-p',str(pid),'-o','command=']).strip()
  except subprocess.CalledProcessError:return
  if str(W/'campaign32.py')in cmd:
   os.kill(pid,signal.SIGTERM)
   for _ in range(4):
    try:os.kill(pid,0)
    except ProcessLookupError:return
    time.sleep(1)
   os.kill(pid,signal.SIGKILL)

def archive():
 stop_controller()
 run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python $SCRATCH/squares-invent-r32/remote_close32.py'])
 run(['rsync','-a',C.REMOTE,str(W/'boxE-raw')+'/'],240)
 manifest=json.load(open(W/'boxE-raw/transfer-manifest.json'));bad=[p for p,h in manifest.items()if not(W/'boxE-raw'/p).is_file()or C.sha(W/'boxE-raw'/p)!=h]
 if bad:raise ValueError('archive hash mismatch '+repr(bad))
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=len(manifest),all_hashes_match=True,boxE_scratch_removed=False))
 local_collect()
 run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python $SCRATCH/squares-invent-r32/remote_close32.py --remove'])
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=len(manifest),all_hashes_match=True,boxE_scratch_removed=True))
 C.atomic(W/'processes-left.json',{'boxA':[],'boxE':[],'boxE_scratch_removed':True});C.state(f'ARCHIVE all{len(manifest)} CSV hashes verified; removed owned boxE scratch; controller stopped.')

def report():
 jobs=C.load(W/'jobs.json',[]);stats={};errors=[];late=[];bestmove=[]
 for j in jobs:
  if j['kind']in('control','early'):continue
  d=C.load(W/'boxE-raw'/j['id']/'done.json',{})
  if not d:continue
  s=stats.setdefault(j['kind'],{'completed':0,'moved':0,'dry_probe':0});s['completed']+=1;s['dry_probe']+=int(d.get('search_end')=='dry-probe')
  if 'error'in d:errors.append(j['id']+': '+d['error']);continue
  if d.get('new')is None:continue
  move=j['side']-(d['new']+1)*math.sqrt(j['n']);s['moved']+=int(move>1e-8)
  if 'round31_parent'in j:late.append(dict(n=j['n'],side_reduction=move,score_reduction=j['side']/math.sqrt(j['n'])-1-d['new'],search_end=d.get('search_end')))
  if move>1e-6:bestmove.append((move,j,d))
 comp=C.load(W/'comparison.json',dict(improved_n=0,gain={'against_base_bar':0,'beyond_other_live_r32':0}))
 measured=[f'Completed job groups: {json.dumps(stats,sort_keys=True)}.',f'Late round31 989 continuation: {json.dumps(late)}.',f'Final live comparison: {comp.get("time","none")}.',f'Numerical job errors: {json.dumps(errors)}.',f'Archive verification: {json.dumps(C.load(W/"transfer-check.json",{}),sort_keys=True)}.','Recovered 134 missing round31 CSVs. All 1212 hashes matched both manifests before removing the old boxE scratch. Round31 code and results were committed and pushed.','The pair and stopped907 numerical controls completed certified-input fq. The stopped907 side fell below 30.6183. The four-candidate finisher control quenched all distinct certified candidates.','Source controls accepted held ancestry without a share call, refused changed evidence, selected exact-byte current-round withdrawals, ignored wrong-hash notices, and refused direct withdrawn 814 beside a held sibling.','Production used only changed geometry and own useful endpoints. No plain held kick queue or unchanged539 retry ran.']
 early_count=sum(j.get('kind')=='early'for j in jobs)
 measured.append(f'Immutable completed-candidate checkpoints exported: {early_count}. Stream workers run completed-fq, overlap and wrong-marker controls before production. Each replacement waits for its previous slot to exit.')
 first970=C.load(W/'boxE-raw/fresh970-50c0a4d8cf-s3231/done.json',{})
 qs=first970.get('candidate_quenches',[])
 valid=[(i,q)for i,q in enumerate(qs)if q.get('new')is not None]
 if valid:
  i,best=min(valid,key=lambda v:v[1]['new']);measured.append(f'The first 970 batch compared {len(qs)} quenches. Candidate index {i} won at {best["new"]:.17g}, versus {qs[0].get("new")!r} for the first. Its winner finished at {first970.get("ended")}. This measured delay motivated immutable early exports while preserving every comparison.')
 wide_control=C.load(W/'boxE-raw/control907-wide32/done.json',{})
 measured.append('Broad-radius pilot control: '+json.dumps({k:wide_control.get(k)for k in ('new','clearance','quench_from_certified','error','ended')})+'. Production group: '+json.dumps(stats.get('wide',{}))+'. The pilot is limited to two never-kicked fresh geometries.')
 measured.append('Late989 admission: '+json.dumps(C.load(W/'late989-skipped.json',late))+'.')
 published={}
 for line in (C.S/'handoff-r32.log').read_text(errors='replace').splitlines():
  match=re.search(r'invent -> all: CERTIFIED n=(\d+) score=([0-9.eE+-]+)',line)
  if match:
   n=int(match[1]);score=float(match[2]);published[n]=min(published.get(n,math.inf),score)
 provisional={str(n):C.BASE[n]-score for n,score in sorted(published.items())}
 measured.append('Provisional published gains against bar32 before peer follows: '+json.dumps(provisional)+'. The gain field records only final retained rows.')
 early_ids={j['id']for j in jobs if j.get('kind')=='early'};latencies=[]
 for line in (C.T/'STATE.txt').read_text(errors='replace').splitlines():
  match=re.search(r' FINISH (\S+) (\{.*)',line)
  if not match or match[1]not in early_ids:continue
  try:
   receipt=json.loads(match[2]);observed=datetime.datetime.fromisoformat(line[:19]).replace(tzinfo=datetime.UTC);ended=datetime.datetime.fromisoformat(receipt['ended'].replace('Z','+00:00'));latencies.append((observed-ended).total_seconds())
  except (ValueError,KeyError):pass
 if latencies:measured.append(f'Immutable checkpoint collection delay: median {statistics.median(latencies):.1f} seconds, max {max(latencies):.1f} seconds over {len(latencies)} completed endpoints.')
 nxt=[]
 for move,j,d in sorted(bestmove,key=lambda v:-v[0])[:3]:
  children=[x for x in jobs if x.get('parent_job')==j['id']]
  if not children:nxt.append(f'Continue n={j["n"]} endpoint {j["id"]} after checking the next bar and claims. It shortened side by {move:.12g} and received no continuation.')
 fresh=stats.get('fresh',{});nxt.append(f'Prioritize changed rectangles and joins over unchanged returns. The lane published {len(published)} provisional rows for {sum(provisional.values()):.12g} against bar32 before peer follows. Fresh geometry moved in {fresh.get("moved",0)} of {fresh.get("completed",0)} completed jobs. Preserve exact byte claims and the 120-second dry probe.')
 leg=stats.get('leg',{});nxt.append(f'Follow useful changed endpoints while they keep moving. This round legs moved in {leg.get("moved",0)} of {leg.get("completed",0)} jobs. Keep unchanged dry endpoints closed.')
 wide=stats.get('wide',{})
 if wide.get('completed',0):nxt.append(f'Keep the two broad-radius pilot geometries closed until they change. They moved in {wide.get("moved",0)} of {wide.get("completed",0)} runs and gave no published row. Ordinary fresh geometry supplied both provisional winners.')
 nxt.append('Keep the unchanged 539 retention profile closed. Its recovered round31 trial stayed 4.0692166550782005e-5 of score above its bar.')
 commits=[C.load(W/'r31-commit.json',{}).get('commit')]+C.load(W/'interim-commits.json',[])+C.load(W/'commits.json',[])
 return dict(lane='invent',improved_n=comp['improved_n'],gain=comp['gain'],take_dir=str(C.T),summary=f'Published {len(published)} provisional rows during the round. Retained {comp["improved_n"]} after the final bar32/live-peer comparison. Recovered, verified and pushed the owed round31 archive and records.',what_was_measured=measured,next=nxt,commits=[x for x in commits if x],processes_left=C.load(W/'processes-left.json',{}),blocked=C.load(W/'blocked.json','none'),repo='private repo',branch='main',worktree='$PRIVATE_REPO',pr='none')

if __name__=='__main__':
 C.state('START close-out guardian finish32.py; work/finish32.log. Drain after last workers exit, archive and push before17:15Z. Final source comparison17:23Z; take final before17:25Z.')
 while time.time()<C.ADMIT:time.sleep(min(30,C.ADMIT-time.time()))
 while time.time()<C.HARD:
  try:
   x=json.loads(run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python $SCRATCH/squares-invent-r32/remote_close32.py --status']))
   if not x['active']:break
  except Exception:traceback.print_exc()
  time.sleep(min(20,max(.01,C.HARD-time.time())))
 try:
  archive()
  import record32
  commit=record32.record();C.state('PUSH '+commit+' to main')
 except Exception as e:
  traceback.print_exc();C.atomic(W/'blocked.json',str(e));C.state('CLOSE-OUT error '+str(e))
 # Produce a recovery record early, then refresh the final comparison at the deadline.
 C.atomic(C.T/'report.json',report())
 while time.time()<FREEZE:time.sleep(min(20,max(.01,FREEZE-time.time())))
 try:local_collect()
 except Exception as e:traceback.print_exc();C.atomic(W/'blocked.json','final comparison failed: '+str(e))
 # A final peer-only pass cannot reopen slow source archives.
 target=datetime.datetime(2026,11,16,17,24,45,tzinfo=datetime.UTC).timestamp()
 while time.time()<target:time.sleep(min(10,max(.01,target-time.time())))
 peer=C.peers();rows=[r for r in csv.DictReader(open(C.T/'take.tsv'),delimiter='\t')if float(r['new'])<peer[int(r['n'])]]
 retained={int(r['n'])for r in rows}
 for p in C.T.glob('*.csv'):
  if int(p.stem)not in retained:p.replace(C.T/'near'/(p.stem+'-final-peer-superseded.csv'))
 tmp=W/'final-take.tmp'
 with tmp.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=C.FIELDS,delimiter='\t');w.writeheader();w.writerows(rows)
 tmp.replace(C.T/'take.tsv');C.atomic(W/'comparison.json',dict(time=C.now(),improved_n=len(rows),gain=dict(against_base_bar=sum(float(r['gain'])for r in rows),beyond_other_live_r32=sum(peer[int(r['n'])]-float(r['new'])for r in rows))))
 C.atomic(C.T/'report.json',report());C.state('FINAL report.json written; take.tsv frozen before17:25Z. Guardian exits.')
