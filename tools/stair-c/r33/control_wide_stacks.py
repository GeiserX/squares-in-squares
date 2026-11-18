"""Check larger whole-stack cuts against an exact complete packing."""
import copy,hashlib,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_stacks as K
K.install()
VARIANTS=[(4,0),(0,4),(4,1),(1,4),(4,4),(5,0),(0,5),(5,5)]
sq=M.np.asarray(M.read_layouts('control975.csv')[975],float);d,why=M.cut(sq,975);assert d is not None,why
rows=[]
for a,b in VARIANTS:
 e=E.expand(d,a,b);assert min(e['s1'],e['s2'])>=4
 c,f1,f2=E.corner(e,'own construction: wide-stack control','our own',f'r33-wide-control-{a}{b}')
 c.update(turn=True,extra_stacks=3)
 P,why=M.assemble(None,975,dict(q=c),dict(q=f1),dict(q=f2),e['s1'],e['s2'],e['f']);assert P is not None,why
 side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(a,b,side,gap)
 rows.append(dict(variant=[a,b],side=side,gap=gap,corner_count=c['count']))
 print('CONTROL wide stacks975',a,b,side,gap,flush=True)
bad=copy.deepcopy(d);bad['zone'][M.np.flatnonzero(bad['zone']=='S1')[0]]='C'
try:E.expand(bad,4,0)
except AssertionError:pass
else:raise AssertionError('partial wide-stack transfer accepted')
Path('wide-stacks-control.json').write_text(json.dumps(dict(passed=True,variants=rows,helper_sha256=hashlib.sha256(Path('corner_stacks.py').read_bytes()).hexdigest())))
print('CONTROL eight wide975 assemblies pass; partial-stack mutant refused',flush=True)
