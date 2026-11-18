"""Bounded subwindow checks on fresh round34 licensed public roots, without a solver."""
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import re
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,T,W,L,END,state,write_json,rows_write,table
sys.path.insert(0,str(L))
import numpy as np
import literature_window as windows
from policy import audit
from walk import validate_job
ROOT=W/'crops34-new-public';ROOT.mkdir(exist_ok=True)


def control():
    rows=[dict(n=4,square_id=i,x=x,y=y,angle=0) for i,(x,y) in enumerate([(0.5,0.5),(0.5,1.5),(1.5,0.5),(1.5,1.5)])]
    yes=windows.scan_one(rows,{3:2.1},1e-8)
    no=windows.scan_one(rows,{3:1.9},1e-8)
    assert 3 in yes and abs(yes[3][0]-2)<1e-12 and not no
    state('CONTROL crop reader: grid4 gives3 at side2 under2.1, refuses1.9')


def resume_finalizer(reason='bounded crop check'):
    path=W/'finish.pid'
    if path.exists():
        pid=int(path.read_text())
        result=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5)
        if '/harvest36/finish.py' in result.stdout:return
    command=['nice','-n','5',str(S/'venv/bin/python'),'-I',str(Path(__file__).with_name('finish.py'))]
    with (W/'finish.log').open('a') as log:
        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
    path.write_text(str(child.pid)+'\n')
    state(f'RESUME finalizer{child.pid} after {reason}; driver unchanged; stop07:23Z, close before07:25Z, publish07:35Z')


def timed_out(*args):raise TimeoutError('crop budget reached')


def main():
    results=[];hits=[];orientations=0;started=time.monotonic()
    deadline=min(END,time.time()+90)
    write_json(ROOT/'deadline.json',dict(global_deadline=END,job_deadline=deadline))
    signal.signal(signal.SIGALRM,timed_out);signal.setitimer(signal.ITIMER_REAL,max(.01,deadline-time.time()))
    try:
        control()
        bars={int(r['n']):float(r['bar']) for r in table(S/'round36-briefs/bar36.tsv')}
        for ledger in S.glob('take-*-r36/take.tsv'):
            if ledger.parent==T:continue
            for r in table(ledger):
                if (ledger.parent/(r['n']+'.csv')).is_file():bars[int(r['n'])]=min(bars[int(r['n'])],float(r['new']))
        limits={n:(score+1)*math.sqrt(n) for n,score in bars.items()}
        withdrawal_lines=[line for log in [S/'handoff-r31.log',S/'handoff-r33.log',S/'handoff-r34.log',S/'handoff-r35.log',S/'handoff-r36.log'] for line in log.read_text().splitlines() if re.search(r'\bWITHDRAW|\bWITHHOLD',line,re.I)]
        roots=[]
        for n in [812,907]:
            eligible=[]
            for p in (T/'near').glob(f'{n}-public*.csv'):
                record=json.loads(Path(str(p)+'.json').read_text())
                if not record['source'].startswith('public jazivxt/'):continue
                if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:continue
                eligible.append((record['score'],p,record))
            if not eligible:continue
            _,p,record=min(eligible,key=lambda r:r[0])
            for line in withdrawal_lines:
                hashes=re.findall(r'sha256(?: prefix)?[ =:]+([0-9a-f]{8,64})',line,re.I)
                if (str(p) in line and not hashes) or any(record['sha256'].startswith(value) for value in hashes):raise ValueError('withdrawn root bytes refused before crop')
            validate_job(record)
            rows=list(csv.DictReader(p.open()))
            if not audit(rows)[0]:raise ValueError('source root share changed')
            array=np.array([[float(row[k]) for k in ['x','y','angle']] for row in rows])
            angles,counts=np.unique(np.round(array[:,2]%(math.pi/2),7),return_counts=True)
            rotations=[0.]+[-float(angles[i]) for i in np.argsort(-counts) if abs(float(angles[i]))>1e-6][:7]
            roots.append((n,p,record,array,rotations))
            results.append(dict(n=n,path=str(p),sha256=record['sha256'],orientations=0,counts=n-1,hits=[]))
        # Cover every source in its original frame before trying tilted frames.
        for round_index in range(8):
            for (n,p,record,array,rotations),result in zip(roots,results):
                if round_index>=len(rotations):continue
                angle=rotations[round_index];co,si=math.cos(angle),math.sin(angle)
                xy=array[:,:2]@np.array([[co,si],[-si,co]])
                turned=[dict(n=n,x=float(x),y=float(y),angle=float(a+angle)) for (x,y),a in zip(xy,array[:,2])]
                found=windows.scan_one(turned,limits,5e-9)
                orientations+=1;result['orientations']+=1
                for count,(side,left,bottom) in found.items():
                    score=side/math.sqrt(count)-1
                    if score>=bars[count]-1e-10:continue
                    lo,hi,yl,yh=windows.extents(turned)
                    keep=(lo>=left-1e-12)&(yl>=bottom-1e-12)&(hi<=left+side+1e-12)&(yh<=bottom+side+1e-12)
                    indices=np.flatnonzero(keep)[:count]
                    if len(indices)!=count:raise ValueError('crop does not contain its named count')
                    crop=[dict(n=count,square_id=i,x=repr(turned[j]['x']-left),y=repr(turned[j]['y']-bottom),angle=repr(turned[j]['angle'])) for i,j in enumerate(indices)]
                    dest=ROOT/f'{count}-from{n}-r{round_index}.csv';rows_write(dest,crop)
                    meta=dict(n=count,kind='public-crop',public_first=True,source=f'subwindow of {p}; rigid rotation {angle!r}; origin '+record['source'],licence=record['licence'],parent=dict(path=str(p),n=n,sha256=record['sha256']),rotation=angle,window=[left,bottom,side],selected_indices=indices.tolist(),score_estimate=score,required_offbox_fq=True)
                    write_json(Path(str(dest)+'.json'),meta)
                    item=dict(n=count,parent=n,path=str(dest),estimated_gain=bars[count]-score)
                    result['hits'].append(item);hits.append(item)
        state(f'FINISH crop scan roots={len(results)} orientations={orientations} raw_hits={len(hits)}; no unquenched row counted')
    except TimeoutError:
        state(f'STOP crop scan at90s cap, completed orientations={orientations}, raw_hits={len(hits)}; bounded diagnostic only')
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        try:write_json(ROOT/'results.json',dict(seconds=time.monotonic()-started,orientations=orientations,inputs=results,hits=hits,scanner_sha256=hashlib.sha256(Path(windows.__file__).read_bytes()).hexdigest()))
        finally:resume_finalizer()

if __name__=='__main__':main()
