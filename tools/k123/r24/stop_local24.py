import pathlib,subprocess,os,signal,time,json
W=pathlib.Path(__file__).resolve().parent
ps=[]
for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 a=line.strip().split(None,2)
 if len(a)==3:ps.append((int(a[0]),int(a[1]),a[2]))
roots={pid for pid,pp,cmd in ps if pid!=os.getpid() and str(W)+'/' in cmd and cmd.split()[0].split('/')[-1] in ['python','python3','Python']};owned=set(roots)
while True:
 more={pid for pid,pp,cmd in ps if pp in owned}-owned
 if not more:break
 owned|=more
for pid in sorted(owned,reverse=True):
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
(W/'local-stopped24.json').write_text(json.dumps(dict(time=time.strftime('%FT%TZ',time.gmtime()),stopped=sorted(owned)),indent=2));print('local controllers stopped',sorted(owned))
