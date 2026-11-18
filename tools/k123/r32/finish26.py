"""Finish the lane at its deadline even if its interactive session is lost."""
import pathlib,subprocess,os,time,json,csv,shutil,re,fcntl,shlex,hashlib,signal,resource
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
REPO=pathlib.Path('$PRIVATE_REPO');LANE=REPO/'lanes/squares';PY=str(S/'venv/bin/python')
SSH=['ssh','-S','/tmp/squares-k123-r32-ssh','boxE'];csv.field_size_limit(20000000)
def journal(message):
 line=time.strftime('%FT%TZ',time.gmtime())+' boxA '+message
 with (T/'STATE.txt').open('a') as h:h.write(line+'\n')
 print(line,flush=True)
def run(args,timeout=180,check=True,cwd=None):
 timeout=min(timeout,float((W/'deadline').read_text())+870-time.time())
 if timeout<=0:raise subprocess.TimeoutExpired(args,0)
 journal('RUN '+shlex.join(args)[:1000]+'; log work/finish26.log; finalization deadline17:30Z')
 process=subprocess.Popen(args,cwd=cwd or W,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:out,err=process.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  os.killpg(process.pid,signal.SIGKILL);out,err=process.communicate();print(out+err,flush=True)
  raise subprocess.TimeoutExpired(args,timeout,output=out,stderr=err)
 result=subprocess.CompletedProcess(args,process.returncode,out,err)
 print(out+err,flush=True)
 if check and result.returncode:raise RuntimeError(f'command failed rc={result.returncode}: {args[0]} {args[1:3]}')
 return result
def git(args,check=True):
 for attempt in range(2):
  result=run(['git',*args],cwd=REPO,check=False,timeout=120)
  if result.returncode and 'index.lock' in result.stdout+result.stderr and attempt==0:time.sleep(3);continue
  if check and result.returncode:raise RuntimeError('git '+args[0]+' failed')
  return result
def write_take(rows):
 with (T/'take.tsv.tmp').open('w',newline='') as h:
  wr=csv.DictWriter(h,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(rows)
 (T/'take.tsv.tmp').replace(T/'take.tsv')
def quarantine(n,reason):
 rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));row=next((r for r in rows if int(r['n'])==n),None)
 if not row:return
 D=W/'withdrawn';D.mkdir(exist_ok=True);(D/f'{n}-final.json').write_text(json.dumps(row))
 path=T/f'{n}.csv'
 if path.exists():shutil.copy(path,D/f'{n}-final.csv')
 write_take([r for r in rows if int(r['n'])!=n])
 digest32=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else 'missing'
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW n={n}, sha256={digest32}, final verifier refused these pinned bytes; {reason[:180]}, {path}\n'
 with (S/'handoff-r32.log').open('a') as h:h.write(line)
 journal('DROP final row '+str(n)+'; '+reason[:180])
 # Keep the CSV in place for recorded descendants and the assembler.
def validate():
 for attempt in range(12):
  result=run([PY,str(W/'validate25.py')],timeout=150,check=False)
  if result.returncode==0:return
  match=re.search(r'AssertionError: \((\d+),',result.stdout+result.stderr)
  if not match:raise RuntimeError('final source/clearance verifier failed without a row number')
  quarantine(int(match[1]),(result.stdout+result.stderr).splitlines()[-1])
 raise RuntimeError('final verifier exceeded twelve row withdrawals')
def artifacts():
 run([PY,str(W/'report32.py'),'--artifacts'])
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round32-section.md')])
 doc=LANE/'avenues/k123.md';text=doc.read_text();at=text.find('\n## Round 32\n')
 if at>=0:text=text[:at]
 doc.write_text(text.rstrip()+'\n\n'+(W/'round32-section.md').read_text())
 dest=LANE/'tools/k123/r32';dest.mkdir(exist_ok=True)
 for name in json.load((W/'owned-helpers26.json').open()):shutil.copy(W/name,dest/name)
 (dest/'lane').mkdir(exist_ok=True)
 for name in ['finesafe.py','methods_take.py','k123_join_diverse29.py']:shutil.copy(W/'lane'/name,dest/'lane'/name)
def commit():
 assert git(['branch','--show-current']).stdout.strip()=='main'
 paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r32-2026-11-16.tsv','lanes/squares/tools/k123/r32']
 command=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m','Finalize round 32 k123 measurements','--',*paths])
 result=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
 if result.returncode:
  if 'index.lock' in result.stdout+result.stderr:time.sleep(3);result=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
  if result.returncode:raise RuntimeError('final exact-path commit failed')
 match=re.search(r'^\[[^\]]+ ([0-9a-f]{7,40})\]',result.stdout,re.M)
 if not match:raise RuntimeError('could not identify own commit')
 sha=git(['rev-parse',match[1]]).stdout.strip();git(['show','--stat',sha])
 files=git(['show','--pretty=','--name-only',sha]).stdout.splitlines()
 assert files and all(p in paths[:2] or p.startswith(paths[2]+'/') for p in files),'commit contains another lane'
 commits=json.load((W/'commits26.json').open()) if (W/'commits26.json').exists() else []
 if sha not in commits:commits.append(sha)
 (W/'commits26.json').write_text(json.dumps(commits))
 pushed=False
 for attempt in range(2):
  pull=git(['pull','--rebase','--autostash','origin','main'],check=False)
  if pull.returncode and ('CONFLICT' in pull.stdout+pull.stderr):break
  push=git(['push','origin','HEAD:main'],check=False)
  if not push.returncode:pushed=True;break
  time.sleep(3)
 actual=git(['log','-1','--format=%H','--grep=^Finalize round 32 k123 measurements$'],check=False).stdout.strip()
 if actual:commits[-1]=actual;(W/'commits26.json').write_text(json.dumps(commits))
 journal('FINISH final commit '+(actual or sha)+(' pushed to origin/main' if pushed else ' not pushed'))
 return pushed
def archive_copy(destination,member='.'):
 journal('START streaming archive cmd=ssh tar | local tar; log work/finish26.log; report deadline17:30Z')
 destination.mkdir(exist_ok=True)
 sender=subprocess.Popen(SSH+['cd $SCRATCH/squares-k123 && COPYFILE_DISABLE=1 tar -czf - '+shlex.quote(member)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 receiver=subprocess.Popen(['tar','-xzf','-','-C',str(destination)],stdin=sender.stdout,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 sender.stdout.close();sender.stdout=None
 try:
  out,err=receiver.communicate(timeout=max(1,min(360,float((W/'deadline').read_text())+870-time.time())));_,senderr=sender.communicate(timeout=max(1,min(120,float((W/'deadline').read_text())+870-time.time())))
  print((out+err+senderr).decode('utf-8','replace'),flush=True)
  if receiver.returncode or sender.returncode:raise RuntimeError('streaming archive failed')
 except BaseException:
  for process in [sender,receiver]:
   if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait()
  raise
 journal('FINISH archive stream copied; checksum verification follows')
def main():
 code_stamp=(W/'finish26.py').stat().st_mtime_ns
 soft,hard=resource.getrlimit(resource.RLIMIT_NOFILE)
 resource.setrlimit(resource.RLIMIT_NOFILE,(max(soft,4096 if hard==resource.RLIM_INFINITY else min(4096,hard)),hard))
 end=min(float((W/'deadline').read_text()),float((W/'finalize-at32').read_text()) if (W/'finalize-at32').exists() else float('inf'));journal(f'START cmd=python finish26.py, automatic finalizer pid={os.getpid()}, search/quench cutoff17:15Z, take final17:25Z, report17:30Z; log work/finish26.log')
 while time.time()<end:time.sleep(max(0,min(30,end-time.time())))
 if (W/'finish26.py').stat().st_mtime_ns!=code_stamp:os.execv(PY,[PY,str(W/'finish26.py')])
 lock=(W/'finalize26.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
 if (W/'finalize26.done').exists():return
 os.environ['K123_FINALIZER_PID']=str(os.getpid())
 journal('START final shutdown, collection and archive. No new numerical search or quench after cutoff.')
 run([PY,str(W/'stop_local25.py')])
 for name in ['stop_remote25.py','manifest25.py']:
  run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r32-ssh',str(W/name),'boxE:scratch/squares-k123/'])
 run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I stop_remote25.py'])
 for i in range(2):
  try:run([PY,str(W/'collect22.py')],timeout=80)
  except (RuntimeError,subprocess.TimeoutExpired) as error:journal('NOTE final collection pass '+str(i)+' '+str(error))
 run([PY,str(W/'history28.py')],timeout=120,check=False)
 run([PY,str(W/'bind_sources29.py')],timeout=180,check=False)
 validate();journal('FINISH numerical and source verification; retain withdrawal checks until the 17:25 take freeze.')
 (W/'take-final26.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime())}))
 run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I manifest25.py'],timeout=240)
 archive=W/'boxE-final';archive.mkdir(exist_ok=True)
 archive_copy(archive)
 run([PY,str(W/'verify_archive25.py')],timeout=240)
 verified=json.load((W/'copy-verified25.json').open());assert not verified['checksum_differences']
 run(SSH+['test -d $SCRATCH/squares-base && rm -rf -- $SCRATCH/squares-k123'],timeout=120)
 journal('FINISH boxE scratch removal after verified copy; shared base preserved.')
 artifacts();pushed=commit()
 end_report=float((W/'deadline').read_text())+600.05
 retained_table32=(T/'take.tsv').read_bytes()
 while time.time()<end_report:
  if time.time()<end_report-15:
   try:run([PY,str(W/'retention32.py')],timeout=min(60,end_report-time.time()-1),check=False)
   except (RuntimeError,subprocess.TimeoutExpired) as error:journal('NOTE late retention refresh '+str(error))
  time.sleep(max(0,min(30,end_report-time.time())))
 if retained_table32!=(T/'take.tsv').read_bytes():
  journal('NOTE late source withdrawals changed the take after the early archive; update the exact results metadata now.')
  artifacts();pushed=commit() and pushed
 run([PY,str(W/'report32.py')])
 if not pushed:
  report=json.load((T/'report.json').open());report['blocked']='not pushed: git push did not complete';report['summary']+=' Final commit not pushed.';(T/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 run(['ssh','-S','/tmp/squares-k123-r32-ssh','-O','exit','boxE'],check=False)
 (W/'finalize26.done').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'pushed':pushed}))
 journal('FINISH report.json written; lane workers stopped and archive verified.')
if __name__=='__main__':
 try:main()
 except BaseException as error:
  journal('ERROR finalizer '+repr(error));(W/'finalize26.error').write_text(repr(error))
  # The report deadline still applies after a cleanup, archive or commit failure.
  os.environ['K123_FINALIZER_PID']=str(os.getpid())
  try:subprocess.run([PY,str(W/'stop_local25.py')],timeout=30,check=False)
  except BaseException:pass
  try:subprocess.run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I stop_remote25.py'],timeout=30,check=False)
  except BaseException:pass
  report_at=float((W/'deadline').read_text())+600.05
  while time.time()<report_at:time.sleep(max(0,min(30,report_at-time.time())))
  try:subprocess.run([PY,str(W/'report32.py')],timeout=20,check=True)
  except BaseException:
   fallback=dict(lane='k123',improved_n=0,gain=dict(against_base_bar=0,beyond_other_live_r32=0),take_dir=str(T),summary='Finalization failed. Retained files require review.',what_was_measured=['Finalization error: '+repr(error)],next=['Finish the recorded finalization steps from work/finish26.log before counting a row.'],commits=json.load((W/'commits26.json').open()) if (W/'commits26.json').exists() else [],processes_left='see finalization log',blocked=repr(error),repo=str(REPO)+' (private repo)',branch='main',worktree=str(REPO),pr='')
   (T/'report.json.tmp').write_text(json.dumps(fallback,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
  if (T/'report.json').exists():
   report=json.load((T/'report.json').open());report['blocked']='finalization incomplete: '+repr(error);report['summary']='Certified take retained. Finalization did not complete; see work/finish26.log.';report['processes_left']='see finalization stop records';(T/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  journal('FINISH fallback report written after take deadline; finalization error remains in work/finish26.log.')
  raise
