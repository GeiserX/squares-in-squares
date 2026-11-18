"""Stop only this lane's workers and solver or transfer children."""
import pathlib,subprocess,os,signal,time,json,sys
R=pathlib.Path.home()/'scratch/squares-k123'
def rows():
 out=[]
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
def ownership(ps):
 requested={int(p.read_text()) for p in R.glob('*.pid') if p.read_text().strip().isdigit()}
 owned={pid for pid,pp,cmd in ps if pid in requested and any(name in cmd for name in ['qrun22.py','third22.py','boxCD_guard33.py','boxCD_guard33b.py','boxE_guard33.py'])};cwd_owned=set()
 candidates={pid for pid,pp,cmd in ps if pid!=os.getpid() and pathlib.Path(cmd.split()[0]).name in ['python','python3','Python','fq','rsync','tar','gzip']}
 for pid,pp,cmd in ps:
  if pid in candidates and str(R)+'/' in cmd:owned.add(pid)
 if candidates:
  try:
   result=subprocess.run(['/usr/sbin/lsof','-a','-p',','.join(map(str,sorted(candidates))),'-d','cwd','-Fn'],text=True,capture_output=True,timeout=15);pid=None
   for line in result.stdout.splitlines():
    if line.startswith('p') and line[1:].isdigit():pid=int(line[1:])
    elif line.startswith('n') and pid in candidates and (line[1:]==str(R) or line[1:].startswith(str(R)+'/')):cwd_owned.add(pid)
  except (OSError,subprocess.TimeoutExpired):pass
 owned|=cwd_owned
 while True:
  more={pid for pid,pp,cmd in ps if pp in owned and pid!=os.getpid()}-owned
  if not more:break
  owned|=more
 owned.discard(os.getpid());return owned,cwd_owned
owned,cwd_owned=ownership(rows())
if '--dry-run' in sys.argv:
 print(json.dumps({'owned':sorted(owned),'cwd_owned':sorted(cwd_owned)}));raise SystemExit
stopped=set()
for sig in [signal.SIGTERM,signal.SIGKILL]:
 current,_=ownership(rows());stopped|=current
 for pid in sorted(current,reverse=True):
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 time.sleep(.5 if sig==signal.SIGTERM else .05)
remaining,_=ownership(rows());report=dict(time=time.strftime('%FT%TZ',time.gmtime()),stopped=sorted(stopped),remaining=sorted(remaining));(R/'processes-stopped25.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert not remaining
