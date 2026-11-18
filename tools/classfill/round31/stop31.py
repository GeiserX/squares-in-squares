"""Stop only the owned worker trees and write a complete archive manifest."""
import os,signal,sys,json,hashlib,subprocess,time
from pathlib import Path
B=Path(__file__).resolve().parent
(B/'STOP').touch()
ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True);pairs=[];roots=set()
for l in ps.splitlines()[1:]:
 q=l.strip().split(None,2)
 if len(q)<3 or not q[0].isdigit() or not q[1].isdigit():continue
 pid,ppid=int(q[0]),int(q[1]);pairs.append((pid,ppid,q[2]))
 if 'worker31.py' in q[2] and pid!=os.getpid():
  # The worker command has no cwd, so only accept a recorded owned worker PID.
  files=list(B.glob('owned-*.json'))
  if any(json.loads(p.read_text()).get('pid')==pid for p in files):roots.add(pid)
for p in B.glob('active-*.json'):
 try:roots.add(json.loads(p.read_text())['pid'])
 except:pass
ids=set(roots)
for _ in range(8):ids|={p for p,parent,_ in pairs if parent in ids}
ids.discard(os.getpid())
for p in sorted(ids,reverse=True):
 try:os.kill(p,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(2)
for p in sorted(ids,reverse=True):
 try:os.kill(p,signal.SIGKILL)
 except ProcessLookupError:pass
# Catch an fq child created between the first process census and its parent's stop.
again=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True)
for line in again.splitlines()[1:]:
 fields=line.strip().split(None,2)
 if len(fields)<3 or not fields[0].isdigit() or not fields[1].isdigit():continue
 pid=int(fields[0]);command=fields[2]
 words=command.split();known={'worker31.py','classfill_finish.py','probe31.py','midm_scan.py','midm_bar30.py','invent_rest.py'}
 own_compute=bool(words) and (words[0]==str(B/'fq') or ('python' in Path(words[0]).name and str(B)+'/' in command and any(Path(word).name in known for word in words)))
 if pid!=os.getpid() and own_compute:
  ids.add(pid)
  try:os.kill(pid,signal.SIGKILL)
  except ProcessLookupError:pass
time.sleep(1)
files={}
for p in B.rglob('*'):
 if p.is_file() and p.name!='archive-manifest.json':files[str(p.relative_to(B))]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
left=[]
for p in ids:
 try:
  os.kill(p,0)
  state=subprocess.run(['ps','-p',str(p),'-o','stat='],capture_output=True,text=True).stdout.strip()
  if state and not state.startswith('Z'):left.append(p)
 except ProcessLookupError:pass
(B/'archive-manifest.json').write_text(json.dumps(dict(files=files,stopped_pids=sorted(ids),remaining=left,time=time.strftime('%FT%TZ',time.gmtime())),indent=1)+'\n')
print('STOPPED',len(ids),'REMAINING',left,'FILES',len(files),flush=True)
