"""Surviving deadline finisher. Do not start numerical work after the cutoff."""
from common28 import *
import signal
REPO=R.parents[1];errors=[];archive={};commits=[]
def run(args,limit=120):
 try:out=cmd(args,timeout=limit)
 except subprocess.CalledProcessError as e:
  if args[0]=='git' and ('index.lock' in (e.stderr or '') or 'push' in args):
   time.sleep(3);out=cmd(args,timeout=limit)
  else:raise
 print(now(),args[:3],out[-2000:],flush=True);return out
note(f'START deadline finisher pid{os.getpid()} end28.py, log work/end28.log, cleanup05:45Z take05:54Z report after05:55Z')
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
  run(['scp','-q',str(W/'stop_manifest28.py'),host+':'+REMOTE+'/stop_manifest28.py'])
  py='scratch/squares-base/venv/bin/python' if host=='boxE' else 'scratch/squares-readers/venv/bin/python'
  run(['ssh',host,py+' -I '+REMOTE+'/stop_manifest28.py'],100)
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
for script in ['withdraw28.py','guard28.py','collect28.py']:
 try:run([sys.executable,str(W/script)],100)
 except Exception as e:errors.append(script+': '+repr(e))
while time.time()<END+480:time.sleep(min(15,END+480-time.time()))
base,live,_=bar();facts=[];final_rows=[]
from light28 import load,side
from prvsim28 import check
from ancestor_share28 import inspect
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
  walked=proof.get('walked',{})
  if isinstance(walked,dict):assert not walked.get('issues') and not walked.get('excluded'),(n,walked.get('issues'),walked.get('excluded'))
  extra=proof.get('resolved_source_snapshots',[])+(walked.get('snapshots',[]) if isinstance(walked,dict) else [])
  for q in extra:assert Path(q['snapshot']).is_file() and hashlib.sha256(Path(q['snapshot']).read_bytes()).hexdigest()==q['sha256'],q['path']
  closure=read(proof['input_proof'],{});text=json.dumps([proof,closure]);hit=next((key for key in read(W/'source-holds.json',{}) if key in text),None);assert hit is None,hit
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
try:run([sys.executable,str(W/'stats28.py')],60)
except Exception as e:errors.append('stats '+repr(e))
m=read(W/'measurements.json',{}).get('summary',{});gain=sum(q['gain'] for q in facts);beyond=sum(q['beyond_live'] for q in facts)
result=R/'results/classfill-r28-2026-11-14.tsv';shutil.copy2(T/'take.tsv',result)
withheld=[read(q,{}) for q in (W/'source-withheld').glob('*.json')]
section=f'''## Round 28

The [results table](../results/classfill-r28-2026-11-14.tsv) retains {len(facts)} counts against bar28.
The gain against the bar is {gain:.12g}. The margin beyond other live round 28 takes is {beyond:.12g}.
Each retained row has floatsafe certification at 2.2e-11 and a completed fq quench from the certified file.
The table names areebbb per-count upstream donors in both source and licence cells.
Inputs and ancestry records have immutable SHA-256 snapshots under `take-classfill-r28/work/` on boxA.

Three remote slots ran on boxE and boxD. Each passed the loose n=2 control from side 2.5 to 2.000000000000406.
The exact excluded public row measured share 1.0 and failed admission.
The retained 793 control measured share 0.0012610340479192938 and passed.
The source checker now accepts the exact original-seed declaration that contains semicolons.
Its control still rejects a separate unknown public source without a licence.

The workers completed {m.get('completed_scans',0)} scans and {m.get('tries',0)} perturbation tries.
{m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side.
These counts include results later refused or superseded.
Source admission and result collection ran independently. Fresh public rows and rectangle designs had priority.
The 00:19 policy update removed share gates for our own layouts, original seeds and descendants.
Direct fetched public starts retain the share test. Ancestry that names the excluded public file still stays out.
The public-copy resolver verifies the raw remote hash and the certification dilation.
The older 375 input matched its receipt hash and dated notebook row.
The 457 source recheck verified 27 immutable source snapshots and resolved every history issue.
Its exact 499 notebook-row control passed with zero error. An altered coordinate failed the control.
The 264, 793 and 798 source rechecks also cleared every path and saved the recovered evidence by hash.
Larger kicks of 0.08 and 0.12 followed the stalled small-kick endpoints.
Their n=2 control ran 526 tries and shortened side 2.0004 to 2.0000000000503197, then completed its certified-file quench.
The three production scans ran 287 tries and moved at most 1.4e-9 of side, with no meaningful gain.
The smaller-kick control used 0.004 and 0.008. Its 552 tries reached the same certified side and completed its quench.
The manual helpers now honor backlog byte claims. Two pending smaller-kick follows were removed before they ran.
Search admission closed at 05:35 UTC. Search and quench work stopped by 05:45 UTC.
Archives were checked by SHA-256 before remote scratch removal.
The own-endpoint cache prevents a byte change from repeating a completed scan.
A replacement of our own take must improve its score by more than 1e-10.
Generation now has one 25-second cap, with fresh directories ahead of frozen inputs.
Job-history preparation now runs before that candidate budget starts.
A late saved-input filter examined 520 files. Of these, 510 met the side allowance, six were scanned or claimed, and four were too far away.
Source walks now have a 45-second admission budget. A timed-out source stays out of the numerical queue.
The public 916 follow stayed out because its frozen notice names the excluded file and lacks a per-count trace.
A sample of 85 inputs stayed distinct under both geometry hashes. Signed-zero normalization collapsed no layouts, so the production hash stayed unchanged.
'''
(W/'doc-r28.md').write_text(section);doc=R/'avenues/classfill.md';text=doc.read_text();marker='\n## Round 28\n';doc.write_text(text.split(marker)[0].rstrip()+'\n\n'+section)
checker=Path('$STYLE_CHECK/check.py')
try:run(['/opt/homebrew/bin/python3',str(checker),'--level','default',str(W/'doc-r28.md')],30)
except Exception as e:errors.append('readable '+repr(e))
# Commit only this lane's exact paths, even when other lanes have staged changes.
paths=['lanes/squares/avenues/classfill.md','lanes/squares/results/classfill-r28-2026-11-14.tsv']
for name in ['harvest_copy28.py','history28.py','ancestor_share28.py','common28.py','prvsim28.py','sharelight28.py','withdraw28.py','intake28.py','collect28.py','stats28.py','share_policy28.py','classfill_sources.py','ancestry24.py','trace_base.py','light28.py','end28.py','admit28.py','collectdriver28.py','near28.py','guard28.py','stop_manifest28.py','geometry_zero_control28.py','source_credits28.py','autoaccept28.py','widekick28.py','checkwide28.py','finekick28.py','checkfine28.py','cancel_claimed28.py','rewalk_retained28.py','rank_reopened28.py','bootstrap28.py','startlocal28.py','continue_own28.py','reopen_own28.py','geometry24.py','verify_archives28.py','worker28.py','control24.py']:
 dest=R/'tools/classfill/round28'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(W/name,dest);paths.append(str(dest.relative_to(REPO)))
try:
 run(['git','-C',str(REPO),'add','--',*paths],30)
 out=run(['git','-C',str(REPO),'commit','--only','-m','squares(classfill): record round 28 measurements','--',*paths],45)
 short=re.search(r'\[main ([0-9a-f]+)\]',out)[1];sha=run(['git','-C',str(REPO),'rev-parse',short],20).strip();commits.append(sha)
 names=run(['git','-C',str(REPO),'show','--pretty=format:','--name-only',sha],20).splitlines();assert set(filter(None,names))<=set(paths),names
 run(['git','-C',str(REPO),'show','--stat','--oneline',sha],20)
 run(['git','-C',str(REPO),'pull','--rebase','--autostash'],60);run(['git','-C',str(REPO),'push','origin','HEAD:main'],60)
 landed=run(['git','-C',str(REPO),'log','-1','--format=%H','--fixed-strings','--grep=squares(classfill): record round 28 measurements'],20).strip()
 if landed:commits[:]=[landed]
 atomic(W/'git-receipt.json',dict(time=now(),commits=commits,push_completed=True))
except Exception as e:errors.append('git not pushed unless receipt exists: '+repr(e))
while time.time()<=END+600:time.sleep(min(10,END+601-time.time()))
ranked=sorted(((k,g) for k,g in m.get('groups',{}).items() if g.get('searched_score_gain',0)>1e-10),key=lambda q:(-q[1].get('searched_score_gain',0)/max(1,q[1].get('completed',0)),-q[1].get('best_side_move',0)))
next_items=[f"Run changed {kind} inputs. Measured {g['completed']} completed scans, {g['entered']} historical take entries, searched score gain {g.get('searched_score_gain',0):.12g}, and best side move {g['best_side_move']:.12g}." for kind,g in ranked[:3]]
next_items+=['Keep the own-layout exemption and exact public-copy controls. Direct fetched public starts retain the share test; explicit excluded-file ancestry stays out.','Defer unchanged dry geometry. Change the topology or repair before a repeat.']
next_items.append('Skip exact byte inputs claimed by backlog, including changed-method follows.')
next_items.append('Cache the deferred old source walks before search. The saved-input filter examined 520 files and found 510 within the side allowance. The 503, 700 and 758 module walks exhausted the 45-second source budget; their inputs were not queued. Ranked paths are in work/reopen-ranked.json.')
report=dict(lane='classfill',improved_n=len(facts),gain=dict(against_base_bar=gain,beyond_other_live_r28=beyond),take_dir=str(T),summary='Retained counts: '+(', '.join(str(q['n']) for q in facts) or 'none')+'. Each retained row has an immutable source audit, remote floatsafe certification and a completed certified-file fq quench.',what_was_measured=[f"{m.get('completed_scans',0)} completed scans, {m.get('tries',0)} perturbation tries, {m.get('moved_over_1e8',0)} starts shortened by more than 1e-8 of side. Counts include later refusals and supersession.",'Per-source measurements: '+json.dumps(m.get('groups',{}),sort_keys=True),'Controls: all three remote loose n2 packings side2.5 -> 2.000000000000406; exact prvsiyan982 share1.0 rejected; retained793 share0.0012610340479192938 accepted.','Legacy 375 and 457 controls passed. The receipt input hash and dated notebook dilation matched. The 457 recheck had no unresolved paths and 27 SHA-verified source snapshots. Exact daily aliases and archived 501 run jobs supplied the missing links.','Signed-zero control: 85 saved inputs gave 85 unique layouts under both hashes, zero collapsed groups; no production hash change.','Fresh k123 inputs were deferred when backlog claimed their exact byte snapshots.','Job return codes: '+json.dumps(m.get('returncodes',{})),'The public 916 follow stayed out. Its gain against the queue-time bar was about 6.442e-5, but the frozen notice names the excluded file and has no per-n trace. Independent own 916 constructions remain eligible.','Final comparisons: '+json.dumps(facts),'Policy: 00:19 own layouts, original seeds and descendants are exempt from share gates. Named excluded-file ancestry and fetched public starts still have their source checks.','Public-copy controls: exact499 notebook coordinates accepted with zero error; altered coordinate rejected; full499 history has zero unresolved paths.','Archive verification: '+json.dumps(archive)],next=next_items,commits=commits,processes_left=[] if len(archive)==2 else ['unverified cleanup, see blocked'],blocked=errors,repo=str(REPO),branch='main',worktree=str(REPO),pr='none (direct main commit)')
report['what_was_measured'].insert(3,'Larger-kick control and certified-file quench: '+json.dumps(read(W/'widekick-control.json',{}),sort_keys=True))
report['what_was_measured'].insert(4,'Smaller-kick control and certified-file quench: '+json.dumps(read(W/'finekick-control.json',{}),sort_keys=True))
report['what_was_measured'].append('The manual larger-kick helper missed backlog claims on 793 and 798. Those completed runs were dry. Their smaller-kick jobs were removed before starting, and both helpers now check exact byte claims.')
report['what_was_measured'].append('Saved-input prefilter: '+json.dumps(read(W/'reopen-ranked.json',{}).get('counts',{}),sort_keys=True)+'. Preparation now runs before the 25-second candidate budget. Old source walks have a 45-second admission budget and remain unqueued when it expires.')
report['what_was_measured'].append('Rechecks of 264, 793 and 798 cleared all history issues and saved 6, 8 and 10 source snapshots, respectively. Search gain by group excludes gain already present in its input packing; the next list ranks that gain per completed scan.')
atomic(T/'report.json',report);note('FINISH report.json written after05:55Z '+json.dumps(dict(rows=len(facts),gain=report['gain'],errors=errors)));print(json.dumps(report,indent=2),flush=True)
