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
  jobs.append((priority,p.stat().st_mtime,p,'final'))
 # r27: contact-LP jobs (lpfeed.py) rank after certified finals below the bar and before chains.
 for p in (ROOT/'lp/jobs').glob('*.json'):
  j=read_json(p)
  if j is None:continue
  jobs.append((j.get('priority',-150),p.stat().st_mtime,p,'lp'))
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
  if (kind=='chain' and not (ROOT/'q'/j['start']).exists()) or (kind=='final' and not (ROOT/'final'/j['input']).exists()) or (kind=='lp' and not (ROOT/'lp'/j['input']).exists()):
   claim.rmdir();continue
  picked=True
  print(time.strftime('%H:%M:%S',time.gmtime()),which,'start',p.name,flush=True)
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
   side,dt=bs.fq_call(str(ROOT/'fq'),str(inp),str(out),[],600)
   result={'side':side,'seconds':dt,'input':j['input'],'output':j['output']}
  tmp=p.with_suffix('.done.tmp');tmp.write_text(json.dumps(result));os.replace(tmp,p.with_suffix('.done'))
  print(time.strftime('%H:%M:%S',time.gmtime()),which,'finish',p.name,str(result)[:250],flush=True)
  break
 if not picked:time.sleep(5)
print('deadline',flush=True)
