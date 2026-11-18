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
  mask=np.array(report['sites_selected']);HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],mask,theta,O,len(Q));LL,OO,SS,RR,TT=HC.fit(1e-10,np.array(report['S']),np.array(report['R']),iters=30);P=HC.layout(TT,OO,SS,RR,LL);gg=float(mlp.min_gap(P));z['continuous']={'side':LL,'gap':gg,'count':len(P)}
  if math.isfinite(LL) and gg>-1e-7 and mlp.side(P)<mlp.side(Q):Q=P
  if len(Q)>best:
   best=len(Q);fs.write_rows(str(D/'model-output.csv'),len(Q),Q);(D/'best-source.json').write_text(json.dumps({'source_index':k,'report':report,'continuous':z.get('continuous'),'side':float(mlp.side(Q))}))
 results.append(z);(D/'result.json').write_text(json.dumps({'changed':'all225 tilted sites have free occupancy, all parent phases fixed; no joint phase search','best_count':best,'seconds':time.time()-start,'results':results},indent=2));print(json.dumps(z),flush=True)
