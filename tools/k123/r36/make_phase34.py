from pathlib import Path
W=Path(__file__).resolve().parent
s=(W/'phase_matching_seed33.py').read_text()
a=s.index('def upright_sets(');b=s.index('j=json.load(open(sys.argv[1]))',a)
s=s[:a]+'''def upright_sets(H,L):
 seed=H.base+H.e*L;m=int(L);slack=L-m;sets=[seed]
 # Interior offsets and opening seams change the physical upright positions.
 phases=[0.,slack*.25,slack*.5,slack*.75,slack]
 axis=[np.arange(m)+.5+d for d in phases]
 for cut in [m//4,m//2,3*m//4]:
  axis.append(np.arange(m)+.5+np.where(np.arange(m)<cut,0.,slack))
 for ix,X in enumerate(axis):
  for iy,Y in enumerate(axis):
   if ix>=5 and iy>=5 and ix!=iy:continue
   U=np.array([(x,y) for x in X for y in Y]);Q=np.column_stack((U,np.zeros(len(U))));assert mlp.min_gap(Q)>-1e-7;sets.append(U)
 # Shift selected compatible parent squares onto new phases, then fill from that grid.
 for dx,dy in [(slack*.25,0.),(0.,slack*.25),(-slack*.25,0.),(0.,-slack*.25),(slack*.5,slack*.5),(-slack*.5,-slack*.5)]:
  initial=seed+[dx,dy];initial=initial[np.all((initial>=.5-1e-9)&(initial<=L-.5+1e-9),axis=1)]
  candidates=np.array([(x,y) for x in axis[2] for y in axis[2]])
  for reverse in [False,True]:
   U=initial.copy()
   for p in candidates[::-1] if reverse else candidates:
    if len(U) and np.any(np.max(abs(U-p),axis=1)<1-2e-9):continue
    U=np.vstack((U,p))
   assert mlp.min_gap(np.column_stack((U,np.zeros(len(U)))))>-1e-7;sets.append(U)
 return sets
''' + s[b:]
s=s.replace("D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True)","D=R/'out/phase34'/j['tag'];D.mkdir(parents=True,exist_ok=True)").replace("mechanism':'bipartite-seed26133'","mechanism':'physical-upright-phase34'").replace("own exact bipartite maximum independent set on a fixed calibrated sliding tilted lattice and a mutually compatible upright completion; model ","own exact bipartite maximum independent set using new interior-phase upright lattices, opening seams and shifted parent uprights; model ")
(W/'phase_physical34.py').write_text(s)
p=W/'verify26.py';s=p.read_text().replace("if j.get('whole_crossover34'):","if j.get('phase_physical34'):\n import runpy\n runpy.run_path(str(R/'phase_physical34.py'),run_name='__main__');raise SystemExit\nif j.get('whole_crossover34'):");p.write_text(s)
