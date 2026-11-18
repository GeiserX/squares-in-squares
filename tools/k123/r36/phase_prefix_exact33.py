"""Certify the upright maximum after the improved prefix sweep incumbent."""
from pathlib import Path
import sys,json,math,time
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
import slide_phase33 as phase
from k123_tartan import Hole
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

q0=refill(3.,np.empty((0,2)),math.pi/4);q1=refill(3.,np.array([[1.5,1.5]]),math.pi/4)
assert len(q0)==9 and len(q1)==5 and mlp.min_gap(q0)>-1e-7 and mlp.min_gap(q1)>-1e-7
print('REFILL_CONTROLS empty=9 central45=5',flush=True)
if j.get('exact_uprights33'):
 check,known=phase.solve(3.,np.array([[0,0]]),math.pi/4,np.array([1.5,1.5]),np.array([0.]),np.array([0.]),1,10,reference={'S':np.array([0.]),'R':np.array([0.])},free_rows32=[],free_columns32=[])
 assert known is not None and len(known)==5 and mlp.min_gap(known)>-1e-7
 print('EXACT_UPRIGHT_CONTROL central45=5',flush=True)
source=R/'out/phase33/verify-phase33-scout0/result.json';r=json.load(source.open());ref=r['learned_reference'];theta=r['theta32'];L=r['L'];O=np.array(r['origin32']);S=np.array(ref['S']);Rv=np.array(ref['R']);S[:0]-=1.;Rv[:0]+=1.;sites=np.array(sorted(double(13,13,2,1)));u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);T=np.array([O+(ii-7+S[kk])*u+(kk-7+Rv[ii])*v for ii,kk in sites]);h=.5*(abs(u[0])+abs(u[1]));wall=max(float(np.max(h-T)),float(np.max(T+h-L)));tilt=np.column_stack((T,np.full(len(T),theta)));gap=float(mlp.min_gap(tilt));result={'controls':[9,5],'source':str(source),'theta':theta,'L':L,'integer_cuts':[0,0],'tilted':len(T),'tilted_gap':gap,'wall_excess':wall,'code_sha256':__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()}
if wall<=1e-7 and gap>-1e-7:
 Q=refill(L,T,theta);result.update(count=len(Q),side=float(mlp.side(Q)),gap=float(mlp.min_gap(Q)),S=S.tolist(),R=Rv.tolist());assert result['gap']>-1e-7
 if j.get('exact_uprights33'):
  aa=int(sites[:,0].max())+1;bb=int(sites[:,1].max())+1;Osmall=O+((aa-1)/2-7)*u+((bb-1)/2-7)*v
  exact,P=phase.solve(L,sites,theta,Osmall,phase.cluster(S[:bb]),phase.cluster(Rv[:aa]),171,15,reference={'S':S[:bb],'R':Rv[:aa]},free_rows32=[],free_columns32=[])
  result['exact_uprights33']={k:exact.get(k) for k in ['status','count','side','gap','dual_bound','solve_seconds','variables']}
  if P is not None:
   assert np.max(abs(P[:len(T),:2]-T))<1e-8 and mlp.min_gap(P)>-1e-7
   if len(P)>=len(Q):Q=P
  mi=sites.min(0);sizes=sites.max(0)-mi+1;ka,kb=map(int,sizes);Oref=O+(mi[0]+(ka-1)/2-7)*u+(mi[1]+(kb-1)/2-7)*v
  HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],sites-mi,theta,Oref,len(Q));SF=S[mi[1]:mi[1]+kb];RF=Rv[mi[0]:mi[0]+ka]
  assert np.max(abs(HC.centres(theta,Oref,SF,RF)-Q[:len(T),:2]))<1e-8
  LL,OO,SS,RR,TT=HC.fit(1e-10,SF,RF,iters=30);P=HC.layout(TT,OO,SS,RR,LL);gg=float(mlp.min_gap(P));result['continuous_fit33']={'side':LL,'gap':gg,'count':len(P)}
  if math.isfinite(LL) and gg>-1e-7 and mlp.side(P)<mlp.side(Q):Q=P
  result.update(count=len(Q),side=float(mlp.side(Q)),gap=float(mlp.min_gap(Q)))
 fs.write_rows(str(D/'model-output.csv'),len(Q),Q)
(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:x for k,x in result.items() if k not in {'S','R'}}),flush=True)
