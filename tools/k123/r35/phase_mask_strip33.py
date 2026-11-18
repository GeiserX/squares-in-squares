"""Probe flexible occupancy masks with a small boundary phase neighborhood."""
from pathlib import Path
import sys,json,math,time,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs,slide_phase33 as phase
from k123_tartan import Hole
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);results=[];best=0;start=time.time()
for case_index,case in enumerate(j['cases']):
 k=case['source_index'];target=int(case['n']);ck=str(case_index)+'-'+str(k)+'-'+str(target)
 r=json.load((R/('out/phase33/verify-phase33-scout'+str(k)+'/result.json')).open());theta=r['theta32'];L=case['side'];O=np.array(r['origin32'])+np.array([(L-r['L'])/2,(L-r['L'])/2]);S=np.array(r['learned_reference']['S']);Rv=np.array(r['learned_reference']['R']);sites=np.array([(ii,jj) for ii in range(15) for jj in range(15)])
 step=math.sqrt(2)*math.sin(abs(theta-math.pi/4));SL=phase.cluster(np.concatenate([S+d*step/3 for d in [-1,0,1]]));RL=phase.cluster(np.concatenate([Rv+d*step/3 for d in [-1,0,1]]))
 report,Q=phase.solve(L,sites,theta,O,SL,RL,target,30,reference={'S':S,'R':Rv},local_choices=3,free_rows32=[0,1,13,14],free_columns32=[0,1,13,14],max_drop=225)
 z={key:report.get(key) for key in ['status','message','count','side','gap','dual_bound','solve_seconds','variables','tilted_selected']};z['source_index']=k;z['target_n']=target;z['target_side']=L
 if Q is not None:
  assert mlp.min_gap(Q)>-1e-7
  fs.write_rows(str(D/('raw-'+ck+'.csv')),len(Q),Q);(D/('raw-'+ck+'.json')).write_text(json.dumps(report))
  mask=np.array(report['sites_selected']);mi=mask.min(0);aa,bb=map(int,mask.max(0)-mi+1);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);Oref=O+(mi[0]+(aa-1)/2-7)*u+(mi[1]+(bb-1)/2-7)*v
  HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],mask-mi,theta,Oref,len(Q));SF=np.array(report['S'])[mi[1]:mi[1]+bb];RF=np.array(report['R'])[mi[0]:mi[0]+aa]
  assert np.max(abs(HC.centres(theta,Oref,SF,RF)-Q[:len(mask),:2]))<1e-8,'cropped-mask coordinate control'
  LL,OO,SS,RR,TT=HC.fit(1e-10,SF,RF,iters=30);z['continuous']={'side':LL if math.isfinite(LL) else None,'count':len(Q)}
  if math.isfinite(LL):
   P=HC.layout(TT,OO,SS,RR,LL);gg=float(mlp.min_gap(P));z['continuous']['gap']=gg
   if gg>-1e-7 and mlp.side(P)<mlp.side(Q):Q=P
  fs.write_rows(str(D/('refit-'+ck+'.csv')),len(Q),Q)
  if len(Q)>best:
   best=len(Q);fs.write_rows(str(D/'model-output.csv'),len(Q),Q);(D/'best-source.json').write_text(json.dumps({'source_index':k,'report':report,'continuous':z.get('continuous'),'side':float(mlp.side(Q))}))
 results.append(z);
 if case.get('control'):assert Q is not None and len(Q)>=target,'flexible-mask positive control failed'
 (D/'result.json').write_text(json.dumps({'changed':'all225 tilted sites have free occupancy; only four boundary rows and columns have three nearby phase choices','best_count':best,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results},indent=2));print(json.dumps(z),flush=True)
