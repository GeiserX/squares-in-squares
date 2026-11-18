import os,sys,json,time,subprocess,signal
from pathlib import Path
B=Path(__file__).resolve().parent;os.chdir(B)
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
slot=sys.argv[1];end=float((B/'deadline').read_text())
def run(cmd,log,limit):
 with open(log,'a') as h:
  p=subprocess.Popen(cmd,stdout=h,stderr=subprocess.STDOUT,start_new_session=True)
  (B/f'active-{slot}.json').write_text(json.dumps(dict(pid=p.pid,cmd=cmd)))
  try:rc=p.wait(timeout=max(1,min(limit,end-time.time()-5)))
  except subprocess.TimeoutExpired:
   # Also stop probe grandchildren, each in their own process group.
   children=subprocess.check_output(['ps','-axo','pid,ppid'],text=True)
   pairs=[list(map(int,l.split())) for l in children.splitlines()[1:] if l.strip()];ids={p.pid}
   for _ in range(6):ids|={a for a,b in pairs if b in ids}
   for pid in sorted(ids,reverse=True):
    try:os.kill(pid,signal.SIGTERM)
    except ProcessLookupError:pass
   try:p.wait(3)
   except subprocess.TimeoutExpired:p.kill();p.wait()
   rc=124
  (B/f'active-{slot}.json').unlink(missing_ok=True)
  return rc
assert run([sys.executable,'-I','control24.py'],B/f'logs/control-{slot}.log',60)==0
assert run([sys.executable,'-I','finecontrol29.py'],B/f'logs/fine-{slot}.log',60)==0
assert run([sys.executable,'-I','loopcontrol33.py'],B/f'logs/loop-{slot}.log',90)==0
while time.time()<end-300 and not (B/'STOP').exists():
 todo=sorted((B/'queue'/slot).glob('*.json'),key=lambda p:(json.load(open(p)).get('priority',9),p.stat().st_mtime))
 if not todo:time.sleep(3);continue
 p=todo[0];j=json.loads(p.read_text());tag=j['tag'];active=p.with_suffix('.active');p.rename(active)
 print(time.strftime('%FT%TZ',time.gmtime()),'START',slot,tag,j['input'],flush=True)
 cmd=[sys.executable,'-I','lane/classfill_finish.py',j['input'],'bar.csv','--tag',tag,'--kick','--seconds',str(j.get('seconds',900)),'--side-slack',str(j.get('slack',0.0005)),'--seed',str(j['seed']),'--source',j['source'],'--licence',j['licence'],'--fq',str(B/'fq')]
 rc=run(cmd,B/f'logs/{tag}.log',j.get('wall',1200));j.update(returncode=rc,completed_utc=time.strftime('%FT%TZ',time.gmtime()))
 (B/'out'/f'{tag}-status.json').write_text(json.dumps(j,indent=1)+'\n');active.rename(p.with_suffix('.done'))
 print(time.strftime('%FT%TZ',time.gmtime()),'DONE',slot,tag,rc,flush=True)
print('WORKER_STOP',slot,time.strftime('%FT%TZ',time.gmtime()),flush=True)
