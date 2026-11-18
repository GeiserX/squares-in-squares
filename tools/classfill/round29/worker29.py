import csv,json,os,signal,subprocess,sys,time
from pathlib import Path
B=Path(__file__).resolve().parent;os.chdir(B)
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
end=float((B/'deadline').read_text());slot=sys.argv[1];qdir=B/'queue'/slot;qdir.mkdir(exist_ok=True)
# Each slot owns one compute child at a time. Enforce the shared hard cutoff.
def run(cmd,log,limit):
 with open(log,'a') as h:
  p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
  try:return p.wait(timeout=max(1,min(limit,end-time.time())))
  except subprocess.TimeoutExpired:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   return 124
# A deliberately loose legal n=2 packing must shrink. Fail closed per worker.
rc=run([sys.executable,'-I','control24.py'],B/f'logs/control-{slot}.log',60)
if rc:raise SystemExit('CONTROL_FAILED '+str(rc))
while time.time()<end-600 and not (B/'STOP').exists():
 todo=sorted(qdir.glob('*.json'),key=lambda p:(json.load(open(p)).get('priority',9),p.stat().st_mtime))
 if not todo:time.sleep(3);continue
 p=todo[0];j=json.load(open(p));tag=j['tag'];print(time.strftime('%FT%TZ',time.gmtime()),'START',slot,tag,j['kind'],flush=True)
 active=p.with_suffix('.active');p.rename(active)
 cmd=[sys.executable,'-I','lane/classfill_finish.py',j['input'],'bar.csv','--tag',tag,'--kick','--seconds',str(j.get('seconds',300)),'--side-slack','0.0005','--seed',str(j['seed']),'--source',j['source'],'--licence',j['licence'],'--fq',str(B/'fq')]
 if j['kind']=='sweep':cmd=[sys.executable,'-I','sweep24.py',str(active)]
 rc=run(cmd,B/f'logs/{tag}.log',j.get('wall',1200))
 j.update(returncode=rc,completed_utc=time.strftime('%FT%TZ',time.gmtime()));(B/f'out/{tag}-status.json').write_text(json.dumps(j,indent=2)+'\n');active.rename(p.with_suffix('.done'))
 print(time.strftime('%FT%TZ',time.gmtime()),'DONE',slot,tag,rc,flush=True)
print('WORKER_STOP',slot,time.strftime('%FT%TZ',time.gmtime()),flush=True)
