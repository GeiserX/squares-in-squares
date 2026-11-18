"""Choose discrete row slides and column slips with all tilted sites retained."""
from pathlib import Path
import os,sys,time,json,math,warnings
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy import sparse
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R/'lane')]
import methods_lp as mlp,family_step as fs
from k123_tartan import Hole
import k123_tartan as tartan
_native_linprog31=tartan.linprog
def _single_thread_lp31(*args,**kwargs):
 options=dict(kwargs.pop('options',{}) or {});options['threads']=1
 with warnings.catch_warnings():
  warnings.filterwarnings('ignore',message='Unrecognized options detected')
  return _native_linprog31(*args,options=options,**kwargs)
tartan.linprog=_single_thread_lp31

def cluster(v,tol=1e-7):
 out=[]
 for x in sorted(v):
  if not out or abs(x-out[-1])>tol:out.append(float(x))
 return np.array(out)

def solve(L,sites,theta,O,Slev,Rlev,goal,seconds,reference=None):
 t0=time.time();sites=np.asarray(sites,int);a=int(sites[:,0].max())+1;b=int(sites[:,1].max())+1
 ns,nr=len(Slev),len(Rlev);sr=b*ns;sc=a*nr;up=[];m=int(L)
 for ax in (0,1):
  for ay in (0,1):
   for i in range(m):
    for j in range(m):up.append((i+.5 if ax==0 else L-i-.5,j+.5 if ay==0 else L-j-.5))
 up=np.array(up);nu=len(up);zbase=sr+sc+nu;nv=zbase+len(sites)*ns*nr;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);h=.5*(abs(u[0])+abs(u[1]));H=.5+h;tol=2e-9
 ri=[];ci=[];vv=[];lower=[];upper=[]
 def add(cols,vals,lo=-np.inf,hi=1.):
  idx=len(lower);ri.extend([idx]*len(cols));ci.extend(cols);vv.extend(vals);lower.append(lo);upper.append(hi)
 for j in range(b):add(list(range(j*ns,(j+1)*ns)),[1.]*ns,1.,1.)
 for i in range(a):add(list(range(sr+i*nr,sr+(i+1)*nr)),[1.]*nr,1.,1.)
 sign=1 if theta>=math.pi/4 else -1
 for j in range(b-1):add(list(range(j*ns,(j+1)*ns))+list(range((j+1)*ns,(j+2)*ns)),list(sign*Slev)+list(-sign*Slev),hi=1e-7)
 for i in range(a-1):add(list(range(sr+i*nr,sr+(i+1)*nr))+list(range(sr+(i+1)*nr,sr+(i+2)*nr)),list(-sign*Rlev)+list(sign*Rlev),hi=1e-7)
 tree=cKDTree(up)
 pairs=tree.query_pairs(math.sqrt(2),output_type='ndarray')
 if len(pairs):
  overlap=np.max(np.abs(up[pairs[:,0]]-up[pairs[:,1]]),axis=1)<1-tol
  for i,j in pairs[overlap]:add([sr+sc+int(i),sr+sc+int(j)],[1.,1.])
 wall_states=set();collision_rows=0
 for cell,(i,j) in enumerate(sites):
  zb=zbase+cell*ns*nr
  for si in range(ns):add([zb+si*nr+rr for rr in range(nr)]+[int(j)*ns+si],[1.]*nr+[-1.],0.,0.)
  for rr in range(nr):add([zb+si*nr+rr for si in range(ns)]+[sr+int(i)*nr+rr],[1.]*ns+[-1.],0.,0.)
  collision_states={}
  for si,S in enumerate(Slev):
   for rr,Rv in enumerate(Rlev):
    c=O+(i-(a-1)/2+S)*u+(j-(b-1)/2+Rv)*v;ys=int(j)*ns+si;yr=sr+int(i)*nr+rr
    if np.any(c<h-tol) or np.any(c>L-h+tol):
     wall_states.add(zb+si*nr+rr);continue
    near=tree.query_ball_point(c,math.sqrt(2)*H)
    if not near:continue
    ds=up[near]-c
    ov=(np.abs(ds[:,0])<H-tol)&(np.abs(ds[:,1])<H-tol)&(np.abs(ds@u)<H-tol)&(np.abs(ds@v)<H-tol)
    for z in np.asarray(near)[ov]:collision_states.setdefault(int(z),[]).append(zb+si*nr+rr);collision_rows+=1
  for z,states in collision_states.items():add([sr+sc+z]+states,[1.]*(len(states)+1))
 add(list(range(sr+sc,zbase)),[1.]*nu,goal-len(sites),np.inf)
 A=sparse.coo_array((np.array(vv), (np.array(ri,dtype=np.int32),np.array(ci,dtype=np.int32))),shape=(len(lower),nv)).tocsc()
 c=np.zeros(nv);c[sr+sc:zbase]=-1
 integrality=np.zeros(nv);integrality[:zbase]=1;bounds_hi=np.ones(nv)
 for index in wall_states:bounds_hi[index]=0
 if reference:
  for j in range(b):c[j*ns:(j+1)*ns]=1e-5*np.abs(Slev-reference['S'][j])
  for i in range(a):c[sr+i*nr:sr+(i+1)*nr]=1e-5*np.abs(Rlev-reference['R'][i])
 build=time.time()-t0
 from scipy.optimize._highspy._core import _Highs
 _Highs.resetGlobalScheduler(True)
 with warnings.catch_warnings():
  warnings.filterwarnings('ignore',message='Unrecognized options detected')
  result=milp(c,integrality=integrality,bounds=Bounds(np.zeros(nv),bounds_hi),constraints=LinearConstraint(A,np.array(lower),np.array(upper)),options={'time_limit':seconds,'mip_rel_gap':0.,'threads':1,'presolve':True})
 report={'L':L,'goal':goal,'a':a,'b':b,'tilted':len(sites),'Slevels':ns,'Rlevels':nr,'variables':nv,'constraints':len(lower),'collision_constraints':collision_rows,'build_seconds':build,'solve_seconds':time.time()-t0-build,'status':int(result.status),'message':str(result.message),'dual_bound':float(result.mip_dual_bound) if getattr(result,'mip_dual_bound',None) is not None else None}
 P=None
 if result.x is not None:
  x=np.rint(result.x);z=A@x;valid=np.all(z>=np.array(lower)-1e-6)&np.all(z<=np.array(upper)+1e-6)
  report['rounded_constraints_pass']=bool(valid)
  if valid:
   S=np.array([Slev[int(np.argmax(x[j*ns:(j+1)*ns]))] for j in range(b)]);Rv=np.array([Rlev[int(np.argmax(x[sr+i*nr:sr+(i+1)*nr]))] for i in range(a)])
   centres=np.array([O+(i-(a-1)/2+S[j])*u+(j-(b-1)/2+Rv[i])*v for i,j in sites]);U=up[x[sr+sc:zbase]>.5]
   P=np.vstack((np.column_stack((centres,np.full(len(sites),theta))),np.column_stack((U,np.zeros(len(U))))))
   report.update(count=len(P),side=float(mlp.side(P)),gap=float(mlp.min_gap(P)),S=S.tolist(),R=Rv.tolist())
 return report,P

def main():
 j=json.load(open(sys.argv[1]));D=R/'out/slidemilp31'/j['tag'];D.mkdir(parents=True,exist_ok=True)
 if j.get('slide_control31'):
  P=mlp.load(str(R/'control261.csv'),{261})[261];H=Hole(P);theta=H.t0;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);sites=H.sites;T=H.T
  cu=T[:,:2]@u-(sites[:,0]-(H.a-1)/2);cv=T[:,:2]@v-(sites[:,1]-(H.b-1)/2)
  sj=np.array([np.mean(cu[sites[:,1]==jj]) for jj in range(H.b)]);rr=np.array([np.mean(cv[sites[:,0]==ii]) for ii in range(H.a)]);Ou=float(sj.mean());Ov=float(rr.mean());S=sj-Ou;Rv=rr-Ov;O=Ou*u+Ov*v
  fitted,Ofit,Sfit,Rfit,tfit=H.fit(1e-10 if H.t0>=math.pi/4 else -1e-10,S,Rv,iters=30)
  fitted_layout=H.layout(tfit,Ofit,Sfit,Rfit,fitted)
  print('CONTROL_LP',json.dumps({'theta_degrees':math.degrees(H.t0),'S_order':np.diff(S).tolist(),'R_order':np.diff(Rv).tolist(),'side':fitted,'gap':float(mlp.min_gap(fitted_layout)),'upright_lattice_error_before':H.off}),flush=True)
  if math.isfinite(fitted) and fitted<16.678781 and mlp.min_gap(fitted_layout)>-1e-7:
   theta=tfit;O=Ofit;S=Sfit;Rv=Rfit
  L=max(16.678779875,min(H.L,fitted))+5e-7
  report,Q=solve(L,sites,theta,O,cluster(S),cluster(Rv),261,60,{'S':S,'R':Rv})
  report.update(control_source_side=H.L,control_tilted=len(T),control_upright_lattice_error=H.off,control_expected=16.678779875,control_code='free row and column choices; no fixed known assignment')
  good=Q is not None and len(Q)>=261 and mlp.min_gap(Q)>-1e-7 and mlp.side(Q)<=16.678781
  report['positive_control_passed']=bool(good)
  (R/'slide-control31.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
  if Q is not None:fs.write_rows(str(D/'control261-result.csv'),len(Q),Q)
  assert good,'slide MILP failed the 261 positive control'
  return
 assert json.load((R/'slide-control31.json').open())['positive_control_passed']
 theta=math.pi/4+math.radians(j['phi']);a=j.get('a',13);b=j.get('b',13);sites=np.array([(i,k) for i in range(a) for k in range(b)]);L=j['L'];tau=math.sqrt(2)*math.tan(abs(math.radians(j['phi'])))/math.cos(math.radians(j['phi']));K=j.get('K',7)
 levels=np.arange(-K,K+1)*tau;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);O=np.array([L/2,L/2])+j.get('offset_u',0)*u+j.get('offset_v',0)*v
 report,Q=solve(L,sites,theta,O,levels,levels,j['n'],j.get('seconds',60))
 (D/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 if Q is None:return
 full=Q.copy();up=np.flatnonzero(np.abs(full[:,2])<1e-10)
 bars={int(f[0]):float(f[1]) for line in (R/'bars.tsv').read_text().splitlines() if len(f:=line.split('\t'))>=2}
 for n in range(j['n'],len(full)+1):
  if n>1000 or n not in bars:continue
  excess=len(full)-n;Q=np.delete(full,up[:excess],axis=0) if excess else full.copy()
  if len(Q)!=n or mlp.min_gap(Q)<-1e-7:continue
  side=float(mlp.side(Q))
  if side>=bars[n]-math.sqrt(n)*1e-10:continue
  tag=j['tag']+'-n'+str(n);target=R/'out/steps'/tag/'raw';target.mkdir(parents=True,exist_ok=True)
  fs.write_rows(str(target/(str(n)+'-slides31.csv')),n,Q)
  record={'n':n,'tag':tag,'pool':j['pool'],'worker':'steps','bar':bars[n],'raw':1,'code':0,'kind':'slide-milp31','side':side,'source':{'recipe_text':'slide_milp31.py constructive discrete row/column slides; parameters '+json.dumps(j,sort_keys=True)+'; model found '+str(len(full))+' squares; retained '+str(n)+'; calibrated on held261','donors':[261]}}
  with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
if __name__=='__main__':main()
