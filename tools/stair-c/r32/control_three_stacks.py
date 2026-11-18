"""Check larger coupled stack transfers before tabulating fresh physical corners."""
import copy,hashlib,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_stacks as K
K.install();n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
results=[]
for a,b in[(1,2),(2,1),(3,0),(0,3),(3,1),(1,3),(3,2),(2,3),(3,3)]:
 e=E.expand(d,a,b);c,f1,f2=E.corner(e,'own construction: coupled stack control','our own','r32-three-stacks-control');c.update(turn=True,extra_stacks=3)
 assert min(e['s1'],e['s2'])>=4
 P,why=M.assemble(None,n,dict(q=c),dict(q=f1),dict(q=f2),e['s1'],e['s2'],e['f']);assert P is not None,why
 side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(a,b,side,gap)
 results.append(dict(variant=[a,b],side=side,gap=gap,corner_count=c['count']))
 print('CONTROL coupled stacks975',a,b,side,gap,flush=True)
bad=copy.deepcopy(d);bad['zone'][M.np.flatnonzero(bad['zone']=='S1')[0]]='C'
try:E.expand(bad,3,0)
except AssertionError:pass
else:raise AssertionError('partial three-stack transfer accepted')
Path('three-stacks-control.json').write_text(json.dumps(dict(passed=True,variants=results,helper_sha256=hashlib.sha256(Path('corner_stacks.py').read_bytes()).hexdigest())))
print('CONTROL nine coupled assemblies passed; partial-stack mutant refused',flush=True)
