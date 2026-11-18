import os,sys,time,json,glob,signal,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import border_sweep as bs
ROOT=Path(__file__).parent
END=1794583200 # overwritten from deadline file
END=float((ROOT/'deadline').read_text())
which=sys.argv[1]
original_call=bs.fq_call
def bounded_call(fq,inp,out,flags,cap):
 remaining=int(END-time.time())
 if remaining<2:return None,0.0
 return original_call(fq,inp,out,flags,min(cap,max(1,remaining-1)))
bs.fq_call=bounded_call
fast=which=='1' and (ROOT/'FAST_OK').exists()
if fast:
 bs.POLISH=[]
 print('positive control passed: worker1 uses two default calls per round',flush=True)
def read_json(path):
 try:
  value=json.load(open(path))
  return value if isinstance(value,dict) else None
 except (OSError,ValueError):return None
def stop(*_): raise SystemExit
signal.signal(signal.SIGTERM,stop)
while time.time()<END:
 jobs=[]
 bars=read_json(ROOT/'bars.json') or {}
 for p in (ROOT/'final').glob('*.job.json'):
  j=read_json(p)
  if j is None:continue
  bar=bars.get(str(j['n']),1e100)
  side=(j['certified_before']+1)*math.sqrt(j['n'])
  # r27: a certified file within 5e-9 of side of the bar (the LP and fq follow of fresh takes) runs before the LP queue.
  priority=-200 if side<bar-math.sqrt(j['n'])*1e-10 else (-170 if side<bar+5e-9 else -10)
  if 'priority' in j:priority=j['priority']  # r28 04:33Z: sfeed self and near follows carry their own priority
  jobs.append((priority,p.stat().st_mtime,p,'final'))
 # r27: contact-LP jobs (lpfeed.py) rank after certified finals below the bar and before chains.
 for p in (ROOT/'lp/jobs').glob('*.json'):
  j=read_json(p)
  if j is None:continue
  jobs.append((j.get('priority',-150),p.stat().st_mtime,p,'lp'))
 # r29 07:30Z: 900 s midm_scan lkick,kick jobs (kfeed29.py) of fresh near files and takes that rebuild's follow skipped
 # with full queues. Worker 2 takes them first; worker 1 only when nothing else waits (fresh follows stay quick).
 for p in (ROOT/"kq/jobs").glob("*.json") if (ROOT/"kq/jobs").exists() else []:  # r30 12:40Z: a kick job runs on the worker its w names (default 2)
  j=read_json(p)
  if j is None or str(j.get("w","2"))!=which:continue
  jobs.append(((-300+j.get('priority',0)) if which=='2' else (-140+max(0,j.get('priority',0))),p.stat().st_mtime,p,'kick'))  # r29 08:30Z: the boundary grow1 priority (-50, -40) orders worker 2 only; worker 1 keeps the take path first  # r29 07:55Z: worker 1 kicks after fresh takes and near files above the bar, before bar-side near files
 for p in ([] if (ROOT/'NOCHAIN').exists() else (ROOT/'q').glob('*.job.json')):
  j=read_json(p)
  if j is None:continue
  rec=ROOT/'q'/j['start'].replace('.start.txt','.k%d.json'%j.get('k',0))
  jobs.append((j['priority']-(20 if not rec.exists() else 0),p.stat().st_mtime,p,'chain'))
 jobs.sort()
 picked=False
 for _,_,p,kind in jobs:
  if p.with_suffix('.done').exists():continue
  claim=p.with_suffix('.claim')
  try: claim.mkdir()
  except FileExistsError:continue
  j=read_json(p)
  if j is None:
   claim.rmdir();continue
  # r26: rsync sends a job before its start (j < s), so a job whose input has not arrived waits.
  if (kind=='chain' and not (ROOT/'q'/j['start']).exists()) or (kind=='final' and not (ROOT/'final'/j['input']).exists()) or (kind=='lp' and not (ROOT/'lp'/j['input']).exists()) or (kind=='kick' and not (ROOT/'kq'/j['input']).exists()):
   claim.rmdir();continue
  picked=True
  print(time.strftime('%H:%M:%S',time.gmtime()),which,'start',p.name,flush=True)
  import math
  if kind=='chain':
   k=j.get('k',0);rec=ROOT/'q'/j['start'].replace('.start.txt','.k%d.json'%k)
   previous=read_json(rec) or {}
   passes=min(6,previous.get('round',0)+1)
   result=bs.quench_one((str(ROOT/'q'/j['start']),str(ROOT/'fq'),600,passes,j.get('kick',.001),k,END))
   now=json.load(open(rec))
   modes=previous.get('modes_by_round',{});modes[str(previous.get('round',0))]='double-default' if fast else 'default+deep'
   now['modes_by_round']=modes
   tmp=rec.with_suffix('.mode.tmp');tmp.write_text(json.dumps(now));os.replace(tmp,rec)
   if now['cut'] and now['round']<6:
    claim.rmdir()
    print(time.strftime('%H:%M:%S',time.gmtime()),which,'saved round',now['round'],p.name,flush=True)
    break
  elif kind=='kick':
   import subprocess
   t0=time.time();out=ROOT/'kq'/j['out'];out.mkdir(parents=True,exist_ok=True)
   sec=int(min(j.get('seconds',900),max(0,END-time.time()-60)))
   if sec<60:rc='deadline'
   else:
    try:
     # r29 08:15Z: a job may name its modes and a donors file (grow1 at the integer band edge: the n-1 layout plus one square)
     extra=(['--donors',str(ROOT/'kq'/j['donors'])] if j.get('donors') else [])+(['--flagsets',j['flagsets']] if j.get('flagsets') else [])
     # r31 (round 31 lesson c): a job with 'probe' P runs its scan for P s (and until 2 tries ended, at most 2P) and is
     # stopped when no try came 3e-9 or more of side below its start (the certify dilation alone moves 1.3e-9 to 1.5e-9).
     pr=subprocess.Popen([sys.executable,'-I',str(ROOT/'kick/midm_scan.py'),'--n',str(j['n']),'--sub',str(ROOT/'kq'/j['input']),'--out',str(out),'--fq',str(ROOT/'fq'),'--seconds',str(sec),'--modes',j.get('modes','lkick,kick'),'--deadline',str(ROOT/'deadline'),'--seed',str(j['seed'])]+extra,cwd=ROOT/'kick',stdout=open(str(out)+'.log','w'),stderr=subprocess.STDOUT,start_new_session=True)
     probe=float(j.get('probe',0));t1=time.time();rc=None;stopped=False
     while rc is None:
      try:rc=pr.wait(timeout=5)
      except subprocess.TimeoutExpired:pass
      if rc is not None:break
      el=time.time()-t1
      if el>sec+180:
       os.killpg(pr.pid,signal.SIGTERM);rc='timeout';break
      if probe and not stopped and el>=probe:
       held=None;tries=0;best=math.inf
       for f in out.glob('scan-*.tsv'):
        for line in open(f):
         if line.startswith('# n='):
          try:held=float(line.split('held=')[1].split()[0])
          except (IndexError,ValueError):pass
         elif not line.startswith('#'):
          c=line.split('\t')
          if len(c)>=5:
           tries+=1
           try:best=min(best,float(c[4]))
           except ValueError:pass
       if held is not None and best<held-3e-9:probe=0;continue
       if tries>=2 or el>=2*probe:
        os.killpg(pr.pid,signal.SIGTERM);stopped=True
        try:rc=pr.wait(timeout=30)
        except subprocess.TimeoutExpired:os.killpg(pr.pid,signal.SIGKILL);rc=pr.wait()
        rc='probe-stop %d tries %.0f s best %r held %r'%(tries,el,best,held)
        with open(next(iter(sorted(out.glob('scan-*.tsv'))),out/'scan-x.tsv'),'a') as h:h.write('# END n=%s tries %d finds 0 best %r held %r seconds %.0f | probe stop: no try 3e-9 below the start in %.0f s\n'%(j['n'],tries,best,held,el,el))
    except Exception as e:rc='error '+repr(e)[:100]
   (out/'DONE').write_text(str(rc))
   result={'rc':rc,'seconds':time.time()-t0}
  elif kind=='lp':
   import subprocess
   t0=time.time();out=ROOT/'lp'/j['out']
   try:
    rc=subprocess.run([sys.executable,'-I','methods_lp.py',j['input'],j['out'],'--ns',str(j['n']),'--jobs','1','--iters','40'],cwd=ROOT/'lp',stdout=open(ROOT/'lp'/(j['out']+'.log'),'w'),stderr=subprocess.STDOUT,timeout=max(5,min(300,END-time.time()-5))).returncode
   except subprocess.TimeoutExpired:rc='timeout'
   out.mkdir(parents=True,exist_ok=True);(out/'DONE').write_text(str(rc))
   result={'rc':rc,'seconds':time.time()-t0}
  else:
   out=ROOT/'final'/j['output']; inp=ROOT/'final'/j['input']
   # r28: a job may name its fq flags (the POLISH flags for converged inputs; quench r27 measured the default flags
   # making 5 of 5 converged builds worse by 1.8e-6 to 2.2e-3 while the polish moved them 7e-12 to 3.8e-7 lower).
   side,dt=bs.fq_call(str(ROOT/'fq'),str(inp),str(out),list(j.get('flags',[])),600)
   result={'side':side,'seconds':dt,'input':j['input'],'output':j['output']}
  tmp=p.with_suffix('.done.tmp');tmp.write_text(json.dumps(result));os.replace(tmp,p.with_suffix('.done'))
  print(time.strftime('%H:%M:%S',time.gmtime()),which,'finish',p.name,str(result)[:250],flush=True)
  break
 if not picked:time.sleep(5)
print('deadline',flush=True)
