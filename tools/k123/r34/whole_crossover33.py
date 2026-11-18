"""Construct spatial crossovers of complete licensed layouts using exact bipartite matching."""
from pathlib import Path
from collections import deque
import sys,json,time,math,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
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


def norm(P):
 P=P.copy();h=.5*(abs(np.cos(P[:,2]))+abs(np.sin(P[:,2])));P[:,:2]-=np.min(P[:,:2]-h[:,None],axis=0);span=np.max(P[:,:2]+h[:,None],axis=0);return P,span

def adjacency(A,B):
 d=B[None,:,:2]-A[:,None,:2];ca=np.cos(A[:,2])[:,None];sa=np.sin(A[:,2])[:,None];cb=np.cos(B[:,2])[None,:];sb=np.sin(B[:,2])[None,:];H=.5+.5*(abs(ca*cb+sa*sb)+abs(ca*sb-sa*cb));dx=d[:,:,0];dy=d[:,:,1];ov=(abs(dx*ca+dy*sa)<H-2e-9)&(abs(-dx*sa+dy*ca)<H-2e-9)&(abs(dx*cb+dy*sb)<H-2e-9)&(abs(-dx*sb+dy*cb)<H-2e-9)
 return [np.flatnonzero(x).tolist() for x in ov]

j=json.load(open(sys.argv[1]));D=R/'out/crossover33'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();end=min(start+j.get('seconds',45),float((R/'search-deadline').read_text())-1);tests=controls();bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};count=0;found=[];summaries=[];halt=False
for case in j['cases']:
 n=case['n'];pool=case['pool'];L=case['L'];A,span=norm(mlp.load(str(R/(pool+'.csv')),{n})[n]);source_side=float(mlp.side(A))
 if source_side>L:continue
 assert mlp.min_gap(A)>-1e-7;left,right,match=independent(adjacency(A,A),n);assert len(left)+len(right)==n,'whole-layout identity control';best=n;cfg=0
 for reflected in [False,True]:
  for turn in range(4):
   B=A.copy()
   if reflected:B[:,0]=source_side-B[:,0];B[:,2]*=-1
   for _ in range(turn):B=np.column_stack((source_side-B[:,1],B[:,0],B[:,2]+math.pi/2))
   B,bspan=norm(B);assert mlp.min_gap(B)>-1e-7
   am=np.maximum(0.,L-span);bm=np.maximum(0.,L-bspan)
   for ax in sorted(set([0.,float(am[0])])):
    for ay in sorted(set([0.,float(am[1])])):
     AA=A.copy();AA[:,:2]+=np.array([ax,ay])
     for bx in sorted(set([0.,float(bm[0]/2),float(bm[0])])):
      for by in sorted(set([0.,float(bm[1]/2),float(bm[1])])):
       if time.time()>=end:halt=True;break
       BB=B.copy();BB[:,:2]+=np.array([bx,by]);adj=adjacency(AA,BB);il,ir,matching=independent(adj,n);N=len(il)+len(ir);count+=1;cfg+=1
       if N>best:
        Q=np.vstack((AA[il],BB[ir]));gap=float(mlp.min_gap(Q));assert gap>-1e-7;side=float(mlp.side(Q));best=N;event={'source_n':n,'pool':pool,'n':N,'side':side,'gap':gap,'reflection':reflected,'quarter_turns':turn,'A_shift':[ax,ay],'B_shift':[bx,by],'matching':matching};fs.write_rows(str(D/('best-'+str(n)+'-'+str(N)+'.csv')),N,Q);print(json.dumps(event),flush=True)
        if N<=1000 and side<bars[N]-1e-8:
         tag=j['tag']+'-n'+str(N);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/(str(N)+'.csv')),N,Q);record={'worker':'steps','pool':pool,'tag':tag,'n':N,'bar':bars[N],'side':side,'raw':1,'mechanism':'whole-layout-crossover33','source':{'recipe_text':'own maximum-independent-set spatial crossover of one complete certified packing and its D4 image; parameters '+json.dumps(event,sort_keys=True),'donors':[n]}}
         with (R/'out/steps/done.jsonl').open('a') as h:h.write(json.dumps(record)+'\n')
         found.append(event);halt=True;break
      if halt:break
     if halt:break
    if halt:break
   if halt:break
  if halt:break
 summaries.append({'source_n':n,'pool':pool,'identity_control':True,'configurations':cfg,'best_count':best});result={'small_graph_controls':tests,'configurations':count,'found':found,'sources':summaries,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()};(D/'result.json').write_text(json.dumps(result,indent=2))
 if halt:break
print(json.dumps(result),flush=True)
