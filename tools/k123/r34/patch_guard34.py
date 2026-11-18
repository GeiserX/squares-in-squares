from pathlib import Path
W=Path(__file__).resolve().parent;p=W/'box_guard34.py';s=p.read_text();marker='def recover_claims():'
block='''def cleanup_orphans():
 active=tree();ps=rows()
 candidates={pid for pid,pp,cmd in ps if pp==1 and pid!=os.getpid() and pid not in active and Path(cmd.split()[0]).name in ['python','python3','Python','fq']}
 if not candidates:return []
 out=subprocess.run(['/usr/sbin/lsof','-a','-p',','.join(map(str,sorted(candidates))),'-d','cwd','-Fpn'],capture_output=True,text=True,timeout=15).stdout
 owned=set();pid=None
 for line in out.splitlines():
  if line.startswith('p') and line[1:].isdigit():pid=int(line[1:])
  elif line.startswith('n') and pid in candidates and (line[1:]==str(R) or line[1:].startswith(str(R)+'/')):owned.add(pid)
 while True:
  more={pid for pid,pp,cmd in ps if pp in owned}-owned
  if not more:break
  owned|=more
 for sig in [signal.SIGCONT,signal.SIGTERM,signal.SIGKILL]:
  for pid in sorted(owned,reverse=True):
   try:os.kill(pid,sig)
   except ProcessLookupError:pass
  if sig==signal.SIGTERM:time.sleep(.1)
 if owned:
  with (R/'orphans34.jsonl').open('a') as f:f.write(json.dumps({'time':time.time(),'stopped':sorted(owned)})+'\\n')
 return sorted(owned)

'''
s=s.replace(marker,block+marker).replace("requeued=recover_claims()","orphans=cleanup_orphans();requeued=recover_claims()").replace("'requeued':requeued}","'requeued':requeued,'orphans_stopped':orphans}")
p.write_text(s)
