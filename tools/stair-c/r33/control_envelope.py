"""Require an actual repaired native805 witness before any new build."""
import hashlib,json,sys,math
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import stair_finesafe as F
import expanded as E
import corner_paths as C
C.install();original=M.assemble
import slide_envelope as S
S.install();rows=[]
for n,path,variants in [(975,'control975.csv',[(0,0),(4,4)]),(805,'donors/805-native-held.csv',[(4,4),(5,5),(4,0),(0,4)])]:
 sq=M.np.asarray(M.read_layouts(path)[n],float);d,why=M.cut(sq,n);assert d is not None,why
 for a,b in variants:
  e=E.expand(d,a,b);c,f1,f2=E.corner(e,'own construction: core slide envelope control','our own',f'r33-envelope-control-{n}-{a}{b}');c['turn']=True
  bump=0. if n==975 else .0001
  args=(None,n,dict(q=c),dict(q=f1),dict(q=f2),e['s1'],e['s2'],e['f']+bump)
  old,oldwhy=original(*args);P,why=M.assemble(*args)
  r=dict(n=n,variant=[a,b],bump=bump,old_fit=old is not None,old_reason=oldwhy,fit=P is not None,reason=why)
  if P is not None:
   side,gap=M.layout_state(P);r.update(side=side,gap=gap,legal=bool(gap>=-1e-7 and side<=d['s']+bump+3e-6))
   bad=P.copy();bad[1]=bad[0];assert M.layout_state(bad)[1]<-.99
   if n==805 and r['legal']:
    raw=[dict(n=str(n),square_id=str(i),x=repr(float(v[0])),y=repr(float(v[1])),angle=repr(float(v[2])))for i,v in enumerate(P)]
    _,safe,score,error=F.work((n,raw));assert safe is not None,error
    clearance=F.fs.clearance(safe);assert clearance>=2.2e-11
    broken=[dict(v)for v in safe];broken[1]=dict(broken[0]);assert F.work((n,broken))[1]is None
    r.update(certified=True,certified_side=(1+score)*math.sqrt(n),certified_clearance=clearance)

  else:r['legal']=False
  if n==975:assert r['legal'],r
  rows.append(r);print('ENVELOPE CONTROL',json.dumps(r),flush=True)
witnesses=[r for r in rows if r['n']==805 and r['legal']and not r['old_fit']]
report=dict(passed=bool(witnesses),positive975=True,duplicate_rejected=True,results=rows,witnesses=witnesses,certified805_witnesses=sum(bool(r.get('certified'))for r in witnesses),helper_sha256=hashlib.sha256(Path('slide_envelope.py').read_bytes()).hexdigest())
Path('slide-envelope-control.json').write_text(json.dumps(report,indent=2));assert witnesses,'core slide envelope supplied no legal805 witness'
print('CONTROL repaired native805 passes full SAT; native975 retained; duplicate rejected',flush=True)
