"""Apply round33 public-only geometry checks to pinned source bytes."""
import csv
import functools
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import zipfile
import numpy as np
from scipy.spatial import cKDTree
L=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(L/'tools/harvest26'))
import audit_ac as A
S=Path('$SCRATCH/bounties-squares')
REFERENCE_ANGLES={}
SEED_ANGLES=[]


def share(a,b):
    """Use the frozen assembler's corner/centre boxes and median-offset ICP."""
    import importlib.util
    if '_assembler' not in globals():
        spec=importlib.util.spec_from_file_location('harvest33_assembler_share',S/'take-assemble-r31/scripts/share31.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.TOLS=(1e-6,1e-3,1e-2)
        globals()['_assembler']=module
    a=np.asarray(a);b=np.asarray(b)
    if a.shape[1]==2:a=np.column_stack((a,np.zeros(len(a))))
    if b.shape[1]==2:b=np.column_stack((b,np.zeros(len(b))))
    result=_assembler.share(a,b)
    return result[1e-6],result[1e-3],result[1e-2],None


@functools.lru_cache(maxsize=1)
def archive_paths():
    paths=[p/'ds/prvsiyan__squares-verified-best-of-1105/data.zip' for p in sorted(S.glob('harvest*')) if (p/'ds/prvsiyan__squares-verified-best-of-1105/data.zip').is_file()]
    for lane in sorted(S.glob('take-harvest-r*')):
        work=lane/'work'
        for public in sorted(work.glob('public*')):
            folder=public/'data/ds/prvsiyan__squares-verified-best-of-1105'
            p=folder/'data.zip'
            if p.is_file():paths.append(p)
    legacy=S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    if legacy not in paths:paths.append(legacy)
    return tuple(paths)


@functools.lru_cache(maxsize=1)
def references():
    versions=[];seen=set()
    for p in archive_paths():
        raw=p.read_bytes();key=hashlib.sha256(raw).hexdigest()
        if key in seen:continue
        seen.add(key);coords={};angles={}
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=[n for n in z.namelist() if Path(n).name=='submission.csv']
            if len(names)!=1:raise ValueError('ambiguous1105 comparison archive')
            with z.open(names[0]) as stream:
                for r in csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8-sig')):
                    coords.setdefault(int(r['n']),[]).append((float(r['x']),float(r['y'])))
                    angles.setdefault(int(r['n']),[]).append(float(r['angle']))
        normalized={}
        for n,rows in coords.items():
            a=np.array(rows)
            if len(a)==n:
                normalized[n]=a-(a.min(0)+a.max(0))/2
                REFERENCE_ANGLES[id(normalized[n])]=np.array(angles[n])
        versions.append((str(p)+' sha256 '+key,normalized))
    return versions


def prvsiyan():return references()[-1][1]


@functools.lru_cache(maxsize=1)
def own_seeds():
    seeds=[]
    for name in ('samanyu_22249.csv','samanyu_bestfit.csv'):
        coords={};angles={}
        with (S/'seeds'/name).open() as f:
            for r in csv.DictReader(f):
                coords.setdefault(int(r['n']),[]).append((float(r['x']),float(r['y'])))
                angles.setdefault(int(r['n']),[]).append(float(r['angle']))
        SEED_ANGLES.append({n:np.array(rows) for n,rows in angles.items()})
        seeds.append({n:(a:=np.array(rows))-(a.min(0)+a.max(0))/2 for n,rows in coords.items() if len(rows)==n})
    return seeds


def is_own_reference(n,target):
    # Equality uses all centres at decimal-export tolerance. This is not a
    # fractional share gate on an own layout.
    target_angles=REFERENCE_ANGLES.get(id(target))
    if target_angles is None:return False
    for index,seeds in enumerate(own_seeds()):
        seed=seeds.get(n)
        if seed is None:continue
        tree=cKDTree(seed)
        for swap in (False,True):
            for sx in (-1,1):
                for sy in (-1,1):
                    c=(target[:,::-1] if swap else target)*[sx,sy]
                    distances,indices=tree.query(c)
                    if float(distances.max())>=1e-7:continue
                    axes=np.column_stack((np.cos(target_angles),np.sin(target_angles)))
                    axes=(axes[:,::-1] if swap else axes)*[sx,sy]
                    transformed=np.arctan2(axes[:,1],axes[:,0])
                    delta=(transformed-SEED_ANGLES[index][n][indices]+np.pi/4)%(np.pi/2)-np.pi/4
                    if float(np.abs(delta).max())<1e-7:return True
    return False


@functools.lru_cache(maxsize=1000)
def excluded(n):
    # Round31 override2 explicitly identifies every harvested1105 version at228
    # as our own Samanyu layout. No geometric share check runs on that row.
    if n==228:return []
    out=[('comparison1105 version '+label.rsplit(' sha256 ',1)[-1],np.column_stack((data[n],REFERENCE_ANGLES[id(data[n])]))) for label,data in references() if n in data and not is_own_reference(n,data[n])]
    if n in (639,691,745,858,918,980):
        out += [(label,np.array([[float(r[k]) for k in ('x','y','angle')] for r in rows])) for label,rows in A.excluded(n) if not label.startswith('prvsiyan')]
    return out


def audit(rows):
    n=int(rows[0]['n']);centres=np.array([[float(r['x']),float(r['y']),float(r.get('angle',0))] for r in rows]);evidence=[]
    import geometry_cache as cache
    targets=excluded(n);identity=cache.key(n,centres,targets)
    found=cache.lookup(identity)
    if found is not None:return bool(found[0]),found[1]
    for label,target in targets:
        s=share(centres,target)
        evidence.append(dict(label=label,share1e6=s[0],share1e3=s[1],share1e2=s[2],maxd=s[3]))
    result=(not any(max(r['share1e3'],r['share1e2'])>=.4 for r in evidence),evidence)
    cache.put(identity,result)
    return result


def snapshot(src,directory):
    src=Path(src);raw=src.read_bytes();key=hashlib.sha256(raw).hexdigest()
    dst=Path(directory)/f'{src.stem}-{key[:16]}{src.suffix}';dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        if hashlib.sha256(dst.read_bytes()).hexdigest()!=key:raise ValueError('snapshot changed')
    else:
        temporary=Path(str(dst)+'.tmp-'+str(os.getpid()))
        try:temporary.write_bytes(raw);temporary.replace(dst)
        finally:
            if temporary.exists():temporary.unlink()
    return dst,key


def control():
    rows=A.read(str(S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'),[858])[858]
    ok,e=audit(rows);assert not ok and max(r['share1e3'] for r in e)==1,e
    independent=[dict(n=453,x=2*(i%22),y=2*(i//22),angle=0) for i in range(453)]
    ok3,e3=audit(independent);assert ok3,e3
    a=np.array([[float(r[k]) for k in ('x','y','angle')] for r in rows]);shifted=a.copy()
    shifted[:,:2]+=np.random.default_rng(31).uniform(-.003,.003,(len(a),2));shifted[:len(a)//5,:2]+=.7
    moved=share(shifted,a);assert moved[1]<.4 and moved[2]>.4,moved
    measured={}
    for n,stem,expected in [(851,'851-public31-985c28a4e8027701',False),(972,'972-public31-6ec80099934d2273',False),(852,'852-public31-4a1ebdb196a8d237',True),(588,'588-public31-22274a69cdb580c5',True)]:
        p=S/'take-harvest-r31/near'/(stem+'.csv')
        if not p.exists():p=S/'take-harvest-r31/work/direct-source-held'/p.name
        ok,ev=audit(list(csv.DictReader(p.open())))
        measured[n]=dict(allowed=ok,share1e3=max((v['share1e3'] for v in ev),default=0.),share1e2=max((v['share1e2'] for v in ev),default=0.))
        assert ok==expected,measured[n]
    assert abs(measured[851]['share1e2']-.46415981198589895)<1e-12
    assert abs(measured[972]['share1e2']-.45267489711934156)<1e-12,measured[972]
    assert excluded(228)==[]
    equality972=[is_own_reference(972,refs[972]) for _,refs in references()]
    assert any(equality972) and not all(equality972),equality972
    print('CONTROL assembler median-ICP: exact858 and moved-copy refuse; spaced453 passes; owned588/228 exempt; public851/972 refuse,852 passes: '+json.dumps(measured),flush=True)
    return e,measured

if __name__=='__main__':control()
