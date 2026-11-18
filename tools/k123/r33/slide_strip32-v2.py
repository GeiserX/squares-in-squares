"""Choose discrete row slides and column slips with all tilted sites retained."""
from pathlib import Path
import os,sys,time,json,math,warnings,hashlib
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy import sparse
CODE_SHA31=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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

def solve(L,sites,theta,O,Slev,Rlev,goal,seconds,reference=None,exact_count=False,local_choices=0,zero_choice=False,max_drop=0,force_drop=None,force_absent=None,forced_upright=None,max_tilted=None,convex_mask=False,mask_core=None,mask_bias=0.,free_rows32=None,free_columns32=None,free_cells32=None,force_row32=None):
 t0=time.time();sites=np.asarray(sites,int);a=int(sites[:,0].max())+1;b=int(sites[:,1].max())+1
 ns,nr=len(Slev),len(Rlev);sr=b*ns;sc=a*nr;up=[];m=int(L);optional=max_drop>0
 for ax in (0,1):
  for ay in (0,1):
   for i in range(m):
    for j in range(m):up.append((i+.5 if ax==0 else L-i-.5,j+.5 if ay==0 else L-j-.5))
 up=np.array(up);nu=len(up);uend=sr+sc+nu;wbase=uend;zbase=uend+(len(sites) if optional else 0);nv=zbase+len(sites)*ns*nr;edge_base=nv;nv+=(b*(a+1)+a*(b+1)) if convex_mask else 0;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);h=.5*(abs(u[0])+abs(u[1]));H=.5+h;tol=2e-9
 ri=[];ci=[];vv=[];lower=[];upper=[]
 def add(cols,vals,lo=-np.inf,hi=1.):
  idx=len(lower);ri.extend([idx]*len(cols));ci.extend(cols);vv.extend(vals);lower.append(lo);upper.append(hi)
 for j in range(b):add(list(range(j*ns,(j+1)*ns)),[1.]*ns,1.,1.)
 for i in range(a):add(list(range(sr+i*nr,sr+(i+1)*nr)),[1.]*nr,1.,1.)
 sign=1 if theta>=math.pi/4 else -1
 for j in range(b-1):add(list(range(j*ns,(j+1)*ns))+list(range((j+1)*ns,(j+2)*ns)),list(sign*Slev)+list(-sign*Slev),hi=1e-7)
 for i in range(a-1):add(list(range(sr+i*nr,sr+(i+1)*nr))+list(range(sr+(i+1)*nr,sr+(i+2)*nr)),list(-sign*Rlev)+list(sign*Rlev),hi=1e-7)
 # Fixed outside parents retain their exact learned level. Free parents keep the selected neighborhood.
 if free_rows32 is not None or free_columns32 is not None:assert reference is not None
 def allowed32(levels,ref,count,is_free):
  if not is_free:
   idx=int(np.argmin(np.abs(levels-ref)));assert abs(levels[idx]-ref)<1e-7
   return {idx}
  result=set(np.argsort(np.abs(levels-ref))[:count]) if count and ref is not None else set(range(len(levels)))
  if zero_choice:result.add(int(np.argmin(np.abs(levels))))
  return result
 SA32={j:allowed32(Slev,reference['S'][j] if reference else None,local_choices,free_rows32 is None or j in free_rows32) for j in range(b)}
 RA32={i:allowed32(Rlev,reference['R'][i] if reference else None,local_choices,free_columns32 is None or i in free_columns32) for i in range(a)}
 if force_row32:
  for jj,si in force_row32.items():add([int(jj)*ns+int(si)],[1.],1.,1.)
 tree=cKDTree(up)
 pairs=tree.query_pairs(math.sqrt(2),output_type='ndarray')
 if len(pairs):
  overlap=np.max(np.abs(up[pairs[:,0]]-up[pairs[:,1]]),axis=1)<1-tol
  for i,j in pairs[overlap]:add([sr+sc+int(i),sr+sc+int(j)],[1.,1.])
 wall_states=set();collision_rows=0
 for cell,(i,j) in enumerate(sites):
  zb=zbase+cell*ns*nr
  for si in range(ns):add([zb+si*nr+rr for rr in range(nr)]+[int(j)*ns+si],[1.]*nr+[-1.],-np.inf if optional else 0.,0.)
  for rr in range(nr):add([zb+si*nr+rr for si in range(ns)]+[sr+int(i)*nr+rr],[1.]*ns+[-1.],-np.inf if optional else 0.,0.)
  if optional:add(list(range(zb,zb+ns*nr))+[wbase+cell],[1.]*(ns*nr)+[-1.],0.,0.)
  collision_states={}
  for si in sorted(SA32[int(j)]):
   S=Slev[si]
   for rr in sorted(RA32[int(i)]):
    Rv=Rlev[rr]
    c=O+(i-(a-1)/2+S)*u+(j-(b-1)/2+Rv)*v;ys=int(j)*ns+si;yr=sr+int(i)*nr+rr
    if np.any(c<h-tol) or np.any(c>L-h+tol):
     wall_states.add(zb+si*nr+rr);continue
    near=tree.query_ball_point(c,math.sqrt(2)*H)
    if not near:continue
    ds=up[near]-c
    ov=(np.abs(ds[:,0])<H-tol)&(np.abs(ds[:,1])<H-tol)&(np.abs(ds@u)<H-tol)&(np.abs(ds@v)<H-tol)
    for z in np.asarray(near)[ov]:collision_states.setdefault(int(z),[]).append(zb+si*nr+rr);collision_rows+=1
  for z,states in collision_states.items():add([sr+sc+z]+states,[1.]*(len(states)+1))
 if optional:
  add(list(range(wbase,zbase)),[1.]*len(sites),len(sites)-max_drop,len(sites)-force_drop if force_drop is not None else max_tilted if max_tilted is not None else len(sites))
  if force_drop is not None:add(list(range(wbase,zbase)),[1.]*len(sites),len(sites)-force_drop,len(sites)-force_drop)
  add(list(range(sr+sc,uend))+list(range(wbase,zbase)),[1.]*(nu+len(sites)),goal,goal if exact_count else np.inf)
 else:add(list(range(sr+sc,uend)),[1.]*nu,goal-len(sites),goal-len(sites) if exact_count else np.inf)
 if convex_mask:
  assert optional and len(sites)==a*b,'convex mask requires the complete candidate grid'
  wm={(int(ii),int(jj)):wbase+cell for cell,(ii,jj) in enumerate(sites)};edge=edge_base
  lines=[[wm[ii,jj] for ii in range(a)] for jj in range(b)]+[[wm[ii,jj] for jj in range(b)] for ii in range(a)]
  for line in lines:
   transitions=[];chain=[None]+line+[None]
   for prev,nxt in zip(chain,chain[1:]):
    cols=[edge];plus=[-1.];minus=[-1.]
    if nxt is not None:cols.append(nxt);plus.append(1.);minus.append(-1.)
    if prev is not None:cols.append(prev);plus.append(-1.);minus.append(1.)
    add(cols,plus,hi=0.);add(cols,minus,hi=0.);transitions.append(edge);edge+=1
   add(transitions,[1.]*len(transitions),hi=2.)
  assert edge==nv
 if forced_upright is not None:
  distance=np.linalg.norm(up-np.array(forced_upright),axis=1);idx=int(np.argmin(distance));assert distance[idx]<1e-8;add([sr+sc+idx],[1.],1.,1.)
 A=sparse.coo_array((np.array(vv), (np.array(ri,dtype=np.int32),np.array(ci,dtype=np.int32))),shape=(len(lower),nv)).tocsc()
 c=np.zeros(nv);c[sr+sc:zbase]=-1
 if optional and mask_core and mask_bias:
  lo_i,hi_i,lo_j,hi_j=mask_core
  for cell,(ii,jj) in enumerate(sites):c[wbase+cell]+=mask_bias*(-1 if lo_i<=ii<hi_i and lo_j<=jj<hi_j else 1)
 integrality=np.zeros(nv);integrality[:zbase]=1;bounds_hi=np.ones(nv)
 for index in wall_states:bounds_hi[index]=0
 for cell in (force_absent or []):bounds_hi[wbase+cell]=0
 for jj,allowed in SA32.items():
  for si in range(ns):
   if si not in allowed:bounds_hi[jj*ns+si]=0
 for ii,allowed in RA32.items():
  for rr in range(nr):
   if rr not in allowed:bounds_hi[sr+ii*nr+rr]=0
 bounds_lo=np.zeros(nv)
 if free_cells32 is not None:
  assert optional,'strip occupancy requires optional cells'
  cells={tuple(c) for c in free_cells32}
  for cell,(ii,jj) in enumerate(sites):
   if (int(ii),int(jj)) not in cells:
    value=1. if mask_core is None or (mask_core[0]<=ii<mask_core[1] and mask_core[2]<=jj<mask_core[3]) else 0.
    bounds_lo[wbase+cell]=bounds_hi[wbase+cell]=value
 if reference:
  for j in range(b):c[j*ns:(j+1)*ns]=1e-5*np.abs(Slev-reference['S'][j])
  for i in range(a):c[sr+i*nr:sr+(i+1)*nr]=1e-5*np.abs(Rlev-reference['R'][i])
 build=time.time()-t0
 from scipy.optimize._highspy._core import _Highs
 _Highs.resetGlobalScheduler(True)
 with warnings.catch_warnings():
  warnings.filterwarnings('ignore',message='Unrecognized options detected')
  result=milp(c,integrality=integrality,bounds=Bounds(bounds_lo,bounds_hi),constraints=LinearConstraint(A,np.array(lower),np.array(upper)),options={'time_limit':seconds,'mip_rel_gap':0.,'threads':1,'presolve':True})
 report={'strip_free_rows32':free_rows32,'strip_free_columns32':free_columns32,'strip_free_cells32':free_cells32,'code_sha256':CODE_SHA31,'L':L,'goal':goal,'local_choices':local_choices,'a':a,'b':b,'tilted':len(sites),'Slevels':ns,'Rlevels':nr,'variables':nv,'constraints':len(lower),'collision_constraints':collision_rows,'build_seconds':build,'solve_seconds':time.time()-t0-build,'status':int(result.status),'message':str(result.message),'dual_bound':float(result.mip_dual_bound) if getattr(result,'mip_dual_bound',None) is not None else None}
 P=None
 if result.x is not None:
  x=np.rint(result.x);z=A@x;valid=np.all(z>=np.array(lower)-1e-6)&np.all(z<=np.array(upper)+1e-6)
  report['rounded_constraints_pass']=bool(valid)
  if valid:
   S=np.array([Slev[int(np.argmax(x[j*ns:(j+1)*ns]))] for j in range(b)]);Rv=np.array([Rlev[int(np.argmax(x[sr+i*nr:sr+(i+1)*nr]))] for i in range(a)])
   kept=sites[x[wbase:zbase]>.5] if optional else sites
   centres=np.array([O+(i-(a-1)/2+S[j])*u+(j-(b-1)/2+Rv[i])*v for i,j in kept]);U=up[x[sr+sc:uend]>.5]
   report.update(tilted_selected=len(kept),sites_selected=kept.tolist(),max_drop=max_drop)
   P=np.vstack((np.column_stack((centres,np.full(len(kept),theta))),np.column_stack((U,np.zeros(len(U))))))
   report.update(count=len(P),side=float(mlp.side(P)),gap=float(mlp.min_gap(P)),S=S.tolist(),R=Rv.tolist())
 return report,P

def main():
 j=json.load(open(sys.argv[1]));D=R/'out/slidestrip32'/j['tag'];D.mkdir(parents=True,exist_ok=True)
 if j.get('strip_bound_control32'):
  args=(4.5,np.array([(0,0),(1,0)]),math.pi/4,np.array([2.25,2.25]),np.array([-.1,0.,.1]),np.array([0.]),2,10)
  kw=dict(reference={'S':np.array([0.]),'R':np.array([0.,0.])},exact_count=True,max_drop=1,free_rows32=[],free_columns32=[],free_cells32=[])
  r0,q0=solve(*args,**kw);r1,q1=solve(*args,**kw,force_row32={0:2})
  good=q0 is not None and len(q0)==2 and r0['tilted_selected']==2 and mlp.min_gap(q0)>-1e-7 and q1 is None and r1['status']==2
  result={'positive':r0,'wrong_fixed_row_refused':r1,'strip_bound_control_passed32':bool(good)};(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert good;return
 if j.get('convex_control31'):
  args=(5.5,np.array([(0,0),(1,0),(2,0)]),math.pi/4,np.array([2.75,2.75]),np.array([0.]),np.array([0.]),2,10)
  r0,q0=solve(*args,exact_count=True,max_drop=1,force_drop=1,force_absent=[1]);r1,q1=solve(*args,exact_count=True,max_drop=1,force_drop=1,force_absent=[1],convex_mask=True)
  good=q0 is not None and len(q0)==2 and r0.get('sites_selected')==[[0,0],[2,0]] and mlp.min_gap(q0)>-1e-7 and q1 is None and r1['status']==2
  result={'code_sha256':CODE_SHA31,'baseline':r0,'hole_refusal':r1,'convex_positive_and_negative_control_passed':bool(good)};(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert good,'convex-mask positive/negative control failed';return
 if j.get('optional_control31'):
  report,Q=solve(4.5,np.array([(0,0),(2,0)]),math.pi/4,np.array([1.5+2**-.5,1.5+2**-.5]),np.array([0.]),np.array([0.]),2,10,exact_count=True,max_drop=1,force_drop=1,force_absent=[0],forced_upright=[1.5,1.5])
  good=Q is not None and len(Q)==2 and report.get('tilted_selected')==1 and mlp.min_gap(Q)>-1e-7
  good=good and report.get('sites_selected')==[[2,0]] and bool(np.any(np.linalg.norm(Q[np.abs(Q[:,2])<1e-10,:2]-np.array([1.5,1.5]),axis=1)<1e-8));report['optional_positive_control_passed']=bool(good);(D/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
  assert good,'forced omission control failed';return
 if j.get('slide_control31'):
  P=mlp.load(str(R/'control261.csv'),{261})[261];H=Hole(P);theta=H.t0;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);sites=H.sites;T=H.T
  cu=T[:,:2]@u-(sites[:,0]-(H.a-1)/2);cv=T[:,:2]@v-(sites[:,1]-(H.b-1)/2)
  sj=np.array([np.mean(cu[sites[:,1]==jj]) for jj in range(H.b)]);rr=np.array([np.mean(cv[sites[:,0]==ii]) for ii in range(H.a)]);Ou=float(sj.mean());Ov=float(rr.mean());S=sj-Ou;Rv=rr-Ov;O=Ou*u+Ov*v
  fitted,Ofit,Sfit,Rfit,tfit=H.fit(1e-10 if H.t0>=math.pi/4 else -1e-10,S,Rv,iters=30)
  fitted_layout=H.layout(tfit,Ofit,Sfit,Rfit,fitted)
  print('CONTROL_LP',json.dumps({'theta_degrees':math.degrees(H.t0),'S_order':np.diff(S).tolist(),'R_order':np.diff(Rv).tolist(),'side':fitted,'gap':float(mlp.min_gap(fitted_layout)),'upright_lattice_error_before':H.off}),flush=True)
  if math.isfinite(fitted) and fitted<16.678781 and mlp.min_gap(fitted_layout)>-1e-7:
   theta=tfit;O=Ofit;S=Sfit;Rv=Rfit
  if j.get('production_reference'):
   sm=float(np.mean(S));rm=float(np.mean(Rv));u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);O=O+sm*u+rm*v;S=S-sm;Rv=Rv-rm
  L=max(16.678779875,min(H.L,fitted))+5e-7
  cref={'S':S,'R':Rv}
  if j.get('production_reference'):
   dt=math.sqrt(2)*math.sin(abs(theta-math.pi/4));cref={'S':(np.arange(H.b)-(H.b-1)/2)*dt,'R':-(np.arange(H.a)-(H.a-1)/2)*dt}
  report,Q=solve(L,sites,theta,O,cluster(S),cluster(Rv),261,60,cref,local_choices=j.get('local_choices',0))
  report.update(control_source_side=H.L,control_tilted=len(T),control_upright_lattice_error=H.off,control_expected=16.678779875,control_code='free row and column choices within '+str(j.get('local_choices',0))+'-level neighborhoods; no fixed known assignment')
  good=Q is not None and len(Q)>=261 and mlp.min_gap(Q)>-1e-7 and mlp.side(Q)<=16.678781
  if good:
   HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],np.array(report.get('sites_selected',sites)),theta,O,len(Q))
   Lc,Oc,Sc,Rc,tc=HC.fit(1e-10 if theta>=math.pi/4 else -1e-10,np.array(report['S']),np.array(report['R']),iters=30)
   Qc=HC.layout(tc,Oc,Sc,Rc,Lc);gc=float(mlp.min_gap(Qc))
   report['continuous_control']={'side':Lc,'gap':gc,'count':len(Qc)}
   good=math.isfinite(Lc) and abs(Lc-16.678779875)<1e-6 and gc>-1e-7
  report['positive_control_passed']=bool(good)
  (R/'slide-control31.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
  if Q is not None:fs.write_rows(str(D/'control261-result.csv'),len(Q),Q)
  assert good,'slide MILP failed the 261 positive control'
  return
 assert json.load((R/'slide-control31.json').open())['positive_control_passed']
 theta=math.pi/4+math.radians(j['phi']);a=j.get('a',13);b=j.get('b',13);halo=j.get('halo',0);sites=np.array(j.get('sites',[(i,k) for i in range(a+2*halo) for k in range(b+2*halo)]),dtype=int);sites-=sites.min(axis=0);a=int(sites[:,0].max())+1;b=int(sites[:,1].max())+1;L=j['L'];tau=math.sqrt(2)*(math.sin(abs(math.radians(j['phi']))) if j.get('scheme')=='sine' else math.tan(abs(math.radians(j['phi'])))/math.cos(math.radians(j['phi'])));K=j.get('K',7)
 levels=np.arange(-K,K+1)*tau if tau>1e-12 else np.array([0.]);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);O=np.array([L/2,L/2])+j.get('offset_u',0)*u+j.get('offset_v',0)*v
 reference=None
 if j.get('local_choices'):
  reference={'S':(np.arange(b)-(b-1)/2)*tau,'R':-(np.arange(a)-(a-1)/2)*tau}
 Slevels=levels;Rlevels=levels;reference_receipt=None
 if j.get('learned_reference'):
  HP=mlp.load(str(R/('control'+str(j['n'])+'.csv')),{j['n']})[j['n']];HH=Hole(HP);turn=theta-HH.t0;S0,R0=HH.start(turn)
  LF,OF,SF,RF,TF=HH.fit(turn,S0,R0,iters=30);QF=HH.layout(TF,OF,SF,RF,LF);gf=float(mlp.min_gap(QF))
  assert math.isfinite(LF) and gf>-1e-7,'learned LP reference failed'
  assert HH.a+2*halo==a and HH.b+2*halo==b and len(HH.sites)==HH.a*HH.b,'reference shape differs'
  if halo:
   step0=math.sqrt(2)*math.sin(abs(theta-math.pi/4));SF=np.r_[SF[0]-step0*np.arange(halo,0,-1),SF,SF[-1]+step0*np.arange(1,halo+1)];RF=np.r_[RF[0]+step0*np.arange(halo,0,-1),RF,RF[-1]-step0*np.arange(1,halo+1)]
  O=OF+np.array([(L-LF)/2,(L-LF)/2]);reference={'S':SF,'R':RF}
  step=math.sqrt(2)*math.sin(abs(theta-math.pi/4));Slevels=cluster(np.concatenate([SF+shift*step for shift in [-1/3,0,1/3]]));Rlevels=cluster(np.concatenate([RF+shift*step for shift in [-1/3,0,1/3]]))
  reference_receipt={'n':j['n'],'side':LF,'gap':gf,'O':OF.tolist(),'S':SF.tolist(),'R':RF.tolist(),'input_sha256':hashlib.sha256((R/('control'+str(j['n'])+'.csv')).read_bytes()).hexdigest()}
  if j.get('learned_control') or j.get('anchor_reference'):
   delta=j.get('anchor_reference',5e-7);L=LF+delta;O=OF+np.array([delta/2,delta/2])
 if j.get('warm_output31'):
  prior=json.load((R/j['warm_report31']).open());Q=mlp.load(str(R/j['warm_output31']),{j['n']})[j['n']];sites=np.array(prior['sites_selected']);Skeep=np.array(prior['S']);Rkeep=np.array(prior['R']);tilt=Q[np.abs(Q[:,2])>1e-10];assert len(tilt)==len(sites) and mlp.min_gap(Q)>-1e-7
  u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);im=sites[:,0];jm=sites[:,1];O=(tilt[:,:2]-np.outer(im-(a-1)/2+Skeep[jm],u)-np.outer(jm-(b-1)/2+Rkeep[im],v)).mean(axis=0);L=float(prior['L']);report=dict(prior)
  report.update(code_sha256=CODE_SHA31,status='warm-refine',message='Refit persisted model topology without another MILP',dual_bound=None,build_seconds=0.,solve_seconds=0.,warm_input_sha256=hashlib.sha256((R/j['warm_output31']).read_bytes()).hexdigest())
 else:
  free_rows32=j.get('free_rows32');free_cols32=j.get('free_columns32')
  free_cells32=([list(map(int,(ii,jj))) for ii,jj in sites if (free_rows32 is not None and int(jj) in free_rows32) or (free_cols32 is not None and int(ii) in free_cols32)] if j.get('strip32') else None)
  forced_holes32={tuple(x) for x in j.get('forced_holes32',[])}
  if forced_holes32:
   assert free_cells32 is not None and forced_holes32<=set(map(tuple,free_cells32)),'forced holes must stay inside the free strips'
  absent32=[cell for cell,(ii,jj) in enumerate(sites) if (j.get('force_halo_absent') and (ii<halo or ii>=a-halo or jj<halo or jj>=b-halo)) or (int(ii),int(jj)) in forced_holes32]
  report,Q=solve(L,sites,theta,O,Slevels,Rlevels,j['n'],j.get('seconds',60),reference=reference,exact_count=j.get('exact_count',False),local_choices=j.get('local_choices',0),zero_choice=j.get('zero_choice',False),max_drop=j.get('max_drop',0),force_drop=j.get('force_drop'),force_absent=absent32,max_tilted=j.get('max_tilted'),convex_mask=j.get('convex_mask',False),mask_core=(halo,a-halo,halo,b-halo) if halo else None,mask_bias=j.get('mask_bias',0.),free_rows32=free_rows32,free_columns32=free_cols32,free_cells32=free_cells32)
 if Q is not None and j.get('forced_holes32'):
  report['forced_holes_absent32']=not(set(map(tuple,j['forced_holes32']))&set(map(tuple,report['sites_selected'])))
  assert report['forced_holes_absent32'],'a forced hole was retained'
 if reference_receipt:report['learned_reference']=reference_receipt
 if j.get('learned_control'):
  good=Q is not None and len(Q)==j['n'] and mlp.min_gap(Q)>-1e-7 and mlp.side(Q)<=L+1e-7;report['learned_positive_control_passed']=bool(good)
  (D/'result.json').write_text(json.dumps(report,indent=2));assert good,'learned production-domain control failed'
 if j.get('rigid_control'):
  good=Q is not None and len(Q)==j['n'] and mlp.min_gap(Q)>-1e-7 and mlp.side(Q)<=L+1e-7
  report['rigid_positive_control_passed']=bool(good)
  (D/'result.json').write_text(json.dumps(report,indent=2));assert good,'rigid phase control failed'
 (D/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
 if Q is None:return
 fs.write_rows(str(D/'topology-start.csv'),len(Q),Q)
 if j.get('continuous_refine'):
  selected=np.array(report.get('sites_selected',sites));mi=selected.min(axis=0);ka,kb=(selected.max(axis=0)-mi+1).tolist();selected=selected-mi
  uu=np.array([math.cos(theta),math.sin(theta)]);vv=np.array([-uu[1],uu[0]]);Oref=O+(mi[0]+(ka-1)/2-(a-1)/2)*uu+(mi[1]+(kb-1)/2-(b-1)/2)*vv
  Sref=np.array(report['S'])[mi[1]:mi[1]+kb];Rref=np.array(report['R'])[mi[0]:mi[0]+ka]
  HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],selected,theta,Oref,len(Q));roundtrip=float(np.max(np.abs(HC.centres(theta,Oref,Sref,Rref)-Q[np.abs(Q[:,2])>1e-10,:2])));assert roundtrip<1e-7,'selected-site frame changed geometry';report['selected_frame_error']=roundtrip
  Lc,Oc,Sc,Rc,tc=HC.fit(1e-10 if theta>=math.pi/4 else -1e-10,Sref,Rref,iters=30)
  Qc=HC.layout(tc,Oc,Sc,Rc,Lc);gc=float(mlp.min_gap(Qc))
  report['continuous_fit']={'side':Lc,'gap':gc,'count':len(Qc)}
  if math.isfinite(Lc) and gc>-1e-7 and mlp.side(Qc)<mlp.side(Q):Q=Qc
 fs.write_rows(str(D/'model-output.csv'),len(Q),Q)
 report['output_count']=len(Q);report['output_side']=float(mlp.side(Q));report['output_gap']=float(mlp.min_gap(Q));(D/'result.json').write_text(json.dumps(report,indent=2));print('CONTINUOUS_OUTPUT',json.dumps(report),flush=True)
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
  record={'n':n,'tag':tag,'pool':j['pool'],'worker':'steps','bar':bars[n],'raw':1,'code':0,'kind':'slide-milp31','side':side,'source':{'recipe_text':'slide_strip32.py constructive discrete row/column slides; parameters '+json.dumps(j,sort_keys=True)+'; model found '+str(len(full))+' squares; retained '+str(n)+'; calibrated on held261'+(' and held'+str(j['n']) if j.get('learned_reference') else ''),'donors':[261,j['n']] if j.get('learned_reference') else [261]}}
  with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
if __name__=='__main__':main()
