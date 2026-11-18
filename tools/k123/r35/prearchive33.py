"""Keep incremental local copies so final shutdown does not depend on a full transfer."""
from pathlib import Path
import subprocess,time,json,signal,os
W=Path(__file__).resolve().parent;T=W.parent
boxes=[('boxE','/tmp/squares-k123-r35-ssh','boxE-final'),('boxD','/tmp/squares-k123-r35-boxD','boxD-final')]
while time.time()<float((W/'search-deadline').read_text()):
 for host,socket,name in boxes:
  D=W/name;D.mkdir(exist_ok=True)
  with (T/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA PRECOPY {host} own scratch into work/{name}; SHA256 validation remains mandatory after workers stop, logwork/prearchive33.log, search15:55Z/hard16:25Z.\n')
  args=['rsync','-az','--partial','-e','ssh -S '+socket,host+':scratch/squares-k123/',str(D)+'/'];p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,text=True)
  try:
   out,err=p.communicate(timeout=min(600,max(1,float((W/'search-deadline').read_text())-time.time())));r={'time':time.strftime('%FT%TZ',time.gmtime()),'host':host,'code':p.returncode,'error':err[-1200:]}
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM);out,err=p.communicate();r={'time':time.strftime('%FT%TZ',time.gmtime()),'host':host,'code':'timeout','error':err[-1200:]}
  print(json.dumps(r),flush=True);(W/('prearchive-'+host+'33.json')).write_text(json.dumps(r))
  if time.time()>=float((W/'search-deadline').read_text()):break
 for _ in range(30):
  if time.time()>=float((W/'search-deadline').read_text()):break
  time.sleep(30)
