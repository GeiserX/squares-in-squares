"""Stage one serial worker on each assigned box with the shared hard deadline."""
import datetime,json,os,pathlib,shlex,subprocess,sys,time
R=pathlib.Path('$PRIVATE_REPO');W=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r31/work');B=W/'box';HERE=R/'lanes/squares/tools/stair-c/r31'
def state(s):
 with (W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA '+s+'\n')
def run(cmd,timeout=90):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout);print(cmd[0],p.returncode,p.stdout[-3000:],p.stderr[-500:],flush=True);p.check_returncode();return p
assert (B/'libbase/library.pkl').exists()
for host,key,part in [('boxC','n',0),('boxD','m',1),('boxE','s',2)]:
 check=run(['ssh','-o','ConnectTimeout=15',host,"ps -axo pid,ppid,command | grep '[w]orker.py' | grep 'squares-stair-c' || true; test ! -d $SCRATCH/squares-stair-c; mkdir -p $SCRATCH/squares-stair-c"],30)
 run(['rsync','-az',str(B)+'/',host+':scratch/squares-stair-c/'],150)
 run(['rsync','-a',str(B/f'state-{part}.pkl'),host+':scratch/squares-stair-c/state.pkl'],40)
 command='''cd "$HOME/scratch/squares-stair-c"
if [ -x "$HOME/scratch/squares-base/venv/bin/python" ]; then ln -s "$HOME/scratch/squares-base/venv" venv; else ln -s "$HOME/scratch/squares-readers/venv" venv; fi
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 venv/bin/python -c 'import scipy; assert scipy.__version__=="1.18.1"'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 venv/bin/python - <<'LAUNCH'
import subprocess,time
f=open('worker.log','ab')
p=subprocess.Popen(['nohup','nice','-n','5','venv/bin/python','-I','worker.py','PART'],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
open('worker.pid','w').write(str(p.pid));time.sleep(2);print('worker',p.pid)
LAUNCH
'''.replace('PART',str(part))
 run(['ssh',host,'sh -s'],30) if False else None
 p=subprocess.run(['ssh',host,'sh -s'],input=command,text=True,capture_output=True,timeout=40);print(host,p.returncode,p.stdout,p.stderr,flush=True);p.check_returncode()
 state('START '+host+' one serial worker part'+str(part)+' nice5 via shared scipy1.18.1 runtime. Log remote $SCRATCH/squares-stair-c/worker.log; search ends23:55Z, all long jobs00:15Z on November16.')
# Start the surviving local coordinator with a separate session.
with (W/'coordinator.log').open('ab') as f:
 p=subprocess.Popen([sys.executable,'-I',str(HERE/'coordinator.py')],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,cwd=R,start_new_session=True)
(W/'coordinator.pid').write_text(str(p.pid));time.sleep(2);state('START local light coordinator pid'+str(p.pid)+' log work/coordinator.log. Collect before feed, max6 donors/90s, bounded live imports. Hard deadline00:15Z on November16.')
