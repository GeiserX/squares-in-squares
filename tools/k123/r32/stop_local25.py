import pathlib,subprocess,os,signal,time,json,sys
W=pathlib.Path(__file__).resolve().parent
def rows():
 out=[]
 for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=l.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
keep={os.getpid(),int(os.environ.get('K123_FINALIZER_PID','0'))}
if (W/'report-clock31.pid').exists():keep.add(int((W/'report-clock31.pid').read_text()))
ps=rows();owned={pid for pid,pp,cmd in ps if str(W)+'/' in cmd and pid not in keep and cmd.split()[0].split('/')[-1] in ['python','python3','Python']}
while True:
 extra={pid for pid,pp,cmd in ps if pp in owned}-owned
 if not extra:break
 owned|=extra
if '--dry-run' in sys.argv:
 print(json.dumps({'owned':sorted(owned),'keep':sorted(keep)}));raise SystemExit
for sig in [signal.SIGTERM,signal.SIGKILL]:
 for pid in sorted(owned,reverse=True):
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 if sig==signal.SIGTERM:time.sleep(.5)
left=[(pid,cmd) for pid,pp,cmd in rows() if pid in owned]
report={'stopped':sorted(owned),'remaining':left};(W/'processes-stopped-local25.json').write_text(json.dumps(report));print(json.dumps(report));assert not left
