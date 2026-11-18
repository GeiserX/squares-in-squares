import argparse,json,os,pathlib,signal,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--root',default='$SCRATCH/squares-stair-c');p.add_argument('--kill',action='store_true');a=p.parse_args();root=str(pathlib.Path(a.root).expanduser().resolve())
def scan():
 result=subprocess.run(['/usr/sbin/lsof','-a','-d','cwd','-Fn'],capture_output=True,text=True)
 ids=set();pid=None
 for line in result.stdout.splitlines():
  if line.startswith('p') and line[1:].isdigit():pid=int(line[1:])
  elif line.startswith('n') and pid is not None and (line[1:]==root or line[1:].startswith(root+'/')):ids.add(pid)
 ids.discard(os.getpid());return ids
before=scan();sent=[]
if a.kill:
 pathlib.Path(root,'STOP').touch()
 for attempt in range(4):
  current=scan()
  if not current:break
  for pid in current:
   try:os.kill(pid,signal.SIGTERM if attempt==0 else signal.SIGKILL);sent.append(pid)
   except ProcessLookupError:pass
  time.sleep(.5)
left=scan();print(json.dumps(dict(root=root,kill=a.kill,before=sorted(before),signalled=sorted(set(sent)),left=sorted(left))),flush=True)
if a.kill and left:raise SystemExit(1)
