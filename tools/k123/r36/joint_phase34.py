"""Choose a joint mask across several physical upright phases using a warm integer model."""
from pathlib import Path
import sys,os,json,time,math,hashlib,itertools
import numpy as np
from scipy.sparse import coo_matrix
from scipy.optimize._highspy import _core as hs
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
from k123_tartan import Hole
ns={};exec(compile((R/'whole_crossover33.py').read_text().split('j=json.load(open(sys.argv[1]))')[0],'matching-pure','exec'),ns)
independent,adjacency=ns['independent'],ns['adjacency']
def solve(n,edges,warm,seconds):
 assert all(not(warm[a]>.5 and warm[b]>.5) for a,b in edges),'infeasible warm collision mask'
 ne=len(edges);rr=np.repeat(np.arange(ne),2);cc=np.array(edges,dtype=np.int32).ravel();A=coo_matrix((np.ones(2*ne),(rr,cc)),shape=(ne,n)).tocsc()
 lp=hs.HighsLp();lp.num_col_=n;lp.num_row_=ne;lp.col_cost_=np.full(n,-1.);lp.col_lower_=np.zeros(n);lp.col_upper_=np.ones(n);lp.row_lower_=np.full(ne,-hs.kHighsInf);lp.row_upper_=np.ones(ne);lp.integrality_=[hs.HighsVarType.kInteger]*n
 mat=hs.HighsSparseMatrix();mat.format_=hs.MatrixFormat.kColwise;mat.num_col_=n;mat.num_row_=ne;mat.start_=A.indptr.astype(np.int32);mat.index_=A.indices.astype(np.int32);mat.value_=A.data;lp.a_matrix_=mat
 h=hs._Highs()
 for k,v in [('output_flag',False),('threads',1),('parallel','off'),('time_limit',float(seconds)),('mip_rel_gap',0.)]:assert h.setOptionValue(k,v)==hs.HighsStatus.kOk,(k,v)
 assert h.passModel(lp)==hs.HighsStatus.kOk
 assert h.setSolution(n,np.arange(n,dtype=np.int32),np.asarray(warm,dtype=float))==hs.HighsStatus.kOk
 start=time.time();status=h.run();info=h.getInfo();sol=h.getSolution();valid=bool(sol.value_valid);x=np.asarray(sol.col_value) if valid else np.asarray(warm);chosen=np.flatnonzero(x>.5);assert all(not(x[a]>.5 and x[b]>.5) for a,b in edges)
 return chosen,dict(status=str(h.getModelStatus()),run_status=str(status),valid_incumbent=valid,count=len(chosen),warm_count=int(np.sum(warm)),dual_bound=-float(info.mip_dual_bound),gap=float(info.mip_gap),nodes=int(info.mip_node_count),solve_seconds=time.time()-start)

def controls():
 for graph in range(8):
  pairs=[(0,1),(0,2),(1,2)];edges=[p for i,p in enumerate(pairs) if graph>>i&1];best=max(mask.bit_count() for mask in range(8) if all(not(mask>>a&1 and mask>>b&1) for a,b in edges));x,r=solve(3,edges,np.zeros(3),1.)
  assert r['valid_incumbent'] and len(x)==best,(graph,r,best)
 try:solve(2,[(0,1)],np.ones(2),1.)
 except AssertionError:pass
 else:raise AssertionError('conflicting warm start admitted')
 return {'general_three_vertex_graphs':8,'conflicting_warm_mask_rejected':True}

def geometry(H,case):
 theta=H.t0 if case.get('control') else math.pi/4+math.radians(case['phi']);S0,R0=H.start(theta-H.t0);LF,OF,SF,RF,TF=H.fit(theta-H.t0,S0,R0,iters=30);assert math.isfinite(LF)
 step=math.sqrt(2)*math.sin(theta-math.pi/4);halo=8;SF=np.r_[SF[0]-step*np.arange(halo,0,-1),SF,SF[-1]+step*np.arange(1,halo+1)];RF=np.r_[RF[0]+step*np.arange(halo,0,-1),RF,RF[-1]-step*np.arange(1,halo+1)];aa,bb=H.a+2*halo,H.b+2*halo;L=LF+1e-6 if case.get('control') else case['side'];O=OF+(L-LF)/2;u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);half=.5*(abs(u[0])+abs(u[1]));T=np.array([O+(i-(aa-1)/2+SF[k])*u+(k-(bb-1)/2+RF[i])*v for i in range(aa) for k in range(bb)]);T=T[np.all((T>=half-1e-10)&(T<=L-half+1e-10),axis=1)];tilt=np.column_stack((T,np.full(len(T),theta)));U0=H.base+H.e*L;up0=np.column_stack((U0,np.zeros(len(U0))))
 il,ir,matching=independent(adjacency(tilt,up0),len(up0));raw=np.vstack((tilt[il],up0[ir]));labels=np.r_[np.full(len(il),-1),ir];wa=adjacency(raw,raw);best=[]
 # The joint graph can represent conflicts within either family. Repair only the warm start.
 orders=[list(range(len(raw))),list(range(len(il),len(raw)))+list(range(len(il))),sorted(range(len(raw)),key=lambda i:len(wa[i]))]
 for order in orders:
  blocked=set();keep=[]
  for i in order:
   if i in blocked:continue
   keep.append(i);blocked.update(k for k in wa[i] if k!=i)
  if len(keep)>len(best):best=keep
 warmQ=raw[best];kept_up=labels[best];kept_up=kept_up[kept_up>=0];assert mlp.min_gap(warmQ)>-1e-7
 core=tilt[il,:2];near=np.min(np.max(abs(U0[:,None,:]-core[None,:,:]),axis=2),axis=1);frozen=up0[(near>2.1)&np.isin(np.arange(len(up0)),kept_up)]
 m=int(L);slack=L-m;phases=[0.,slack/2,slack];grid=np.array([(i+.5+dx,k+.5+dy) for dx in phases for dy in phases for i in range(m) for k in range(m)]);U=np.unique(np.round(np.vstack((U0,grid)),12),axis=0);Q=np.vstack((tilt,np.column_stack((U,np.zeros(len(U))))))
 if len(frozen):Q=Q[np.array([not x for x in adjacency(Q,frozen)])]
 within=np.full(len(warmQ),True)
 if len(frozen):within=np.min(np.max(abs(warmQ[:,None,:]-frozen[None,:,:]),axis=2),axis=1)>1e-8
 want=warmQ[within];dist=np.max(abs(want[:,None,:]-Q[None,:,:]),axis=2);ids=np.argmin(dist,axis=1);assert np.max(dist[np.arange(len(want)),ids])<1e-8
 warm=np.zeros(len(Q));warm[ids]=1.;edges=[(i,k) for i,a in enumerate(adjacency(Q,Q)) for k in a if k>i]
 assert len(frozen)+int(warm.sum())==len(warmQ)
 return Q,frozen,edges,warm,dict(L=L,reference_side=LF,phi=math.degrees(theta)-45,frozen=len(frozen),variables=len(Q),edges=len(edges),seed_mask_count=len(warmQ),upright_phases=len(phases)**2)

j=json.load(open(sys.argv[1]));D=R/'out/jointphase34'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();control=controls();H=Hole(mlp.load(str(R/(j['pool']+'.csv')),{j['seed_n']})[j['seed_n']]);bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};results=[];found=[]
for ci,case in enumerate(j['cases']):
 Q,F,edges,warm,context=geometry(H,case);ids,receipt=solve(len(Q),edges,warm,case.get('seconds',15));P=np.vstack((F,Q[ids]));N=len(P);gap=float(mlp.min_gap(P));side=float(mlp.side(P));assert gap>-1e-7,(gap,receipt)
 receipt.update(context);receipt.update(n=N,side=side,min_gap=gap,case=case);results.append(receipt);print(json.dumps(receipt),flush=True)
 if case.get('control'):assert receipt['valid_incumbent'] and N>=j['seed_n'],'known held mask did not survive the joint phase model'
 if N<=1000 and side<bars[N]-1e-8:
  tag=j['tag']+'-case'+str(ci)+'-n'+str(N);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/f'{N}.csv'),N,P)
  record=dict(worker='steps',pool=j['pool'],tag=tag,n=N,bar=bars[N],side=side,raw=1,mechanism='joint-physical-phase-MIP34',source={'recipe_text':'own collision-graph integer mask combining nine physical upright grid phases and a calibrated tilted grid; parameters '+json.dumps(receipt,sort_keys=True),'donors':[j['seed_n']]})
  with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  found.append(receipt)
 (D/'result.json').write_text(json.dumps({'controls':control,'seed_n':j['seed_n'],'results':results,'found':found,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
