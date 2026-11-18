from pathlib import Path
import sys,os,subprocess,json
W=Path(__file__).parent;sys.path.insert(0,str(W))
from common28 import note
note('CORRECTION retained793 source control actual share0.0012610340479192938 (accepted), exact prvsiyan9821.0 (rejected).')
# Driver process caps and stop files survive a lost agent session.
owned={}
for name in ['collectdriver28.py','admit28.py']:
 p=subprocess.Popen([sys.executable,'-u',str(W/name)],stdout=open(W/(name[:-3]+'.log'),'a'),stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
 owned[name]=p.pid;note(f'START boxA light driver {name} pid{p.pid} log work/{name[:-3]}.log deadline05:45Z')
(W/'local-owned.json').write_text(json.dumps(owned))
print(owned)
