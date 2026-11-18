from pathlib import Path
import datetime,json,os,signal,subprocess,time,sys
r=Path(sys.argv[1]);deadline=float((r/'deadline.txt').read_text())
while time.time()<deadline-2: time.sleep(min(30,deadline-2-time.time()))
started=datetime.datetime.now(datetime.timezone.utc).isoformat();(r/'STOP').touch();ps={}
for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines():
 row=line.split(None,2)
 if len(row)==3 and row[0].isdigit():ps[int(row[0])]=(int(row[1]),row[2])
roots=[]
for name in ['worker0.pid','worker1.pid','worker2.pid','scanner.pid']:
 p=r/name
 if p.exists():
  pid=int(p.read_text())
  if pid in ps and str(r) in ps[pid][1] and 'forensics_' in ps[pid][1]:roots.append(pid)
desc=set(roots)
while True:
 more={pid for pid,(parent,cmd) in ps.items() if parent in desc}
 if more<=desc:break
 desc|=more
for pid in desc:
 try:os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT)
 except ProcessLookupError:pass
time.sleep(.2)
for pid in desc:
 try:os.kill(pid,signal.SIGKILL)
 except ProcessLookupError:pass
result=dict(started=started,finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline=deadline,stopped=sorted(desc))
(r/'deadline-receipt.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
