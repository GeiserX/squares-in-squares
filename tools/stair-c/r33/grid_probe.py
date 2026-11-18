"""Check a tabulated knot that lies between the old start probes and the live bar."""
import csv,hashlib,json,math,os,pickle,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_paths as C
control=json.load(open('corner-paths-control.json'));assert control['passed']and control['helper_sha256']==hashlib.sha256(Path('corner_paths.py').read_bytes()).hexdigest()
C.install();lib=M.Library('libbase');bar={int(k):v for k,v in json.load(open('bar.json')).items()};chosen=None
for p in sorted(Path('raw-a').glob('*.nostart'),key=lambda p:p.stat().st_mtime,reverse=True):
    j=json.load(open(p));ids=j.get('ids',[])
    if j.get('bar_start_probe')and ids and ids[0]=='997r30expandd894cab8829f10.C'and set(ids)<=set(lib.byid):chosen=(p,j);break
assert chosen is not None,'no measured failed recipe'
p,j=chosen;n=j['n'];m=math.isqrt(n-1);ids=j['ids'];co,f1,f2=[lib.byid[k]for k in ids];reports=[]
for f in [.990,.995]:
    if m+f>=bar[n]:continue
    started=time.time();i=int(M.np.argmin(abs(M.FF-f)));pit1=1/math.cos(M.flush_tilt(co['q']['c1'],f));pit2=1/math.cos(M.flush_tilt(co['q']['c2'],f))
    model_y=m+f-j['stacks'][0]*pit1-f1['L'][i];model_x=m+f-j['stacks'][1]*pit2-f2['L'][i]
    pairs=[(float(y),float(x))for y,x in zip(co['Y'][:,i],co['X'][:,i])]
    fit_costs=[k for k,(y,x)in enumerate(pairs)if y<=model_y+1e-9 and x<=model_x+1e-9]
    actual1=M.far_at(f1['q'],f);actual2=M.far_at(f2['q'],f)
    r=dict(n=n,f=f,source=str(p),ids=ids,stacks=j['stacks'],table_corner=pairs,table_caps=[float(model_y),float(model_x)],table_fit_costs=fit_costs,table_far=[float(f1['L'][i]),float(f2['L'][i])],actual_far=[None if actual1 is None else float(actual1[0]),None if actual2 is None else float(actual2[0])])
    P,why=M.assemble(None,n,co,f1,f2,*j['stacks'],f);r.update(fit=P is not None,reason=why,seconds=time.time()-started)
    if P is not None:
        side,gap=M.layout_state(P);r.update(side=side,gap=gap)
        if gap>=-1e-7 and side<bar[n]-1e-8:
            name=f'{n}-grid-knot-{int(f*10000)}-'+hashlib.sha256(repr(ids+j['stacks']).encode()).hexdigest()[:12]
            out=Path('raw-a')/(name+'.csv');M.write_layout(str(out),n,P)
            meta=dict(n=n,built=side,predicted=m+f,start=side,stacks=j['stacks'],squeeze='exact table knot assembly',seconds={'grid_probe':r['seconds']},modules=[dict(id=k,source=lib.byid[k]['q']['src'],licence=lib.byid[k]['q']['licence'])for k in ids])
            out.with_suffix('.json').write_text(json.dumps(meta));r['raw_file']=str(out)
    reports.append(r);Path('grid-probes.json').write_text(json.dumps(reports,indent=2));print('GRID PROBE',json.dumps(r),flush=True)
