"""Drain four owned boxE slots, verify the archive, and freeze round 34."""
import pathlib,sys,os,json,time,csv,math,subprocess,hashlib,traceback,signal,datetime,re
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
for k in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import campaign35base as C
FINAL=datetime.datetime(2026,11,17,16,34,40,tzinfo=datetime.UTC).timestamp()
def run(args,timeout=60,cwd=None):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,cwd=cwd)
 print(p.stdout,flush=True);p.check_returncode();return p.stdout

def local_collect():
 old=C.cmd;C.cmd=lambda *unused:''
 try:return C.collect()
 finally:C.cmd=old

def stop_controller():
 (W/'STOP').touch()
 if not(W/'campaign.pid').exists():return
 pid=int((W/'campaign.pid').read_text())
 p=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
 if str(W/'campaign35.py')not in p.stdout:return
 os.kill(pid,signal.SIGTERM)
 for _ in range(5):
  try:os.kill(pid,0)
  except ProcessLookupError:return
  time.sleep(1)
 os.kill(pid,signal.SIGKILL)

def archive():
 stop_controller();total=0
 for h in C.HOSTS:
  run(['ssh',h,C.rpy(h)+' $SCRATCH/squares-invent-r35/remote_close35.py'])
  run(['rsync','-a',C.remote_of(h),str(W/'boxE-raw')+'/'],240)
  manifest=json.load(open(W/'boxE-raw/transfer-manifest.json'))
  bad=[p for p,v in manifest.items()if not(W/'boxE-raw'/p).is_file()or C.sha(W/'boxE-raw'/p)!=v]
  if bad:raise ValueError('archive hash mismatch '+h+' '+repr(bad[:15]))
  (W/'boxE-raw'/f'transfer-manifest-{h}.json').write_text(json.dumps(manifest));total+=len(manifest)
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=total,all_hashes_match=True,boxE_scratch_removed=False,hosts=C.HOSTS))
 local_collect()
 for h in C.HOSTS:
  (W/'boxE-raw/transfer-manifest.json').write_text((W/'boxE-raw'/f'transfer-manifest-{h}.json').read_text())
  run(['rsync','-a',str(W/'boxE-raw'/f'transfer-manifest-{h}.json'),C.remote_of(h)+'transfer-manifest.json'])
  run(['ssh',h,C.rpy(h)+' $SCRATCH/squares-invent-r35/remote_close35.py --remove'])
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=total,all_hashes_match=True,boxE_scratch_removed=True,hosts=C.HOSTS,earlier_boxE_archive='boxE-raw/transfer-manifest-boxE.json'))
 C.atomic(W/'processes-left.json',{'boxA':[],**{h:[] for h in C.HOSTS},'boxE_scratch_removed':True,'box_scratch_removed':C.HOSTS})
 C.state(f'ARCHIVE all {total} CSV hashes verified on {C.HOSTS}; removed owned box scratch; controller stopped.')

def report():
 jobs=C.load(W/'jobs.json',[]);stats={};errors=[];unfollowed=[]
 for j in jobs:
  if j['kind']in('control','early'):continue
  d=C.load(W/'boxE-raw'/j['id']/'done.json',{})
  if not d:continue
  s=stats.setdefault(j['kind'],dict(completed=0,moved=0,dry_probe=0));s['completed']+=1;s['dry_probe']+=int(d.get('search_end')=='dry-probe')
  if 'error'in d:errors.append(j['id']+': '+d['error']);continue
  if d.get('new')is None:continue
  move=j['side']-(d['new']+1)*math.sqrt(j['n']);s['moved']+=int(move>1e-8)
  if move>1e-6 and not any(x.get('parent_job')==j['id']for x in jobs):unfollowed.append((move,j,d))
 comp=C.load(W/'comparison.json',dict(improved_n=0,gain={'against_base_bar':0,'beyond_other_live_r35':0}))
 published={}
 for line in (C.S/'handoff-r35.log').read_text(errors='replace').splitlines():
  match=re.search(r'invent -> all: CERTIFIED n=(\d+) score=([0-9.eE+-]+)',line)
  if match:
   n=int(match[1]);published[n]=min(published.get(n,math.inf),float(match[2]))
 measured=[f'Completed job groups: {json.dumps(stats,sort_keys=True)}.',f'Latest live comparison: {comp.get("time","pending")}.',f'Numerical job errors: {json.dumps(errors)}.',f'Archive verification: {json.dumps(C.load(W/"transfer-check.json",{}),sort_keys=True)}.',f'Provisional maximum per-n gains against bar35: {json.dumps({str(n):C.BASE[n]-s for n,s in sorted(published.items())})}.','The k123 held-catalogue adapter verified the actual259 submitted geometry hash. Wrong hash, count and mixed-parent controls failed.',
 'Three boxE slots used changed rectangles and joins. Plain held kicks and the completed wide pilot stayed closed. Changed own endpoints receive at most one dry leg.','Pair and stopped907 numerical controls gate production. Every distinct certified candidate completes the full default and polish fq loop before comparison. Immutable completed checkpoints export before the whole batch finishes.','Round32 held-root controls accepted exact submitted coordinates without a share call. Changed coordinates, changed evidence and exact-byte withdrawals failed. Wrong-hash notices passed. The direct withdrawn814 fixture is checked separately.','The initial worker startup exposed a missing control2 checkpoint dependency. All four workers exited before searches. The corrected order runs checkpoint controls after control2 and before production.','The historical970 source control failed closed on a superseded forensics849 path. It supplied no production input.']
 fresh=stats.get('fresh',{});leg=stats.get('leg',{})
 nxt=[f'Prioritize changed rectangles and joins: round34 fresh runs moved 56/100, versus 0/25 legs. This round fresh geometry moved in {fresh.get("moved",0)} of {fresh.get("completed",0)} jobs; {len(published)} provisional rows were handed off. Preserve exact geometry keys and the 120-second dry probe.',f'Follow only useful lowest-live changed endpoints and stop after one dry leg. Legs moved in {leg.get("moved",0)} of {leg.get("completed",0)} jobs.']
 for move,j,d in sorted(unfollowed,key=lambda x:-x[0])[:3]:
  if d['new']<=C.peers()[j['n']]+1e-6/math.sqrt(j['n']):nxt.append(f'Check uncontinued endpoint n={j["n"]} {j["id"]} against the next bar and byte claims. It shortened side by {move:.12g}.')
 nxt+=['Keep unchanged539 and the completed broad-radius pilot closed. Round32 gave no published row from either profile.','Keep held roots bound to their submitted file, accepted gate and exact coordinates. Reopen source deferrals only when their metadata changes.']
 return dict(lane='invent',improved_n=comp['improved_n'],gain=comp['gain'],take_dir=str(C.T),summary=('Running with three bounded boxE workers. Search and quench stop by 16:05 UTC. 'if not C.load(W/'transfer-check.json',{}).get('boxE_scratch_removed')else'Archived. ')+f'Published {len(published)} provisional rows. Retained {comp["improved_n"]} after the latest bar35 and live-peer comparison.',what_was_measured=measured,next=nxt,commits=C.load(W/'commits.json',[]),processes_left=C.load(W/'processes-left.json',{'boxA':[int((W/(v+'.pid')).read_text())for v in('campaign','finish')if(W/(v+'.pid')).exists()],'boxE':[int(p.read_text())for p in sorted((W/'boxE-raw').glob('worker[1234].pid'))]}),blocked=C.load(W/'blocked.json','none'),repo='private repo',branch='main',worktree='$PRIVATE_REPO',pr='none')

class FinalAuditDeadline(BaseException):pass
def bounded_final_audit():
 def expired(*unused):raise FinalAuditDeadline('final source audit exceeded85s')
 old=signal.signal(signal.SIGALRM,expired);signal.alarm(85)
 try:return local_collect()
 finally:signal.alarm(0);signal.signal(signal.SIGALRM,old)

def final_peers():
 peer=C.peers();rows=[r for r in csv.DictReader(open(C.T/'take.tsv'),delimiter='\t')if float(r['new'])<peer[int(r['n'])]and float(r['new'])<C.BASE[int(r['n'])]-1e-10]
 retained={int(r['n'])for r in rows}
 for p in C.T.glob('*.csv'):
  if int(p.stem)not in retained:p.replace(C.T/'near'/(p.stem+'-final-peer-superseded.csv'))
 tmp=W/'final-take.tmp'
 with tmp.open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=C.FIELDS,delimiter='\t');w.writeheader();w.writerows(rows)
 tmp.replace(C.T/'take.tsv')
 C.atomic(W/'comparison.json',dict(time=C.now(),improved_n=len(rows),gain=dict(against_base_bar=sum(float(r['gain'])for r in rows),beyond_other_live_r35=sum(peer[int(r['n'])]-float(r['new'])for r in rows))))

if __name__=='__main__':
 C.state('START finish35 guardian: admission15:37Z, numeric16:05Z, archive/push before16:20Z; final peer comparison16:34:40Z.')
 while time.time()<C.ADMIT:time.sleep(min(30,C.ADMIT-time.time()))
 while time.time()<C.HARD:
  try:
   act=[json.loads(run(['ssh',h,C.rpy(h)+' $SCRATCH/squares-invent-r35/remote_close35.py --status']))['active']for h in C.HOSTS]
   if not any(act):break
  except Exception:traceback.print_exc()
  time.sleep(min(20,max(.01,C.HARD-time.time())))
 try:
  archive()
  import record35
  commit=record35.record();C.state('PUSH '+commit+' to main')
 except Exception as e:
  traceback.print_exc();C.atomic(W/'blocked.json',str(e));C.state('CLOSEOUT error '+str(e))
 C.atomic(C.T/'report.json',report())
 target=FINAL-120
 while time.time()<target:time.sleep(min(20,max(.01,target-time.time())))
 try:bounded_final_audit()
 except (Exception,FinalAuditDeadline)as e:
  traceback.print_exc();C.atomic(W/'blocked.json','final source comparison failed: '+str(e))
  # Keep the immutable files for review while withholding an incomplete final source check.
  for p in C.T.glob('*.csv'):p.replace(C.T/'near'/(p.stem+'-final-source-deferred.csv'))
  (C.T/'take.tsv').write_text('\t'.join(C.FIELDS)+'\n');C.hand('WITHDRAW current invent take after incomplete final source recheck; immutable endpoints remain in near/. '+str(e))
 while time.time()<FINAL:time.sleep(min(10,max(.01,FINAL-time.time())))
 final_peers();C.atomic(C.T/'report.json',report());C.state('FINAL report.json written; take.tsv frozen before16:35Z. Guardian exits.')
