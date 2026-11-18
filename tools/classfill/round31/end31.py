"""Freeze the take before assembly and write the report first at its deadline."""
import sys,time,subprocess,os,signal,json,hashlib,csv,math,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import run31 as C
T=C.T;S=C.S;END=C.END;FINAL=END+600;REPO=Path('$PRIVATE_REPO');errors=[]
def until(t):
 while time.time()<t:time.sleep(min(30,t-time.time()))
def safe(fn,label):
 try:return fn()
 except Exception as e:errors.append(label+': '+repr(e));C.note('FINAL_ERROR '+label+' '+repr(e));return None

def stop():
 (W/'STOP').touch()
 ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True);entries={}
 for line in ps.splitlines()[1:]:
  q=line.strip().split(None,2)
  if len(q)==3 and q[0].isdigit() and q[1].isdigit():entries[int(q[0])]=(int(q[1]),q[2])
 roots=set()
 for file,script in [('controller-pid','run31.py'),('freshguard-pid','freshguard31.py')]:
  if not (W/file).exists():continue
  pid=int((W/file).read_text())
  if pid in entries and str(W/script) in entries[pid][1]:roots.add(pid)
 owned=set(roots)
 for _ in range(8):owned|={pid for pid,(parent,command) in entries.items() if parent in owned}
 for pid in sorted(owned,reverse=True):
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 time.sleep(.5)
 for pid in owned:
  command=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
  if str(W) in command or C.ROOT in command:
   try:os.kill(pid,signal.SIGKILL)
   except ProcessLookupError:pass
 C.atom(W/'local-stop-receipt.json',dict(stopped=sorted(owned),time=C.now()))
 for host in dict(C.HOSTS):
  if not C.read(W/'stop-prestaged.json',{}).get(host):
   for f in W.glob('owned-'+host+'-*.json'):C.cmd(['scp','-q',str(f),host+':'+C.ROOT+'/'+f.name])
   C.cmd(['scp','-q',str(W/'stop31.py'),host+':'+C.ROOT+'/stop31.py'])
  py='$SCRATCH/squares-base/venv/bin/python' if host=='boxE' else '$SCRATCH/squares-readers/venv/bin/python'
  C.note('STOP_REMOTE '+host+' '+C.cmd(['ssh',host,py+' '+C.ROOT+'/stop31.py'],timeout=70).strip())

def archive():
 result={}
 for host in dict(C.HOSTS):
  local=W/('remote-final-'+host);local.mkdir(exist_ok=True)
  C.cmd(['rsync','-az',host+':'+C.ROOT+'/',str(local)+'/'],timeout=120)
  manifest=C.read(local/'archive-manifest.json',{});assert manifest.get('files'),host+' missing manifest'
  for name,rec in manifest['files'].items():
   p=local/name;assert p.is_file() and C.sha(p)==rec['sha256'],host+' changed '+name
  assert not manifest.get('remaining'),host+' has live processes'
  result[host]=dict(files=len(manifest['files']),bytes=sum(r['bytes'] for r in manifest['files'].values()),remaining=manifest.get('remaining'))
  # Required results are already in the verified full copy and collected local out.
  C.cmd(['ssh',host,'rm -rf '+C.ROOT])
 C.atom(W/'archive-verification.json',result);return result

def finalcompare():
 base,live=C.bars();take={}
 for r in C.rows(T/'take.tsv'):
  n=int(r['n']);score=float(r['new'])
  if score<live[n]-1e-10 and (T/f'{n}.csv').exists():take[n]=r
  else:
   C.note('FINAL_SUPERSEDED n'+str(n));(T/f'{n}.csv').unlink(missing_ok=True)
 C.table(take);return take

def measurements():
 allrecords=[C.read(p,{}) for p in (W/'candidates').glob('*.json')];records=[r for r in allrecords if r.get('job',{}).get('n',0)>40];stats={};tries=0;finds=0;probes=0
 for host in dict(C.HOSTS):
  for p in (W/host/'out').glob('finish-*/kick/scan-*.tsv'):
   tag=p.parent.parent.name.removeprefix('finish-')
   if C.read(W/'jobs'/f'{tag}.json',{}).get('n',0)<=40:continue
   for l in p.read_text().splitlines():
    if l[:1].isdigit():tries+=1
    if l.startswith('# FIND'):finds+=1
  for p in (W/host/'out').glob('finish-*/kick/probe.json'):
   tag=p.parent.parent.name.removeprefix('finish-')
   if C.read(W/'jobs'/f'{tag}.json',{}).get('n',0)>40:probes+=bool(C.read(p,{}).get('stopped_no_find'))
 for r in records:
  j=r['job'];kind=j['kind'];st=stats.setdefault(kind,dict(scans=0,changed=0,max_side_move=0))
  st['scans']+=1;delta=r['finish']['finish_start_side']-(1+r['score'])*math.sqrt(j['n']);st['changed']+=delta>1e-8;st['max_side_move']=max(st['max_side_move'],delta)
 base,_=C.bars();best={}
 for r in records:
  n=r['job']['n']
  if r.get('finish',{}).get('finish_quenched') and r.get('quench_receipt',{}).get('completed') and base[n]-r['score']>1e-10:best[n]=max(best.get(n,0),base[n]-r['score'])
 m=dict(best_gains_against_bar=best,completed_scans=len(records),tries=tries,raw_finds=finds,stopped_probes=probes,kinds=stats,control_returns=len(allrecords)-len(records));C.atom(W/'measurements.json',m);return m

def repo_finish():
 take=finalcompare();m=measurements();table=REPO/'lanes/squares/results/classfill-r31-2026-11-16.tsv';shutil.copy2(T/'take.tsv',table)
 doc=REPO/'lanes/squares/avenues/classfill.md'
 gain=sum(float(r['gain']) for r in take.values())
 text='\n\n## Round 31\n\nThe [results table](../results/classfill-r31-2026-11-16.tsv) retains '+str(len(take))+' counts.\nThe gain against bar31 is '+format(gain,'.12g')+'.\n'
 text+='The workers completed '+str(m['completed_scans'])+' scans and '+str(m['tries'])+' perturbation tries.\nThe 120-second probe stopped '+str(m['stopped_probes'])+' scans without a certified gain above 1e-10.\n'
 text+='Every retained row passed border finesafe at 2.2e-11 and a quench from its certified file.\nInput projections preserve the held container hash and each source table record.\nSearch and quench shared the 00:15 UTC deadline.\n'
 text+='\nThe measured next steps and immutable receipts remain in `take-classfill-r31/work/` on boxA.\n'
 (W/'doc-r31.md').write_text(text)
 checker='$STYLE_CHECK/check.py'
 subprocess.run(['/opt/homebrew/bin/python3',checker,'--level','default',str(W/'doc-r31.md')],check=True,capture_output=True,text=True)
 with doc.open('a') as f:f.write(text)
 tool=REPO/'lanes/squares/tools/classfill/round31';tool.mkdir(exist_ok=True)
 for name in ['run31.py','end31.py','stop31.py','reportclock31.py','fresh31.py','freshguard31.py','sourcecontrol31.py','light29.py','physical30.py']:shutil.copy2(W/name,tool/name)
 for name in ['probe31.py','worker31.py','probecontrol31.py']:shutil.copy2(W/'stage'/name,tool/name)
 shutil.copy2(W/'stage/lane/classfill_finish.py',tool/'classfill_finish.py')
 paths=['lanes/squares/avenues/classfill.md','lanes/squares/results/classfill-r31-2026-11-16.tsv','lanes/squares/tools/classfill/round31']
 def git(args):return subprocess.run(['git',*args],cwd=REPO,check=True,capture_output=True,text=True,timeout=120).stdout
 # Commit only our paths and leave other staged paths out of this commit.
 staged=git(['diff','--cached','--name-only']).strip()
 if staged:C.note('GIT shared staged paths stay untouched by commit --only: '+staged.replace('\n',','))
 import shlex
 command='git add -- '+' '.join(shlex.quote(p) for p in paths)+' && git commit --only -m '+shlex.quote('squares: record classfill round 31 probes and certified results')+' -- '+' '.join(shlex.quote(p) for p in paths)
 for attempt in range(2):
  result=subprocess.run(['sh','-c',command],cwd=REPO,capture_output=True,text=True,timeout=120)
  if result.returncode==0:break
  if attempt==0 and 'index.lock' in result.stderr:time.sleep(3);continue
  raise RuntimeError(result.stderr or result.stdout)
 sha=git(['log','-1','--format=%H','--','lanes/squares/results/classfill-r31-2026-11-16.tsv']).strip()
 (W/'git-show-stat.txt').write_text(git(['show','--stat','--oneline',sha]))
 changed=git(['show','--pretty=format:','--name-only',sha]).splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in changed if p),changed
 C.atom(W/'git-receipt.json',dict(commits=[sha],files=changed,pushed=False))
 for attempt in range(2):
  try:
   git(['pull','--rebase','--autostash']);sha=git(['log','-1','--format=%H','--','lanes/squares/results/classfill-r31-2026-11-16.tsv']).strip();git(['push','origin','HEAD:main']);break
  except Exception:
   if attempt:raise
   time.sleep(3)
 C.atom(W/'git-receipt.json',dict(commits=[sha],files=changed,pushed=True));return sha

def main():
 until(END-25)
 import importlib
 importlib.reload(C)
 safe(stop,'stop')
 until(END+1)
 # Drain completed outputs before removing verified remote scratch.
 safe(C.collect,'final collect');safe(archive,'archive')
 safe(repo_finish,'repository finish')
 until(FINAL-30)
 take=safe(finalcompare,'final compare') or {};m=safe(measurements,'measurements') or {};base,live=C.bars();git=C.read(W/'git-receipt.json',{})
 C.note('FINAL take.tsv frozen '+C.now())
 report=dict(lane='classfill',improved_n=len(take),gain=dict(against_base_bar=sum(base[n]-float(r['new']) for n,r in take.items()),beyond_other_live_r31=sum(live[n]-float(r['new']) for n,r in take.items())),take_dir=str(T),summary='Retained '+str(len(take))+' counts. Certified parents superseded by other lanes are excluded from the retained gain. Immutable numerical and source receipts remain under work/.',what_was_measured=[str(m.get('completed_scans',0))+' completed scans; '+str(m.get('tries',0))+' perturbation tries; '+str(m.get('raw_finds',0))+' raw finds.',str(m.get('stopped_probes',0))+' scans stopped after the 120-second probe found no certified gain above 1e-10.','Per-method measurements (changed means side reduction above 1e-8): '+json.dumps(m.get('kinds',{}),sort_keys=True),'Best certified gains against bar31 before the live-take comparison: '+json.dumps(m.get('best_gains_against_bar',{}),sort_keys=True),'The probe control continued the loose two-square improvement and stopped the tight control. Controls were excluded from production measurements.','Every retained result passed border finesafe at 2.2e-11 and a completed certified-file fq quench on its assigned remote box.','Original-byte direct/pandas audit snapshots: '+json.dumps(C.read(W/'direct-audit-summary.json',[]),sort_keys=True),'Input rows were pinned to the submitted round30c container and their inherited source-table records. Held layouts had no share gate.','Remote archive verification: '+json.dumps(C.read(W/'archive-verification.json',{}),sort_keys=True),'Final table frozen before 00:25 UTC. Report written at the deadline before any later work.'],next=['Give every useful held-row find two additional seeds even after a dry first leg. Our n818 second extra seed added 1.166e-4 of side; the first scan supplied 2.233e-6 of score before peer follows.','Require a certified gain at the 120-second probe before spending the remaining 900 seconds. This round stopped '+str(m.get('stopped_probes',0))+' dry probes; raw changes near 1e-9 of side disappeared at certification.','Follow changed rectangle geometry with a complete source walk and exact-byte claims. Measured rectangle returns: '+json.dumps(m.get('kinds',{}).get('fresh-rectangle',{}),sort_keys=True)+'. Keep unchanged seed and rounding-only preparation repeats closed.'],commits=git.get('commits',[]),processes_left=[] if C.read(W/'archive-verification.json',{}) else ['cleanup not verified'],blocked=errors+([] if git.get('pushed') else ['not pushed']),repo=str(REPO),branch='main',worktree=str(REPO),pr='none (direct main commit)')
 pending=W/'report-final.json';pending.write_text(json.dumps(report,indent=2)+'\n')
 # This rename is the first action once the report deadline passes.
 until(FINAL)
 os.replace(pending,T/'report.json')

if __name__=='__main__':main()
