"""Surviving deadline finisher. Do not start numerical work after the cutoff."""
from common29 import *
import signal
REPO=R.parents[1];errors=[];archive={};commits=[]
def run(args,limit=120):
 try:out=cmd(args,timeout=limit)
 except subprocess.CalledProcessError as e:
  if args[0]=='git' and ('index.lock' in (e.stderr or '') or 'push' in args):
   time.sleep(3);out=cmd(args,timeout=limit)
  else:raise
 print(now(),args[:3],out[-2000:],flush=True);return out
note(f'START deadline finisher pid{os.getpid()} end29.py, log work/end29.log, cleanup17:45Z take17:54Z report after17:55Z')
while time.time()<END:time.sleep(min(15,END-time.time()))
(W/'STOP').touch()
for script,pid in read(W/'local-owned.json',{}).items():
 try:
  line=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
  if str(W/script) in line:os.killpg(pid,signal.SIGTERM);note(f'STOP local driver {script} pid{pid}')
 except (ProcessLookupError,subprocess.SubprocessError):pass
time.sleep(3)
for host in ['boxE','boxD']:
 try:
  run(['scp','-q',str(W/'stop_manifest29.py'),host+':'+REMOTE+'/stop_manifest29.py'])
  py='scratch/squares-base/venv/bin/python' if host=='boxE' else 'scratch/squares-readers/venv/bin/python'
  run(['ssh',host,py+' -I '+REMOTE+'/stop_manifest29.py'],100)
  dest=W/('remote-final-'+host);dest.mkdir(exist_ok=True)
  run(['rsync','-az','--exclude=tmp/','--exclude=__pycache__/',host+':'+REMOTE+'/',str(dest)+'/'],120)
  manifest=read(dest/'archive-manifest.json',{});assert manifest
  for rel,sha in manifest.items():assert hashlib.sha256((dest/rel).read_bytes()).hexdigest()==sha,rel
  st=read(dest/'stop-result.json',{});assert st.get('left')==[] and st['scipy']=='1.18.1',st
  archive[host]=dict(files=len(manifest),bytes=sum((dest/q).stat().st_size for q in manifest),left=[],scipy=st['scipy'])
  for name in ['out','logs']:run(['rsync','-a',str(dest/name)+'/',str(W/host/name)+'/'])
  run(['ssh',host,'rm -rf -- '+REMOTE])
 except Exception as e:errors.append(host+' cleanup: '+repr(e));note('CLEANUP_ERROR '+repr(e))
atomic(W/'archive-verification.json',dict(time=now(),hosts=archive,errors=errors))
for script in ['withdraw29.py','guard29.py','collect29.py']:
 try:run([sys.executable,str(W/script)],100)
 except Exception as e:errors.append(script+': '+repr(e))
while time.time()<END+480:time.sleep(min(15,END+480-time.time()))
base,live,_=bar();facts=[];final_rows=[]
from light29 import load,side
from prvsim29 import check
from ancestor_share29 import inspect
for r in rows(T/'take.tsv'):
 n=int(r['n']);p=T/f'{n}.csv';score=float(r['new'])
 try:
  sha=hashlib.sha256(p.read_bytes()).hexdigest()
  if not (score<base[n]-1e-10 and score<live[n]-1e-10):
   shutil.move(p,W/f'{n}-final-superseded.csv');note(f'FINAL_RETIRE n{n} score{score} live{live[n]}');continue
  assert abs(side(load(str(p),{n})[n])/math.sqrt(n)-1-score)<1e-14
  # Own search outputs are exempt from the share gate.
  proof=next((read(q,{}) for q in (W/'audited').glob('*.json') if read(q,{}).get('certified_output_sha256')==sha and read(q,{}).get('accepted')),None)
  assert proof and proof.get('quench_receipt',{}).get('finish_quenched'),(n,sha,'missing receipt')
  anc=inspect(proof['input_proof']);assert not anc['excluded'] and not anc['errors'],(n,anc)
  public_review=proof.get('public_root_review',{});assert public_review.get('complete') and public_review.get('source_proof_sha256')==hashlib.sha256(Path(proof['input_proof']).read_bytes()).hexdigest()
  for pin in public_review.get('pins',[]):assert Path(pin['snapshot']).is_file() and hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()==pin['sha256']
  from publishgate29 import check as independent_check
  inputs=list((W/'inputs').glob(f'{n}-{proof["tag"]}.csv'));assert len(inputs)==1
  independent=independent_check(proof['tag'],n,proof['input_proof'],inputs[0],seconds=max(1,min(180,int(END+585-time.time()))),force=True);assert independent.get('clean'),independent.get('hits')
  walked=proof.get('walked',{})
  if isinstance(walked,dict):assert not walked.get('issues') and not walked.get('excluded'),(n,walked.get('issues'),walked.get('excluded'))
  extra=proof.get('resolved_source_snapshots',[])+(walked.get('snapshots',[]) if isinstance(walked,dict) else [])
  for q in extra:assert Path(q['snapshot']).is_file() and hashlib.sha256(Path(q['snapshot']).read_bytes()).hexdigest()==q['sha256'],q['path']
  closure=read(proof['input_proof'],{});text=json.dumps([proof,closure]);hit=hold_hit(proof,closure);assert hit is None,hit
 except Exception as e:
  errors.append(f'final n{n} withheld: '+repr(e));note(f'FINAL_WITHHOLD n{n} '+repr(e))
  if p.exists():shutil.move(p,W/f'{n}-final-withheld.csv')
  continue
 r['held']=repr(base[n]);r['gain']=repr(base[n]-score);final_rows.append(r);facts.append(dict(n=n,new=score,base=base[n],gain=base[n]-score,beyond_live=live[n]-score,sha256=sha))
# Full evidence checks finish first. Compare live bars again immediately before the take deadline.
while time.time()<END+590:time.sleep(min(5,END+590-time.time()))
late_base,late_live,_=bar();prior={f['n']:f for f in facts};kept=[];facts=[]
for r in final_rows:
 n=int(r['n']);score=float(r['new'])
 if score>=late_base[n]-1e-10 or score>=late_live[n]-1e-10:
  shutil.move(T/f'{n}.csv',W/f'{n}-late-superseded.csv');note(f'FINAL_LATE_RETIRE n{n} score{score} live{late_live[n]}');continue
 r['held']=repr(late_base[n]);r['gain']=repr(late_base[n]-score);kept.append(r)
 f=prior[n];f.update(base=late_base[n],gain=late_base[n]-score,beyond_live=late_live[n]-score);facts.append(f)
final_rows=kept
with open(T/'take.tsv.tmp','w',newline='') as h:o=csv.DictWriter(h,fieldnames=COL,delimiter='\t');o.writeheader();o.writerows(final_rows)
os.replace(T/'take.tsv.tmp',T/'take.tsv');note('FINAL take.tsv frozen '+now());atomic(W/'final-comparison.json',dict(time=now(),rows=facts))
try:run([sys.executable,str(W/'stats29.py')],60)
except Exception as e:errors.append('stats '+repr(e))
m=read(W/'measurements.json',{}).get('summary',{});gain=sum(q['gain'] for q in facts);beyond=sum(q['beyond_live'] for q in facts)
result=R/'results/classfill-r30-2026-11-15.tsv';shutil.copy2(T/'take.tsv',result)
section=f"""## Round 30

The [results table](../results/classfill-r30-2026-11-15.tsv) retains {len(facts)} counts against bar30.
The gain against the bar is {gain:.12g}. The margin beyond other live round 30 takes is {beyond:.12g}.
Each retained row passed bisected floatsafe certification at 2.2e-11 and completed an fq quench from its certified file.
Inputs and source records have immutable SHA-256 snapshots under `take-classfill-r30/work/` on boxA.

The workers completed {m.get('completed_scans',0)} scans and {m.get('tries',0)} perturbation tries.
{m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side.
These counts include results later refused or superseded.
Fresh rectangle compositions and changed certified layouts had priority.
Already completed geometry stayed closed. Backlog byte claims stayed reserved.
boxE ran two slots and boxD ran one. All three passed the loose n=2 fq control.
Own layouts and original seeds have no share gate. Direct fetched public starts retain that test.
Explicit excluded-file ancestry stays out. Source walks that exceed their time budget stay unqueued.
Search admission closed at 17:35 UTC. Search and quenches shared the 17:45 UTC cutoff.
{("Both remote archives were checked by SHA-256 before removal." if len(archive)==2 else "Archive or cleanup errors remain in the report.")}
The finishing quench now certifies every returned attempt, including moves below the former 3e-9 side threshold.
Its n=2 control shortened side 2.000000001 to 2.000000000022. Both default and polish attempts completed.
The source resolver pins cached table reads and preserves byte-specific withdrawals.
Its copied793 independent control passed. The initial rectangle747 control exposed a broad inherited join rule. The later source policy narrows it to the exact join names.
"""
(W/'doc-r30.md').write_text(section)
doc=R/'avenues/classfill.md';text=doc.read_text();marker='\n## Round 30\n';doc.write_text(text.split(marker)[0].rstrip()+'\n\n'+section)
checker=Path('$STYLE_CHECK/check.py')
try:run(['/opt/homebrew/bin/python3',str(checker),'--level','default',str(W/'doc-r30.md')],30)
except Exception as e:errors.append('readable '+repr(e))
paths=['lanes/squares/avenues/classfill.md','lanes/squares/results/classfill-r30-2026-11-15.tsv']
for file in sorted(W.glob('*.py')):
 dest=R/'tools/classfill/round30'/file.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest);paths.append(str(dest.relative_to(REPO)))
while time.time()<=END+600:time.sleep(min(10,END+601-time.time()))
ranked=sorted(((k,g) for k,g in m.get('groups',{}).items() if g.get('searched_score_gain',0)>1e-10),key=lambda q:(-q[1].get('searched_score_gain',0)/max(1,q[1].get('completed',0)),-q[1].get('best_side_move',0)))
next_items=[f"Run changed {kind} inputs. Measured {g['completed']} completed scans, {g['entered']} take entries, searched score gain {g.get('searched_score_gain',0):.12g}, and best side move {g['best_side_move']:.12g}." for kind,g in ranked[:3]]
if not next_items:
 next_items=[f"Run changed {kind} inputs. Among inputs with complete recorded source graphs and no known refusal, {g['completed']} completed scans made {g['tries']} tries and moved at most {g['best_side_move']:.12g} of side." for kind,g in sorted(m.get('eligible_groups',{}).items(),key=lambda kv:-kv[1]['best_side_move'])[:2]]
next_items+=[f"Keep changed fresh compositions first. {m.get('completed_scans',0)} scans completed this round. Repeating unchanged geometry adds no measured new start, so honor the saved geometry and byte-claim records.",'Cache deferred source histories before numerical dispatch. The three former 45-second timeouts completed in6.25,0.26 and0.17 seconds after duplicate text edges were removed; incomplete proofs stay out.']
report=dict(lane='classfill',improved_n=len(facts),gain=dict(against_base_bar=gain,beyond_other_live_r30=beyond),take_dir=str(T),summary=('Retained counts: '+', '.join(str(q['n']) for q in facts)+'. Each row has complete source records, bisected floatsafe certification and a certified-file fq quench.' if facts else 'No retained rows beat bar30 and the live round30 takes with complete source approval.'),what_was_measured=[f"{m.get('completed_scans',0)} completed scans, {m.get('tries',0)} perturbation tries, {m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side. Counts include later refusals and supersession.",'Per-source measurements: '+json.dumps(m.get('groups',{}),sort_keys=True),'Source-graph-complete groups after known refusals: '+json.dumps(m.get('eligible_groups',{}),sort_keys=True),'All three remote loose n2 packings shortened side2.5 to2.000000000000406. Source controls accepted own and original-seed inputs and rejected excluded-file public ancestry. Share and retention-note controls passed.','Job return codes: '+json.dumps(m.get('returncodes',{})),'Final comparisons: '+json.dumps(facts),'Archive verification: '+json.dumps(archive)],next=next_items,commits=commits,processes_left=[] if len(archive)==2 else ['unverified cleanup, see blocked'],blocked=errors,repo=str(REPO),branch='main',worktree=str(REPO),pr='none (direct main commit)')
report['what_was_measured'] += ['Subthreshold quench control: '+json.dumps(read(W/'quench-control-result.json',{}),sort_keys=True),'Table pin control: '+json.dumps(dict(passed=read(W/'table-pin-control.json',{}).get('passed'),snapshots=len(read(W/'table-pin-control.json',{}).get('snapshots',[])))),'Own801 historical fallback control: '+str(read(W/'own801-control.json',{}).get('passed')),'Public-first ancestor controls: original own seed503 received no share measurement; public416 share1.0 rejected. Interim503 was withdrawn because its public-first703 donor measured0.47368421052631576. '+json.dumps(read(W/'public-root-503.json',{}).get('excluded',[])),'Rollover comparison fixed: basebar30 was always used; competing take tables now read live r30 rather than frozen r28. All retained rows use the corrected comparison.','Narrow join rule control: '+json.dumps(read(W/'narrow-join-control.json',{}),sort_keys=True),'Archived-input controls: '+json.dumps(dict(early_take_issues=len(read(W/'early-take-control.json',{}).get('history',{}).get('issues',[])),own23_exercised=read(W/'own23-control-exercised.json',{}).get('passed'),own23_pins=len(read(W/'own23-control-exercised.json',{}).get('history',{}).get('snapshots',[])),receipt=read(W/'input-addressed-receipt-control.json',{}).get('passed'))), 'Two coarse geometry groups repeated at six decimals; the production eight-decimal hash was retained. Historical public roots still need their byte-bound review before a take counts.','The412 endpoint gained5.900478557352429e-5 against bar30 and reached0.024491395170857855, but its complete100-pin source chain still reaches public-first jonathan750 share0.8253333333333334. It remained out.','The926 endpoint gained2.0151071522533925e-7 against bar30 but remained out. Exact archived copies recovered47 source pins, then the complete chain exposed public-first jonathan750 share0.8253333333333334 in two identical kept versions. Its original own seed is different. This numerical gain is excluded.','Independent source controls: copied793 accepted. The broad inherited 745/858 rule was narrowed after main corrected its rectangle747 false match.']
atomic(T/'report.json',report);note('FINISH report.json written after17:55Z '+json.dumps(dict(rows=len(facts),gain=report['gain'],errors=errors)))

try:
 run(['git','-C',str(REPO),'add','--',*paths],30)
 out=run(['git','-C',str(REPO),'commit','--only','-m','squares(classfill): record round 30 measurements','--',*paths],45)
 short=re.search(r'\[main ([0-9a-f]+)\]',out)[1];sha=run(['git','-C',str(REPO),'rev-parse',short],20).strip();commits.append(sha)
 names=run(['git','-C',str(REPO),'show','--pretty=format:','--name-only',sha],20).splitlines();assert set(filter(None,names))<=set(paths),names
 run(['git','-C',str(REPO),'show','--stat','--oneline',sha],20)
 run(['git','-C',str(REPO),'pull','--rebase','--autostash'],60);run(['git','-C',str(REPO),'push','origin','HEAD:main'],60)
 landed=run(['git','-C',str(REPO),'log','-1','--format=%H','--fixed-strings','--grep=squares(classfill): record round 30 measurements'],20).strip()
 if landed:commits[:]=[landed]
 atomic(W/'git-receipt.json',dict(time=now(),commits=commits,push_completed=True))
except Exception as e:errors.append('git not pushed unless receipt exists: '+repr(e))

report['commits']=commits;report['blocked']=errors;atomic(T/'report.json',report);note('REPORT_GIT_UPDATED '+json.dumps(dict(commits=commits,errors=errors)));print(json.dumps(report,indent=2),flush=True)
