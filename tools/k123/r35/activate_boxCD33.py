"""Start the granted fresh-geometry slots after the central workers finish switching partitions."""
from pathlib import Path
import subprocess,json,time,sys,os,hashlib
W=Path(__file__).resolve().parent;PY=str(W.parent.parent/'venv/bin/python');SSH0=['ssh','-S','/tmp/squares-k123-r35-ssh','boxE'];SSH1=['ssh','-S','/tmp/squares-k123-r35-boxD','boxD'];end=time.time()+260
if (W/'boxCD-active33').exists():raise SystemExit('already active')
while time.time()<end:
 p=subprocess.run(SSH0+['cat $SCRATCH/squares-k123/partition-ready33.json'],capture_output=True,text=True,timeout=20)
 if p.returncode==0:
  r=json.loads(p.stdout);(W/'partition-ready33.json').write_text(json.dumps(r));break
 time.sleep(5)
else:raise RuntimeError('boxE partition switch did not finish; extra workers remain off')
subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-boxD','boxD:scratch/squares-k123/boxD-control33.json',str(W/'boxD-control33.json')],check=True,timeout=30)
c=json.load((W/'boxD-control33.json').open());assert c['scipy']=='1.18.1' and len(c['controls'])==2 and all(abs(z['side']-21.564693167754)<1e-7 for z in c['controls']);assert c['fq_sha256']==hashlib.sha256((W/'fq-boxCD33').read_bytes()).hexdigest()
subprocess.run([PY,str(W/'bridge_boxCD33.py'),'--once'],check=True,timeout=180)
# Remote guard counts the current processes before each launch and enforces load >9.
subprocess.run(SSH1+['cd $SCRATCH/squares-k123 && nohup nice -n 5 $SCRATCH/squares-quench/venv/bin/python -I boxCD_guard33.py > out/boxCD-guard33.log 2>&1 < /dev/null &'],check=True,timeout=30)
(W/'boxCD-active33').write_text(str(time.time()))
with (W/'bridge-boxCD33.log').open('a') as out:p=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/'bridge_boxCD33.py')],stdout=out,stderr=out,stdin=subprocess.DEVNULL,start_new_session=True)
(W/'bridge-boxCD33.pid').write_text(str(p.pid))
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: granted four extra boxD fresh-join slots started after controls444 at1.001 and1.005 both printed21.564693167754, scipy1.18.1. Fresh recipe signatures split disjointly from boxE; prior claims remain closed. Guard pauses all4 above load9 and resumes below8, two checks. Data-only bridge feeds boxE finesafe/fullfq/source checks. Own $SCRATCH/squares-k123 will be stopped, copied and SHA256 verified before removal. Local bridge pid'+str(p.pid)+', $SCRATCH/bounties-squares/take-k123-r33/work/bridge-boxCD33.log\n'
for q in [W.parent/'STATE.txt',W.parent.parent/'handoff-r35.log']:
 with q.open('a') as f:f.write(line)
print(line,flush=True)
