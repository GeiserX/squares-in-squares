"""Check two-stack transfers against the whole source layout and its run model."""
import copy,hashlib,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_stacks as K
assert json.load(open('corner-stacks-control.json'))['passed']
K.install();n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
results=[]
for a,b in[(2,0),(0,2),(2,2)]:
    e=E.expand(d,a,b);qc,q1,q2=E.corner(e,'own construction: two-stack control','our own','r29-two-stacks-control');qc.update(turn=True,extra_stacks=3)
    assert e['s1']>=4 and e['s2']>=4
    P,why=M.assemble(None,n,dict(q=qc),dict(q=q1),dict(q=q2),e['s1'],e['s2'],e['f']);assert P is not None,why
    side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
    results.append(dict(variant=[a,b],side=side,gap=gap,corner_count=qc['count']))
    print('CONTROL two stacks975',a,b,side,gap,'corner count',qc['count'],flush=True)
bad=copy.deepcopy(d);bad['zone'][M.np.flatnonzero(bad['zone']=='S1')[0]]='C'
try:E.expand(bad,2,0)
except AssertionError:pass
else:raise AssertionError('incomplete two-stack transfer accepted')
Path('two-stacks-control.json').write_text(json.dumps(dict(passed=True,variants=results,helper_sha256=hashlib.sha256(Path('corner_stacks.py').read_bytes()).hexdigest())))
print('CONTROL incomplete two-stack mutant rejected',flush=True)
