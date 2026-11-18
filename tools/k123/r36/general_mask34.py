"""Make a collision mask around an arbitrary complete packing, without a block reader."""
from pathlib import Path
import sys,json,time,math,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs
ns={};exec(compile((R/'mask_exchange34.py').read_text().rsplit('j=json.load(open(sys.argv[1]))',1)[0],'mask-pure','exec'),ns)
improve=ns['improve'];adjacency=ns['adjacency'];controls=ns['controls']
j=json.load(open(sys.argv[1]));D=R/'out/generalmask34'/j['tag'];D.mkdir(parents=True,exist_ok=True);start=time.time();ctl=controls();P0=mlp.load(str(R/(j['pool']+'.csv')),{j['seed_n']})[j['seed_n']];P0=P0.copy();half=.5*(abs(np.cos(P0[:,2]))+abs(np.sin(P0[:,2])));P0[:,:2]-=np.min(P0[:,:2]-half[:,None],axis=0);source_side=float(mlp.side(P0));L=source_side+1e-6 if j.get('control') else j['side'];assert L>=source_side;P=P0.copy();P[:,:2]*=L/source_side
axis=np.minimum(P[:,2]%(math.pi/2),math.pi/2-P[:,2]%(math.pi/2))<1e-8;up=P[axis];tilt=P[~axis];assert len(tilt)
near=np.min(np.max(abs(up[:,None,:2]-tilt[None,:,:2]),axis=2),axis=1);F=up[near>2.1];parts=[P]
for dtheta in [-.5,0.,.5]:
 for du,dv in [(0.,0.),(-.125,0.),(.125,0.),(0.,-.125),(0.,.125)]:
  T=tilt.copy();theta=tilt[:,2];T[:,0]+=du*np.cos(theta)-dv*np.sin(theta);T[:,1]+=du*np.sin(theta)+dv*np.cos(theta);T[:,2]+=math.radians(dtheta);parts.append(T)
m=int(L);f=L-m;parts.append(np.array([(i+.5+dx,k+.5+dy,0.) for dx in [0.,f/2,f] for dy in [0.,f/2,f] for i in range(m) for k in range(m)]));Q=np.unique(np.round(np.vstack(parts),12),axis=0);h=.5*(abs(np.cos(Q[:,2]))+abs(np.sin(Q[:,2])));Q=Q[np.all((Q[:,:2]>=h[:,None]-1e-10)&(Q[:,:2]<=L-h[:,None]+1e-10),axis=1)]
if len(F):Q=Q[np.array([not x for x in adjacency(Q,F)])]
if len(F):within=np.min(np.max(abs(P[:,None,:]-F[None,:,:]),axis=2),axis=1)>1e-8
else:within=np.ones(len(P),bool)
wanted=P[within];dist=np.max(abs(wanted[:,None,:]-Q[None,:,:]),axis=2);initial=np.argmin(dist,axis=1);assert np.max(dist[np.arange(len(initial)),initial])<1e-8;assert len(set(initial))+len(F)==j['seed_n'];adj=adjacency(Q,Q);budget=max(0,min(j.get('seconds',60),float((R/'search-deadline').read_text())-time.time()-1));best,receipt=improve(adj,initial,budget,j.get('seed',34),j.get('target_n',1001)-len(F));PP=np.vstack((F,Q[best]));N=len(PP);assert mlp.min_gap(PP)>-1e-7;fs.write_rows(str(D/'best.csv'),N,PP)
receipt.update(controls=ctl,source_n=j['seed_n'],source_side=source_side,model_side=L,initial_count=j['seed_n'],n=N,side=float(mlp.side(PP)),min_gap=float(mlp.min_gap(PP)),frozen=len(F),variables=len(Q),tilted_source_cells=len(tilt),seconds=time.time()-start,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),mask_helper_sha256=hashlib.sha256((R/'mask_exchange34.py').read_bytes()).hexdigest())
if j.get('control'):assert N>=j['seed_n'] and abs(receipt['side']-source_side)<2e-6,'complete-source control failed'
variants=[]
for mask in improve.elite:
 if set(mask)==set(initial) or len(set(mask)^set(initial))<4:continue
 variants.append((len(set(mask)^set(initial)),mask))
variants.sort(reverse=True);candidates=[('best',PP)]+[(f'variant{i}',np.vstack((F,Q[x[1]]))) for i,x in enumerate(variants[:2])];notes=[];bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};receipt['raw_crossing']=False
for label,X in candidates:
 NN=len(X);before=float(mlp.side(X));after=before
 if j.get('quench_donors'):
  from midm_scan import to_fq,from_fq,quench
  out=D/label;out.mkdir(exist_ok=True);s,A=to_fq(X);s2,A2=quench(str(Path.home()/'scratch/squares-base/fq'),str(out),s,A,(),timeout=max(1,min(30,float((R/'deadline').read_text())-time.time())))
  if s2 is None:notes.append(dict(label=label,completed=False,before=before));continue
  X=from_fq(A2);after=float(mlp.side(X));assert mlp.min_gap(X)>-1e-7;fs.write_rows(str(D/(label+'-fq.csv')),NN,X)
 notes.append(dict(label=label,before=before,after=after,completed=True,quench_ran=bool(j.get('quench_donors'))))
 if NN<=1000 and after<bars[NN]-1e-8:
  tag=j['tag']+'-'+label+'-n'+str(NN);raw=R/'out/steps'/tag/'raw';raw.mkdir(parents=True,exist_ok=True);fs.write_rows(str(raw/f'{NN}.csv'),NN,X);receipt['raw_crossing']=True
  event={**receipt,'candidate':label,'after_generation_fq':after};record=dict(worker='steps',pool=j['pool'],tag=tag,n=NN,bar=bars[NN],side=after,raw=1,mechanism='complete-layout-mask34',source={'recipe_text':'own collision-mask construction from a complete owned packing, nine upright phases and virtual tilted-cell rotations/translations; integer exchanges '+json.dumps(event,sort_keys=True),'donors':[j['seed_n']]})
  with (R/'out/steps/done.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
receipt['quench_candidates']=notes;(D/'result.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
