"""boxE side of the round 34 watchdog: slot status, slot restart, job stop."""
import pathlib,subprocess,json,sys,os,re,signal,time
D=pathlib.Path.home()/'scratch/squares-invent-r34';os.chdir(D)
PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
def rows():return subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines()
def alive(pid):
 try:os.kill(pid,0);return True
 except OSError:return False
def inflight(slot):
 started=None
 for l in (D/'pipe.log').read_text(errors='replace').splitlines():
  m=re.search(rf'slot={slot} START (\S+)',l)
  if m:started=m[1]
  m=re.search(rf'slot={slot} END (\S+)',l)
  if m and m[1]==started:started=None
 return started
def status():
 out={}
 for slot in ('1','2','3','4'):
  pid=int((D/f'worker{slot}.pid').read_text())
  ok=alive(pid)and any(r.split(None,1)[0]==str(pid)and 'worker34.py'in r for r in rows())
  out[slot]=dict(pid=pid,alive=ok,job=inflight(slot))
 return out
cmd=sys.argv[1]
if cmd=='status':print(json.dumps(status()))
elif cmd=='restart':
 slot=sys.argv[2];s=status()[slot]
 if s['alive']:print(json.dumps(dict(slot=slot,restarted=False)));raise SystemExit
 job=s['job'];cleared=[]
 if job and not(D/job/'done.json').exists():
  q=[j for j in json.load(open(D/'queue.json'))if j['id']==job]
  for p in [D/'locks'/job]+([D/'active'/str(q[0]['n'])]if q else[]):
   if p.is_dir():p.rmdir();cleared.append(str(p))
 with (D/f'worker{slot}.log').open('a')as h:
  p=subprocess.Popen(['nohup','nice','-n','5',PY,'-u',str(D/'worker34.py'),slot],stdout=h,stderr=subprocess.STDOUT,start_new_session=True,cwd=D)
 (D/f'worker{slot}.pid').write_text(str(p.pid));print(json.dumps(dict(slot=slot,restarted=True,pid=p.pid,cleared=cleared,job=job)))
elif cmd=='stop':
 job=sys.argv[2];killed=[]
 for r in rows():
  pid,c=r.strip().split(None,1)
  if job in c and 'worker34.py'not in c and 'wd_remote34'not in c:
   try:os.kill(int(pid),signal.SIGTERM);killed.append(int(pid))
   except OSError:pass
 print(json.dumps(dict(job=job,killed=killed)))
