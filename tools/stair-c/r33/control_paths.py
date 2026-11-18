"""Test all-path corner fitting on a full packing before probing failed recipes."""
import glob,hashlib,json,math,os,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import corner_paths as C
import expanded as E
import modules as M
C.branch_control();C.install()
n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
for a,b in[(0,0),(1,0),(0,1),(1,1)]:
    e=E.expand(d,a,b);qc,q1,q2=E.corner(e,'own construction: corner path control','our own','r30-path-control');qc['turn']=True
    if(a,b)==(0,0):
        M.corner_at=C.ORIGINAL
        lost,_=M.assemble(None,n,dict(q=qc),dict(q=q1),dict(q=q2),e['s1'],e['s2'],e['f'])
        assert lost is None,'original rotating fitter should reproduce the lost valid start'
        C.install()
    P,why=M.assemble(None,n,dict(q=qc),dict(q=q1),dict(q=q2),e['s1'],e['s2'],e['f'])
    assert P is not None,why
    side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
    print('CONTROL real975 all paths',a,b,'side',side,'gap',gap,flush=True)
assert M.corner_at(qc,float(d['f']),0.,0.)is None
Path('corner-paths-control.json').write_text(json.dumps(dict(passed=True,n=975,variants=4,helper_sha256=hashlib.sha256(Path('corner_paths.py').read_bytes()).hexdigest())))
lib=M.Library('libbase');bar={int(k):v for k,v in json.load(open('bar.json')).items()};results=[]
for p in sorted(glob.glob('raw-a/*.nostart'),key=os.path.getmtime,reverse=True):
    j=json.load(open(p));ids=j.get('ids',[])
    if not j.get('bar_start_probe')or not ids or'r30expand'not in ids[0]or not set(ids)<=set(lib.byid):continue
    n=j['n'];m=math.isqrt(n-1);f=min(.9999,bar[n]-m)
    args=(None,n,*[lib.byid[k]for k in ids],*j['stacks'],f)
    M.corner_at=C.ORIGINAL
    old,oldwhy=M.assemble(*args)
    C.install();P,why=M.assemble(*args);item=dict(n=n,ids=ids,old_reason=oldwhy,new_reason=why,fit=P is not None)
    if P is not None:
        side,gap=M.layout_state(P);item.update(side=side,gap=gap)
        if gap>=-1e-7:
            folder=Path('path-starts');folder.mkdir(exist_ok=True);out=folder/Path(p).with_suffix('.csv').name;M.write_layout(str(out),n,P)
            item.update(file=str(out),stacks=j['stacks'],f=f)
    results.append(item);print('PATH PROBE',json.dumps(item),flush=True)
    if len(results)>=2:break
Path('corner-paths-probes.json').write_text(json.dumps(results,indent=2))
