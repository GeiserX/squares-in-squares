"""Stop the lane, verify its archive, publish the final measurements and commit own paths."""
from pathlib import Path
import csv,json,subprocess,sys,time,os,signal,hashlib,shlex,datetime,re,shutil
csv.field_size_limit(16000000)
W=Path(__file__).parent;T=W.parent;B=T.parent;REPO=Path('$PRIVATE_REPO');PY=str(B/'venv/bin/python');R=W/'boxE25'
sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'))
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+s+'\n')
def call(args,name,timeout=180,cwd=None):
 p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=timeout);(W/name).write_text(p.stdout+p.stderr)
 if p.returncode:raise RuntimeError(name+' rc='+str(p.returncode))
 return p.stdout

def stop():
 (W/'STOP-COLLECT').touch();p=W/'collector-pid'
 if p.exists():
  pid=int(p.read_text());cmd=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
  if str(W/'manage25.py') in cmd:
   os.killpg(pid,signal.SIGTERM);time.sleep(2)
 remote='''from pathlib import Path
import subprocess,os,signal,time,json
r=Path.home()/'scratch/squares-twoshort';(r/'STOP25').touch();time.sleep(5);events=[]
for name in ['worker1.pid','worker2.pid']:
 p=r/name
 if not p.exists():continue
 pid=int(p.read_text());cmd=subprocess.run(['/bin/ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
 if str(r/'worker25.py') not in cmd:continue
 lines=subprocess.check_output(['/bin/ps','-axo','pid,ppid,pgid,command'],text=True).splitlines()[1:]
 for line in lines:
  x=line.split(None,3)
  if len(x)<4 or int(x[1])!=pid:continue
  child=int(x[0]);group=int(x[2])
  if group==child:
   try:os.killpg(group,signal.SIGTERM);events.append(dict(child=child,worker=pid))
   except ProcessLookupError:pass
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(2)
(r/'stopped-owned.json').write_text(json.dumps(events))
print(events)
'''
 call(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(remote)],'stop-owned.log',60)
 state('STOP owned workers and collector; ownership checked by absolute command and recorded PID files. Deadline02:45UTC.')

def finalize():
 if '--at-deadline' in sys.argv:
  while time.time()<int((W/'deadline').read_text())+3:time.sleep(min(30,max(1,int((W/'deadline').read_text())+3-time.time())))
 if (W/'FINALIZED').exists():return
 try:(W/'FINALIZE-CLAIM').mkdir()
 except FileExistsError:return
 stop()
 if not (W/'final-collection-coverage.json').exists():call([PY,str(W/'manage25.py'),'--no-intake'],'final-collect.log',300)
 call([PY,str(W/'copy25.py')],'final-copy.log',300)
 call([PY,str(W/'certify25.py'),str(W/'stage')],'final-certify.log',240)
 call([PY,str(W/'prune_take25.py')],'final-prune.log',180)
 call([PY,str(W/'audit_near25.py')],'final-near-audit.log',240)
 state('FINISH final collection and verified boxE copy; waiting for final take boundary. Log work/final-copy.log.')
 boundary=int(datetime.datetime(2026,11,14,2,55,tzinfo=datetime.timezone.utc).timestamp())
 while time.time()<boundary:time.sleep(min(30,max(1,boundary-time.time())))
 call([PY,str(W/'prune_take25.py')],'final-boundary-prune.log',120)
 from bar25 import base
 from admit25 import store
 from source25 import credited_cells
 import floatsafe
 base_scores=base();rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));peers=dict(base_scores)
 for p in B.glob('take-*-r25/take.tsv'):
  if p.parent==T:continue
  for r in csv.DictReader(open(p),delimiter='\t'):peers[int(r['n'])]=min(peers[int(r['n'])],float(r['new']))
 keep=[]
 for r in rows:
  n=int(r['n']);file=T/(str(n)+'.csv');ok,_=store(dict(source=r['source'],licence=r['licence']),n=n)
  data=[{k:x[k] for k in ['n','square_id','x','y','angle']} for x in csv.DictReader(open(file))];_,fr,score,error=floatsafe.work((n,data))
  if ok and credited_cells(r['source'],r['licence']) and fr is not None and score<base_scores[n]-1e-10 and score<peers[n]-1e-10:
   r.update(held=base_scores[n],new=score,gain=base_scores[n]-score)
   tmp=file.with_suffix('.csv.tmp')
   with tmp.open('w',newline='') as f:
    cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
   tmp.replace(file);keep.append(r)
  else:
   dst=T/'near'/(str(n)+'-final-withheld.csv');shutil.copy2(file,dst);dst.with_suffix('.json').write_text(json.dumps(r));file.unlink();state('DROP final row '+str(n)+' failed source, numerical or live comparison.')
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(keep)
 (T/'take.tsv.tmp').replace(T/'take.tsv')
 kept_names={str(r['n'])+'.csv' for r in keep}
 for p in T.glob('*.csv'):
  if p.name not in kept_names:
   d=W/'orphaned-final';d.mkdir(exist_ok=True);p.replace(d/p.name);state('DROP orphan top-level csv '+p.name)
 call([PY,str(W/'results25.py'),str(W/'results-current.tsv')],'final-results.log',60)
 manifest=json.load(open(R/'final-manifest.json'));valid_files=set(manifest['files']);valid_dirs=set(manifest.get('dirs',[]))
 done=[json.load(open(p)) for p in R.glob('done/*.json') if str(p.relative_to(R)) in valid_files];kicks=[d for d in done if 'tries' in d and not d.get('tag','').startswith('control')];builds=[p for p in R.glob('designs/*/builds/*.json') if not p.parent.parent.name.startswith('control')];qs=[json.load(open(p)) for p in R.glob('q/*/meta.json')];screens=[d for d in done if d.get('kind')=='design' and d.get('rc')==0]
 pending=[json.load(open(p)) for p in R.glob('jobs/*.json') if str(p.relative_to(R)) in valid_files and 'locks/'+p.name not in valid_dirs and 'done/'+p.name not in valid_files];specs=sum(len(json.load(open(p))) for p in R.glob('designs/*/unstarted.json'))
 gain=sum(base_scores[int(r['n'])]-float(r['new']) for r in keep);extra=sum(peers[int(r['n'])]-float(r['new']) for r in keep);copy=json.load(open(W/'copy-verified.json'))
 stats=dict(kicks=len(kicks),tries=sum(d['tries'] for d in kicks),builds=len(builds),screens=len(screens),quenches=sum(q.get('quench_rc')==0 for q in qs),pending_jobs=len(pending),saved_specs=specs,copy=copy)
 (W/'final-stats.json').write_text(json.dumps(stats,indent=2))
 results=REPO/'lanes/squares/results/twoshort-r25-2026-11-14.tsv';shutil.copy2(W/'results-current.tsv',results)
 section=f'''## 15. Round 25 (2026-11-13 and 14)

The final take retains {len(keep)} counts.
Its gain is {gain:.12g} against the source-admitted base and {extra:.12g} beyond the other live takes.
The [measurement table](../results/twoshort-r25-2026-11-14.tsv) records {len(kicks)} kick scans, {stats['tries']} tries and {len(builds)} builds.
The lane completed {len(screens)} library screens and {stats['quenches']} quenches on two boxE slots.

The first saved 975 build crossed its base by 6.4434e-9 of score.
Its raw kick removed 2.438388e-6 of side in 18 tries.
Invent then held the same floor within 1.6e-14 of score, so this lane withdrew 975.
The 968 kick removed 2.3975e-5 of side in nine tries and completed its quench.
The 918 transplant lost 1.3387e-5 of side and its continuation was dry in 15 tries.
It remained above the proved round 24 reference.
Four 974 family starts were dry in 44 tries.
Unchanged joint row and column transfers stayed closed.

### Source and intake checks

Source evidence is cached by hash and donor version.
The checker selects one provenance-registry row, which avoids unrelated source histories.
Its control accepts the selected own row and rejects the selected unlicensed row.
A classfill input hash and its selected producer row close the frozen 918 tree.
Reader snapshot 6851644d preserves the old 911 parent when its live file changes.
New metadata can admit a refused file and later source changes can revoke that admission.
File-byte pins and selected source-record pins use separate hash checks.
Their control accepts unchanged evidence and rejects changed bytes or metadata.
Overlapping copies fail the numerical control, while the known 973 packing passes.

New library requests keep their named modules and admitted partners.
The pair control preserves all three original 973 module and lens pairs exactly.
Family screens retain the original 48 counts and add fresh hosts, shells and matching side fractions.
Each build batch has a six-minute limit and each build call has a two-minute limit.
A queue control promotes one family alongside raw layouts and blocks replayed aliases.

The collector stalled during module cleanup after its 01:29 checkpoint.
It restarted at 02:10, and collecting commands now flush output and exit directly.
The final archive verifies {copy['files']} files and {copy['symlinks']} symlinks.
It preserves {len(pending)} pending jobs and {specs} saved specifications.
The lane removes its boxE scratch after the verified copy and preserves squares-base.
The [round 25 tools](../tools/twoshort/r25/) hold the worker, source checks and collection code.

'''
 (W/'round25-section.md').write_text(section)
 call(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round25-section.md')],'readable.log',60)
 doc=REPO/'lanes/squares/avenues/twoshort.md';text=doc.read_text();marker='## 15. Round 25 (2026-11-13 and 14)'
 if marker in text:text=text[:text.index(marker)]+text[text.index('## Files',text.index(marker)):]
 text=text.replace('## Files',section+'## Files',1);doc.write_text(text)
 dest=REPO/'lanes/squares/tools/twoshort/r25';dest.mkdir(parents=True,exist_ok=True);names=[]
 for p in W.glob('*.py'):
  if p.name in ['setup25.py']:continue
  shutil.copy2(p,dest/p.name);names.append(str((dest/p.name).relative_to(REPO)))
 paths=['lanes/squares/avenues/twoshort.md','lanes/squares/results/twoshort-r25-2026-11-14.tsv']+sorted(names)
 call([PY,'-m','compileall','-q',str(dest)],'compile.log',60);call(['git','diff','--check','--',*paths],'diff-check.log',60,REPO)
 def git(args,name,timeout=90):
  for attempt in range(2):
   p=subprocess.run(args,cwd=REPO,capture_output=True,text=True,timeout=timeout);(W/name).write_text(p.stdout+p.stderr)
   if p.returncode==0:return p.stdout
   if 'index.lock' in p.stderr and attempt==0:time.sleep(3);continue
   raise RuntimeError(name+' rc='+str(p.returncode))
 message='squares: record twoshort round 25 measurements and source checks'
 command=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m',message,'--',*paths]);git(['/bin/zsh','-c',command],'commit.log')
 commit=git(['git','log','-1','--format=%H','--grep=^'+message+'$'],'commit-sha.log').strip();stat=git(['git','show','--stat',commit],'commit-stat.log');changed=git(['git','diff-tree','--no-commit-id','--name-only','-r',commit],'commit-paths.log').splitlines();assert set(changed)<=set(paths)
 pushed=False
 for attempt in range(2):
  try:
   git(['git','pull','--rebase','--autostash'],'pull.log');git(['git','push','origin','HEAD:main'],'push.log');pushed=True;break
  except Exception:
   if attempt==0:time.sleep(3)
 commit=git(['git','log','-1','--format=%H','--grep=^'+message+'$'],'commit-final-sha.log').strip()
 # The copy is already verified and no remote process may own this root.
 cleanup='''from pathlib import Path
import subprocess,shutil,json
r=Path.home()/'scratch/squares-twoshort'
text=subprocess.check_output(['/bin/ps','-axo','pid,command'],text=True)
for line in text.splitlines():
 if str(r/'worker25.py') in line:raise RuntimeError('owned worker remains: '+line)
shutil.rmtree(r)
print('removed verified squares-twoshort; squares-base preserved')
'''
 call(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -c '+shlex.quote(cleanup)],'cleanup.log',60)
 report=dict(lane='twoshort',improved_n=len(keep),gain=dict(base_bar=gain,other_live_r25=extra),take_dir=str(T),summary=f'Retained {len(keep)} counts after certified-input boxE quenches, source checks and final peer comparisons. '+('Commit pushed to main.' if pushed else 'Commit not pushed.'),what_was_measured=[f"{len(kicks)} kick scans, {stats['tries']} tries, {len(builds)} full builds, {len(screens)} completed library screens and {stats['quenches']} completed quenches.", 'The saved 975 build crossed its reference by 6.4434e-9 score before invent superseded it at the same floor. Its first continuation was dry.', 'The 968 kick removed 2.3975e-5 of side in nine tries and completed its certified-input quench. File-byte and selected-record pin controls passed.', 'The collector stalled in Python module cleanup after the 01:29 checkpoint until its 02:10 restart. Collecting commands now flush output and exit directly.', 'The fresh 918 kick removed 1.3387e-5 of side, but its continuation was dry in 15 tries and it remained above the clean frozen 918.', 'The frozen 918 source audit selected registry row 917 and matched the classfill input SHA; unrelated unlicensed row 581 was excluded from that source tree.', 'Positive controls rebuilt 973 exactly, improved 793, preserved exact module/lens pairs and rejected an overlap, changed source metadata and prohibited roots.', f"Final copy verified {copy['files']} files and {copy['symlinks']} symlinks before boxE scratch removal.", 'An early basename-only process stop on PID42658 lacked cwd proof. The handoff log flags its unconfirmed owner. Subsequent stops use owned PID files and absolute commands.'],next=['Run fresh licensed whole layouts and give useful raw finds one continuation. The 968 scan removed 2.3975e-5 of side in nine tries and its quenched file passed the source walk.', f"Run fresh module families on their hosts and matching fractions next. The saved 975 build crossed its reference, while the old 48-count-only screens missed fresh host targets. {specs} full specifications remain.", 'Give each useful raw find one continuation. The 860 leg removed 0.0001409587 of side, while the 918 leg was dry in 15 tries.', f"Rerank the {len(pending)} pending jobs by the next clean base and skip backlog claims. Preserve full module specifications and six-minute batches.", 'Keep selected-row registry and immutable reader snapshots. The 918 audit otherwise followed unrelated 581, and the reader 911 live parent differs from its retained snapshot.', 'Leave unchanged 974 floors and joint transfers closed. Four 974 starts were dry in 44 tries; round 23 joint transfers settled 109 starts without a qualifying row.'],commits=[commit],processes_left='None owned by this lane. boxE workers, descendants and local collector stopped. Verified boxE scratch removed; squares-base preserved.',blocked='none' if pushed else 'not pushed',repo='private repo',branch='main',worktree=str(REPO),pr='none')
 (T/'report.json').write_text(json.dumps(report,indent=2));(W/'FINALIZED').write_text(time.strftime('%FT%TZ',time.gmtime()));state('FINAL report.json written; commit '+commit+(' pushed.' if pushed else ' not pushed.'));print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':
 try:
  finalize();sys.stdout.flush();sys.stderr.flush();os._exit(0)
 except Exception as e:state('FINALIZER ERROR '+repr(e));(W/'finalize-error.txt').write_text(repr(e));raise
