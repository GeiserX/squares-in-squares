#!/usr/bin/env python3
from pathlib import Path
import sys,time,json,math,collections,datetime,argparse
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));import family_loop as f
ap=argparse.ArgumentParser(description='Find same-side layouts with new folded angle profiles among recent near files.')
ap.add_argument('work',type=Path);ap.add_argument('--round',default='r23');ap.add_argument('--limit',type=int,default=60)
ap.add_argument('--recent',type=float,default=2400);ap.add_argument('--side-tol',type=float,default=1e-6);ap.add_argument('--angle-tol',type=float,default=0.01)
ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
w=a.work.resolve();s=w.parent.parent;D=w/'deploy/donors'
paths=[p for p in s.glob('take-*-'+a.round+'/near/*.csv') if p.parent.parent!=w.parent and p.stat().st_mtime>time.time()-a.recent]
paths=sorted(paths,key=lambda p:-p.stat().st_mtime)[:a.limit]
cache={};found=[];stat=collections.Counter();t0=time.time()
def signature(P):
 L,P=f.fs.canon(P);a=np.mod(P[:,2],math.pi/2);return L,np.sort(np.minimum(a,math.pi/2-a))
for p in paths:
 try:
  ns=f._ns_of(str(p))
  if len(ns)!=1 or not 1<=ns[0]<=1000:continue
  n=ns[0];P=f.fs.load(str(p))[n];L,sig=signature(P);stat['tested']+=1
  if n not in cache:
   ds=[]
   for q in D.glob(f'{n}-*.csv'):
    Q=f.fs.load(str(q))[n];side,angles=signature(Q);ds.append((str(q),side,angles))
   cache[n]=ds
  close=[(str(q),abs(side-L),float(np.max(abs(angles-sig)))) for q,side,angles in cache[n] if abs(side-L)<a.side_tol]
  if not close:stat['no_side_twin']+=1;continue
  stat['side_twins']+=1
  closest=min(close,key=lambda q:q[2])
  if closest[2]<=a.angle_tol:stat['angle_signature_close']+=1;continue
  env=f.readable(P,n)
  if env is None:stat['novel_angles_unreadable']+=1;continue
  so,lic=f.near_metadata(str(p),n)
  found.append(dict(n=n,path=str(p),side=L,minimum_angle_difference=closest[2],nearest_donor=closest[0],side_difference=closest[1],env=env,source=so,licence=lic))
  stat['readable_novel_angles']+=1
 except Exception as e:stat['errors']+=1;print(str(p),type(e).__name__,str(e)[:150],flush=True)
result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),seconds=time.time()-t0,statistics=dict(stat),candidates=found)
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(seconds=result['seconds'],statistics=result['statistics'],candidates=[dict(n=r['n'],path=r['path'],minimum_angle_difference=r['minimum_angle_difference']) for r in found],output=str(a.output)),indent=2),flush=True)
