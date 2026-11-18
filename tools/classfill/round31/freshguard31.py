"""Bound source admission without blocking the numerical dispatch controller."""
import os,sys,time,subprocess,signal
from pathlib import Path
W=Path(__file__).resolve().parent
with (W/'fresh31.log').open('a') as log:
 p=subprocess.Popen([sys.executable,'-u',str(W/'fresh31.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=p.wait(timeout=120)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(3)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  rc=124
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' FINISH source admission guard rc'+str(rc)+'; log work/fresh31.log; source only, no local search.\n')
