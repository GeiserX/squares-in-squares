"""Optimize constructive masks by exact matching after fixing a compatible upright candidate set."""
from pathlib import Path
from collections import deque
import os,sys,json,math,time,hashlib,itertools
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
from k123_tartan import Hole

def independent(adj,nv):
 nu=len(adj);pu=[-1]*nu;pv=[-1]*nv
 while True:
  dist=[0 if v<0 else -1 for v in pu];q=deque(u for u in range(nu) if pu[u]<0);found=False
  while q:
   u=q.popleft()
   for v in adj[u]:
    w=pv[v]
    if w<0:found=True
    elif dist[w]<0:dist[w]=dist[u]+1;q.append(w)
  if not found:break
  def dfs(u):
   for v in adj[u]:
    w=pv[v]
    if w<0 or dist[w]==dist[u]+1 and dfs(w):pu[u]=v;pv[v]=u;return True
   dist[u]=-1;return False
  if not any([dfs(u) for u in range(nu) if pu[u]<0]):break
 zl={u for u in range(nu) if pu[u]<0};zr=set();q=deque(zl)
 while q:
  u=q.popleft()
  for v in adj[u]:
   if pu[u]==v or v in zr:continue
   zr.add(v);w=pv[v]
   if w>=0 and w not in zl:zl.add(w);q.append(w)
 left=sorted(zl);right=[v for v in range(nv) if v not in zr];match=sum(v>=0 for v in pu)
 assert len(left)+len(right)==nu+nv-match
 assert all(u not in zl or v in zr for u,edges in enumerate(adj) for v in edges)
 return left,right,match

def controls():
 for g in range(512):
  adj=[[v for v in range(3) if g>>(3*u+v)&1] for u in range(3)];a,b,m=independent(adj,3);best=max(mask.bit_count() for mask in range(64) if all(not(mask>>u&1 and mask>>(3+v)&1) for u,edges in enumerate(adj) for v in edges));assert len(a)+len(b)==best
 return 512

def upright_sets(H,L):
 seed=H.base+H.e*L;m=int(L);allup=np.unique(np.round(np.array([(i+.5 if ax==0 else L-i-.5,k+.5 if ay==0 else L-k-.5) for ax in [0,1] for ay in [0,1] for i in range(m) for k in range(m)]),12),axis=0);sets=[];seen=set()
 seeds=[seed,np.empty((0,2))]+[seed[np.random.default_rng(k).random(len(seed))<.5] for k in range(4)]+[seed[seed[:,0]<L/2],seed[seed[:,0]>=L/2]]
 for initial in seeds:
  for swap in [False,True]:
   for sx in [-1,1]:
    for sy in [-1,1]:
     chosen=initial.copy();xx=allup[:,1] if swap else allup[:,0];yy=allup[:,0] if swap else allup[:,1]
     for p in allup[np.lexsort((sy*yy,sx*xx))]:
      if len(chosen) and np.any(np.max(abs(chosen-p),axis=1)<1-2e-9):continue
      chosen=np.vstack((chosen,p))
     key=tuple(map(tuple,np.round(chosen[np.lexsort((chosen[:,1],chosen[:,0]))],9)))
     if key in seen:continue
     seen.add(key);Q=np.column_stack((chosen,np.zeros(len(chosen))));assert mlp.min_gap(Q)>-1e-7;sets.append(chosen)
 return sets
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);start=time.time();checks=controls();H=Hole(mlp.load(str(R/'phaselattice33.csv'),{368})[368]);bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};sets_cache={};best=0;tested=0;rows=[];found=[];control_passed=False;halt=False
for ci,case in enumerate(j['cases']):
 casebest=0;theta=math.pi/4+math.radians(case['phi']);turn=theta-H.t0;S0,R0=H.start(turn);LF,OF,SF,RF,TF=H.fit(turn,S0,R0,iters=30);assert math.isfinite(LF);step=math.sqrt(2)*math.sin(theta-math.pi/4);halo=8;SF=np.r_[SF[0]-step*np.arange(halo,0,-1),SF,SF[-1]+step*np.arange(1,halo+1)];RF=np.r_[RF[0]+step*np.arange(halo,0,-1),RF,RF[-1]-step*np.arange(1,halo+1)];aa=H.a+2*halo;bb=H.b+2*halo;sites=np.array([(ii,jj) for ii in range(aa) for jj in range(bb)]);L=LF+1e-6 if case.get('control') else case['side'];baseO=OF+np.array([(L-LF)/2,(L-LF)/2]);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);h=.5*(abs(u[0])+abs(u[1]));margin=.5+h
 if L not in sets_cache:sets_cache[L]=upright_sets(H,L)
 offsets=[(0.,0.)] if case.get('control') else [(0.,0.)]+[(a,b) for a in [-.5,-.25,0.,.25,.5] for b in [-.5,-.25,0.,.25,.5] if (a,b)!=(0.,0.)]
 for du,dv in offsets:
  if time.time()-start>j.get('seconds',45):halt=True;break
  O=baseO+du*u+dv*v;centres=np.array([O+(ii-(aa-1)/2+SF[jj])*u+(jj-(bb-1)/2+RF[ii])*v for ii,jj in sites]);T=centres[np.all((centres>=h-1e-9)&(centres<=L-h+1e-9),axis=1)];tilt=np.column_stack((T,np.full(len(T),theta)));
  if mlp.min_gap(tilt)<-1e-7:
   assert not case.get('control'),'invalid control tilted grid'
   continue
  for ui,U in enumerate(sets_cache[L]):
   ds=U[None,:,:]-T[:,None,:];overlap=(abs(ds[:,:,0])<margin-2e-9)&(abs(ds[:,:,1])<margin-2e-9)&(abs(ds@u)<margin-2e-9)&(abs(ds@v)<margin-2e-9);adj=[np.flatnonzero(a).tolist() for a in overlap];left,right,matching=independent(adj,len(U));count=len(left)+len(right);tested+=1
   if case.get('control') and count>=368:control_passed=True
   if count>casebest:
    casebest=count
    Q=np.vstack((tilt[left],np.column_stack((U[right],np.zeros(len(right))))));gap=float(mlp.min_gap(Q));assert gap>-1e-7;side=float(mlp.side(Q));best=max(best,count);event={'case':ci,'target_n':case.get('n'),'phi':case['phi'],'offset':[du,dv],'upright_set':ui,'tilt_candidates':len(T),'upright_candidates':len(U),'edges':int(overlap.sum()),'matching':matching,'count':count,'tilted_kept':len(left),'side':side,'gap':gap};rows.append(event);fs.write_rows(str(D/('best-'+str(count)+'.csv')),count,Q);(D/('best-'+str(count)+'.json')).write_text(json.dumps(event));print('BEST',json.dumps(event),flush=True)
    if count<=1000 and side<bars[count]-1e-8:
     tag=j['tag']+'-n'+str(count);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/(str(count)+'.csv')),count,Q);record={'worker':'steps','pool':'phaselattice33','tag':tag,'n':count,'bar':bars[count],'side':side,'raw':1,'mechanism':'bipartite-upright-diversity33','source':{'recipe_text':'own exact bipartite maximum independent set on a fixed calibrated sliding tilted lattice and a mutually compatible upright completion; model '+json.dumps(event,sort_keys=True),'donors':[368]}}
     with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
     found.append(event);halt=True;break
  if halt:break
 if case.get('control'):assert control_passed,'held368 compatible-upright control failed'
 result={'graph_controls':checks,'held368_control':control_passed,'tested':tested,'best_count':best,'found':found,'improvements':rows,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(D/'result.json').write_text(json.dumps(result,indent=2))
 if halt:break
assert control_passed
print(json.dumps(result),flush=True)
