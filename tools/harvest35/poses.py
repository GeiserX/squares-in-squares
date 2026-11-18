"""Recognise repeated poses across decimal exports without merging new geometry."""
import csv
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree


def read(path):
    with open(path) as stream:
        return np.array([[float(r[k]) for k in ('x','y','angle')] for r in csv.DictReader(stream)])


def equal(a,b,tolerance=1e-8):
    if a.shape!=b.shape:return False
    ac=a[:,:2]-(a[:,:2].min(0)+a[:,:2].max(0))/2
    bc=b[:,:2]-(b[:,:2].min(0)+b[:,:2].max(0))/2
    tree=cKDTree(bc)
    axes=np.column_stack((np.cos(a[:,2]),np.sin(a[:,2])))
    for swap in (False,True):
        for sx in (-1,1):
            for sy in (-1,1):
                c=(ac[:,::-1] if swap else ac)*[sx,sy]
                distances,indices=tree.query(c)
                if distances.max()>=tolerance or len(set(indices))!=len(a):continue
                v=(axes[:,::-1] if swap else axes)*[sx,sy]
                angles=np.arctan2(v[:,1],v[:,0])
                delta=(angles-b[indices,2]+np.pi/4)%(np.pi/2)-np.pi/4
                if np.abs(delta).max()<tolerance:return True
    return False


def control():
    a=np.array([[0.,0.,.17],[2.,0.,.38],[0.,3.,-.4]])
    b=a.copy();b[:,:2]+=10
    assert equal(a,b)
    b[0,2]+=.001
    assert not equal(a,b)
    b=a.copy();b[0,0]+=.001
    assert not equal(a,b)
    from common import T
    starts=sorted((T/'near').glob('577-public31-*.csv'))
    if starts:
        real=read(starts[0]);copy=real.copy();copy[:,:2]+=3.25
        assert equal(real,copy)
        copy[0,2]+=.001
        assert not equal(real,copy)
    if len(starts)>=2:print('MEASURE first two577 exports equal at1e-8:',equal(read(starts[0]),read(starts[1])),flush=True)
    print('CONTROL repeated decimal-export pose accepted; changed centre or angle refused',flush=True)

if __name__=='__main__':control()
