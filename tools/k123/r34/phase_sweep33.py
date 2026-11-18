"""Enumerate concrete integer slip cuts before any further joint phase solve."""
from pathlib import Path
import sys,json,math,time,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
from doublejog32 import double
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);tol=2e-9
def refill(L,T,theta):
 m=int(L);up=np.array([(i+.5 if ax==0 else L-i-.5,k+.5 if ay==0 else L-k-.5) for ax in [0,1] for ay in [0,1] for i in range(m) for k in range(m)])
 up=np.unique(np.round(up,12),axis=0);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);H=.5+.5*(abs(u[0])+abs(u[1]))
 if len(T):
  ds=up[:,None,:]-T[None,:,:];ov=(abs(ds[:,:,0])<H-tol)&(abs(ds[:,:,1])<H-tol)&(abs(ds@u)<H-tol)&(abs(ds@v)<H-tol);up=up[~ov.any(1)]
 best=[]
 for swap in [False,True]:
  for sx in [-1,1]:
   for sy in [-1,1]:
    xx=up[:,1] if swap else up[:,0];yy=up[:,0] if swap else up[:,1];chosen=[]
    for k in np.lexsort((sy*yy,sx*xx)):
     p=up[k]
     if chosen and np.any(np.max(abs(np.array(chosen)-p),axis=1)<1-tol):continue
     chosen.append(p)
    if len(chosen)>len(best):best=chosen
 return np.vstack((np.column_stack((T,np.full(len(T),theta))),np.column_stack((np.asarray(best).reshape(-1,2),np.zeros(len(best))))))

start=time.time();sites=np.array(sorted(double(13,13,2,1)));best=0;attempted=0;valid=0;top=[];finished=True
for source_index in range(6):
 source=R/('out/phase33/verify-phase33-scout'+str(source_index)+'/result.json');r=json.load(source.open());ref=r['learned_reference'];theta=r['theta32'];L=r['L'];O=np.array(r['origin32']);S0=np.array(ref['S']);R0=np.array(ref['R']);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);h=.5*(abs(u[0])+abs(u[1]));cuts=[(3,3)]+[(a,b) for a in range(len(S0)+1) for b in range(len(R0)+1) if (a,b)!=(3,3)]
 for cs,cr in cuts:
  if time.time()-start>j.get('seconds',45):finished=False;break
  attempted+=1;S=S0.copy();Rv=R0.copy();S[:cs]-=1.;Rv[:cr]+=1.;T=np.array([O+(ii-7+S[kk])*u+(kk-7+Rv[ii])*v for ii,kk in sites]);wall=max(float(np.max(h-T)),float(np.max(T+h-L)))
  if wall>1e-7:continue
  tilt=np.column_stack((T,np.full(len(T),theta)))
  if mlp.min_gap(tilt)<-1e-7:continue
  valid+=1;Q=refill(L,T,theta);count=len(Q)
  if count>best:
   best=count;assert mlp.min_gap(Q)>-1e-7;z={'source_index':source_index,'cuts':[cs,cr],'count':count,'side':float(mlp.side(Q)),'gap':float(mlp.min_gap(Q)),'S':S.tolist(),'R':Rv.tolist(),'theta':theta,'L':L,'origin':O.tolist()};top.append(z);fs.write_rows(str(D/'model-output.csv'),count,Q);(D/'best.json').write_text(json.dumps(z));print('BEST',json.dumps({k:v for k,v in z.items() if k not in {'S','R'}}),flush=True)
  if source_index==0 and (cs,cr)==(3,3):assert count==355,('prefix3control',count)
 if not finished:break
result={'attempted':attempted,'valid':valid,'best_count':best,'target_count':367,'finished':finished,'seconds':time.time()-start,'changed':'enumerated fixed integer prefix cuts, no joint solver','controls':'source0 cuts3/3 reproduces355','code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'improvements':[{k:v for k,v in z.items() if k not in {'S','R'}} for z in top]};(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
