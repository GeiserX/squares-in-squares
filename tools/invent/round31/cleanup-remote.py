import os,pathlib,subprocess,signal,time,json
D=pathlib.Path.home()/'scratch/squares-invent-r31'
pids=set()
for p in D.glob('worker*.pid'):
 pid=int(p.read_text())
 try:command=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
 except subprocess.CalledProcessError:continue
 if 'worker31.py 'not in command and 'worker31-v2.py 'not in command:continue
 try:cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True)
 except subprocess.CalledProcessError:continue
 if any(line=='n'+str(D)for line in cwd.splitlines()):pids.add(pid)
rows=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines()
owned=set(pids)
for _ in range(4):
 for line in rows:
  a=line.strip().split(None,2)
  if len(a)==3 and int(a[1])in owned:owned.add(int(a[0]))
for pid in owned:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(3)
for pid in owned:
 try:os.kill(pid,signal.SIGKILL)
 except ProcessLookupError:pass
import hashlib
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest()for p in D.rglob('*.csv')}
(D/'transfer-manifest.json').write_text(json.dumps(manifest))
print(json.dumps({'stopped':sorted(owned),'csvs':len(manifest)}))
