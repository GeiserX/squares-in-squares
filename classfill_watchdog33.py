"""Bound a search subprocess and preserve its completed checkpoint files."""
import os,signal,subprocess,time

def run(command,log,budget):
 p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:return p.wait(timeout=max(.01,budget)),False
 except subprocess.TimeoutExpired:
  pairs=[]
  for line in subprocess.check_output(['ps','-axo','pid=,ppid='],text=True).splitlines():
   try:pairs.append(tuple(map(int,line.split())))
   except ValueError:pass
  owned={p.pid}
  for _ in range(16):owned|={pid for pid,parent in pairs if parent in owned}
  for sig in (signal.SIGTERM,signal.SIGKILL):
   for pid in sorted(owned,reverse=True):
    try:os.kill(pid,sig)
    except ProcessLookupError:pass
   if sig==signal.SIGTERM:time.sleep(.2)
  p.wait();return p.returncode,True

if __name__=='__main__':
 import tempfile,sys
 from pathlib import Path
 with tempfile.TemporaryDirectory() as td:
  p=Path(td)/'checkpoint';log=open(Path(td)/'log','w')
  rc,timed=run([sys.executable,'-c','print("completed")'],log,2);assert rc==0 and not timed
  rc,timed=run([sys.executable,'-c','import pathlib,sys,time;pathlib.Path(sys.argv[1]).write_text("saved");time.sleep(10)',str(p)],log,.2)
  assert timed and rc!=0 and p.read_text()=='saved'
 print('SEARCH_WATCHDOG_CONTROL_PASS completed command passes; stalled command stops and preserves checkpoint')
