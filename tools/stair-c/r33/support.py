"""Stage controlled fresh held geometry and keep the matched return experiments alive."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
W=Path('$SCRATCH/bounties-squares/take-stair-c-r33/work')
END=datetime.datetime(2026,11,16,23,45,tzinfo=datetime.timezone.utc).timestamp()
def launch(script,key,args=()):
 f=(W/(key+'.log')).open('ab');p=subprocess.Popen(['nohup','nice','-n','5',sys.executable,'-I',str(H/script),*args],stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 (W/(key+'.pid')).write_text(str(p.pid))
 with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+f' boxA START {key} pid{p.pid}, {script} {list(args)}, log work/{key}.log, deadline16:45Z.\n')
 return p
while time.time()<END and not(W/'coordinator.pid').exists():time.sleep(5)
if time.time()>=END:sys.exit()
# All remote numerical work stays in the existing serial worker's queue.
for host in ['boxC','boxD','boxE']:
 request=W/'box/requests/000-returned-stacks.json'
 request.write_text(json.dumps(dict(name='returned-stacks-control',command=['venv/bin/python','-I','control_return_stacks.py'],limit=90)))
 subprocess.run(['rsync','-a',str(W/'box/two-stacks-control.json'),host+':scratch/squares-stair-c/'],check=True,capture_output=True,timeout=40)
 subprocess.run(['rsync','-a',str(request),host+':scratch/squares-stair-c/requests/'],check=True,capture_output=True,timeout=40)
launch('fresh_held.py','fresh-held',['805','812','871','997'])
launch('fresh_held.py','held-canonical',['--canonical','805','812','871','997','995'])
launch('pair_driver.py','pair-driver')
launch('own_kicks.py','own-kicks')
launch('feedback_finals.py','feedback-finals')
launch('fresh_return_stacks.py','return-stacks')
