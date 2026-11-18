"""Drain owned workers, verify copies, freeze the take, then publish the timed report."""
import pathlib,sys,os,signal,time,json,csv,hashlib,subprocess,traceback
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
sys.path.insert(0,str(W));import campaign31 as C
R=C.R;REPO=R.parents[1];PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=C.HARD;FREEZE=float((W/'freeze-deadline').read_text());REPORT=float((W/'report-deadline').read_text())
def run(a,timeout=90):return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout,check=True).stdout

def summary():
 jobs=C.load(W/'jobs.json',[]);ends=[];counts={};trials=0
 for j in jobs:
  if j['kind']=='control':continue
  d=C.load(W/'boxE-raw'/j['id']/'done.json',{})
  if not d:continue
  ends.append((j,d));k=j['kind'];c=counts.setdefault(k,dict(jobs=0,errors=0,dry_probes=0,moved=0,side_reduction=0.0));c['jobs']+=1;c['errors']+=bool(d.get('error'));c['dry_probes']+=d.get('search_end')=='dry-probe'
  if d.get('quench_from_certified')and not d.get('error'):
   delta=j['side']-(d['new']+1)*(j['n']**.5)
   if delta>1e-8:c['moved']+=1;c['side_reduction']+=delta
  for p in (W/'boxE-raw'/j['id']).glob('*-*.tsv'):
   trials+=sum(bool(l and l[0].isdigit())for l in p.read_text().splitlines())
 comparison=C.load(W/'comparison.json',dict(improved_n=0,gain=dict(against_base_bar=0,beyond_other_live_r31=0)))
 return jobs,ends,counts,trials,comparison

def report_object():
 jobs,ends,counts,trials,comparison=summary();measure=[f'{len(ends)} production jobs ended with {trials} logged trials.']
 for k,c in counts.items():measure.append(f'{k}: {c["jobs"]} completed receipts, {c["errors"]} errors, {c["dry_probes"]} dry probes stopped, {c["moved"]} side reductions above 1e-8, summed side reduction {c["side_reduction"]:.12g}.')
 early=sum(not d.get('candidate_quenches')for j,d in ends);late=len(ends)-early
 measure.append(f'Early finisher: {early} jobs certified every raw candidate and the start, then quenched the smallest certified file. The revised finisher ended {late} jobs and quenched every distinct certified candidate before comparison.')
 measure+=['Movements compare each certified endpoint with its own start. They are not additive score gains. Only files below bar31 by more than 1e-10 and below every live round31 take count.','The revised finisher certifies every saved candidate and the start with border finesafe. It quenches each distinct certified candidate, compares the completed results, and checks native and pandas clearance of at least 2.2e-11.','Shared starts carry SHA-256 claims. Dry 900-second kicks stop at about 120 seconds. Productive own endpoints retain the complete frozen source walk and numerical receipts.','Held ancestry and own layouts receive no numeric share gate. Direct public-first branches are deferred by this campaign. Missing pins and recorded excluded sources remain refused.']
 controls=C.load(W/'boxE-raw/control907/done.json',{})
 if controls.get('new')is not None:measure.append(f'The stopped907 control reached side {(controls["new"]+1)*(907**.5):.15g}, clearance {controls.get("clearance")}, with completed fq from certified input.')
 transfer=C.load(W/'transfer-check.json',{})
 measure.append('Transfer and cleanup: '+json.dumps(transfer,sort_keys=True))
 measure.append('The all-candidate selection control, submitted-held archive-cut controls and exact direct814 negative control passed. A shared source-tool update changed its share tuple from three fields to four. The lane adapter was repaired, and source errors now defer one input instead of stalling the queue.')
 measure.append('Final comparison time: '+comparison.get('time','none')+'.')
 nxt=['Kick eligible held geometries that have not had a recent kick, then fresh source-valid rectangles and joins. Use exact-byte claims and a 120-second dry probe. Round30 held coverage yielded 494 and 791, while fresh starts moved in 3 of 6 normal jobs.','Continue certified endpoints whose first scan gains more than 1e-6 of side. Give two further seeds after a first gain of at least 1e-5. Preserve the frozen parent graph and certified-input fq receipt.','Keep every raw candidate through certification before selecting the fq input. Round30 bounded702 lost its raw gain at certification, and the older worker finished only the last raw file.']
 from insights31 import insights
 extra,nxt=insights();measure.extend(extra)
 return dict(lane='invent',improved_n=comparison['improved_n'],gain=comparison['gain'],take_dir=str(T),summary=f'Retained {comparison["improved_n"]} rows after certified-input fq and final bar31/live-peer comparison. Report written after the take deadline.',what_was_measured=measure,next=nxt,commits=C.load(W/'commits.json',[]),processes_left=C.load(W/'processes-left.json',{}),blocked=C.load(W/'blocked.json','none'),repo='private repo',branch='main',worktree=str(REPO),pr='none')

def cleanup():
 (W/'STOP').touch()
 pidfile=W/'campaign.pid'
 if pidfile.exists():
  try:os.kill(int(pidfile.read_text()),signal.SIGTERM)
  except ProcessLookupError:pass
 # Match only owned scratch and direct descendants. Search subprocesses are in their own sessions.
 code="""import os,pathlib,subprocess,signal,time,json
D=pathlib.Path.home()/'scratch/squares-invent-r31'
pids={int(p.read_text())for p in D.glob('worker*.pid')}
rows=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines()
owned=set(pids)
for _ in range(4):
 for line in rows:
  a=line.strip().split(None,2)
  if len(a)==3 and int(a[1])in owned:owned.add(int(a[0]))
for pid in owned:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(3)
for pid in owned:
 try:os.kill(pid,signal.SIGKILL)
 except ProcessLookupError:pass
import hashlib
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest()for p in D.rglob('*.csv')}
(D/'transfer-manifest.json').write_text(json.dumps(manifest))
print(json.dumps({'stopped':sorted(owned),'csvs':len(manifest)}))
"""
 remote=W/'cleanup-remote.py';remote.write_text(code)
 run(['rsync','-a',str(remote),C.REMOTE])
 result=run(['ssh','-o','BatchMode=yes','boxE','$SCRATCH/squares-base/venv/bin/python $SCRATCH/squares-invent-r31/cleanup-remote.py'])
 C.state('FINALIZER stopped owned boxE workers '+result.strip())
 # Copy the complete owned directory once, including every CSV and receipt.
 run(['rsync','-a',C.REMOTE,str(W/'boxE-raw')+'/'],timeout=240)
 manifest=json.load(open(W/'boxE-raw/transfer-manifest.json'));bad=[name for name,digest in manifest.items()if not(W/'boxE-raw'/name).is_file()or C.sha(W/'boxE-raw'/name)!=digest]
 if bad:raise RuntimeError('copy hash mismatch '+repr(bad))
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=len(manifest),all_hashes_match=True,boxE_scratch_removed=False))
 C.collect()
 run(['ssh','-o','BatchMode=yes','boxE','rm -rf $SCRATCH/squares-invent-r31'])
 C.atomic(W/'transfer-check.json',dict(csv_files_copied=len(manifest),all_hashes_match=True,boxE_scratch_removed=True))
 C.atomic(W/'processes-left.json',{'boxA':[],'boxE':[],'boxE_scratch_removed':True})
 C.state('FINALIZER every boxE CSV hash checked; removed owned scratch only; no numerical processes remain.')

def compare_local():
 # No rsync after remote cleanup. Re-evaluate all completed immutable receipts against live peers.
 peer=C.peers();best={};jobs=C.load(W/'jobs.json',[])
 for j in jobs:
  if j['kind']=='control':continue
  folder=W/'boxE-raw'/j['id'];d=C.load(folder/'done.json',{});p=folder/'final'/f'{j["n"]}.csv'
  if d.get('error')or not d.get('quench_from_certified')or not p.exists():continue
  if C.sha(p)!=d['sha256']:continue
  n=j['n'];score=d['new']
  if score>=C.BASE[n]-1e-10 or score>=peer[n]:continue
  if not C.G.check(j,p)['clean']:continue
  if score<C.BASE[n]-1e-10 and score<peer[n]and(n not in best or score<best[n][1]['new']):best[n]=(j,d,p)
 rows=[]
 for n,(j,d,p)in sorted(best.items()):
  import shutil
  shutil.copyfile(p,T/f'{n}.csv')
  source='invent round31 '+j['program']+' from '+j['origin']+'; input sha256 '+j['input_sha256']+'; ancestry '+j['ancestry']+'; parent '+j['source']+'; completed certified-input fq receipt '+str(p.parent.parent/'done.json')
  rows.append(dict(n=n,held=C.BASE[n],new=d['new'],gain=C.BASE[n]-d['new'],source=source,licence=j['licence']))
 current={int(r['n'])for r in rows}
 for p in T.glob('*.csv'):
  if int(p.stem)not in current:p.replace(T/'near'/f'{p.stem}-final-superseded.csv')
 tmp=W/'final-take.tmp'
 with tmp.open('w',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=C.FIELDS,delimiter='\t');writer.writeheader();writer.writerows(rows)
 tmp.replace(T/'take.tsv');C.atomic(W/'comparison.json',dict(time=C.now(),improved_n=len(rows),gain=dict(against_base_bar=sum(r['gain']for r in rows),beyond_other_live_r31=sum(peer[r['n']]-r['new']for r in rows))))
 C.state('FINAL COMPARE '+json.dumps(C.load(W/'comparison.json',{})))

def git_record():
 dest=R/'tools/invent/round31';dest.mkdir(exist_ok=True)
 import shutil
 for p in W.glob('*.py'):shutil.copyfile(p,dest/p.name)
 jobs,ends,counts,trials,comparison=summary();results=R/'results/invent-r31-2026-11-16.tsv'
 with results.open('w',newline='')as h:
  writer=csv.writer(h,delimiter='\t');writer.writerow(['job','n','kind','seed','start_side','new_score','side_reduction','search_end','error','input_sha256','source_graph'])
  for j,d in ends:writer.writerow([j['id'],j['n'],j['kind'],j['seed'],j['side'],d.get('new',''),j['side']-(d['new']+1)*math.sqrt(j['n'])if d.get('new')is not None else'',d.get('search_end',''),d.get('error',''),j['input_sha256'],j.get('ancestry','')])
 text='\n## Round 31 (2026-11-15 to 2026-11-16)\n\n'
 text+=f'boxE ran three bounded worker slots. They ended {len(ends)} production jobs and logged {trials} trials.\n'
 text+='Each dry kick stopped after about 120 seconds. Productive searches could use 900 seconds.\n'
 text+='The finisher certified every raw candidate and the start. The first cohort quenched the smallest certified score.\n'
 text+='The revised finisher quenched every distinct certified candidate before comparing completed endpoints.\n'
 text+='Native and pandas reads required clearance of at least 2.2e-11. Shared starts carried exact SHA-256 claims.\n'
 text+='Own endpoints extended the frozen source graph through the completed numerical receipt.\n'
 text+='Held ancestry received no share gate. This campaign deferred direct public-first branches.\n'
 for k,c in counts.items():text+=f'The {k} queue ended {c["jobs"]} jobs. {c["moved"]} shortened side by more than 1e-8.\n'
 text+='Movement is measured from each job start and is not additive score gain.\n'
 text+='The final take and report use the final live comparison at the take deadline.\n'
 text+='Full receipts are in [the round 31 results](../results/invent-r31-2026-11-16.tsv).\n'
 doc=R/'avenues/invent.md'
 if '## Round 31 (2026-11-15 to 2026-11-16)'not in doc.read_text():
  with doc.open('a')as f:f.write(text)
 prose=W/'round31-prose.md';prose.write_text(text)
 check='$STYLE_CHECK/check.py'
 run(['/opt/homebrew/bin/python3',check,'--level','default',str(prose)])
 paths=[str(p.relative_to(REPO))for p in dest.glob('*.py')]+[str(results.relative_to(REPO)),str(doc.relative_to(REPO))]
 run(['git','add','--',*paths]);output=run(['git','commit','--only','-m','Measure round 31 invent searches and certify retained candidates','--',*paths]);commit=run(['git','rev-parse','HEAD']).strip();C.atomic(W/'commits.json',[commit])
 C.state('COMMIT '+commit+' '+run(['git','show','--stat','--oneline',commit]).strip())
 run(['git','pull','--rebase','--autostash']);run(['git','push','origin','HEAD:main']);C.state('PUSH '+commit+' to main')

if __name__=='__main__':
 import math
 os.chdir(REPO)
 C.state('START finalizer deadline00:15Z, final comparison00:24:30Z, atomic report00:25:01Z; work/finish.log')
 while time.time()<HARD:time.sleep(min(15,max(.01,HARD-time.time())))
 try:cleanup()
 except Exception as e:traceback.print_exc();C.atomic(W/'blocked.json','cleanup incomplete: '+str(e));C.state('FINALIZER cleanup error '+str(e))
 try:compare_local();git_record()
 except Exception as e:traceback.print_exc();C.atomic(W/'blocked.json','final record incomplete or not pushed: '+str(e));C.state('FINALIZER record error '+str(e))
 while time.time()<FREEZE:time.sleep(min(15,max(.01,FREEZE-time.time())))
 try:compare_local()
 except Exception as e:traceback.print_exc();C.atomic(W/'blocked.json','final comparison incomplete: '+str(e))
 report=report_object();pending=W/'report.pending.json';pending.write_text(json.dumps(report,indent=2)+'\n')
 while time.time()<REPORT:time.sleep(min(.2,max(.001,REPORT-time.time())))
 # The report is the first operation after the deadline wait.
 pending.replace(T/'report.json')
 C.state('REPORT written after00:25Z; finalizer exits')
