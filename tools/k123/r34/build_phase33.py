"""Extend the finite offset domains and keep auxiliary states only where allowed."""
from pathlib import Path
W=Path(__file__).resolve().parent;s=(W/'slide_strip32.py').read_text();s=s.replace('"""Choose discrete row slides and column slips with all tilted sites retained."""','"""Choose integer parent phases as well as learned fractional row and column offsets."""')
s=s.replace('force_row32=None):','force_row32=None,parent_phases33=None,force_phases33=None):')
start=s.index(' # Fixed outside parents retain their exact learned level.')
end=s.index(' if force_row32:',start)
block=s[start:end]
block=block.replace("  result=set(np.argsort(np.abs(levels-ref))[:count]) if count and ref is not None else set(range(len(levels)))", "  result=set()\n  if count and ref is not None:\n   for phase33 in (parent_phases33 or [0.]):result.update(np.argsort(np.abs(levels-ref-phase33))[:count])\n  else:result=set(range(len(levels)))")
s=s[:start]+s[end:]
needle=' ns,nr=len(Slev),len(Rlev);sr=b*ns;sc=a*nr;up=[];m=int(L);optional=max_drop>0'
s=s.replace(needle, " ns,nr=len(Slev),len(Rlev)\n"+block+" state33={cell:[(si,rr) for si in sorted(SA32[int(jj)]) for rr in sorted(RA32[int(ii)])] for cell,(ii,jj) in enumerate(sites)}\n nz33=sum(len(x) for x in state33.values())\n sr=b*ns;sc=a*nr;up=[];m=int(L);optional=max_drop>0")
s=s.replace('nv=zbase+len(sites)*ns*nr;', 'nv=zbase+nz33;')
s=s.replace(' wall_states=set();collision_rows=0\n for cell,(i,j) in enumerate(sites):\n  zb=zbase+cell*ns*nr\n  for si in range(ns):add([zb+si*nr+rr for rr in range(nr)]+[int(j)*ns+si],[1.]*nr+[-1.],-np.inf if optional else 0.,0.)\n  for rr in range(nr):add([zb+si*nr+rr for si in range(ns)]+[sr+int(i)*nr+rr],[1.]*ns+[-1.],-np.inf if optional else 0.,0.)\n  if optional:add(list(range(zb,zb+ns*nr))+[wbase+cell],[1.]*(ns*nr)+[-1.],0.,0.)', ''' wall_states=set();collision_rows=0;nextz33=zbase
 for cell,(i,j) in enumerate(sites):
  zz33={state:nextz33+k for k,state in enumerate(state33[cell])};nextz33+=len(zz33)
  for si in sorted(SA32[int(j)]):
   zlist33=[zz33[si,rr] for rr in sorted(RA32[int(i)])];add(zlist33+[int(j)*ns+si],[1.]*len(zlist33)+[-1.],-np.inf if optional else 0.,0.)
  for rr in sorted(RA32[int(i)]):
   zlist33=[zz33[si,rr] for si in sorted(SA32[int(j)])];add(zlist33+[sr+int(i)*nr+rr],[1.]*len(zlist33)+[-1.],-np.inf if optional else 0.,0.)
  if optional:add(list(zz33.values())+[wbase+cell],[1.]*len(zz33)+[-1.],0.,0.)''')
s=s.replace('wall_states.add(zb+si*nr+rr)', 'wall_states.add(zz33[si,rr])').replace('.append(zb+si*nr+rr)', '.append(zz33[si,rr])')
s=s.replace(' tree=cKDTree(up)', ''' if force_phases33 is not None:
  assert reference is not None
  for jj in range(b):
   si=int(np.argmin(np.abs(Slev-reference['S'][jj]-force_phases33[0])));assert abs(Slev[si]-reference['S'][jj]-force_phases33[0])<1e-7
   add([jj*ns+si],[1.],1.,1.)
  for ii in range(a):
   rr=int(np.argmin(np.abs(Rlev-reference['R'][ii]-force_phases33[1])));assert abs(Rlev[rr]-reference['R'][ii]-force_phases33[1])<1e-7
   add([sr+ii*nr+rr],[1.],1.,1.)
 tree=cKDTree(up)''')
s=s.replace("'origin32':np.asarray(O).tolist()", "'phase_offsets33':parent_phases33,'active_joint_states33':nz33,'origin32':np.asarray(O).tolist()")
s=s.replace(" assert json.load((R/'slide-control31.json').open())['positive_control_passed']", " if not j.get('learned_control'):assert json.load((R/'phase-control33.json').open())['passed']")
needle=" O=O+j.get('origin_shift_u32',0.)*u+j.get('origin_shift_v32',0.)*v"
s=s.replace(needle,""" phases33=j.get('parent_phases33',[0.])
 Slevels=cluster(np.concatenate([Slevels+phase for phase in phases33]));Rlevels=cluster(np.concatenate([Rlevels+phase for phase in phases33]))
"""+needle)
s=s.replace("free_columns32=free_cols32,free_cells32=free_cells32)","free_columns32=free_cols32,free_cells32=free_cells32,parent_phases33=phases33,force_phases33=j.get('force_phases33'))")
s=s.replace("R/'out/slidestrip32'", "R/'out/phase33'").replace('slide_strip32.py constructive discrete row/column slides','slide_phase33.py constructive row/column slides and integer parent phases')
assert 'zb+si*nr+rr' not in s and 'zb=zbase+cell*ns*nr' not in s
(W/'slide_phase33.py').write_text(s)
import ast
ast.parse(s);print('phase33 generated',len(s.splitlines()),'lines')
