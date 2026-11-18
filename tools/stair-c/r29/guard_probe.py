"""Replay the measured escaped table fit with the new cut-constrained corner."""
import csv,json,math,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_guard as G
assert json.load(open('corner-guard-control.json'))['passed']
G.install();lib=M.Library('libbase');rows=json.load(open('grid-probes.json'))
old=next(r for r in rows if r['f']==.995);ids=list(old['ids']);ids[0]=ids[0].replace('r29expand','r29guard')
assert set(ids)<=set(lib.byid),ids
n=old['n'];f=old['f'];m=math.isqrt(n-1);co,f1,f2=[lib.byid[k]for k in ids]
i=int(M.np.argmin(abs(M.FF-f)));caps=old['table_caps']
pairs=[(float(y),float(x))for y,x in zip(co['Y'][:,i],co['X'][:,i])]
fits=[k for k,(y,x)in enumerate(pairs)if y<=caps[0]+1e-9 and x<=caps[1]+1e-9]
start=time.time();P,why=M.assemble(None,n,co,f1,f2,*old['stacks'],f)
r=dict(n=n,f=f,old_gap=old.get('gap'),new_table_corner=pairs,table_caps=caps,table_fit_costs=fits,fit=P is not None,reason=why,seconds=time.time()-start,ids=ids)
if P is not None:
 side,gap=M.layout_state(P);r.update(side=side,gap=gap)
 # A legal replay remains a real candidate and goes through certified-file fq.
 if gap>=-1e-7:
  name=f'{n}-guard-grid-replay';out=Path('raw-a')/(name+'.csv');M.write_layout(str(out),n,P)
  meta=dict(n=n,built=side,predicted=m+f,start=side,stacks=old['stacks'],squeeze='guarded exact-knot replay',seconds={'guard_probe':r['seconds']},modules=[dict(id=k,source=lib.byid[k]['q']['src'],licence=lib.byid[k]['q']['licence'])for k in ids])
  out.with_suffix('.json').write_text(json.dumps(meta));r['raw_file']=str(out)
Path('guard-grid-probes.json').write_text(json.dumps(r,indent=2));print('GUARD GRID PROBE',json.dumps(r),flush=True)
