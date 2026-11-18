"""Measure angled rectangle windows before admitting any new part or start."""
from pathlib import Path
import hashlib
import json
import math
import os
import pickle
import signal
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import forensics_compose as fc
import forensics_interior as fi
import forensics_rect as rect


def rotate(q,angle):
    result=np.array(q,copy=True)
    c,s=math.cos(angle),math.sin(angle)
    result[:,:2]=result[:,:2]@np.array([[c,s],[-s,c]])
    result[:,2]+=angle
    return result


def control(source):
    side,q=fc.frame(rect.layouts(source)[686])
    part=dict(rect.sym8(q,side))[5];corners=fc.corners(part)
    ix=np.flatnonzero((corners[:,:,0].max(1)<=9+12/17+2e-8)&(corners[:,:,1].max(1)<=18+12/17+2e-8))
    assert len(ix)==168
    planted=rotate(part[ix],.23)
    recovered=rotate(planted,-.23)
    yes=fi.windows(recovered,9+12/17+2e-8,18+12/17+2e-8,1)[0][0]
    no=fi.windows(planted,9+12/17+2e-8,18+12/17+2e-8,1)[0][0]
    assert yes==168 and no<168,(yes,no)
    assert np.max(np.abs(recovered-part[ix]))<2e-14
    print('CONTROL inverse angle restores168; wrong angle retains'+str(no),flush=True)
    return dict(restored=yes,wrong_angle=no)


def measure(jobfile):
    job=json.loads(Path(jobfile).read_text());root=Path(job['root']);deadline=float(job['deadline'])
    signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-time.time()))
    processes=subprocess.check_output(['ps','-ww','-axo','pid,command'],text=True)
    assert not any(str(root/'code'/name)+' ' in line for line in processes.splitlines() for name in ['forensics_scan25.py','forensics_probe26.py'])
    (root/'scanner.pid').write_text(str(os.getpid()))
    cache=pickle.load(Path(job['cache']).open('rb'));table=cache['TF'][...,0]
    targets={int(n):float(v) for n,v in job['targets'].items()}
    started=time.time();cases=[];useful=[]
    for source in job['sources']:
        path=Path(source['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        _,q=fc.frame(rect.layouts(path)[source['n']])
        angles=np.mod(q[:,2]+math.pi/4,math.pi/2)-math.pi/4
        values,counts=np.unique(np.round(angles,4),return_counts=True)
        chosen=[float(v) for v,c in sorted(zip(values,counts),key=lambda a:-a[1]) if abs(v)>.01 and c>=3][:6]
        chosen=list(dict.fromkeys(chosen+[math.pi/12,math.pi/6,math.pi/4]))
        for angle in chosen:
            rotated=rotate(q,-angle)
            for width,height in job['shapes']:
                before=time.time();parts=[]
                for count,x,y,indices in fi.windows(rotated,width+.72,height+.72,2):
                    excess=count-width*height
                    if excess<=0:continue
                    _,part=fc.frame(rotated[indices]);corners=fc.corners(part)
                    fraction=float(max(corners[:,:,0].max()-width,corners[:,:,1].max()-height))
                    old=float(table[width,height,excess]) if excess<table.shape[2] else float('inf')
                    if fraction>=old-1e-8:continue
                    hits=[]
                    for n,side in targets.items():
                        m=math.isqrt(n);k=n-m*m
                        if max(width,height)>m:continue
                        if excess==k and m+fraction<side-1e-8:hits.append(dict(n=n,gap=m+fraction-side,kind='single'))
                        if width<m and height<m and 0<k-excess<table.shape[2]:
                            other=float(table[m-width,m-height,k-excess]);gap=m+max(fraction,other)-side
                            if gap<.004:hits.append(dict(n=n,gap=gap,kind='pair'))
                    entry=dict(source=source['canonical'],n=source['n'],angle=angle,w=width,h=height,excess=excess,fraction=fraction,old_fraction=old,indices=[int(i) for i in indices],hits=hits)
                    parts.append(entry)
                    if hits:useful.append(entry)
                cases.append(dict(source=source['canonical'],n=source['n'],angle=angle,w=width,h=height,better_parts=len(parts),best_excess=max([p['excess'] for p in parts],default=0),seconds=time.time()-before))
    result=dict(control=job['control'],seconds=time.time()-started,cases=cases,new_parts=sum(r['better_parts'] for r in cases),useful=useful,starts_written=0)
    Path(job['out']).write_text(json.dumps(result,indent=2));print(json.dumps(dict(cases=len(cases),new_parts=result['new_parts'],useful=len(useful),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control(sys.argv[2])
    else:measure(sys.argv[2])
