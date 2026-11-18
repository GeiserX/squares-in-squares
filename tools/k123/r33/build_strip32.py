from pathlib import Path
W=Path(__file__).resolve().parent;s=(W/'slide_milp31.py').read_text().replace('slide_milp31.py','slide_strip32.py').replace("R/'out/slidemilp31'","R/'out/slidestrip32'")
s=s.replace('mask_bias=0.):','mask_bias=0.,free_rows32=None,free_columns32=None,free_cells32=None,force_row32=None):')
s=s.replace(' tree=cKDTree(up)',''' # Fixed outside parents retain their exact learned level. Free parents keep the selected neighborhood.
 if free_rows32 is not None or free_columns32 is not None:assert reference is not None
 def allowed32(levels,ref,count,is_free):
  if not is_free:
   idx=int(np.argmin(np.abs(levels-ref)));assert abs(levels[idx]-ref)<1e-7
   return {idx}
  result=set(np.argsort(np.abs(levels-ref))[:count]) if count and ref is not None else set(range(len(levels)))
  if zero_choice:result.add(int(np.argmin(np.abs(levels))))
  return result
 SA32={j:allowed32(Slev,reference['S'][j] if reference else None,local_choices,free_rows32 is None or j in free_rows32) for j in range(b)}
 RA32={i:allowed32(Rlev,reference['R'][i] if reference else None,local_choices,free_columns32 is None or i in free_columns32) for i in range(a)}
 if force_row32:
  for jj,si in force_row32.items():add([int(jj)*ns+int(si)],[1.],1.,1.)
 tree=cKDTree(up)''',1)
s=s.replace('  for si,S in enumerate(Slev):\n   for rr,Rv in enumerate(Rlev):','  for si in sorted(SA32[int(j)]):\n   S=Slev[si]\n   for rr in sorted(RA32[int(i)]):\n    Rv=Rlev[rr]')
a=s.index(' if local_choices and reference:');b=s.index(' if reference:\n  for j in range(b):c[',a)
s=s[:a]+''' for jj,allowed in SA32.items():
  for si in range(ns):
   if si not in allowed:bounds_hi[jj*ns+si]=0
 for ii,allowed in RA32.items():
  for rr in range(nr):
   if rr not in allowed:bounds_hi[sr+ii*nr+rr]=0
 bounds_lo=np.zeros(nv)
 if free_cells32 is not None:
  assert optional,'strip occupancy requires optional cells'
  cells={tuple(c) for c in free_cells32}
  for cell,(ii,jj) in enumerate(sites):
   if (int(ii),int(jj)) not in cells:
    value=1. if mask_core is None or (mask_core[0]<=ii<mask_core[1] and mask_core[2]<=jj<mask_core[3]) else 0.
    bounds_lo[wbase+cell]=bounds_hi[wbase+cell]=value
'''+s[b:]
s=s.replace('bounds=Bounds(np.zeros(nv),bounds_hi)','bounds=Bounds(bounds_lo,bounds_hi)')
s=s.replace("report={'code_sha256':CODE_SHA31,", "report={'strip_free_rows32':free_rows32,'strip_free_columns32':free_columns32,'strip_free_cells32':free_cells32,'code_sha256':CODE_SHA31,")
s=s.replace(" if j.get('convex_control31'):",''' if j.get('strip_bound_control32'):
  args=(4.5,np.array([(0,0),(1,0)]),math.pi/4,np.array([2.25,2.25]),np.array([-.1,0.,.1]),np.array([0.]),2,10)
  kw=dict(reference={'S':np.array([0.]),'R':np.array([0.,0.])},exact_count=True,max_drop=1,free_rows32=[],free_columns32=[],free_cells32=[])
  r0,q0=solve(*args,**kw);r1,q1=solve(*args,**kw,force_row32={0:2})
  good=q0 is not None and len(q0)==2 and r0['tilted_selected']==2 and mlp.min_gap(q0)>-1e-7 and q1 is None and r1['status']==2
  result={'positive':r0,'wrong_fixed_row_refused':r1,'strip_bound_control_passed32':bool(good)};(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True);assert good;return
 if j.get('convex_control31'):''')
s=s.replace("  report,Q=solve(L,sites,theta,O,Slevels,Rlevels,j['n'],", """  free_rows32=j.get('free_rows32');free_cols32=j.get('free_columns32')
  free_cells32=([list(map(int,(ii,jj))) for ii,jj in sites if (free_rows32 is not None and int(jj) in free_rows32) or (free_cols32 is not None and int(ii) in free_cols32)] if j.get('strip32') else None)
  report,Q=solve(L,sites,theta,O,Slevels,Rlevels,j['n'],""")
s=s.replace("mask_bias=j.get('mask_bias',0.))", "mask_bias=j.get('mask_bias',0.),free_rows32=free_rows32,free_columns32=free_cols32,free_cells32=free_cells32)")
s=s.replace("  report['learned_positive_control_passed']=bool(good)", """  if good and j.get('strip32'):
   fixed_rows=[r for r in range(b) if r not in (j.get('free_rows32') or [])];fixed_cols=[c for c in range(a) if c not in (j.get('free_columns32') or [])]
   eS=max((abs(report['S'][r]-reference['S'][r]) for r in fixed_rows),default=0.);eR=max((abs(report['R'][c]-reference['R'][c]) for c in fixed_cols),default=0.)
   report['fixed_parent_max_error32']=max(eS,eR);good=good and max(eS,eR)<1e-7
  report['learned_positive_control_passed']=bool(good)""")
(W/'slide_strip32.py').write_text(s)
import ast
ast.parse(s)
p=W/'verify26.py';s=p.read_text().replace("if j.get('slide_control31') or j.get('slide_milp31'):","if j.get('slide_strip32'):\n import runpy\n runpy.run_path(str(R/'slide_strip32.py'),run_name='__main__');raise SystemExit\nif j.get('slide_control31') or j.get('slide_milp31'):");p.write_text(s)
print('new strip model parses',len(s))
