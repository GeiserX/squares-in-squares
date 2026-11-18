"""Measure whether the no-slide guard rejects any complete legal native layout."""
import ast,copy,hashlib,inspect,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_paths as C
C.install()
original=M.assemble;tree=ast.parse(inspect.getsource(original));changed=0
class Relax(ast.NodeTransformer):
 def visit_Return(self,node):
  global changed
  if isinstance(node.value,ast.Tuple)and any(isinstance(v,ast.Constant)and v.value=='the corner grants a far zone no slide'for v in node.value.elts):
   changed+=1;return ast.copy_location(ast.Pass(),node)
  return node
tree=Relax().visit(tree);ast.fix_missing_locations(tree);assert changed==1
ns=dict(M.__dict__);exec(compile(tree,'slide-guard-probe','exec'),ns);relaxed=ns['assemble']
results=[]
for n,path,variants in [(975,'control975.csv',[(0,0),(4,4)]),(805,'donors/805-native-held.csv',[(4,4),(5,5),(4,0),(0,4)])]:
 sq=M.np.asarray(M.read_layouts(path)[n],float);d,why=M.cut(sq,n);assert d is not None,why
 for a,b in variants:
  for bump in ([0.]if n==975 else[0.,.0001,.0002,.0003]):
   e=E.expand(d,a,b);c,f1,f2=E.corner(e,'own construction: slide guard probe','our own',f'r33-slide-probe-{n}-{a}{b}');c['turn']=True
   args=(None,n,dict(q=c),dict(q=f1),dict(q=f2),e['s1'],e['s2'],e['f']+bump)
   old,reason=original(*args);candidate,why=relaxed(*args)
   record=dict(n=n,variant=[a,b],fraction_bump=bump,old_fit=old is not None,old_reason=reason,relaxed_fit=candidate is not None,new_reason=why)
   if candidate is not None:
    side,gap=M.layout_state(candidate);legal=bool(len(candidate)==n and gap>=-1e-7 and side<=d['s']+bump+2e-6)
    record.update(side=side,gap=gap,legal=legal)
    bad=candidate.copy();bad[1]=bad[0];assert M.layout_state(bad)[1]<-.99
   else:record['legal']=False
   if n==975:assert record['legal'],record
   results.append(record);print('SLIDE GUARD PROBE',json.dumps(record),flush=True)
report=dict(passed=True,positive975=True,duplicate_rejected=True,changed_guard_count=changed,results=results,legal805_witnesses=[r for r in results if r['n']==805 and r['legal']and not r['old_fit']])
Path('slide-guard-probe.json').write_text(json.dumps(report,indent=2))
