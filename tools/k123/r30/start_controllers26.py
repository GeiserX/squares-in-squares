import subprocess,pathlib,os
W=pathlib.Path(__file__).resolve().parent
for mode in ['collect','stage']:
 with open(W/f'{mode}-resident26.log','a') as f:
  p=subprocess.Popen(['/usr/bin/nice','-n','5','$SCRATCH/bounties-squares/venv/bin/python',str(W/'resident25.py'),mode],stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
  (W/f'{mode}.pid').write_text(str(p.pid));print(mode,p.pid)
