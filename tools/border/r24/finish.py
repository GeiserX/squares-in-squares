from pathlib import Path
import subprocess,sys,json,csv,hashlib,os,time,datetime,math,collections,shutil
csv.field_size_limit(16*1024*1024)
W=Path(__file__).parent;T=W.parent;S=T.parent;R=Path('$PRIVATE_REPO');L=R/'lanes/squares';P=str(S/'venv/bin/python');REMOTE='boxC:scratch/squares-border-r24/'
def log(msg):
 line=datetime.datetime.now(datetime.timezone.utc).isoformat()+' boxA '+msg
 print(line,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(line+'\n')
def run(args,**kw):
 for attempt in range(2):
  r=subprocess.run(args,capture_output=True,text=True,**kw)
  if r.returncode and 'index.lock' in r.stderr and not attempt:time.sleep(3);continue
  if r.stdout:print(r.stdout,flush=True)
  if r.returncode:print(r.stderr,flush=True);r.check_returncode()
  return r.stdout
end=float((W/'deadline').read_text())
if '--now' not in sys.argv:
 while time.time()<end:time.sleep(min(30,end-time.time()))
log('FINISH search and certified-file quenches share22:15Z. Stop owned collector and workers, then drain completed proofs.')
pid=int((W/'driver.pid').read_text())
cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
if str(W/'driver.py') in cmd:
 try:os.kill(pid,15)
 except ProcessLookupError:pass
stop='''/usr/bin/python3 - <<'STOP'
from pathlib import Path
import subprocess,os,signal
r=Path.home()/'scratch/squares-border-r24'
pids=[]
for name in ['worker1.pid','worker2.pid','control.pid']:
 try:pid=int((r/name).read_text())
 except (OSError,ValueError):continue
 cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
 cwd=subprocess.run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True).stdout
 if ('n'+str(r)) in cwd.splitlines() and ('worker.py' in cmd or 'fast_control.py' in cmd):pids.append(pid)
for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 parts=line.strip().split(None,2)
 if len(parts)<3:continue
 pid,ppid,cmd=parts
 if int(ppid) in pids or str(r)+'/fq ' in cmd:
  try:os.kill(int(pid),signal.SIGTERM)
  except ProcessLookupError:pass
for pid in pids:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
print('stopped owned workers',pids)
STOP'''
run(['ssh','boxC',stop])
# Read functions without running the scanner loop or reinitializing queues.
s=(W/'driver.py').read_text();s=s[:s.index("log('start round24 collector/scanner")]
ns={'__name__':'border_drain','__file__':str(W/'driver.py')};exec(compile(s,str(W/'driver.py'),'exec'),ns)
ns['refresh']();ns['sync']();ns['collect']();ns['refresh']()
run([P,'-I',str(W/'export_raw_near.py')])
archive=W/'remote-final';archive.mkdir(exist_ok=True)
run(['rsync','-a',REMOTE,str(archive)+'/'])
proof=json.loads(run(['ssh','boxC',"cd $SCRATCH/squares-border-r24; /usr/bin/python3 - <<'PY'\nfrom pathlib import Path\nimport hashlib,json\nprint(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('.').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))\nPY"]))
assert all((archive/p).exists() and hashlib.sha256((archive/p).read_bytes()).hexdigest()==h for p,h in proof.items())
(W/'remote-sha256.json').write_text(json.dumps(proof,indent=2));log(f'copied {len(proof)} remote files and verified SHA-256')
log('workers stopped and archive verified. Final competing-take refresh at22:23Z, before22:25 take deadline.')
if '--now' not in sys.argv:
 while time.time()<end+480:time.sleep(min(30,end+480-time.time()))
ns['refresh']()
validation=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);pol=ns['sp'].classify(row['source'],row['licence'])
 assert ns['qualifies'](n,float(row['new']),pol)
 ref=ns['sp'].OLD22[n] if n in ns['sp'].RELAXED and pol['status']=='none' else ns['held'][n]
 validation.append(dict(n=n,score=ref))
with open(W/'validation-details.csv','w') as f:
 wr=csv.DictWriter(f,fieldnames=['n','score']);wr.writeheader();wr.writerows(validation)
run([P,'-I',str(L/'literature_check.py'),str(W/'validation-details.csv'),str(T)])
run([P,'-I',str(W/'verify_proofs.py')]);run([P,'-I',str(W/'measure.py')])
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
# Preserve complete notices for frozen parents that were accepted in the candidate.
import re
# Publication already appends notices from the pinned parent tree.
# Method or comparison references are not extra ancestry roots.
for row in rows:
 row['source'],row['licence']=ns['enrich_source'](row['source'],row['licence'])
kept=[]
for row in rows:
 pol=ns['sp'].classify(row['source'],row['licence'])
 row['licence']=re.sub(r'Samanyu ancestry:[^;\n]*','',row['licence']).strip('; ')+'; '+ns['sp'].label(pol)
 n=int(row['n']);ref=ns['sp'].OLD22[n] if n in ns['sp'].RELAXED and pol['status']=='none' else ns['held'][n]
 row['held']=repr(ref);row['gain']=repr(ref-float(row['new']))
 if ns['qualifies'](n,float(row['new']),pol):kept.append(row)
 else:
  n=int(row['n']);dst=T/'near'/f'{n}-final-source-policy.csv'
  if (T/f'{n}.csv').exists():shutil.move(T/f'{n}.csv',dst)
  dst.with_suffix('.json').write_text(json.dumps(row,indent=2));log(f'withdrew {n} after complete source notices')
rows=kept
ns['write_take'](rows)
held=ns['held'];bars={n:float(r['new']) for n,r in ns['current'].items()}
assert all(ns['qualifies'](int(r['n']),float(r['new']),ns['sp'].classify(r['source'],r['licence'])) for r in rows)
gain=sum(held[int(r['n'])]-float(r['new']) for r in rows);extra=sum(ns['policy_floor'](int(r['n']),ns['sp'].classify(r['source'],r['licence']))-float(r['new']) for r in rows)
public_b=dict(held)
for n in ns['sp'].RELAXED:public_b[n]=ns['sp'].OLD22[n]
gain_b=sum(public_b[int(r['n'])]-float(r['new']) for r in rows)
measures=list(csv.DictReader(open(W/'measure.tsv'),delimiter='\t'));starts=sum(int(r['starts']) for r in measures)
manifest={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')};pending=[]
for p in (W/'q').glob('*.job.json'):
 ident=p.name.removesuffix('.job.json');r=manifest[ident]
 if not p.with_name(ident+'.k0.json').exists():
  j=json.load(open(p));n=int(r['n']);pending.append(dict(id=ident,donor=r['donor'],n=n,kind=r['kind'],margin=float(r['built_L'])-(bars[n]+1)*math.sqrt(n),priority=j['priority'],source=r['donor_source'],job=str(p)))
pending.sort(key=lambda x:(x['priority'],x['margin']))
with open(W/'unstarted.tsv','w') as f:
 wr=csv.DictWriter(f,fieldnames=['id','donor','n','kind','margin','priority','source','job'],delimiter='\t');wr.writeheader();wr.writerows(pending)
near=len(list((T/'near').glob('*.csv')));done=len(list((W/'final').glob('*.job.done')))
result=L/'results/border-r24-2026-11-13.tsv';result.write_bytes((T/'take.tsv').read_bytes())
section=f'''\n### Round 24: fresh closure and shell returns (2026-11-13)\n\nThe final take holds {len(rows)} n. Its gain against the round 23 candidate is {gain:.12f}. Its gain beyond other live round 24 takes in the same source group is {extra:.12f}. Against the round 23b file, it gains {gain_b:.12f}. Sources and licences are in [the results table](../results/border-r24-2026-11-13.tsv).\n\nTwo quench slots ran on boxC until 22:15 UTC. The collector measured {starts} starts on {len(measures)} donor pairs. It read {done} completed certified-file quench jobs and exported {near} near layouts. Another {len(pending)} starts have no record. Their exact inputs remain in `take-border-r24/work/unstarted.tsv`.\n\nFresh round 24 files took priority over the frozen queue. The named near files of 992, 929 and 851 each received a one-shell cut and a restored border. Each set has four cuts and four border orientations. The raw near feed ran after each queue sync from the first saved result. Its side limit stayed at 0.015.\n\nThe first two-default control used a different saved input and missed its threshold at side 30.907306623320885. The exact archived input then passed at 30.902488813593994. One slot used those defaults. The other kept the default and deep calls. A two-border control certified 485 to 577 at side 24.525789210324547 against a deliberately raised bar. A duplicate-square control failed. The ancestry control rejected a poisoned parent from the excluded harvest 745.\n\nThe main handoff held 20 candidate rows for Samanyu seed ancestry. Recorded public and original roots can replace those rows against round 22. Samanyu descendants keep the candidate-a bar and name their seed n. Unresolved seed ancestry cannot enter the take. The lane imports the soft and forensics source policies. The table's old score follows the row's eligibility reference.\n\nA provisional 228 matched candidate-a numerically. Its full parent tree reached Samanyu seed 365 through 735, so it left the take. The local donor labels had missed that root. The new control binds a retained descriptor to a byte-identical donor CSV. It refuses a descriptor whose recorded end differs by 0.1.\n\nAt 21:34 UTC a 735 window of the new CC0-derived 847 passed its numerical and source checks. Its input tree ends in samanyu1808/sis-final-packings at n=123 and n=365. It matches candidate-a and recovers 0.000291795863 against round 23b.\n\nThe source check follows versioned reader records and source-override sidecars. A clean new 918 passed. The excluded harvest 745 and old forensics 980 failed. The geometry audit found no equivalent starts at 1e-8 precision and no completed round 23 repeats.\n\nThe fresh border cap rose from 0.012 to 0.02 after a reader 921 was skipped at margin 0.012768. It has 17 and 16 tilted wall contacts. Queue priority follows earlier measured yields. Its control puts 931 before 911 and 873. A saved chain within 0.001 of the bar gets priority after closing 75% of its margin.\n\nThree gap variants on the first promising 634-to-685 donor passed floatsafe at side 26.6884042288564. They move the free gap to the first or last tilted wall square. Their measurements are included below.\n\nEvery retained result passed floatsafe and the independent metric and clearance checks. Its certified input received an fq quench on boxC. The final archive passed SHA-256 comparisons before the scratch was removed. All owned workers stopped.\n\n| donor | target | kind | starts | best give-back | raw end minus live bar |\n|---|---|---|---|---|---|\n'''
for r in measures:
 section+='| '+' | '.join([r['donor'],r['n'],r['kind'],r['starts'],f"{float(r['giveback']):.7g}",f"{float(r['end_minus_bar']):.7g}"])+' |\n'
(W/'round24-section.md').write_text(section)
run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round24-section.md')])
doc=L/'avenues/literature.md';text=doc.read_text();idx=text.find('\n### Round 24:');doc.write_text((text if idx<0 else text[:idx])+section)
# Preserve the exact lane runners that generated the queue and receipts.
code=L/'tools/border/r24';code.mkdir(exist_ok=True)
files=['driver.py','worker.py','initial_queue.py','provenance.py','export_raw_near.py','verify_proofs.py','measure.py','prioritize_r24.py','gap_follow.py','recover_unstarted.py','source_policy.py','finish.py']
for name in files:shutil.copyfile(W/name,code/name)
paths=['lanes/squares/avenues/literature.md','lanes/squares/results/border-r24-2026-11-13.tsv']+['lanes/squares/tools/border/r24/'+name for name in files]
def check_commit(sha):
 run(['git','show','--stat','--oneline',sha],cwd=R)
 names=set(run(['git','diff-tree','--no-commit-id','--name-only','-r',sha],cwd=R).splitlines())
 assert names and names<=set(paths), 'commit contains paths outside the border lane: '+str(names-set(paths))
 assert str(result.relative_to(R)) in names
import shlex
quoted=' '.join(shlex.quote(p) for p in paths)
run(['zsh','-c',f"git add {quoted} && git commit --only {quoted} -m 'squares: record border round 24 closure and returns'"],cwd=R)
sha=run(['git','log','-1','--format=%H','--',str(result.relative_to(R))],cwd=R).strip();check_commit(sha)
pushed=False
for attempt in range(2):
 try:
  run(['git','pull','--rebase','--autostash'],cwd=R)
  sha=run(['git','log','-1','--format=%H','--',str(result.relative_to(R))],cwd=R).strip()
  check_commit(sha)
  run(['git','push','origin','HEAD:main'],cwd=R);pushed=True;break
 except subprocess.CalledProcessError:
  if not attempt:time.sleep(3)
run(['ssh','boxC','rm -rf $SCRATCH/squares-border-r24'])
measurements=[f"{r['donor']} -> {r['n']} ({r['kind']}): {r['starts']} starts, best give-back {float(r['giveback']):.9g}, raw end minus live bar {float(r['end_minus_bar']):.9g}." for r in measures]
pending_proofs=[]
ours={int(r['n']):float(r['new']) for r in rows}
for job in (W/'final').glob('*.job.json'):
 meta=json.load(open(job));receipt=job.with_suffix('.done')
 if receipt.exists() and json.load(open(receipt)).get('side') is not None:continue
 n=int(meta['n']);pol=ns['sp'].manifest_policy(meta['manifest'])
 if pol['status']=='unknown':continue
 bar=ns['policy_floor'](n,pol);score=meta['certified_before']
 own=next((r for r in rows if int(r['n'])==n),None)
 if own and not(n in ns['sp'].RELAXED and pol['status']=='none' and ns['sp'].classify(own['source'],own['licence'])['status']!='none'):bar=min(bar,float(own['new']))
 if score<bar-1e-10:pending_proofs.append(dict(n=n,score=score,gain=bar-score,job=str(job)))
pending_proofs.sort(key=lambda q:-q['gain'])
with open(W/'pending-proofs.tsv','w') as f:
 wr=csv.DictWriter(f,fieldnames=['n','score','gain','job'],delimiter='\t');wr.writeheader();wr.writerows(pending_proofs)
next_items=[]
# Keep the best measured future inputs first.
for r in sorted(measures,key=lambda r:float(r['end_minus_bar'])):
 if float(r['end_minus_bar'])>0 and float(r['giveback'])>1e-5:
  next_items.append(f"Try a changed shell return on {r['n']} from donor {r['donor']}. It gave back {float(r['giveback']):.9g} of side and missed the final bar by {float(r['end_minus_bar']):.9g}. Saved endpoints are in near/.")
 if len(next_items)>=3:break
next_items.insert(0,'Close fresh rectangle and joined designs before repeats. Round 23 donor 847 opened 735 and 790. This round reserved both worker slots for fresh handoffs before the frozen queue.')
next_items.insert(0,'Trace full immutable parent trees before counting clean replacements. A numerically proved 228 was withdrawn when the 735 parent tree exposed Samanyu seed 365. Local donor labels had missed that root.')
next_items.append(f'Rerank work/unstarted.tsv against the next candidate. It retains {len(pending)} exact starts without a quench record. Fresh geometry paid in earlier rounds and repeated floors did not.')
next_items=[f"Finish the saved certified-input proof for n={r['n']} before repeating search. Its staged score is {r['gain']:.9g} below the final live bar, but its required remote quench did not finish: {r['job']}" for r in pending_proofs]+next_items
report=dict(lane='border',improved_n=len(rows),gain=dict(against_round23_candidate=gain,beyond_other_live_r24_same_source_group=extra,against_round23b=gain_b),take_dir=str(T),summary=f'Final take: {len(rows)} n. Measured {starts} starts on {len(measures)} donor pairs, read {done} certified-input quench receipts, exported {near} near layouts. '+('Committed and pushed.' if pushed else 'Committed, not pushed.'),what_was_measured=['At 21:34, the 735 window of the new CC0-derived 847 passed the independent metric, clearance and byte-exact proof checks. Its full input tree ends in samanyu1808/sis-final-packings CC0 files n=123 and n=365. It matches candidate-a and recovers 0.000291795863 against submitted 23b at first publication.','Withdrew a provisional 228 after its numerical proof. The full 735 parent tree exposed Samanyu seed 365, so it did not qualify against candidate-a. A retained descriptor bound to identical donor bytes now supplies the full trace. A descriptor end changed by 0.1 is refused. No 228 gain is counted.','Applied the main 20:05 source-group handoff by importing soft and forensics policies. Every take row labels Samanyu seed n or recorded public/own roots. A clean 735 midpoint between candidate-a and round 22 passed; the same score with Samanyu seed 365 failed. Unknown seed ancestry is excluded.','The exact archived two-default control passed at side 30.902488813593994. An earlier control used a different input and failed at 30.907306623320885.','The two-border positive control certified 485 to 577 at side 24.525789210324547 against a worsened bar. Duplicate squares and a forbidden 745 ancestor were rejected.','Built 48 shell-return starts from the three named near files. Each named target received a first pass. Fresh r24 donors had priority over the frozen backlog.', 'The geometry audit found 0 equivalent starts at 1e-8 and 0 completed r23 repeats. Source-override 534 and versioned reader 921 controls passed. Fresh clean 918 passed while excluded harvest 745 and old forensics 980 failed.', 'The reader 921 border at margin 0.012768005837568097 and walls 17/16 exposed the old 0.012 cap. Fresh r24 borders now use 0.02. Queue ranking control puts 931 before 911 before 873 and advances saved rounds closing 75% within 0.001 of the bar.','Raw float-safe near export ran from the first saved result with a 0.015 side cap. Near files stayed outside the take until the required certified-file quench completed.','The first and last tilted-wall gap variants 6,18,26 on donor 634 passed floatsafe as 685 starts at side 26.6884042288564. They change the border free-gap placement. A saved 685 first round that gave 0.001676 of side received continuation priority.', 'Every final file passed the independent metric and clearance check and the byte-exact certified-input proof check.',f'Copied and SHA-256-verified {len(proof)} remote files before cleanup. All owned processes stopped.']+[f"Retained n={r['n']}, score {float(r['new']):.16g}, gain against candidate-a {held[int(r['n'])]-float(r['new']):.9g}, against submitted 23b {public_b[int(r['n'])]-float(r['new']):.9g}; {ns['sp'].label(ns['sp'].classify(r['source'],r['licence']))}." for r in rows]+measurements,next=next_items,commits=[sha],processes_left='none',blocked='' if pushed else 'not pushed',repo=str(R)+' (private repo)',branch='main',worktree=str(R),pr='none (direct push to main, '+('pushed' if pushed else 'not pushed')+')')
(T/'report.json').write_text(json.dumps(report,indent=2)+'\n');log('FINAL report.json written, take.tsv matches committed table, no owned workers remain')
print(json.dumps(report,indent=2),flush=True)
