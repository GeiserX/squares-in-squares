"""Rank fresh raw starts by measured side margin and suppress copies of one geometry."""
import csv
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import methods_lp as mlp


def same_geometry(a,b,tolerance=1e-7):
    if len(a)!=len(b):return False
    a=mlp.normal(a);b=mlp.normal(b);tree=cKDTree(a[:,:2])
    for mirror in (False,True):
        for quarter in range(4):
            q=b.copy()
            if mirror:q[:,0]*=-1;q[:,2]=math.pi-q[:,2]
            for _ in range(quarter):
                q[:,:2]=q[:,[1,0]]*[-1,1];q[:,2]+=math.pi/2
            q=mlp.normal(q);dist,ix=tree.query(q[:,:2])
            if dist.max()>tolerance or len(set(ix))!=len(a):continue
            da=np.abs((q[:,2]-a[ix,2]+math.pi/4)%(math.pi/2)-math.pi/4)
            if da.max()<tolerance:return True
    return False


def apply(r):
    bars=r.live_bars();groups={};changed=[];canceled=[]
    for p in (r.W/'jobs').glob('*.json'):
        j=json.loads(p.read_text())
        if not j.get('raw_design') or j.get('leg'):continue
        table=r.rows(r.W/('r%d.tsv'%j['k']))[0]
        gap=(float(table['score'])-bars[j['n']])*math.sqrt(j['n'])
        groups.setdefault(j['n'],[]).append((gap,-j['created'],p,j))
    for n,items in groups.items():
        representatives=[]
        # Started files lead the comparison pool. Their geometry has already had a probe.
        items.sort(key=lambda x:(not (r.W/'boxE/claims'/x[2].stem).exists(),x[0],x[1]))
        for gap,stamp,p,j in items:
            if (r.W/'cancel'/p.stem).exists():continue
            source=r.W/j['sub']
            if not source.exists():continue
            a=mlp.load(str(source),{n})[n]
            started=(r.W/'boxE/claims'/p.stem).exists()
            duplicate=next((old for old,b in representatives if same_geometry(a,b)),None)
            if duplicate and not started:
                target=r.W/'cancel'/p.stem;target.parent.mkdir(exist_ok=True);target.touch();canceled.append(target)
                r.state('CANCEL duplicate raw geometry k%d n%d matches k%d within1e-7 centers and angles in a symmetry; original geometry still runs'%(j['k'],n,duplicate['k']))
                continue
            representatives.append((j,a))
            priority=(.7 if n<640 else .9) if gap<=.0005 else (1.7 if n<640 else 1.9)
            if not started and priority!=j['priority']:
                j['priority']=priority;r.atomic(p,json.dumps(j));changed.append(p)
    if canceled:r.run(['rsync','-a']+[str(p) for p in canceled]+[r.REMOTE+'cancel/'])
    if changed:r.run(['rsync','-a']+[str(p) for p in changed]+[r.REMOTE+'jobs/'])
    if changed or canceled:r.state('ORDER fresh near starts: %d reprioritized by .0005side margin; %d duplicate geometries canceled'%(len(changed),len(canceled)))


def control():
    p=np.array([[.5,.5,0],[1.5,.5,0],[.5,1.5,0.]])
    assert same_geometry(p,p+[3,5,0])
    q=p.copy();q[-1,0]+=.15
    assert not same_geometry(p,q)
    q=p.copy();q[:,:2]=q[:,[1,0]]*[-1,1];q[:,2]+=math.pi/2
    assert same_geometry(p,q)
    print('CONTROL geometry: translation and turn copies matched; equal-side layout with .15 center move remained distinct')


if __name__=='__main__':control()
