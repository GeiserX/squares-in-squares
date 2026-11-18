"""Repair fresh rectangle interfaces with fixed-angle local mixed-integer models."""
from pathlib import Path
import hashlib
import json
import math
import os
import pickle
import signal
import sys
import time
import warnings
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.optimize import Bounds,LinearConstraint,milp
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
import forensics_compose as fc
import forensics_slide34 as slide
import forensics_drop33 as collision


def repair(q,labels,side,joint,radius,trust,seconds,branch_radius=0.):
    started=time.time();n=len(q)
    mobile=set(np.flatnonzero(np.linalg.norm(q[:,:2]-joint,axis=1)<=radius).tolist())
    edges=collision.collisions(q)
    mobile.update(map(int,edges.ravel()))
    selected=sorted(mobile);position={i:j for j,i in enumerate(selected)};nv=2*len(selected)
    half=.5*(np.abs(np.cos(q[:,2]))+np.abs(np.sin(q[:,2])))
    lower=[];upper=[]
    for i in selected:
        for d in range(2):lower.append(max(half[i],q[i,d]-trust));upper.append(min(side-half[i],q[i,d]+trust))
    if any(a>b for a,b in zip(lower,upper)):return None,dict(reason='empty trust box',seconds=time.time()-started)
    integrality=[0]*nv;ri=[];ci=[];values=[];lbs=[];ubs=[];binary=0;cross_pairs=0;internal_pairs=0
    def linear(i,j,axis):
        coefficients={};constant=0.
        for k,sign in [(j,1.),(i,-1.)]:
            if k in position:
                for d in range(2):coefficients[2*position[k]+d]=sign*axis[d]
            else:constant+=sign*float(axis@q[k,:2])
        lo=constant+sum(v*(lower[k] if v>=0 else upper[k]) for k,v in coefficients.items())
        hi=constant+sum(v*(upper[k] if v>=0 else lower[k]) for k,v in coefficients.items())
        return coefficients,constant,lo,hi
    def row(coefficients,lo,hi=np.inf):
        index=len(lbs);lbs.append(lo);ubs.append(hi)
        for k,v in coefficients.items():ri.append(index);ci.append(k);values.append(v)
    pairs=sorted(cKDTree(q[:,:2]).query_pairs(math.sqrt(2)*(1+2*trust)+1e-7))
    for i,j in pairs:
        if i not in mobile and j not in mobile:continue
        ua=np.array([math.cos(q[i,2]),math.sin(q[i,2])]);va=np.array([-ua[1],ua[0]])
        ub=np.array([math.cos(q[j,2]),math.sin(q[j,2])]);vb=np.array([-ub[1],ub[0]])
        choices=[];seen=set()
        for axis in [ua,va,ub,vb]:
            need=.5*sum(abs(float(axis@v)) for v in [ua,va,ub,vb])
            for sign in [1.,-1.]:
                direction=sign*axis;key=tuple(np.round(direction,12))
                if key in seen:continue
                seen.add(key);coefficients,constant,lo,hi=linear(i,j,direction)
                choices.append((float(direction@(q[j,:2]-q[i,:2]))-need,coefficients,constant,lo,hi,need))
        if any(v[3]>=v[5] for v in choices):continue
        cross=(labels[i] in (0,1) and labels[j] in (0,1) and labels[i]!=labels[j])
        internal=(branch_radius>0 and i in mobile and j in mobile and np.linalg.norm(q[i,:2]-joint)<=branch_radius and np.linalg.norm(q[j,:2]-joint)<=branch_radius and max(v[0] for v in choices)<.25)
        if not (cross or internal):
            best=max(choices,key=lambda v:v[0])
            if best[4]<best[5]-1e-9:return None,dict(reason='fixed contact branch blocked',seconds=time.time()-started,mobile=len(selected))
            row(best[1],best[5]-best[2]);continue
        possible=[v for v in choices if v[4]>=v[5]-1e-9]
        if not possible:return None,dict(reason='cross pair cannot separate inside trust box',seconds=time.time()-started,mobile=len(selected))
        switches=[]
        if cross:cross_pairs+=1
        else:internal_pairs+=1
        for gap,coefficients,constant,lo,hi,need in possible:
            z=len(lower);lower.append(0.);upper.append(1.);integrality.append(1);switches.append(z);binary+=1
            big=max(0.,need-lo)+1e-9;coefficients=dict(coefficients);coefficients[z]=-big
            row(coefficients,need-big-constant)
        row({z:1. for z in switches},1.,1.)
    matrix=coo_matrix((values,(ri,ci)),shape=(len(lbs),len(lower))).tocsc()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',message='Unrecognized options detected.*threads.*')
        result=milp(np.zeros(len(lower)),integrality=np.array(integrality),bounds=Bounds(lower,upper),constraints=LinearConstraint(matrix,lbs,ubs),options={'time_limit':seconds,'mip_rel_gap':0.,'presolve':True,'threads':1})
    record=dict(status=int(result.status),message=str(result.message),seconds=time.time()-started,mobile=len(selected),binaries=binary,cross_pairs=cross_pairs,internal_disjunctions=internal_pairs,branch_radius=branch_radius,constraints=len(lbs),nodes=getattr(result,'mip_node_count',None))
    if result.x is None:return None,record
    out=q.copy();out[selected,:2]=result.x[:nv].reshape(-1,2);bounds=fc.corners(out);overlap=fc.worst_overlap(out)
    record.update(overlap=float(overlap),side=float(fc.frame(out)[0]))
    if bounds.min()<-1e-7 or bounds.max()>side+1e-7 or overlap<-1e-7:
        record['rejected_numerical_incumbent']=True;return None,record
    return out,record


def control():
    import scipy
    assert scipy.__version__=='1.18.1',scipy.__version__
    q=np.array([[.5,.5,0.],[1.5,.5,0.],[.5,1.5,0.],[1.25,1.25,0.]])
    labels=np.array([0,0,1,1]);assert fc.worst_overlap(q)<-.2
    out,record=repair(q,labels,2.05,np.array([1.,1.]),10.,.4,3.)
    assert out is not None and fc.worst_overlap(out)>-1e-7,record
    expanded,rec=repair(q,labels,2.05,np.array([1.,1.]),10.,.4,3.,branch_radius=2.5)
    assert expanded is not None and fc.worst_overlap(expanded)>-1e-7,rec
    blocked,rec=repair(q,labels,2.05,np.array([1.,1.]),10.,.05,3.,branch_radius=2.5);assert blocked is None,rec
    blocked,rec=repair(q,labels,1.99,np.array([1.,1.]),10.,.4,3.);assert blocked is None,rec
    print('CONTROL fixed-angle four-square core repaired; insufficient trust and undersized board refused; scipy1.18.1 HiGHS threads1',flush=True)


def run(jobfile):
    job=json.loads(Path(jobfile).read_text());root=Path(job['root']);signal.setitimer(signal.ITIMER_REAL,max(.1,job['deadline']-time.time()));(root/'scanner.pid').write_text(str(os.getpid()))
    cache=pickle.load(Path(job['cache']).open('rb'));out=Path(job['out']);out.mkdir(parents=True,exist_ok=True);cases=[];exports=[];started=time.time()
    for item in job['cases']:
        remaining=job['deadline']-time.time()
        if remaining<3:break
        n=item['n'];m=math.isqrt(n);side=item['side'];f=side-m;wa,ha,ea=item['w'],item['h'],item['e'];wb,hb,eb=m-wa,m-ha,n-m*m-ea
        ka,a=slide.part(cache,item['ga'],wa,ha,ea,item['fa']);kb,b=slide.part(cache,item['gb'],wb,hb,eb,item['fb'])
        assert list(ka)==item['A']['source'] and list(kb)==item['B']['source']
        a[:,1]=side-a[:,1];a[:,2]*=-1;b[:,0]=side-b[:,0];b[:,2]*=-1
        grid=[(i+.5,j+.5,0.) for i in range(wa) for j in range(hb)]+[(side-.5-i,side-.5-j,0.) for i in range(wb) for j in range(ha)]
        q=np.r_[a,b,np.asarray(grid).reshape(-1,3)];labels=np.r_[np.zeros(len(a),int),np.ones(len(b),int),np.full(len(grid),2,int)]
        candidate,record=repair(q,labels,side,np.array([wa+f/2,hb+f/2]),job['radius'],job['trust'],min(job['seconds'],remaining-1),branch_radius=job.get('branch_radius',0.));record.update(n=n,target_side=side,initial_overlap=float(fc.worst_overlap(q)));cases.append(record)
        if candidate is None:continue
        digest=hashlib.sha256(candidate.tobytes()).hexdigest()[:16];dest=out/f'{n}-ctip34-{digest}.csv';fc.write_csv(str(dest),n,candidate)
        meta=dict(n=n,side=side,kind='fixed-angle mixed-integer interface core',A=item['A'],B=item['B'],interface_model=record,source_cache_sha256=job['cache_sha256'])
        Path(str(dest)+'.json').write_text(json.dumps(meta));exports.append(dict(path=dest.name,**record))
    result=dict(seconds=time.time()-started,cases=cases,exports=exports);Path(job['measurement']).write_text(json.dumps(result,indent=2));print(json.dumps(dict(cases=len(cases),exports=len(exports),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    else:run(sys.argv[2])
