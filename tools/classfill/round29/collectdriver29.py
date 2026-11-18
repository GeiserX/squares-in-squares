from common29 import *
note(f'START light collection driver pid{os.getpid()}, work/collectdriver.log, deadline11:45Z. Search stays on the three remote slots.')
while time.time()<END+20 and not (W/'STOP').exists():
 t=time.time()
 for host in ['boxE','boxD']:
  d=W/host;d.mkdir(exist_ok=True)
  try:subprocess.run(['rsync','-az','--exclude=tmp/',host+':'+REMOTE+'/out',host+':'+REMOTE+'/logs',str(d)+'/'],timeout=90,check=False)
  except Exception as e:print('SYNC_ERROR',host,repr(e),flush=True)
 try:subprocess.run([sys.executable,str(W/'collect29.py')],timeout=180,check=False)
 except Exception as e:print('COLLECT_ERROR',repr(e),flush=True)
 (W/'handoff-latest.txt').write_text((S/'handoff-r29.log').read_text())
 atomic(W/'heartbeat.json',dict(time_utc=now(),pid=os.getpid()))
 for i in range(max(1,int((60-time.time()+t)/3))):
  if (W/'STOP').exists():break
  time.sleep(3)
note('FINISH collection driver')
