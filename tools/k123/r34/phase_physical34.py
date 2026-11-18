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
 seed=H.base+H.e*L;m=int(L);slack=L-m;sets=[seed]
 # Interior offsets and opening seams change the physical upright positions.
 phases=[0.,slack*.25,slack*.5,slack*.75,slack]
 axis=[np.arange(m)+.5+d for d in phases]
 for cut in [m//4,m//2,3*m//4]:
  axis.append(np.arange(m)+.5+np.where(np.arange(m)<cut,0.,slack))
 for ix,X in enumerate(axis):
  for iy,Y in enumerate(axis):
   if ix>=5 and iy>=5 and ix!=iy:continue
   U=np.array([(x,y) for x in X for y in Y]);Q=np.column_stack((U,np.zeros(len(U))));assert mlp.min_gap(Q)>-1e-7;sets.append(U)
 # Shift selected compatible parent squares onto new phases, then fill from that grid.
 for dx,dy in [(slack*.25,0.),(0.,slack*.25),(-slack*.25,0.),(0.,-slack*.25),(slack*.5,slack*.5),(-slack*.5,-slack*.5)]:
  initial=seed+[dx,dy];initial=initial[np.all((initial>=.5-1e-9)&(initial<=L-.5+1e-9),axis=1)]
  candidates=np.array([(x,y) for x in axis[2] for y in axis[2]])
  for reverse in [False,True]:
   U=initial.copy()
   for p in candidates[::-1] if reverse else candidates:
    if len(U) and np.any(np.max(abs(U-p),axis=1)<1-2e-9):continue
    U=np.vstack((U,p))
   assert mlp.min_gap(np.column_stack((U,np.zeros(len(U)))))>-1e-7;sets.append(U)
 return sets
j=json.load(open(sys.argv[1]));D=R/'out/phase34'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();checks=controls();H=Hole(mlp.load(str(R/(j['pool']+'.csv')),{j['seed_n']})[j['seed_n']]);bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};sets_cache={};best=0;tested=0;rows=[];found=[];control_passed=False;halt=False
for ci,case in enumerate(j['cases']):
 casebest=0
 if case.get('control'):case={**case,'phi':math.degrees(H.t0)-45.}
 theta=math.pi/4+math.radians(case['phi']);turn=theta-H.t0;S0,R0=H.start(turn);LF,OF,SF,RF,TF=H.fit(turn,S0,R0,iters=30);assert math.isfinite(LF);step=math.sqrt(2)*math.sin(theta-math.pi/4);halo=8;SF=np.r_[SF[0]-step*np.arange(halo,0,-1),SF,SF[-1]+step*np.arange(1,halo+1)];RF=np.r_[RF[0]+step*np.arange(halo,0,-1),RF,RF[-1]-step*np.arange(1,halo+1)];aa=H.a+2*halo;bb=H.b+2*halo;sites=np.array([(ii,jj) for ii in range(aa) for jj in range(bb)]);L=LF+1e-6 if case.get('control') else case['side'];baseO=OF+np.array([(L-LF)/2,(L-LF)/2]);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);h=.5*(abs(u[0])+abs(u[1]));margin=.5+h
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
   if case.get('control') and count>=j['seed_n']:control_passed=True
   if count>casebest:
    casebest=count
    Q=np.vstack((tilt[left],np.column_stack((U[right],np.zeros(len(right))))));gap=float(mlp.min_gap(Q));assert gap>-1e-7;side=float(mlp.side(Q));best=max(best,count);event={'case':ci,'target_n':case.get('n'),'phi':case['phi'],'offset':[du,dv],'upright_set':ui,'tilt_candidates':len(T),'upright_candidates':len(U),'edges':int(overlap.sum()),'matching':matching,'count':count,'tilted_kept':len(left),'side':side,'gap':gap};rows.append(event);fs.write_rows(str(D/('best-'+str(count)+'.csv')),count,Q);(D/('best-'+str(count)+'.json')).write_text(json.dumps(event));print('BEST',json.dumps(event),flush=True)
    if count<=1000 and side<bars[count]-1e-8:
     tag=j['tag']+'-n'+str(count);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/(str(count)+'.csv')),count,Q);record={'worker':'steps','pool':j['pool'],'tag':tag,'n':count,'bar':bars[count],'side':side,'raw':1,'mechanism':'physical-upright-phase34','source':{'recipe_text':'own exact bipartite maximum independent set using new interior-phase upright lattices, opening seams and shifted parent uprights; model '+json.dumps(event,sort_keys=True),'donors':[j['seed_n']]}}
     with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
     found.append(event);halt=True;break
  if halt:break
 if case.get('control'):assert control_passed,'seed compatible-upright control failed'
 result={'graph_controls':checks,'seed_n':j['seed_n'],'seed_control':control_passed,'last_case':ci,'last_offset':[du,dv],'last_upright_set':ui,'budget_exhausted':time.time()-start>j.get('seconds',45),'tested':tested,'best_count':best,'found':found,'improvements':rows,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(D/'result.json').write_text(json.dumps(result,indent=2))
 if halt:break
assert control_passed
print(json.dumps(result),flush=True)
