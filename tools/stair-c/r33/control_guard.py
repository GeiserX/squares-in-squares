"""Check full-layout preservation and reject the observed escaped corner state."""
import copy,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_guard as G
n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
G.install()
for a,b in[(0,0),(1,0),(0,1),(1,1)]:
    e=E.expand(d,a,b);qc,q1,q2=E.corner(e,'own construction: cut guard control','our own','r30-guard-control');qc['turn']=True;qc=G.tag(qc)
    assert G.valid(qc,e['f'],qc['P'],qc['y0'],qc['x0'])
    P,why=M.assemble(None,n,dict(q=qc),dict(q=q1),dict(q=q2),e['s1'],e['s2'],e['f'])
    assert P is not None,why
    side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
    print('CONTROL guard975',a,b,side,gap,flush=True)
    changed=qc['P'].copy();changed[:,1]+=10
    assert not G.valid(qc,e['f'],changed,qc['y0'],qc['x0'])
lib=M.Library('libbase');q=copy.deepcopy(lib.byid['997r30expandd894cab8829f10.C']['q']);guarded=G.tag(q)
at=G.ORIGINAL_LEN(q,q['f0'],q['P'],q['y0']+1e-6,q['x0']+1e-6,(1.,.02))
for f in M.path(q['f0'],.995):
    assert at is not None
    at=G.ORIGINAL_LEN(q,float(f),at[2],at[0]+.02,at[1]+.02,(1.,.02))
assert at is not None and not G.valid(guarded,.995,at[2],at[0],at[1]),'observed escape not refused'
print('CONTROL observed997 escape refused at .995; y0/x0',at[:2],flush=True)
Path('corner-guard-control.json').write_text(json.dumps(dict(passed=True,n=975,variants=4,escaped_y0=float(at[0]),escaped_x0=float(at[1]))))
