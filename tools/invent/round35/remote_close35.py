"""Drain only the owned worker tree and hash its CSV archive."""
import pathlib,subprocess,os,signal,time,json,hashlib,shutil,sys
D=pathlib.Path.home()/'scratch/squares-invent-r35'
owned=set();rows=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines()
for p in D.glob('worker[1234].pid'):
 pid=int(p.read_text())
 try:cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
 except subprocess.CalledProcessError:continue
 if 'worker35.py 'not in cmd:continue
 cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True,stderr=subprocess.DEVNULL)
 if 'n'+str(D)in cwd.splitlines():owned.add(pid)
if '--status'in sys.argv:print(json.dumps({'active':sorted(owned)}));sys.exit()
for _ in range(6):
 for row in rows:
  v=row.strip().split(None,2)
  if len(v)==3 and int(v[1])in owned:owned.add(int(v[0]))
for pid in owned:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(2)
for pid in owned:
 try:os.kill(pid,signal.SIGKILL)
 except ProcessLookupError:pass
manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest()for p in D.rglob('*.csv')}
if '--remove'in sys.argv:
 assert manifest==json.load(open(D/'transfer-manifest.json'))
 shutil.rmtree(D);print('REMOVED OWNED r35 SCRATCH')
else:
 (D/'transfer-manifest.json').write_text(json.dumps(manifest));print(json.dumps(dict(stopped=sorted(owned),csv_files=len(manifest))))
