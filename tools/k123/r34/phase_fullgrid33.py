"""Extend the fixed-phase occupancy search to tilted sites outside the old square window."""
from pathlib import Path
import sys,json,math,hashlib,time
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import methods_lp as mlp,family_step as fs,slide_phase33 as phase
from k123_tartan import Hole
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);P0=mlp.load(str(R/'phaselattice33.csv'),{368})[368];H=Hole(P0);results=[];start=time.time()
for idx,case in enumerate(j['cases']):
 target=case['n'];theta=math.pi/4+math.radians(case['phi']);turn=theta-H.t0;S0,R0=H.start(turn);LF,OF,SF,RF,TF=H.fit(turn,S0,R0,iters=30)
 assert math.isfinite(LF),'held368 phase fit failed';QF=H.layout(TF,OF,SF,RF,LF);assert mlp.min_gap(QF)>-1e-7
 step=math.sqrt(2)*math.sin(abs(theta-math.pi/4));halo=int(j.get('halo',8));SF=np.r_[SF[0]-step*np.arange(halo,0,-1),SF,SF[-1]+step*np.arange(1,halo+1)];RF=np.r_[RF[0]+step*np.arange(halo,0,-1),RF,RF[-1]-step*np.arange(1,halo+1)];aa=H.a+2*halo;bb=H.b+2*halo;sites=np.array([(ii,jj) for ii in range(aa) for jj in range(bb)]);L=LF+1e-6 if case.get('control') else case['side'];O=OF+np.array([(L-LF)/2,(L-LF)/2])
 report,Q=phase.solve(L,sites,theta,O,phase.cluster(SF),phase.cluster(RF),target,15,reference={'S':SF,'R':RF},free_rows32=[],free_columns32=[],max_drop=len(sites))
 z={k:report.get(k) for k in ['status','count','side','gap','dual_bound','solve_seconds','variables','tilted_selected']};z.update(index=idx,phi=case['phi'],target_n=target,reference_side=LF,target_side=L,candidate_sites=len(sites))
 u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);hh=.5*(abs(u[0])+abs(u[1]));centres=np.array([O+(ii-(aa-1)/2+SF[jj])*u+(jj-(bb-1)/2+RF[ii])*v for ii,jj in sites]);z['wall_valid_sites']=int(np.all((centres>=hh-1e-9)&(centres<=L-hh+1e-9),axis=1).sum())
 if Q is not None:
  assert mlp.min_gap(Q)>-1e-7;fs.write_rows(str(D/('raw-'+str(idx)+'.csv')),len(Q),Q);(D/('raw-'+str(idx)+'.json')).write_text(json.dumps(report))
  mask=np.array(report['sites_selected']);mi=mask.min(0);ka,kb=map(int,mask.max(0)-mi+1);u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);Oref=O+(mi[0]+(ka-1)/2-(aa-1)/2)*u+(mi[1]+(kb-1)/2-(bb-1)/2)*v
  HC=Hole.parts(L,Q[np.abs(Q[:,2])<1e-10,:2],mask-mi,theta,Oref,len(Q));SS=np.array(report['S'])[mi[1]:mi[1]+kb];RR=np.array(report['R'])[mi[0]:mi[0]+ka];assert np.max(abs(HC.centres(theta,Oref,SS,RR)-Q[:len(mask),:2]))<1e-8
  LC,OC,SC,RC,TC=HC.fit(1e-10,SS,RR,iters=30);z['continuous_side']=LC if math.isfinite(LC) else None
  if math.isfinite(LC):
   QC=HC.layout(TC,OC,SC,RC,LC);gc=float(mlp.min_gap(QC));z['continuous_gap']=gc
   if gc>-1e-7 and mlp.side(QC)<mlp.side(Q):Q=QC
  fs.write_rows(str(D/('refit-'+str(idx)+'.csv')),len(Q),Q)
 if case.get('control'):assert Q is not None and len(Q)>=368,'held368 mask control failed'
 results.append(z);(D/'result.json').write_text(json.dumps({'source':'owned held368','source_pool_sha256':hashlib.sha256((R/'phaselattice33.csv').read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'seconds':time.time()-start,'results':results},indent=2));print(json.dumps(z),flush=True)
