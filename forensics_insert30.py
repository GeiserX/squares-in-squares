"""Replace an interior patch, testing actual intersections across its box boundary."""
from pathlib import Path
import datetime,hashlib,json,math,os,signal,sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr
import forensics_boxscan as boxes


def primitives():
    side=2+1/math.sqrt(2)
    five=np.array([[x,y,0.] for x,y in [( .5,.5),(.5,side-.5),(side-.5,.5),(side-.5,side-.5)]]+[[side/2,side/2,math.pi/4]])
    outer=side+1;far=outer-.5
    ten=np.vstack([five,np.array([[far,j+.5,0.] for j in range(2)]+[[i+.5,far,0.] for i in range(2)]+[[far,far,0.]])])
    return {5:five,10:ten}


def place(q,a,x,y,extent):
    x0,x1,y0,y1=boxes.aabb(q)
    inside=(x0>=x-1e-9)&(x1<=x+extent+1e-9)&(y0>=y-1e-9)&(y1<=y+extent+1e-9)
    inter=(x1>x+1e-9)&(x0<x+extent-1e-9)&(y1>y+1e-9)&(y0<y+extent-1e-9)
    moved=a.copy();moved[:,:2]+=[x,y]
    crossing=inter&~inside
    gap=fc.worst_overlap(moved,q[crossing]) if crossing.any() else math.inf
    return inside,moved,gap,int(crossing.sum())


def control():
    a=primitives()[5];s=fc.frame(a)[0]
    q=np.array([[x,y,0.] for x,y in [(2.5,2.5),(2.5,2+s-.5),(2+s-.5,2.5),(2+s-.5,2+s-.5)]]+[[2+.1-1/math.sqrt(2),2+s/2,math.pi/4]])
    assert fc.worst_overlap(q)>-1e-10
    inside,moved,gap,crossing=place(q,a,2,2,s);candidate=np.vstack([q[~inside],moved])
    assert inside.sum()==4 and crossing==1 and gap>-1e-10 and fc.worst_overlap(candidate)>-1e-10
    assert len(candidate)==6
    bad=q.copy();bad[-1,0]+=.6
    _,_,badgap,_=place(bad,a,2,2,s);assert badgap<-.01,badgap
    print('CONTROL valid source with boundary-crossing square: clean-box test fails, exact replacement fits6; shifted intrusion fails',gap,badgap,flush=True)
    return dict(source_gap=fc.worst_overlap(q),positive_gap=gap,negative_gap=badgap,positive_n=6,crossing=1)


def write_primitives(directory):
    directory=Path(directory);directory.mkdir(exist_ok=True)
    code=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();out=[]
    snapshot=directory/('generator-'+code+'.py');snapshot.write_bytes(Path(__file__).read_bytes())
    for n,q in primitives().items():
        p=directory/(str(n)+'.csv');fc.write_csv(p,n,q)
        record=dict(n=n,source='our own design: analytic four axis corners and one 45-degree centre; ten adds five far-wall grid squares',licence='own analytic construction',generator=str(snapshot),generator_sha256=code,packing_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        Path(str(p)+'.json').write_text(json.dumps(record));out.append(record)
    return out



def read_template(root,item):
    p=Path(root)/item['relative'];payload=p.read_bytes()
    assert hashlib.sha256(payload).hexdigest()==item['sha256'], 'changed template bytes'
    n=int(item['n']);loaded=fr.layouts(p);assert set(loaded)=={n} and len(loaded[n])==n
    q=loaded[n];side,a=fc.frame(q)
    if item.get('source_sha256'):
        record=json.loads(Path(str(p)+'.json').read_text())
        assert record['n']==n and record['packing_sha256']==item['sha256']
        assert record['source_sha256']==item['source_sha256'], 'changed template source binding'
        assert len(record['parents'])==1 and record['parents'][0][1]==n
    else:assert np.max(np.abs(np.asarray(q)-primitives()[n]))<1e-12
    assert np.isfinite(a).all() and fc.worst_overlap(a)>-1e-8
    return side,a


def main(jobfile):
    job=json.loads(Path(jobfile).read_text());root=Path(job['root']);name=job.get('output','scan-box-intrusions30');assert Path(name).name==name and name.startswith('scan-');out=root/name/'raw';out.mkdir(parents=True,exist_ok=True)
    limit=min(float((root/'deadline.txt').read_text()),float(job['deadline']));signal.setitimer(signal.ITIMER_REAL,max(.1,limit-time.time()))
    (root/'scanner.pid').write_text(str(os.getpid()));proof=control();stats=dict(control=proof,hosts=[],attempts=0,near_intersections=0,exported=0,best_gap=None,max_overlap=job.get('max_overlap',.002));start=time.time()
    donors=[]
    donor_seen=set()
    for item in job['templates']:
        side,a=read_template(root,item)
        for sym,r in fr.sym8(a,side):
            canon=r.copy();canon[:,2]%=math.pi/2;canon=np.round(canon,10);canon=canon[np.lexsort((canon[:,2],canon[:,1],canon[:,0]))];key=hashlib.sha256(canon.tobytes()).hexdigest()
            if key not in donor_seen:donors.append((item,side,r,sym));donor_seen.add(key)
    bars={int(k):float(v) for k,v in job['sides'].items()};saved={}
    for host in job['hosts']:
        if time.time()>limit-5 or stats['exported']>=job.get('max_exports',math.inf):break
        p=root/'feed'/host['relative'];assert hashlib.sha256(p.read_bytes()).hexdigest()==host['sha256'];n=int(host['n']);side,q=fc.frame(fr.layouts(p)[n])
        if fc.worst_overlap(q)<-1e-6:continue
        x0,x1,y0,y1=boxes.aabb(q);up=np.abs(np.sin(2*q[:,2]))<1e-6
        anchors=np.unique(np.round(np.vstack([np.column_stack([x0[up],y0[up]]),np.column_stack([x1[up],y0[up]]),np.column_stack([x0[up],y1[up]]),np.column_stack([x1[up],y1[up]])]),7),axis=0)
        count=0
        for item,extent,a,sym in donors:
            if time.time()>limit-5 or stats['exported']>=job.get('max_exports',math.inf):break
            ns=int(item['n'])
            for dx,dy in [(0,0),(0,1),(1,0),(1,1)]:
                positions=anchors-[dx*extent,dy*extent]
                for x,y in positions:
                    if time.time()>limit-5 or stats['exported']>=job.get('max_exports',math.inf):break
                    if min(x,y)<-1e-8 or max(x+extent,y+extent)>side+1e-8:continue
                    inside=(x0>=x-1e-9)&(x1<=x+extent+1e-9)&(y0>=y-1e-9)&(y1<=y+extent+1e-9)
                    gain=ns-int(inside.sum());target=n+gain
                    if gain<=0 or target>1000 or side>=bars[target]-1e-7:continue
                    stats['attempts']+=1
                    inside,moved,gap,crossing=place(q,a,float(x),float(y),extent)
                    if crossing:stats['near_intersections']+=1
                    if stats['best_gap'] is None or gap>stats['best_gap']:
                        stats['best_gap']=gap;stats['closest']=dict(host=n,target=target,template=ns,box=[float(x),float(y)],gap=gap)
                    if gap < -stats['max_overlap']:continue
                    combined=np.vstack([q[~inside],moved]);actual,_=fc.frame(combined)
                    if actual>=bars[target]-1e-7:continue
                    digest=hashlib.sha256(np.round(combined,10).tobytes()).hexdigest()[:16]
                    if digest in saved:continue
                    if saved.get(target,0)>=2:continue
                    saved[digest]=True;saved[target]=saved.get(target,0)+1
                    name=f'{target}-insert30-{digest}-c.csv';dest=out/name;fc.write_csv(dest,target,combined)
                    parts=dict(n=target,side=actual,kind='interior box replacement with exact crossing-square checks',A=dict(source=[host['canonical'],n]),B=dict(source=[item['canonical'],ns],sym=sym),recipe=dict(box=[float(x),float(y),extent],removed=[int(i) for i in np.flatnonzero(inside)],crossing=crossing,gap=None if math.isinf(gap) else gap,host_sha256=host['sha256'],template_sha256=item['sha256']))
                    Path(str(dest)+'.json').write_text(json.dumps(parts));stats['exported']+=1;count+=1
        stats['hosts'].append(dict(n=n,source=host['canonical'],anchors=len(anchors),exports=count))
    stats['seconds']=time.time()-start;measurement=job.get('measurement','insert30-measurement.json');assert Path(measurement).name==measurement;(root/measurement).write_text(json.dumps(stats,indent=2));print(json.dumps(stats),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='control':control()
    elif sys.argv[1]=='primitives':print(json.dumps(write_primitives(sys.argv[2])))
    else:main(sys.argv[1])
