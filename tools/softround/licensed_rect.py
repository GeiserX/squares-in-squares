"""Rebuild the measured 847 rectangle recipe from an actual licensed 581."""
import hashlib
import itertools
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

H = Path(__file__).resolve().parent
LANE = H.parents[1]
sys.path.insert(0,str(LANE));sys.path.insert(0,str(H))
import ctl
import policy
import provenance
import forensics_compose as fc
import forensics_rect as fr

W=Path(ctl.W)


def windows(path):
    side,Q=fc.frame(fr.layouts(str(path))[581]);out={}
    for sym,R in fr.sym8(Q,side):
        K=fc.corners(R)
        for w,h in ((14,15),(15,14)):
            d=np.maximum(K[:,:,0].max(1)-w,K[:,:,1].max(1)-h)
            f=max(0.,float(np.sort(d)[212]))
            take=np.flatnonzero(d<=f+1e-15)[:213]
            if len(take)==213:out[(sym,w,h)]=(f,R[take].copy())
    return out


def compose(parts,sa,sb,collide=0.):
    fa,A=parts[(sa,14,15)];fb,B=parts[(sb,15,14)];side=29+max(fa,fb)
    A=A.copy();A[:,1]=side-A[:,1];A[:,2]=-A[:,2]
    B=B.copy();B[:,0]=side-B[:,0];B[:,2]=-B[:,2]
    if fc.worst_overlap(A,B)<-max(1e-9,collide):return None
    grid=[(i+.5,j+.5,0.) for i in range(14) for j in range(14)]
    grid += [(side-.5-i,side-.5-j,0.) for i in range(15) for j in range(15)]
    X=np.r_[A,B,np.array(grid)]
    if len(X)!=847 or fc.worst_overlap(X)<-max(1e-9,collide):return None
    return side,X


def rows(X):
    return [dict(n=847,square_id=i,x=repr(float(x)),y=repr(float(y)),angle=repr(float(a))) for i,(x,y,a) in enumerate(X)]


def main():
    assert time.time()<float((W/'deadline').read_text())
    control_dir=W/'boxD/run/847-rectcontrol'
    log=(control_dir/'chain.log').read_text()
    assert 'CHAINEND' in log and 'FQCHECK' in log, 'repair control has not completed'
    controls=[]
    for path in control_dir.glob('raw/*.csv'):
        _,score,cert=ctl.cert((str(path),str(path)))
        if cert is not None:controls.append((score,path,cert))
    assert controls,'repair control produced no legal rectangle'
    sc,path,frrows=min(controls,key=lambda r:r[0])
    control_side=(1+sc)*math.sqrt(847)
    assert abs(control_side-29.600801735541854)<1e-4,control_side
    proof=dict(control_side=control_side,control_score=sc,control_n=len(frrows),control_file=str(path))
    print('CONTROL repaired old recipe847',proof,flush=True)
    source=provenance.S/'take-k123-r24/581.csv';input_bytes=source.read_bytes();ancestry=provenance.trace(source,581);assert ancestry['ok'],ancestry
    assert input_bytes==source.read_bytes(),'source changed while tracing'
    origin_policy=policy.classify(ancestry['source'],ancestry['licence'],ancestry);assert origin_policy['status']=='none',origin_policy
    d=W/'licensed-rectangle';d.mkdir(exist_ok=True);snap=d/'581-actual-cc0.csv';snap.write_bytes(input_bytes)
    receipt=dict(path=str(source),n=581,verified_ancestry=True,ancestry=ancestry['evidence'],snapshot_sha256=hashlib.sha256(snap.read_bytes()).hexdigest())
    Path(str(snap)+'.origin.json').write_text(json.dumps(receipt,indent=2))
    snap.with_suffix('.json').write_text(json.dumps(dict(n=581,source=ancestry['source'],licence=ancestry['licence']),indent=2))
    parts=windows(snap);best=[]
    oldbar=(1+policy.old_scores()[847])*math.sqrt(847)
    tested=0
    for sa,sb in itertools.product(range(8),repeat=2):
        if 29+max(parts[(sa,14,15)][0],parts[(sb,15,14)][0])>=oldbar:continue
        tested+=1
        built=compose(parts,sa,sb,collide=.015)
        if built is not None:best.append((built[0],sa,sb,built[1]))
    proof.update(tested=tested,valid=len(best),origin_policy=origin_policy)
    (W/'licensed-rect-control.json').write_text(json.dumps(proof,indent=2))
    assert best,'no licensed composition below the round22 bar'
    side,sa,sb,X=min(best,key=lambda x:(x[0],x[1],x[2]))
    predicted=side
    raw_overlap=fc.worst_overlap(X)
    X[:,:2]*=1+.02/(side-1)
    side,_=fc.frame(X)
    target=d/'847-built.csv'
    meta=dict(n=847,side=side,source='own measured rectangle reconstruction with forensics_rect.sym8 and forensics_compose; actual new CC0-derived581 snapshot '+str(snap)+'; '+ancestry['source'],licence=ancestry['licence']+'; Samanyu ancestry: none (recorded public/own roots)',parts=dict(A=dict(source=[str(snap),581],sym=sa,w=14,h=15,excess=3),B=dict(source=[str(snap),581],sym=sb,w=15,h=14,excess=3)),source_policy=origin_policy,predicted_side=predicted,raw_overlap=raw_overlap,centre_inflation=1+.02/(predicted-1))
    target.with_suffix('.json').write_text(json.dumps(meta,indent=2));ctl.write_rows(str(target),rows(X))
    result=dict(path=str(target),side=side,predicted_side=predicted,raw_overlap=raw_overlap,symA=sa,symB=sb,source=meta['source'],licence=meta['licence'],proof=provenance.trace(target,847))
    assert result['proof']['ok'],result['proof']
    pol=policy.classify(result['source'],result['licence'],result['proof']);assert pol['status']=='none',pol
    (W/'licensed-rectangle.json').write_text(json.dumps(result,indent=2))
    print('LICENSED actual fresh input',result['side'],'predicted',predicted,'raw gap',raw_overlap,'valid',len(best),'syms',sa,sb,flush=True)


if __name__=='__main__':main()
