"""Continue a 120-second probe only after a certified improvement."""
import sys,time,subprocess,signal,os,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'lane'))
args=sys.argv[1:];out=Path(args[args.index('--out')+1]);seconds=float(args[args.index('--seconds')+1]);barinput=None
if '--input-side' in args:
 i=args.index('--input-side');barinput=float(args[i+1]);del args[i:i+2]
probe_seconds=120
if '--probe-seconds' in args:
 i=args.index('--probe-seconds');probe_seconds=float(args[i+1]);del args[i:i+2]
code=Path(__file__).parent/'lane'/'midm_scan.py'
if barinput is not None:code=code.with_name('midm_bar30.py');args+=['--input-side',str(barinput)]
p=subprocess.Popen([sys.executable,'-I',str(code),*args],start_new_session=True);t=time.time();stopped=False;checked=False;review={}
while p.poll() is None:
 if time.time()-t>probe_seconds and not checked:
  checked=True;raw=list((out/'raw').glob('*.csv'));productive=False
  if raw:
   os.killpg(p.pid,signal.SIGSTOP)
   try:
    import classfill_finish as F
    n=int(args[args.index('--n')+1]);sub=Path(args[args.index('--sub')+1]);start=F.certify(sub,n);best=None
    for f in raw:
     r=F.certify(f,n)
     if r and (best is None or r[0]<best):best=r[0]
    productive=bool(start and best is not None and best<start[0]-1e-10)
    review=dict(start_certified_score=start[0] if start else None,best_certified_score=best,productive=productive)
   finally:os.killpg(p.pid,signal.SIGCONT)
  if not productive:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   stopped=True;break
 time.sleep(1)
(out/'probe.json').write_text(json.dumps(dict(seconds=time.time()-t,stopped_no_find=stopped,returncode=p.returncode,requested=seconds,certified_review=review))+'\n')
print('PROBE31', 'STOP_NO_CERTIFIED_FIND' if stopped else 'DONE',time.time()-t,review,flush=True)
if p.returncode and not stopped:sys.exit(p.returncode)
