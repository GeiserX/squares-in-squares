from pathlib import Path
import subprocess,json,time
W=Path(__file__).resolve().parent;S=W.parent.parent
for host in ['boxC','boxD']:
 assert json.load((W/host/'control34.json').open())['side']==21.564693167754
 cfg=json.load((W/host/'runtime33.json').open())
 # Do not launch while the initial queue is absent. Empty guards safely wait for the bridge.
 subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34.log 2>&1 < /dev/null &'],check=True)
with (W/'bridge34.log').open('a') as out:p=subprocess.Popen(['nohup','nice','-n','5',str(S/'venv/bin/python'),str(W/'bridge34.py')],stdout=out,stderr=out,stdin=subprocess.DEVNULL,start_new_session=True)
(W/'bridge34.pid').write_text(str(p.pid))
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: boxC two and boxD five fresh-join slots started. Both 444 controls21.564693167754; scipy1.18.1. Ten disjoint recipe partitions cover boxE3/boxC:2/boxD:5. boxE fourth slot scans and certifies. Guards enforce load<9 (boxE16), own process caps and interrupted-claim requeue. '+str(W)+'\n'
for path in [W.parent/'STATE.txt',S/'handoff-r35.log']:
 with path.open('a') as f:f.write(line)
print(line)
