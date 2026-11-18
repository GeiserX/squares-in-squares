"""Replace each completed slot with the checkpoint writer without adding a slot."""
import pathlib,subprocess,os,time,json
D=pathlib.Path.home()/'scratch/squares-invent-r32';os.chdir(D);old={s:int((D/f'worker{s}.pid').read_text())for s in('1','2','3')}
for s,pid in old.items():
 cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip();assert cmd.endswith('worker32.py '+s),(s,cmd)
(D/'STOP32').touch();new={};deadline=float((D/'deadline').read_text())
while len(new)<3 and time.time()<deadline-300:
 for slot,pid in old.items():
  if slot in new:continue
  try:os.kill(pid,0);continue
  except ProcessLookupError:pass
  with(D/f'worker{slot}-stream.log').open('a')as f:
   p=subprocess.Popen(['nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'-u','worker32-stream.py',slot],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=D)
  (D/f'worker{slot}.pid').write_text(str(p.pid));new[slot]=p.pid;(D/'rolling32.json').write_text(json.dumps(dict(old=old,new=new,time=time.strftime('%FT%TZ',time.gmtime()))));print('REPLACED',slot,pid,p.pid,flush=True)
 time.sleep(3)
print('ROLL COMPLETE',new,flush=True)
