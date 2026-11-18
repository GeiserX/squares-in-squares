"""Optimize the occupancy mask with parent phases fixed to measured valid values."""
from pathlib import Path
import sys,json,math,time,hashlib
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs,slide_phase33 as phase
from k123_tartan import Hole
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);results=[];best=0;start=time.time()
for k in range(6):
 r=json.load((R/('out/phase33/verify-phase33-scout'+str(k)+'/result.json')).open());theta=r['theta32'];L=r['L'];O=np.array(r['origin32']);S=np.array(r['learned_reference']['S']);Rv=np.array(r['learned_reference']['R']);sites=np.array([(ii,jj) for ii in range(15) for jj in range(15)])
 report,Q=phase.solve(L,sites,theta,O,phase.cluster(S),phase.cluster(Rv),363,15,reference={'S':S,'R':Rv},free_rows32=[],free_columns32=[],max_drop=225)
 z={key:report.get(key) for key in ['status','message','count','side','gap','dual_bound','solve_seconds','variables','tilted_selected']};z['source_index']=k
 if Q is not None:
  assert mlp.min_gap(Q)>-1e-7
  fs.write_rows(str(D/('raw-'+str(k)+'.csv')),len(Q),Q);(D/('raw-'+str(k)+'.json')).write_text(json.dumps(report))
  mask=np.array(report['sites_selected']);mi=mask.min(0);aa,bb=map(int,mask.max(0)-mi+1);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);Oref=O+(mi[0]+(aa-1)/2-7)*u+(mi[1]+(bb-1)/2-7)*v
  HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],mask-mi,theta,Oref,len(Q));SF=np.array(report['S'])[mi[1]:mi[1]+bb];RF=np.array(report['R'])[mi[0]:mi[0]+aa]
  assert np.max(abs(HC.centres(theta,Oref,SF,RF)-Q[:len(mask),:2]))<1e-8,'cropped-mask coordinate control'
  LL,OO,SS,RR,TT=HC.fit(1e-10,SF,RF,iters=30);z['continuous']={'side':LL if math.isfinite(LL) else None,'count':len(Q)}
  if math.isfinite(LL):
   P=HC.layout(TT,OO,SS,RR,LL);gg=float(mlp.min_gap(P));z['continuous']['gap']=gg
   if gg>-1e-7 and mlp.side(P)<mlp.side(Q):Q=P
  fs.write_rows(str(D/('refit-'+str(k)+'.csv')),len(Q),Q)
  if len(Q)>best:
   best=len(Q);fs.write_rows(str(D/'model-output.csv'),len(Q),Q);(D/'best-source.json').write_text(json.dumps({'source_index':k,'report':report,'continuous':z.get('continuous'),'side':float(mlp.side(Q))}))
 results.append(z);(D/'result.json').write_text(json.dumps({'changed':'all225 tilted sites have free occupancy, all parent phases fixed; no joint phase search','best_count':best,'seconds':time.time()-start,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'results':results},indent=2));print(json.dumps(z),flush=True)
