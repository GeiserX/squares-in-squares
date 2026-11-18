"""Test one rigid rotation of the entire packing, with all contacts preserved."""
import argparse,csv,json,math,pathlib,sys,time
import numpy as np
from scipy.spatial import ConvexHull

def side(P):
 h=.5*(abs(np.cos(P[:,2]))+abs(np.sin(P[:,2])));return float(np.ptp(np.r_[P[:,:2]-h[:,None],P[:,:2]+h[:,None]],axis=0).max())
def rotate(P,t):
 Q=P.copy();c=math.cos(t);s=math.sin(t);Q[:,:2]=P[:,:2]@np.array([[c,s],[-s,c]]);Q[:,2]+=t;return Q

def fit(P):
 angles=P[:,2,None]+np.pi/4+np.arange(4)[None,:]*np.pi/2
 vertices=(P[:,None,:2]+np.stack([np.cos(angles),np.sin(angles)],axis=2)*2**-.5).reshape(-1,2);vertices=vertices[ConvexHull(vertices).vertices]
 def objective(t):
  c=math.cos(t);s=math.sin(t);a=vertices@np.array([[c,s],[-s,c]]);return float(np.ptp(a,axis=0).max())
 grid=np.linspace(-np.pi/4,np.pi/4,721);values=np.array([objective(t)for t in grid]);candidates=[(objective(0.),0.)]
 local=[i for i in range(1,len(grid)-1)if values[i]<=values[i-1]and values[i]<=values[i+1]]
 for i in sorted(local,key=lambda i:values[i])[:32]:
  left,right=float(grid[i-1]),float(grid[i+1]);ratio=(5**.5-1)/2;x=right-ratio*(right-left);y=left+ratio*(right-left);fx,fy=objective(x),objective(y)
  for _ in range(65):
   if fx<fy:right,y,fy=y,x,fx;x=right-ratio*(right-left);fx=objective(x)
   else:left,x,fx=x,y,fy;y=left+ratio*(right-left);fy=objective(y)
  candidates.extend([(fx,x),(fy,y),(float(values[i]),float(grid[i]))])
 candidates += [(float(values[0]),float(grid[0])),(float(values[-1]),float(grid[-1]))]
 L,t=min(candidates);return rotate(P,t),t

def controls():
 P=np.array([[.5,.5,0.],[1.5001,.5,0.]])
 initial=rotate(P,.13);Q,t=fit(initial);assert side(initial)-side(Q)>.1 and abs(side(Q)-2.0001)<1e-9
 assert np.max(abs(np.linalg.norm(initial[:,None,:2]-initial[None,:,:2],axis=2)-np.linalg.norm(Q[:,None,:2]-Q[None,:,:2],axis=2)))<1e-12
 Q,t=fit(P);assert abs(side(Q)-side(P))<1e-10
 print('CONTROL rigid rotation shortened rotated n2, preserved pair distances, and kept the axis-aligned optimum',flush=True)

def main():
 a=argparse.ArgumentParser();a.add_argument('n',type=int);a.add_argument('start');a.add_argument('out');a.add_argument('--seconds',type=float);a.add_argument('--seed');a.add_argument('--modes');a.add_argument('--bar');a.add_argument('--deadline');a.add_argument('--fq');args=a.parse_args();controls()
 rows=list(csv.DictReader(open(args.start)));P=np.array([[float(r[k])for k in('x','y','angle')]for r in rows]);assert len(P)==args.n
 old=side(P);Q,t=fit(P);new=side(Q);dest=pathlib.Path(args.out);(dest/'raw').mkdir(exist_ok=True,parents=True)
 (dest/'globalfit.json').write_text(json.dumps(dict(old_side=old,new_side=new,rotation=t,method='721-angle grid with bounded refinement of up to32 local minima')))
 if new<old-1e-9:
  h=.5*(abs(np.cos(Q[:,2]))+abs(np.sin(Q[:,2])));Q[:,:2]-=(Q[:,:2]-h[:,None]).min(0)
  with (dest/'raw'/f'{args.n}-rigid-1.csv').open('w',newline='')as stream:
   writer=csv.writer(stream);writer.writerow(['n','square_id','x','y','angle']);writer.writerows((args.n,i,*map(float,p))for i,p in enumerate(Q))
 print(json.dumps(dict(n=args.n,old_side=old,new_side=new,rotation=t)),flush=True)
if __name__=='__main__':main()
