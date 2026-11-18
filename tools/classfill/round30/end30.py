"""Finalize at the assigned round30 deadline, retaining a recoverable report."""
from common29 import *
import signal
REPO=R.parents[1]
errors=[];archive={};commits=[]
def wait_until(target):
 while time.time()<target:time.sleep(min(15,target-time.time()))
def run(args,timeout=120):
 try:out=cmd(args,timeout=timeout)
 except subprocess.CalledProcessError as e:
  if args[0]=='git' and 'index.lock' in (e.stderr or ''):
   time.sleep(3);out=cmd(args,timeout=timeout)
  else:raise
 print(now(),args[:3],out[-1800:],flush=True);return out
note(f'START deadline finisher end30.py pid{os.getpid()}; long jobs end17:45Z, final table17:54:50Z, report17:55:01Z')
wait_until(END)
(W/'STOP').touch()
for script,pid in read(W/'local-owned.json',{}).items():
 try:
  command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
  if str(W/script) in command:os.killpg(pid,signal.SIGTERM);note(f'STOP {script} pid{pid}')
 except (ProcessLookupError,subprocess.SubprocessError):pass
time.sleep(2)
for host in ['boxE','boxD']:
 try:
  run(['scp','-q',str(W/'stop_manifest29.py'),host+':'+REMOTE+'/stop_manifest29.py'])
  py='scratch/squares-base/venv/bin/python' if host=='boxE' else 'scratch/squares-readers/venv/bin/python'
  run(['ssh',host,py+' -I '+REMOTE+'/stop_manifest29.py'],100)
  dest=W/('remote-final-'+host);dest.mkdir(exist_ok=True)
  run(['rsync','-az','--exclude=tmp/','--exclude=__pycache__/',host+':'+REMOTE+'/',str(dest)+'/'],120)
  manifest=read(dest/'archive-manifest.json',{});assert manifest
  for rel,digest in manifest.items():assert hashlib.sha256((dest/rel).read_bytes()).hexdigest()==digest,rel
  st=read(dest/'stop-result.json',{});assert st.get('left')==[] and st['scipy']=='1.18.1',st
  archive[host]=dict(files=len(manifest),bytes=sum((dest/q).stat().st_size for q in manifest),processes_left=[],scipy=st['scipy'])
  for name in ['out','logs']:run(['rsync','-a',str(dest/name)+'/',str(W/host/name)+'/'])
  run(['ssh',host,'rm -rf -- '+REMOTE])
 except Exception as e:errors.append(host+' cleanup: '+repr(e));note('CLEANUP_ERROR '+repr(e))
atomic(W/'archive-verification.json',dict(time=now(),hosts=archive,errors=errors))
for script in ['withdraw29.py','collect29.py']:
 try:run([sys.executable,str(W/script)],100)
 except Exception as e:errors.append(script+': '+repr(e))
try:run([sys.executable,str(W/'stats29.py')],60)
except Exception as e:errors.append('stats: '+repr(e))
# Complete all evidence checks before the assembler's final copy.
facts=[];kept=[]
from light29 import load,side
from ancestor_share29 import inspect
from public_review30 import review
from publishgate29 import check as independent
base,live,_=bar()
for row in rows(T/'take.tsv'):
 n=int(row['n']);score=float(row['new']);p=T/f'{n}.csv'
 try:
  digest=hashlib.sha256(p.read_bytes()).hexdigest()
  assert abs(side(load(p,{n})[n])/math.sqrt(n)-1-score)<1e-14
  proof=next((read(q,{}) for q in (W/'audited').glob('*.json') if read(q,{}).get('accepted') and read(q,{}).get('certified_output_sha256')==digest),None)
  assert proof and proof.get('quench_receipt',{}).get('finish_quenched'),'missing certified-file receipt'
  closure=proof['input_proof'];source=read(closure,{})
  assert not hold_hit(proof,source),'withdrawn byte source'
  anc=inspect(closure);assert not anc['excluded'] and not anc['errors'],anc
  public=review(closure);assert public['complete'],'public terminal review incomplete'
  for pin in public['pins']:assert hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()==pin['sha256']
  h=source.get('expanded',{}).get('history',{});assert not h.get('issues') and not h.get('excluded'),h.get('issues')
  inputs=list((W/'inputs').glob(f'{n}-{proof["tag"]}.csv'));assert len(inputs)==1
  gate=independent(proof['tag'],n,closure,inputs[0],seconds=max(1,min(90,int(END+500-time.time()))),force=True);assert gate['clean'],gate.get('hits')
  if score>=base[n]-1e-10 or score>=live[n]-1e-10:
   shutil.move(p,W/f'{n}-final-superseded.csv');note(f'FINAL_RETIRE n{n} live{live[n]}');continue
  kept.append(row);facts.append(dict(n=n,new=score,base=base[n],gain=base[n]-score,beyond_live=live[n]-score,sha256=digest))
 except Exception as e:
  errors.append(f'final n{n} withheld: '+repr(e));note(f'FINAL_WITHHOLD n{n} '+repr(e))
  if p.exists():shutil.move(p,W/f'{n}-final-withheld.csv')
wait_until(END+590)
base,live,_=bar();final=[];newfacts=[]
for row,fact in zip(kept,facts):
 n=int(row['n']);score=float(row['new'])
 if score>=base[n]-1e-10 or score>=live[n]-1e-10:
  shutil.move(T/f'{n}.csv',W/f'{n}-late-superseded.csv');note(f'FINAL_RETIRE n{n} live{live[n]}');continue
 row['held']=repr(base[n]);row['gain']=repr(base[n]-score);final.append(row)
 fact.update(base=base[n],gain=base[n]-score,beyond_live=live[n]-score);newfacts.append(fact)
facts=newfacts
with open(T/'take.tsv.tmp','w',newline='') as h:wr=csv.DictWriter(h,fieldnames=COL,delimiter='\t');wr.writeheader();wr.writerows(final)
os.replace(T/'take.tsv.tmp',T/'take.tsv');note('FINAL take.tsv frozen '+now());atomic(W/'final-comparison.json',dict(time=now(),rows=facts))
m=read(W/'measurements.json',{}).get('summary',{});gain=sum(f['gain'] for f in facts);beyond=sum(f['beyond_live'] for f in facts)
result=R/'results/classfill-r30-2026-11-15.tsv';shutil.copy2(T/'take.tsv',result)
controls=read(W/'public-controls30.json',{})
section=f'''## Round 30

The [results table](../results/classfill-r30-2026-11-15.tsv) retains {len(facts)} counts against bar30.
The gain against the bar is {gain:.12g}. The margin beyond other live round 30 takes is {beyond:.12g}.
Each retained file passed bisected floatsafe certification at 2.2e-11 and completed an fq quench from its certified file.
Inputs and source records have immutable SHA-256 snapshots under `take-classfill-r30/work/` on boxA.

The workers completed {m.get('completed_scans',0)} scans and {m.get('tries',0)} perturbation tries.
{m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side.
These measurements include later source refusals and superseded results.
Fresh rectangles and changed joins had priority. Completed geometry and backlog byte claims stayed closed.
boxE ran two compute slots and boxD ran one.
All three loose n=2 controls shortened side 2.5 to 2.000000000000406.
The bar-input n=2 control shortened side 2.0004 to 2.000000000022.
The first fq input exactly matched the bar, and the certified-file quench completed.
Fresh rectangle jobs then received a 900-second budget at the bar input side.
The six-try rigidity stop also passed its loose n=2 control before activation.
A second preparation order certifies and quenches an owned seed before its 300-second kick.
That path passed a loose n=2 control, including the final certified-file quench.
The fallback first screened 15 held starts, retaining their historical source graphs.
Direct catalogue extraction supplied 24 alternative candidates within the side allowance.
Each catalogue start names a pinned extraction receipt.
Fresh compositions kept higher queue priority.
The prepared-endpoint follow first entered n653 at score 0.01670080981033295.
That entry gained 1.107545635203877e-7 against bar30 before later follows or supersession.
Its recorded root was the owned Samanyu seed, with no public-first source.
The exact certified output received a high-priority follow.
A later comparison used 180-second family local kicks without fq inside each try.
Its tilted n=2 control shortened a raw search result before the final fq step.
The family comparisons use existing boxE slots and honor backlog byte reservations.
The public terminal preflight accepted own roots and the notebook 793 control.
It rejected the fetched notebook 750 control before numerical admission.
The named-member adapters read `local_bank.csv` and `packings.csv` as data.
Their absent-count controls stayed unapproved.
Exact public-first row pins can bind changing archives without a geometry inference from descendants.
The row-pin control accepted notebook 793 and rejected an altered SHA-256 record.
Own layouts and original seeds have no share gate.
A bare public reference with different archived layouts needs an exact version before admission.
Search admission closed at 17:35 UTC. Search and quench work shared the 17:45 UTC cutoff.
{'Both remote archives passed SHA-256 checks before scratch removal.' if len(archive)==2 else 'Cleanup errors remain in the report.'}
'''
(W/'doc-r30.md').write_text(section)
doc=R/'avenues/classfill.md';doc.write_text(doc.read_text().split('\n## Round 30\n')[0].rstrip()+'\n\n'+section)
try:run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'doc-r30.md')],30)
except Exception as e:errors.append('readable: '+repr(e))
nexts=[]
for kind,g in sorted(m.get('eligible_groups',{}).items(),key=lambda kv:(-kv[1].get('searched_score_gain',0)/max(1,kv[1].get('completed',0)),-kv[1].get('best_side_move',0)))[:3]:
 nexts.append(f"Run {kind} on changed geometry. Measured {g.get('completed',0)} completed scans and {g.get('tries',0)} tries. Searched score gain was {g.get('searched_score_gain',0):.12g}. Maximum side reduction was {g.get('best_side_move',0):.12g}.")
nexts+=['Bind inherited public roots to exact archived versions before dispatch. Round29 lost n412 gain5.90048e-5 and n926 gain2.01511e-7 to public-first750 ancestry.','Keep source caches and byte-specific snapshots. Repeating completed geometry stays closed unless the topology or search mechanism changes.']
report=dict(lane='classfill',improved_n=len(facts),gain=dict(against_base_bar=gain,beyond_other_live_r30=beyond),take_dir=str(T),summary=(f'Retained {len(facts)} counts with complete source checks and certified-file fq quench.' if facts else 'No retained improvements beat bar30 and every live round30 take with complete source approval.'),what_was_measured=[f"{m.get('completed_scans',0)} completed scans; {m.get('tries',0)} perturbation tries; {m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side. Totals include refused and superseded results.",'Source groups: '+json.dumps(m.get('groups',{}),sort_keys=True),'Public preflight dispositions: '+json.dumps(m.get('public_preflight',{}),sort_keys=True),'Intake dispositions: '+json.dumps(m.get('intake_dispositions',{}),sort_keys=True),'Source-graph-complete groups: '+json.dumps(m.get('eligible_groups',{}),sort_keys=True),'Public preflight controls: '+json.dumps(controls),'Bar-input control: '+json.dumps(read(W/'bar-control-result.json',{})),'Rigidity-stop control: '+json.dumps(read(W/'stop6-control-result.json',{})),'Named source member controls: '+json.dumps(read(W/'member-controls30.json',{})),'Pinned public-row controls: '+json.dumps(read(W/'pinned-controls30.json',{})),'Pre-quench preparation control: '+json.dumps(read(W/'preq-control-result.json',{})),'Owned catalogue extraction: '+json.dumps(read(W/'original-seed-controls30.json',{})),'Owned catalogue pool: '+json.dumps(read(W/'original-pool30.json',{})),'Final comparisons: '+json.dumps(facts),'Remote archives: '+json.dumps(archive)],next=nexts,commits=commits,processes_left=[] if len(archive)==2 else ['cleanup not verified; see blocked'],blocked=errors,repo=str(REPO),branch='main',worktree=str(REPO),pr='none (direct main commit)')
report['what_was_measured']=[
 f"{m.get('completed_scans',0)} completed production scans and {m.get('tries',0)} perturbation tries. {m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side. Totals include later refusals and supersession.",
 'Per-source numerical measurements: '+json.dumps(m.get('groups',{}),sort_keys=True),
 'Current source-preflight dispositions: '+json.dumps(m.get('public_preflight',{}),sort_keys=True),
 'All three loose n2 worker controls shortened side2.5 to2.000000000000406. Bar-input, rigidity-stop and quench-first controls passed, including certified-file finishing quenches.',
 'Numerical side changes use completed certified endpoints, including their finishing quenches. The family-lkick control produced a shorter raw n2 result before fq. Detailed receipts remain in work/invent-control30.json.','Source controls accepted exact notebook793 and rejected public750. Named members local_bank931 and packings501 were read; absent1001 stayed unapproved. A pinned793 source row bound its archive, and an altered pin failed.',
 'The attempted held-row identity check did not establish untouched catalogue identity. Inherited source graphs remained required. Direct catalogue starts have extraction receipts under work/seed-identity; the fallback pool is recorded in work/original-pool30.json.',
 'The prepared-endpoint follow entered653 at score0.01670080981033295 for1.107545635203877e-7 against bar30. Its source graph contained only the owned Samanyu seed. A follow used its exact certified bytes. Final retention is listed separately.','At15:26 the backlog derivative of our exact653 parent scored0.016700455174849305. Its source record pins parent sha2569ce41d58df256bde373e09c54ab4862d4f439310e715fe6cc574eff9f0c9cde1. That observed peer score is not added to our gain.','The manual653 follow began after an earlier backlog reservation and returned the same score. A common dispatch reservation guard now covers manual helpers. Its regression control rejected that recorded653 reservation and accepted an unclaimed n2 control.','Final retained comparisons: '+json.dumps(facts,sort_keys=True),
 'Archive verification: '+json.dumps(archive,sort_keys=True)
]
wait_until(END+601)
atomic(T/'report.json',report);note('FINISH report.json written after17:55Z '+json.dumps(dict(rows=len(facts),gain=report['gain'],errors=errors)))
paths=['lanes/squares/avenues/classfill.md','lanes/squares/results/classfill-r30-2026-11-15.tsv']
for file in sorted(W.glob('*.py')):
 dest=R/'tools/classfill/round30'/file.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest);paths.append(str(dest.relative_to(REPO)))
for name in ['classfill_finish.py','midm_bar30.py']:
 dest=R/'tools/classfill/round30/worker'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/'stage/lane'/name,dest);paths.append(str(dest.relative_to(REPO)))
try:
 # --only keeps other lanes' staged files out of this commit.
 run(['git','-C',str(REPO),'add','--',*paths],30)
 out=run(['git','-C',str(REPO),'commit','--only','-m','squares(classfill): record round 30 measurements','--',*paths],45)
 short=re.search(r'\[main ([0-9a-f]+)\]',out)[1];sha=run(['git','-C',str(REPO),'rev-parse',short],20).strip();commits.append(sha)
 names=run(['git','-C',str(REPO),'show','--pretty=format:','--name-only',sha],20).splitlines();assert set(filter(None,names))<=set(paths),names
 run(['git','-C',str(REPO),'show','--stat','--oneline',sha],20)
 run(['git','-C',str(REPO),'pull','--rebase','--autostash'],60);run(['git','-C',str(REPO),'push','origin','HEAD:main'],60)
 landed=run(['git','-C',str(REPO),'log','-1','--format=%H','--fixed-strings','--grep=squares(classfill): record round 30 measurements'],20).strip()
 if landed:commits[:]=[landed]
 atomic(W/'git-receipt.json',dict(time=now(),commits=commits,push_completed=True))
except Exception as e:errors.append('not pushed: '+repr(e))
report['commits']=commits;report['blocked']=errors;atomic(T/'report.json',report);note('REPORT_GIT_UPDATED '+json.dumps(dict(commits=commits,errors=errors)));print(json.dumps(report,indent=2),flush=True)
