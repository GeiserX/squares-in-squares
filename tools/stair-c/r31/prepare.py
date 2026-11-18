"""Fingerprint exact module geometry for table reuse and recipe exclusion."""
import csv,hashlib,json,os,pickle,re,shutil,sys
import numpy as np
ROOT='$SCRATCH/bounties-squares'
LANE='.'
WORK=ROOT+'/take-stair-c-r31/work'
sys.path.insert(0,LANE)
import modules as M

def fingerprint(q):
    def norm(x):
        if isinstance(x,np.ndarray):return ('array',x.shape,str(x.dtype),np.round(x,11).tolist())
        if isinstance(x,np.generic):return x.item()
        if isinstance(x,dict):return {k:norm(v) for k,v in sorted(x.items())}
        if isinstance(x,(list,tuple)):return [norm(v) for v in x]
        return x
    skip={'id','src','licence','tag','n','m','k','ours','sig','loss0','tilt0'}
    return hashlib.sha256(json.dumps(norm({k:v for k,v in q.items() if k not in skip}),sort_keys=True).encode()).hexdigest()
