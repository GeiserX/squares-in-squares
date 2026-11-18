"""Cross distinct complete layouts by exact bipartite matching of their collision graph."""
from pathlib import Path
from collections import deque
import sys,json,time,math,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
# Import only the pure matching and geometry definitions from the previous controlled implementation.
namespace={};src=(R/'whole_crossover33.py').read_text();exec(compile(src.split('j=json.load(open(sys.argv[1]))')[0],str(R/'whole_crossover33.py'),'exec'),namespace)
independent=namespace['independent'];controls=namespace['controls'];norm=namespace['norm'];adjacency=namespace['adjacency']
j=json.load(open(sys.argv[1]));D=R/'out/crossover34'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();end=min(start+j.get('seconds',90),float((R/'search-deadline').read_text())-1);graph=controls();bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};pool=j['pool'];P=mlp.load(str(R/(pool+'.csv')));results=[];count=0;found=[]
# Identity must reproduce its count before any distinct-parent crossover runs.
nc=j['cases'][0]['a'];C,span=norm(P[nc]);il,ir,m=independent(adjacency(C,C),len(C));assert len(il)+len(ir)==nc
for case in j['cases']:
 na,nb=case['a'],case['b'];L=case['L'];A,sa=norm(P[na]);B0,sb0=norm(P[nb]);aside=float(mlp.side(A));bside=float(mlp.side(B0));best=max(na,nb);configs=0
 if max(aside,bside)>L+1e-8:continue
 assert mlp.min_gap(A)>-1e-7 and mlp.min_gap(B0)>-1e-7
 for reflected in [False,True]:
  for turn in range(4):
   B=B0.copy()
   if reflected:B[:,0]=bside-B[:,0];B[:,2]*=-1
   for _ in range(turn):B=np.column_stack((bside-B[:,1],B[:,0],B[:,2]+math.pi/2))
   B,sb=norm(B);am=np.maximum(0.,L-sa);bm=np.maximum(0.,L-sb)
   for ax,ay,bx,by in [(0.,0.,x,y) for x in sorted(set([0.,float(bm[0]/2),float(bm[0])])) for y in sorted(set([0.,float(bm[1]/2),float(bm[1])]))]+[(float(am[0]),float(am[1]),x,y) for x in [0.,float(bm[0])] for y in [0.,float(bm[1])]]:
    if time.time()>=end:break
    AA=A.copy();AA[:,:2]+=[ax,ay];BB=B.copy();BB[:,:2]+=[bx,by];il,ir,matching=independent(adjacency(AA,BB),len(BB));N=len(il)+len(ir);configs+=1;count+=1
    if N>best:
     Q=np.vstack((AA[il],BB[ir]));gap=float(mlp.min_gap(Q));assert gap>-1e-7;side=float(mlp.side(Q));best=N;event=dict(a=na,b=nb,L=L,n=N,side=side,gap=gap,reflection=reflected,turn=turn,shifts=[ax,ay,bx,by],matching=matching)
     fs.write_rows(str(D/f'best-{na}-{nb}-{N}.csv'),N,Q);print(json.dumps(event),flush=True)
     if N<=1000 and side<bars[N]-1e-8:
      tag=j['tag']+'-'+str(na)+'-'+str(nb)+'-n'+str(N);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/f'{N}.csv'),N,Q)
      record=dict(worker='steps',pool=pool,tag=tag,n=N,bar=bars[N],side=side,raw=1,mechanism='distinct-layout-crossover34',source={'recipe_text':'own exact maximum-independent-set spatial crossover of two different complete held or source-cleared layouts; model '+json.dumps(event,sort_keys=True),'donors':[na,nb]})
      with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
      found.append(event)
   if time.time()>=end:break
  if time.time()>=end:break
 results.append(dict(a=na,b=nb,configurations=configs,best_count=best))
 result=dict(graph_controls=graph,identity_control_n=nc,identity_control=True,configurations=count,pairs=results,found=found,seconds=time.time()-start,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());(D/'result.json').write_text(json.dumps(result,indent=2))
 if time.time()>=end:break
print(json.dumps(result),flush=True)
