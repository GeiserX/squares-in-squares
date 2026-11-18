"""Solve rigid corner translations using the arrangement of SAT boundary lines."""
from pathlib import Path
import hashlib
import json
import math
import os
import pickle
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree
import forensics_compose as fc
import forensics_rect as rect


def solve(a,b,lower,upper,clearance=2e-10):
    lower=np.asarray(lower,dtype=float);upper=np.asarray(upper,dtype=float)
    if np.any(lower>upper+1e-12):return None,0
    upper=np.maximum(lower,upper)
    corners=np.array([[x,y] for x in [lower[0],upper[0]] for y in [lower[1],upper[1]]])
    radius=math.sqrt(2)+float(np.linalg.norm(corners,axis=1).max())+1e-7
    neighbors=cKDTree(a[:,:2]).query_ball_tree(cKDTree(b[:,:2]),radius)
    indices=[(i,j) for i,js in enumerate(neighbors) for j in js]
    if not indices:return (lower+upper)/2,1
    ia,ib=np.asarray(indices,dtype=int).T;qa=a[ia];qb=b[ib]
    ua=np.column_stack([np.cos(qa[:,2]),np.sin(qa[:,2])]);va=np.column_stack([-ua[:,1],ua[:,0]])
    ub=np.column_stack([np.cos(qb[:,2]),np.sin(qb[:,2])]);vb=np.column_stack([-ub[:,1],ub[:,0]])
    axes=np.stack([ua,va,ub,vb],axis=1)
    radii=.5*sum(np.abs(np.einsum('pai,pi->pa',axes,v)) for v in [ua,va,ub,vb])
    delta=np.einsum('pai,pi->pa',axes,qa[:,:2]-qb[:,:2])
    projections=delta[None,:,:]+np.einsum('ci,pai->cpa',corners,axes)
    guaranteed=np.any((projections.min(0)>=radii+clearance)|(projections.max(0)<=-radii-clearance),axis=1)
    axes=axes[~guaranteed];radii=radii[~guaranteed];delta=delta[~guaranteed]
    if not len(axes):return (lower+upper)/2,1
    normals=np.concatenate([axes.reshape(-1,2),-axes.reshape(-1,2),np.eye(2)])
    offsets=np.r_[(radii+clearance-delta).ravel(),(radii+clearance+delta).ravel(),lower]
    normals=np.r_[normals,np.eye(2)];offsets=np.r_[offsets,upper]
    i,j=np.triu_indices(len(normals),1);u=normals[i];v=normals[j]
    det=u[:,0]*v[:,1]-u[:,1]*v[:,0];valid=np.abs(det)>1e-12;i=i[valid];j=j[valid];u=u[valid];v=v[valid];det=det[valid]
    points=np.column_stack([(offsets[i]*v[:,1]-u[:,1]*offsets[j])/det,(u[:,0]*offsets[j]-offsets[i]*v[:,0])/det])
    points=points[np.all(points>=lower-1e-12,axis=1)&np.all(points<=upper+1e-12,axis=1)]
    points=np.unique(np.round(np.r_[corners,((lower+upper)/2)[None,:],np.clip(points,lower,upper)],12),axis=0)
    checked=0
    for start in range(0,len(points),256):
        trial=points[start:start+256];gap=np.abs(delta[None,:,:]+np.einsum('ci,pai->cpa',trial,axes))-radii[None,:,:]
        feasible=np.all(gap.max(2)>=clearance*.4,axis=1);checked+=len(trial)
        if feasible.any():return trial[np.flatnonzero(feasible)[0]],checked
    return None,checked


def control():
    a=np.array([[1.4,.5,0.]]);b=np.array([[.5,.5,0.]])
    assert fc.worst_overlap(a,b)<-.09
    found,checked=solve(a,b,[0.,0.],[.2,0.]);assert found is not None
    moved=a.copy();moved[:,:2]+=found;assert fc.worst_overlap(moved,b)>-1e-9
    blocked,_=solve(a,b,[0.,0.],[.05,0.]);assert blocked is None
    other=np.array([[2.3,.5,0.]])
    blocked,_=solve(a,np.r_[b,other],[0.,0.],[.2,0.]);assert blocked is None
    a=np.array([[1.348,1.624,-.1]]);b=np.array([[1.548,.6,-.1]])
    assert fc.worst_overlap(a,b)<-1e-4
    found,_=solve(a,b,[0.,0.],[.04,0.]);assert found is not None
    moved=a.copy();moved[:,:2]+=found
    complete=np.r_[moved,b,np.array([[.5,.5,0.],[2.45,2.45,0.]])]
    assert fc.worst_overlap(complete)>-1e-9 and fc.corners(complete).min()>=0. and fc.corners(complete).max()<=2.95
    blocked,_=solve(a,b,[0.,0.],[.005,0.]);assert blocked is None
    print('CONTROL overlap0.1 and a complete tilted corner fixture repaired; insufficient ranges and opposing obstacle refused',flush=True)


def part(cache,gid,w,h,e,f):
    key,side,q=cache['src'][gid//8];r=dict(rect.sym8(q,side))[gid%8];corners=fc.corners(r)
    indices=np.flatnonzero(np.maximum(corners[:,:,0].max(1)-w,corners[:,:,1].max(1)-h)<=f+1e-12)[:w*h+e]
    if len(indices)!=w*h+e:raise ValueError('cached crop count differs')
    return key,r[indices].copy()


def run(jobfile):
    job=json.loads(Path(jobfile).read_text());root=Path(job['root']);deadline=float(job['deadline'])
    signal.setitimer(signal.ITIMER_REAL,max(.1,deadline-time.time()));(root/'scanner.pid').write_text(str(os.getpid()))
    cache=pickle.load(Path(job['cache']).open('rb'));out=Path(job['out']);out.mkdir(parents=True,exist_ok=True)
    cases=[];exports=[];started=time.time()
    for item in job['cases']:
        if time.time()>deadline-2:break
        n=item['n'];m=math.isqrt(n);side=item['side'];f=side-m;wa,ha,ea=item['w'],item['h'],item['e'];wb,hb,eb=m-wa,m-ha,n-m*m-ea
        for tag in ['A','B']:
            gid=item['ga' if tag=='A' else 'gb'];expected=item[tag]['source'];assert list(cache['src'][gid//8][0])==expected
        ka,a=part(cache,item['ga'],wa,ha,ea,item['fa']);kb,b=part(cache,item['gb'],wb,hb,eb,item['fb'])
        a[:,1]=side-a[:,1];a[:,2]*=-1;b[:,0]=side-b[:,0];b[:,2]*=-1
        ac=fc.corners(a);bc=fc.corners(b);amin=ac.min((0,1));amax=ac.max((0,1));bmin=bc.min((0,1));bmax=bc.max((0,1))
        al=np.array([-amin[0],hb-amin[1]]);au=np.array([wa+f-amax[0],side-amax[1]])
        bl=np.array([wa-bmin[0],-bmin[1]]);bu=np.array([side-bmax[0],hb+f-bmax[1]])
        before=fc.worst_overlap(a,b)
        point,tested=solve(a,b,al-bu,au-bl)
        result=dict(n=n,before=before,points=tested,feasible=point is not None,raw_side=item['raw_side'],side=side)
        cases.append(result)
        if point is None:continue
        lo=np.maximum(al,point+bl);hi=np.minimum(au,point+bu)
        if np.any(lo>hi+2e-11):raise ValueError('relative shift has no absolute decomposition')
        shift_a=(lo+hi)/2;shift_b=shift_a-point;a[:,:2]+=shift_a;b[:,:2]+=shift_b
        grid=[(i+.5,j+.5,0.) for i in range(wa) for j in range(hb)]+[(side-.5-i,side-.5-j,0.) for i in range(wb) for j in range(ha)]
        q=np.r_[a,b,np.asarray(grid).reshape(-1,3)];bounds=fc.corners(q);overlap=fc.worst_overlap(q)
        result.update(after=overlap,shift_a=shift_a.tolist(),shift_b=shift_b.tolist())
        if len(q)!=n or bounds.min()<-1e-9 or bounds.max()>side+1e-9 or overlap<-1e-9:raise ValueError(('rigid translation failed complete packing check',result))
        digest=hashlib.sha256(np.round(q,12).tobytes()).hexdigest()[:16];dest=out/f'{n}-slide34-{digest}.csv'
        if dest.exists():continue
        fc.write_csv(str(dest),n,q)
        meta=dict(n=n,side=side,kind='rigid translated corner pair',A=item['A'],B=item['B'],rigid_shift=dict(point=point.tolist(),a=shift_a.tolist(),b=shift_b.tolist(),solver='SAT line arrangement',input_cache_sha256=job['cache_sha256']))
        Path(str(dest)+'.json').write_text(json.dumps(meta));exports.append(dict(path=dest.name,**result))
    result=dict(seconds=time.time()-started,cases=cases,exports=exports);Path(job['measurement']).write_text(json.dumps(result,indent=2));print(json.dumps(dict(cases=len(cases),feasible=sum(c['feasible'] for c in cases),exports=len(exports),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    else:run(sys.argv[2])
