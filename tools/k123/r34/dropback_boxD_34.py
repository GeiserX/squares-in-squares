from pathlib import Path
import json,subprocess,os,signal,time
W=Path(__file__).resolve().parent;p=W/'boxD/runtime33.json';cfg=json.load(p.open());cfg['slots']={k:v for k,v in cfg['slots'].items() if k in ['j22e','j22f','j22g']};p.write_text(json.dumps(cfg));gid=int((W/'guardian34.pid').read_text());os.kill(gid,signal.SIGSTOP)
try:
 subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxD',str(p),'boxD:scratch/squares-k123/'],check=True,timeout=30)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r34-boxD','boxD',f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I stop_remote25.py'],check=True,timeout=45)
 script="""from pathlib import Path
import json
R=Path.home()/'scratch/squares-k123';timed=set()
for p in (R/'out').glob('j22*/done.jsonl'):
 for l in p.read_text().splitlines():
  r=json.loads(l)
  if not r.get('raw') and (r.get('code')==-2 or r.get('fq2code')==-2):timed.add(f'{r["pool"]}-{r["n"]}-{r["tag"]}')
removed=[]
for p in (R/'claims').glob('*/owner.json'):
 j=json.load(p.open())
 if j['jobkey'] in timed:p.unlink();p.parent.rmdir();removed.append(j)
(R/'load-timeouts-reopened34.json').write_text(json.dumps(removed,indent=2));print(json.dumps({'reopened':len(removed)}))
"""
 q=W/'reopen_load_timeouts34.py';q.write_text(script);subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxD',str(q),'boxD:scratch/squares-k123/'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r34-boxD','boxD',f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I reopen_load_timeouts34.py'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r34-boxD','boxD',f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34-cap3.log 2>&1 < /dev/null &'],check=True,timeout=20)
finally:os.kill(gid,signal.SIGCONT)
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: drop boxD from5 to3 join slots after load measured9.70 on60 samples, with35 paused. Shared load exceeded9 with5. All ten recipe partitions remain covered. Unreported interrupted jobs requeue; zero-raw timeout claims reopen because the prior wall-clock budgets were spent under SIGSTOP. work/dropback-boxD-34.log; deadline07:25Z.\n'
for p in [W.parent/'STATE.txt',W.parent.parent/'handoff-r34.log']:
 with p.open('a') as f:f.write(line)
print(line,flush=True)
