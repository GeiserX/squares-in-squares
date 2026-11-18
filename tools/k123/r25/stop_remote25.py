import pathlib,subprocess,os,signal,time,json
R=pathlib.Path.home()/'scratch/squares-k123'
def rows():
 out=[]
 for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=l.strip().split(None,2)
  if len(a)==3:out.append((int(a[0]),int(a[1]),a[2]))
 return out
ps=rows();requested={int(p.read_text()) for p in R.glob('*.pid') if p.read_text().strip().isdigit()};roots={pid for pid,pp,cmd in ps if pid in requested and ('qrun22.py' in cmd or 'third22.py' in cmd)}
owned=set(roots)
for pid,pp,cmd in ps:
 if str(R)+'/' in cmd and pid!=os.getpid() and cmd.split()[0].split('/')[-1] in ['python','python3','Python','fq']:owned.add(pid)
while True:
 more={pid for pid,pp,cmd in ps if pp in owned}-owned
 if not more:break
 owned|=more
for sig in [signal.SIGTERM,signal.SIGKILL]:
 for pid in sorted(owned,reverse=True):
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 if sig==signal.SIGTERM:time.sleep(.5)
remaining=[(pid,cmd) for pid,pp,cmd in rows() if pid in owned];report=dict(time=time.strftime('%FT%TZ',time.gmtime()),stopped=sorted(owned),remaining=remaining);(R/'processes-stopped25.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert not remaining
