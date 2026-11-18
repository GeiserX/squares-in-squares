import sys,subprocess,tarfile,shlex,json,os,time
from pathlib import Path
W=Path(__file__).parent
sys.path.insert(0,str(W))
from common29 import cmd,note,REMOTE
for host in ['boxE','boxD']:
 cmd(['ssh',host,'mkdir -p '+REMOTE])
 bundle=W/'stage28.tar.gz'
 with tarfile.open(bundle,'w:gz') as tf:
  for p in (W/'stage').iterdir():tf.add(p,arcname=p.name)
 cmd(['scp','-q',str(bundle),host+':'+REMOTE+'/stage28.tar.gz'])
 cmd(['ssh',host,'cd '+REMOTE+' && tar xzf stage28.tar.gz && rm stage28.tar.gz'])
 interpreter='$SCRATCH/squares-base/venv/bin/python' if host=='boxE' else '$SCRATCH/squares-readers/venv/bin/python'
 slots=['A','B'] if host=='boxE' else ['C']
 owned=[]
 for slot in slots:
  line='cd '+REMOTE+' && nohup nice -n 5 '+interpreter+' -u worker29.py '+slot+' > logs/worker-'+slot+'.log 2>&1 < /dev/null & echo $!'
  out=cmd(['ssh',host,line]);print(host,slot,out,flush=True);owned.append(int(out.strip().splitlines()[-1]))
  note(f'START {host} slot{slot} worker29.py pid{owned[-1]} log {REMOTE}/logs/worker-{slot}.log common deadline11:45Z search11:35Z')
 (W/(host+'-owned-workers.json')).write_text(json.dumps(owned))
 receipt=W/(host+'-owned-workers.json');cmd(['scp','-q',str(receipt),host+':'+REMOTE+'/owned-workers.json'])
print('BOOTSTRAP_COMPLETE',flush=True)
