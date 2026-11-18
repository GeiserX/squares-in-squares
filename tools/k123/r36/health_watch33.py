"""Keep the observed boxE outage from silently consuming the remaining search window."""
from pathlib import Path
import subprocess,os,signal,json,time,traceback
W=Path(__file__).resolve().parent;T=W.parent;missing=0;last=None
while time.time()<float((W/'deadline').read_text()):
 try:
  args=['ssh','-S','/tmp/squares-k123-r36-ssh','boxE','cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I health_probe33.py'+(' --recover' if missing>=2 else '')];p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,text=True)
  try:out,err=p.communicate(timeout=20)
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGKILL);p.communicate();raise
  if p.returncode:raise RuntimeError(err[-600:])
  s=json.loads(out);missing=missing+1 if not s['guard'] and not s['roots'] else 0;(W/'boxE-health33.json').write_text(json.dumps(s));key=(bool(s['guard']),len(s['roots']),s['recovered'])
  if key!=last:
   with (T/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+' boxA BOXE HEALTH '+json.dumps(s)+'; recover only after two empty-pool probes, numeric cap4, logwork/health-watch33.log, hard23:45Z.\n')
   last=key
  print(json.dumps(s),flush=True)
 except Exception:traceback.print_exc()
 time.sleep(30)
