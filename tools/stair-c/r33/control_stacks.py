"""Preserve complete source assemblies before adding following-stack obstacles."""
import hashlib,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_stacks as S
S.install();n=975;sq=M.np.asarray(M.read_layouts('control975.csv')[n],float);d,why=M.cut(sq,n);assert d is not None,why
measure=[]
for a,b in[(0,0),(1,0),(0,1),(1,1)]:
    e=E.expand(d,a,b);qc,q1,q2=E.corner(e,'own construction: following stacks control','our own','r30-stacks-control');qc.update(turn=True,extra_stacks=3)
    assert e['s1']>=4 and e['s2']>=4
    P0,mode0=S.ORIGINAL_STATE(qc,e['f'],qc['P'],qc['y0'],qc['x0'])
    P1,mode1=S.corner_state(qc,e['f'],qc['P'],qc['y0'],qc['x0'])
    assert len(P1)-len(P0)==3*(qc['c1']+qc['c2'])
    assert M.np.array_equal(P1[:len(P0)],P0)
    P,why=M.assemble(None,n,dict(q=qc),dict(q=q1),dict(q=q2),e['s1'],e['s2'],e['f']);assert P is not None,why
    side,gap=M.layout_state(P);assert gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
    mutant=P1.copy();mutant[-1]=mutant[0];assert not M.legal(mutant,mode1),'overlapping following-stack square escaped the local check'
    measure.append(dict(variant=[a,b],side=side,gap=gap,extra_bodies=len(P1)-len(P0)))
    print('CONTROL following stacks975',a,b,side,gap,'extra bodies',len(P1)-len(P0),flush=True)
Path('corner-stacks-control.json').write_text(json.dumps(dict(passed=True,n=n,variants=measure,helper_sha256=hashlib.sha256(Path('corner_stacks.py').read_bytes()).hexdigest())))
