"""Compare the known false fit with the following-stack physical model."""
import copy,json,math,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_paths as C
import corner_stacks as K
assert json.load(open('corner-stacks-control.json'))['passed']
C.install();lib=M.Library('libbase');old=next(r for r in json.load(open('grid-probes.json'))if r['f']==.995)
n=old['n'];f=old['f'];ids=old['ids'];co,f1,f2=[lib.byid[k]for k in ids]
def inspect(P,q):
 side,gap=M.layout_state(P);g,A,B,phi=M.best_axes(P,M.pair_list(P,math.sqrt(2)+.001));i=int(M.np.argmin(g))
 bounds=[q['count'],q['count']+old['stacks'][0]*q['c1'],q['count']+old['stacks'][0]*q['c1']+old['stacks'][1]*q['c2']]
 bounds.extend([bounds[-1]+f1['q']['count'],bounds[-1]+f1['q']['count']+f2['q']['count']])
 def zone(k):return next((name for end,name in zip(bounds,['corner','run1','run2','far1','far2'])if k<end),'grid')
 return dict(side=side,gap=gap,worst_pair=[int(A[i]),int(B[i])],zones=[zone(A[i]),zone(B[i])],positions=P[[A[i],B[i]]].tolist())
reports=[]
for extra in[0,3]:
 if extra:K.install()
 qc=copy.deepcopy(co['q']);qc['extra_stacks']=extra
 start=time.time();P,why=M.assemble(None,n,dict(co,q=qc),f1,f2,*old['stacks'],f)
 r=dict(extra_stacks=extra,n=n,f=f,fit=P is not None,reason=why,seconds=time.time()-start)
 if P is not None:r.update(inspect(P,qc))
 reports.append(r);print('FOLLOWING STACKS PROBE',json.dumps(r),flush=True)
 if extra and P is not None and r['gap']>=-1e-7:
  name=f'{n}-following-stacks-grid-replay';out=Path('raw-a')/(name+'.csv');M.write_layout(str(out),n,P)
  qid=ids[0].replace('r30expand','r30stacks')
  meta=dict(n=n,built=r['side'],predicted=math.isqrt(n-1)+f,start=r['side'],stacks=old['stacks'],squeeze='following-stacks exact-knot replay',seconds={'stacks_probe':r['seconds']},modules=[dict(id=qid,source=qc['src']+'; corner with three following stacks (1, 0)',licence=qc['licence'])]+[dict(id=k,source=lib.byid[k]['q']['src'],licence=lib.byid[k]['q']['licence'])for k in ids[1:]])
  out.with_suffix('.json').write_text(json.dumps(meta));r['raw_file']=str(out)
 Path('stacks-grid-probes.json').write_text(json.dumps(reports,indent=2))
