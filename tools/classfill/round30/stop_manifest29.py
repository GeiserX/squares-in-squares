import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent
assert B.name=='squares-classfill-r30'
(B/'STOP').touch()
expected=json.loads((B/'owned-workers.json').read_text())
def processes():
 info={}
 for line in subprocess.check_output(['ps','-axo','pid=,ppid=,pgid=,command='],text=True).splitlines():
  a=line.split(None,3)
  if len(a)==4:
   try:pid,ppid,pgid=map(int,a[:3]);info[pid]=dict(pid=pid,ppid=ppid,pgid=pgid,command=a[3])
   except ValueError:pass
 return info
def in_lane_cwd(pid):
 try:
  text=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True,stderr=subprocess.DEVNULL,timeout=10)
  paths=[Path(line[1:]) for line in text.splitlines() if line.startswith('n')]
  return any(q==B or B in q.parents for q in paths)
 except (subprocess.SubprocessError,OSError):return False
info=processes();owned={p for p in expected if p in info and 'worker29.py' in info[p]['command'] and in_lane_cwd(p)}
for _ in range(20):
 extra={p for p,q in info.items() if q['ppid'] in owned}
 if extra<=owned:break
 owned|=extra
# Fq and scan calls name this scratch explicitly, even if a worker exited.
owned|={p for p,q in info.items() if str(B) in q['command'] and p!=os.getpid() and 'stop_manifest29.py' not in q['command'] and in_lane_cwd(p)}
records=[info[p] for p in sorted(owned)];groups={q['pgid'] for q in records if q['pid'] not in expected and q['pgid']!=os.getpgrp()}
killed=[]
for group in groups:
 try:os.killpg(group,signal.SIGTERM);killed.append(dict(group=group,signal='TERM'))
 except ProcessLookupError:pass
for p in owned:
 try:os.kill(p,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(2)
current=processes()
for p in owned:
 if p in current and current[p]['command']==info[p]['command']:
  try:os.kill(p,signal.SIGKILL);killed.append(dict(pid=p,signal='KILL'))
  except ProcessLookupError:pass
time.sleep(1)
current=processes();left=[q for p,q in current.items() if p in owned and q['command']==info[p]['command']]
import numpy,scipy,pandas,mpmath
result=dict(time_utc=time.strftime('%FT%TZ',time.gmtime()),owned=records,killed=killed,left=left,python=sys.version,scipy=scipy.__version__,numpy=numpy.__version__,pandas=pandas.__version__,mpmath=mpmath.__version__,excluded_from_archive=['venv','tmp','__pycache__'])
(B/'stop-result.json').write_text(json.dumps(result,indent=1)+'\n')
manifest={}
for root,dirs,files in os.walk(B):
 dirs[:]=[q for q in dirs if q not in ['venv','tmp','__pycache__']]
 for name in files:
  p=Path(root)/name
  if p.name=='archive-manifest.json' or p.is_symlink():continue
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
  manifest[str(p.relative_to(B))]=h.hexdigest()
(B/'archive-manifest.json').write_text(json.dumps(manifest,indent=1)+'\n')
print(json.dumps(dict(time=result['time_utc'],left=left,files=len(manifest))))
if left:raise SystemExit(1)
