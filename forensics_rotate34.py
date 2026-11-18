"""Test continuous crop orientation on fresh, source-cleared host geometry."""
from pathlib import Path
import hashlib
import json
import math
import signal
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.optimize import minimize_scalar
import forensics_compose as fc
import forensics_rect as rect
import forensics_interior as fi


def rotate(q, angle):
    out=np.array(q,copy=True)
    c,s=math.cos(angle),math.sin(angle)
    out[:,:2]=out[:,:2]@np.array([[c,s],[-s,c]])
    out[:,2]+=angle
    return out


def fraction(q,w,h,angle):
    _,out=fc.frame(rotate(q,angle))
    corners=fc.corners(out)
    return max(0.,float(corners[:,:,0].max())-w,float(corners[:,:,1].max())-h)


def optimize(q,w,h):
    fit=minimize_scalar(lambda a:fraction(q,w,h,a),bounds=(-.04,.04),method='bounded',options={'xatol':1e-11,'maxiter':80})
    before=fraction(q,w,h,0.)
    if fit.fun<before:return float(fit.x),float(fit.fun),before
    return 0.,before,before


def control():
    q=np.array([[x+.5,y+.5,0.] for x in range(3) for y in range(2)])
    planted=rotate(q,.02)
    angle,after,before=optimize(planted,3,2)
    assert len(planted)==6 and before>.02 and after<1e-8,(angle,after,before)
    _,out=fc.frame(rotate(planted,angle))
    assert fc.worst_overlap(out)>-1e-8
    duplicate=np.r_[out,out[:1]]
    assert fc.worst_overlap(duplicate)<-.9
    print('CONTROL rotated six-square crop restored below1e-8; wrong angle exceeds0.02; duplicate overlap rejected',flush=True)


def run(jobfile):
    job=json.loads(Path(jobfile).read_text());root=Path(job['root']);deadline=float(job['deadline'])
    signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-time.time()))
    import subprocess,os
    ps=subprocess.check_output(['ps','-ww','-axo','pid,command'],text=True)
    assert not any(str(root/'code'/name)+' ' in ps for name in ['forensics_scan25.py','forensics_probe26.py','forensics_angle34.py'])
    (root/'scanner.pid').write_text(str(os.getpid()))
    import pickle
    cache=pickle.load(Path(job['cache']).open('rb'));table=cache['TF'][...,0]
    targets={int(n):float(v) for n,v in job['targets'].items()}
    cases=[];improvements=[];exports=[];started=time.time()
    for source in job['sources']:
        path=Path(source['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256']
        _,q=fc.frame(rect.layouts(path)[source['n']])
        for w,h in job['shapes']:
            for count,x,y,indices in fi.windows(q,w+.72,h+.72,3):
                excess=count-w*h
                if excess<=0 or excess>=table.shape[2]:continue
                part=q[indices];angle,after,before=optimize(part,w,h);old=float(table[w,h,excess])
                entry=dict(source=source['canonical'],n=source['n'],w=w,h=h,count=count,excess=excess,angle=angle,before=before,after=after,old=old)
                cases.append(entry)
                if after>=old-1e-8:continue
                hits=[]
                for n,side in targets.items():
                    m=math.isqrt(n);k=n-m*m
                    if max(w,h)>m:continue
                    if excess==k and m+after<side-1e-8:hits.append(dict(n=n,kind='single',gap=m+after-side))
                    if w<m and h<m and 0<k-excess<table.shape[2]:
                        gap=m+max(after,float(table[m-w,m-h,k-excess]))-side
                        if gap<.004:hits.append(dict(n=n,kind='pair',gap=gap))
                entry.update(hits=hits,indices=[int(i) for i in indices]);improvements.append(entry)
                if not hits:continue
                _,out=fc.frame(rotate(part,angle));assert len(out)==count and fc.worst_overlap(out)>-1e-8
                digest=hashlib.sha256(np.ascontiguousarray(out).tobytes()).hexdigest()[:20]
                folder=root/'interior'/f'{source["n"]}-anglemin34';folder.mkdir(parents=True,exist_ok=True)
                dest=folder/f'{count}-interior-{digest}.csv';fc.write_csv(str(dest),count,out)
                local=Path(job['local_work'])/'interior'/folder.name/dest.name
                metadata=dict(n=count,kind='continuously rotated interior rectangle',parents=[[source['canonical'],source['n']]],source='fresh host rectangle crop with continuous rigid rotation',host_sha256=source['sha256'],indices=entry['indices'],angle=angle,w=w,h=h,fraction=after,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),measurement=entry)
                Path(str(dest)+'.json').write_text(json.dumps(metadata));exports.append(dict(path=str(local),**entry))
    result=dict(seconds=time.time()-started,cases=cases,new_parts=improvements,exports=exports)
    Path(job['out']).write_text(json.dumps(result,indent=2));print(json.dumps(dict(cases=len(cases),new_parts=len(improvements),exports=len(exports),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    else:run(sys.argv[2])
