"""Search joint masks with mixed tilted angles through valid integer interchanges."""
from pathlib import Path
import sys,json,time,math,random,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
from k123_tartan import Hole
ns={};exec(compile((R/'joint_phase34.py').read_text().rsplit('j=json.load(open(sys.argv[1]))',1)[0],'joint-pure','exec'),ns)
adjacency=ns['adjacency'];geometry=ns['geometry']

def improve(adj,initial,seconds,seed=34,goal=None):
 rng=random.Random(seed);n=len(adj);adj=[set(x)-{i} for i,x in enumerate(adj)];bits=[sum(1<<k for k in a) for a in adj];S=set(initial);assert all(not(adj[v]&S) for v in S),'invalid initial mask';c=[len(a&S) for a in adj];best=set(S);elite=[set(S)];rounds=swaps=0;end=time.time()+seconds
 def alter(remove,add):
  nonlocal swaps
  for v in remove:
   assert v in S;S.remove(v)
   for u in adj[v]:c[u]-=1
  for v in add:
   assert v not in S and c[v]==0,(v,c[v]);S.add(v)
   for u in adj[v]:c[u]+=1
  swaps+=1
 def fill():
  free=[v for v in range(n) if v not in S and c[v]==0];rng.shuffle(free)
  for v in free:
   if c[v]==0:alter([], [v])
 def refine():
  fill();one={};two={}
  for v in range(n):
   if v in S or c[v] not in [1,2]:continue
   hit=tuple(sorted(adj[v]&S))
   (one if len(hit)==1 else two).setdefault(hit,[]).append(v)
  for hit,pool in one.items():
   for ai,a in enumerate(pool):
    for b in pool[ai+1:]:
     if b not in adj[a]:alter(hit,[a,b]);return True
  pairs=list(two);rng.shuffle(pairs)
  for hit in pairs[:2000]:
   pool=two[hit]+one.get((hit[0],),[])+one.get((hit[1],),[])
   if len(pool)<3:continue
   universe=sum(1<<v for v in pool)
   for a in pool:
    choices=universe&~bits[a]&~(1<<a)
    while choices:
     bbit=choices&-choices;b=bbit.bit_length()-1;choices^=bbit;kbits=choices&~bits[b]
     if kbits:
      k=(kbits&-kbits).bit_length()-1;alter(hit,[a,b,k]);return True
    universe&=~(1<<a)
  return False
 while True:
  changed=refine()
  if len(S)>len(best):best=set(S);elite=[set(S)]
  elif len(S)==len(best) and S!=best and len(elite)<32:elite.append(set(S))
  rounds+=1
  if goal is not None and len(best)>=goal:break
  if time.time()>=end:break
  if changed:continue
  if rng.random()<.15:
   S.clear();S.update(rng.choice(elite));c[:]=[len(a&S) for a in adj]
  candidates=[v for v in range(n) if v not in S and 1<=c[v]<=5]
  if not candidates:break
  v=rng.choice(candidates);alter(list(adj[v]&S),[v]);fill()
 assert all(not(adj[v]&best) for v in best)
 improve.elite=[sorted(x) for x in elite]
 return sorted(best),{'rounds':rounds,'interchanges':swaps,'best_count':len(best)}

def controls():
 for graph in range(8):
  pairs=[(0,1),(0,2),(1,2)];edges=[p for i,p in enumerate(pairs) if graph>>i&1];a=[set() for _ in range(3)]
  for u,v in edges:a[u].add(v);a[v].add(u)
  expected=max(mask.bit_count() for mask in range(8) if all(not(mask>>u&1 and mask>>v&1) for u,v in edges));x,r=improve(a,[],0);assert len(x)==expected,(graph,x,expected)
 a=[set(range(2,5)),set(range(2,5)),{0,1},{0,1},{0,1}];x,r=improve(a,[0,1],0);assert len(x)==3,'two-for-three interchange control'
 try:improve([{1},{0}],[0,1],0)
 except AssertionError:pass
 else:raise AssertionError('conflicting initial mask accepted')
 return {'general_graphs':8,'two_for_three_exchange':True,'conflicting_mask_rejected':True}

j=json.load(open(sys.argv[1]));D=R/'out/maskexchange34'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();ctl=controls();H=Hole(mlp.load(str(R/(j['pool']+'.csv')),{j['seed_n']})[j['seed_n']]);case=j['case'];Q,F,edges,warm,context=geometry(H,case);base=Q.copy();basewarm=base[np.flatnonzero(warm>.5)]
for phi in j.get('angles',[-.5,.5]):
 other={**case,'control':False,'phi':phi,'side':context['L']};V,VF,ve,vw,vc=geometry(H,other);Q=np.vstack((Q,V))
Q=np.unique(np.round(Q,12),axis=0)
if len(F):Q=Q[np.array([not x for x in adjacency(Q,F)])]
dist=np.max(abs(basewarm[:,None,:]-Q[None,:,:]),axis=2);ids=np.argmin(dist,axis=1);assert np.max(dist[np.arange(len(basewarm)),ids])<1e-8
adj=adjacency(Q,Q);initial=sorted(set(ids));assert len(initial)+len(F)==context['seed_mask_count'];P0=np.vstack((F,Q[initial]));assert mlp.min_gap(P0)>-1e-7
budget=max(0,min(j.get('seconds',45),float((R/'search-deadline').read_text())-time.time()-1));best,receipt=improve(adj,initial,budget,j.get('seed',34),j.get('target_n',1001)-len(F));P=np.vstack((F,Q[best]));N=len(P);gap=float(mlp.min_gap(P));side=float(mlp.side(P));assert gap>-1e-7;fs.write_rows(str(D/'best.csv'),N,P)
receipt.update(controls=ctl,seed_n=j['seed_n'],source_mask=context['seed_mask_count'],initial_count=len(initial)+len(F),n=N,side=side,min_gap=gap,variables=len(Q),frozen=len(F),angles=j.get('angles',[-.5,.5]),seconds=time.time()-start,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
if case.get('control'):assert N>=j['seed_n'],'mixed-angle held mask control failed'
bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};receipt['raw_crossing']=False
variants=[]
for mask in improve.elite:
 if set(mask)==set(initial) or len(set(mask)^set(initial))<4:continue
 QQ=np.vstack((F,Q[mask]));mixed=len(np.unique(np.round(QQ[abs(QQ[:,2])>1e-6,2],6)));variants.append((mixed,len(set(mask)^set(initial)),mask))
variants.sort(key=lambda z:(-z[0],-z[1]));candidates=[('best',P)]+[(f'variant{i}',np.vstack((F,Q[x[2]]))) for i,x in enumerate(variants[:2])];receipt['changed_mask_candidates']=len(variants);quench_notes=[]
for label,PP in candidates:
 NN=len(PP);before=float(mlp.side(PP));after=before
 if j.get('quench_donors'):
  from midm_scan import to_fq,from_fq,quench
  qdir=D/label;qdir.mkdir(exist_ok=True);ss,XX=to_fq(PP);s2,X2=quench(str(Path.home()/'scratch/squares-base/fq'),str(qdir),ss,XX,(),timeout=max(1,min(30,float((R/'deadline').read_text())-time.time())))
  if s2 is None:
   quench_notes.append(dict(label=label,completed=False,before=before));continue
  PP=from_fq(X2);after=float(mlp.side(PP));assert mlp.min_gap(PP)>-1e-7
  fs.write_rows(str(D/(label+'-fq.csv')),NN,PP)
 quench_notes.append(dict(label=label,completed=True,before=before,after=after))
 if NN<=1000 and after<bars[NN]-1e-8:
  tag=j['tag']+'-'+label+'-n'+str(NN);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/f'{NN}.csv'),NN,PP);receipt['raw_crossing']=True
  event={**receipt,'candidate':label,'after_generation_quench':after};record=dict(worker='steps',pool=j['pool'],tag=tag,n=NN,bar=bars[NN],side=after,raw=1,mechanism='mixed-angle-mask-exchange34',source={'recipe_text':'own independent mask across mixed calibrated tilted grids and nine physical upright phases; integer exchanges '+json.dumps(event,sort_keys=True),'donors':[j['seed_n']]})
  with (R/'out/steps/done.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
receipt['quench_candidates']=quench_notes;receipt['joint_geometry_sha256']=hashlib.sha256((R/'joint_phase34.py').read_bytes()).hexdigest();(D/'result.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
