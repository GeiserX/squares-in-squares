#!/usr/bin/env python3
"""Give an outer column unequal contact gaps and small alternating rotations.

Each rotated column cell stays against the outer wall. Its extra height comes
from the existing gap budget. Nearby tilted cells enter the column's seam
before a local soft repair and a full family squeeze.
"""
import csv,json,math,os,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import family_step as F
import methods_soft as S
import methods_lp as LP
import modules as M


def column(P):
    return np.array(sorted(np.flatnonzero((P[:,0]<.7)&(np.abs(P[:,2])<.04)),key=lambda i:P[i,1]),int)


def seed(P,L,angle,intrusion,phase):
    Q=P.copy(); ids=column(P)
    if angle==0 and intrusion==0:return Q,ids
    if len(ids)<10:raise ValueError('no outer column')
    n=len(ids); signs=np.where((np.arange(n)+phase)%2,1.,-1.)
    # Opposite signs create unequal notches at successive contacts.
    Q[ids,2]=angle*signs
    h=.5*(np.abs(np.cos(Q[ids,2]))+np.abs(np.sin(Q[ids,2])))
    free=L-2*h.sum()
    if free<0:raise ValueError('column rotation uses more than the available height')
    old=np.maximum(np.diff(P[ids,1])-1.,0.)
    weights=np.r_[max(P[ids[0],1]-.5,0.),old,max(L-P[ids[-1],1]-.5,0.)]+1e-6
    # Tilt direction puts most slack on one side of each contact.
    weights[1:-1]*=np.where(signs[:-1]>0,4.,.25)
    gaps=free*weights/weights.sum()
    Q[ids,0]=h+1e-9
    Q[ids,1]=np.cumsum(np.r_[gaps[0]+h[0],h[:-1]+h[1:]+gaps[1:-1]])
    arm=(Q[:,0]<2.2)&(np.abs(Q[:,2])>.1)
    Q[arm,0]-=intrusion
    assert len(Q)==len(P) and Q[ids,1][-1]+h[-1]<=L+1e-8
    return Q,ids


def control(path,n):
    L,P=F.canon(F.load(path)[n]);Q,ids=seed(P,L,0.,0.,0)
    gap=LP.min_gap(P);assert len(P)==n and len(ids)>=10 and np.array_equal(P,Q) and gap>=-1e-7
    S.load_kernel()
    pairs=LP.pair_list(P,math.sqrt(2)+.2)
    legal=S.c_energy(P,L,pairs)[0] if S.KERN is not None else S.total_energy(P,L)
    bad=P.copy();bad[ids[1]]=bad[ids[0]]
    rejected=S.total_energy(bad,L)
    assert legal<1e-12 and rejected>.9
    print('CONTROL interlock',n,'column',len(ids),'gap',gap,'identity',np.max(abs(P-Q)),'energy',legal,'duplicate',rejected,flush=True)
    return L,P


def run(path,n,out,angle,intrusion,phase):
    L,P=control(path,n);t=time.time();Q,ids=seed(P,L,angle,intrusion,phase)
    act=(Q[:,0]<3.2)|((np.min(np.abs(Q[:,1,None]-Q[ids,1]),axis=1)<.08)&(Q[:,0]<4.))
    before=S.total_energy(Q,L)
    for _ in range(5):
        Q,e=S.relax_local(Q,L,act,maxiter=1200)
        if e<1e-13:break
    print('LOCAL',n,'angle',angle,'intrusion',intrusion,'phase',phase,'active',int(act.sum()),'energy',before,e,'seconds',time.time()-t,flush=True)
    os.makedirs('interlock-near',exist_ok=True)
    M.write_layout('interlock-near/'+os.path.basename(out)+'.csv',n,Q)
    if e>1e-3:
        print('REFUSED local repair',e,flush=True);return
    F.set_limit(200)
    try:R,side,tr=F.squeeze(Q,iters=50,fq=True,apart=.03,log=lambda s:print(s,flush=True))
    except Exception as exc:print('REFUSED full repair',str(exc),flush=True);return
    M.write_layout(out+'.csv',n,R)
    provenance=json.load(open('inputs/provenance.json'))[str(n)]
    mods=[dict(q,source='asymmetric outer-column interlock from '+provenance['path']+'; '+q['source']) for q in provenance['modules']]
    json.dump(dict(n=n,built=side,held=L,predicted=L,start=L,stacks=[0,0],seconds={'interlock':time.time()-t},modules=mods,angle=angle,intrusion=intrusion,phase=phase,trace=tr),open(out+'.json','w'))
    print('BUILT',n,side,'source delta',side-L,flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control(sys.argv[2],int(sys.argv[3]))
    else:run(sys.argv[2],int(sys.argv[3]),sys.argv[4],float(sys.argv[5]),float(sys.argv[6]),int(sys.argv[7]))
