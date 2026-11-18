"""Replace each worker after its current job, with no extra numerical slot."""
import pathlib,os,time,subprocess,json
D=pathlib.Path(__file__).resolve().parent;os.chdir(D)
old={s:int((D/f'worker{s}.pid').read_text())for s in ('1','2','3')}
for s,pid in old.items():
 cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
 assert cmd.endswith('worker31.py '+s),(s,pid,cmd)
(D/'STOP31').touch();new={};hard=float((D/'deadline').read_text())
while len(new)<3 and time.time()<hard-300:
 for slot,pid in old.items():
  if slot in new:continue
  try:os.kill(pid,0);continue
  except ProcessLookupError:pass
  with (D/f'worker{slot}-v2.log').open('a')as f:
   p=subprocess.Popen(['nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'-u','worker31-v2.py',slot],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=D)
  (D/f'worker{slot}.pid').write_text(str(p.pid));new[slot]=p.pid
  (D/'rolling-workers.json').write_text(json.dumps(dict(old=old,new=new,time=time.strftime('%FT%TZ',time.gmtime()))))
  print(time.strftime('%FT%TZ',time.gmtime()),'replaced',slot,pid,'->',p.pid,flush=True)
 time.sleep(5)
print('ROLL_COMPLETE',new,flush=True)
