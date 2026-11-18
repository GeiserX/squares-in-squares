import fcntl,os,pathlib,signal,subprocess,sys,tarfile,time,json
remaining=float(open('deadline').read())-time.time()
if remaining<=0:sys.exit(0)
if os.path.exists('NO_NEW_BUILDS') and not any(x.endswith('quench22.py') for x in sys.argv[1:]):
 print('FINAL WINDOW: new search deferred; certified-file quenches remain enabled',flush=True);sys.exit(0)
os.environ['SQ_TMP']=os.path.abspath('tmp');os.makedirs(os.environ['SQ_TMP'],exist_ok=True)
os.makedirs('pool-locks',exist_ok=True);locks=[]
for pool in sorted({x for x in sys.argv[1:] if x.startswith('lib-') and '/' not in x}):
 h=open('pool-locks/'+pool+'.lock','a');fcntl.flock(h,fcntl.LOCK_SH)
 if not os.path.exists(pool+'/library.pkl') and os.path.exists('pool-archive/'+pool+'.tar.gz'):
  fcntl.flock(h,fcntl.LOCK_UN);fcntl.flock(h,fcntl.LOCK_EX)
  if not os.path.exists(pool+'/library.pkl'):
   with tarfile.open('pool-archive/'+pool+'.tar.gz') as tf:
    for m in tf.getmembers():
     if not m.name.startswith(pool+'/') or '..' in pathlib.Path(m.name).parts:raise ValueError('unsafe pool member')
    tf.extractall('.',filter='data')
  fcntl.flock(h,fcntl.LOCK_SH)
 locks.append(h)
cmd=sys.argv[1:]
for i,x in enumerate(cmd):
 if x.endswith('/modules.py') and i+5<len(cmd) and cmd[i+1]=='job':
  name=cmd[i+5];os.makedirs('blog',exist_ok=True)
  json.dump(dict(command=cmd,library=cmd[i+2],name=name),open('blog/'+name+'.recipe.json','w'));break
if os.path.exists('EARLY_JOB_READY'):
 for i,x in enumerate(cmd):
  if x.endswith('/modules.py') and i+1<len(cmd) and cmd[i+1]=='job':cmd=cmd[:i]+['lane/stair-c_job.py']+cmd[i:];break
p=subprocess.Popen(cmd,start_new_session=True)
try:sys.exit(p.wait(timeout=max(1.,float(open('deadline').read())-time.time())))
except subprocess.TimeoutExpired:
 os.killpg(p.pid,signal.SIGTERM)
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL)
 sys.exit(124)
