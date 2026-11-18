"""Fourth-slot recipe: reconstruct a licensed 365 from the actual CC0 input."""
import pathlib,json,sys,os,time,math
import numpy as np
R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));sys.path.insert(0,str(R));os.chdir(R)
import rigidsoft as rs,rigidsoft_band as rb,rigidsoft_hop as rh,family_step as fs
from scipy.spatial import cKDTree
j=json.load(open(sys.argv[1]))
if j.get('recipe')=='asbuilt847':
 import licensed_asbuilt24;licensed_asbuilt24.run(j);sys.exit(0)
if j.get('recipe')=='band847':
 import licensed_band24;licensed_band24.run(j);sys.exit(0)
if j.get('recipe')=='parts':
 import licensed_parts24;licensed_parts24.run(j);sys.exit(0)
if j.get('recipe')=='self228':
 import licensed_self24;licensed_self24.run(j);sys.exit(0)
if j.get('recipe')=='join581':
 import licensed_join24;licensed_join24.run(j);sys.exit(0)
if j.get('recipe')=='kick365':
 import licensed_kick24;licensed_kick24.run(j);sys.exit(0)
D=R/'out/cc0-rebuild365';D.mkdir(exist_ok=True);(D/'tmp').mkdir(exist_ok=True);fq=str(pathlib.Path.home()/'scratch/squares-base/fq');end=float((R/'deadline').read_text());source='samanyu1808/sis-final-packings :: data.zip!submission.csv, CC0: Public Domain; actual public365 input; rigidsoft_band.fault BR8:14, row10 flip and rows3:10 flip, then fq'
def save(s,X,label):
 P=X.copy();P[:,2]=np.radians(P[:,2]);p=D/f'365-{label}.csv';fs.write_rows(str(p),365,P);pathlib.Path(str(p)+'.json').write_text(json.dumps(dict(n=365,side=s,source=source,licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no',phase=label)));print('SAVED',label,s,p,flush=True)
def quench(s,X,flags):
 left=end-time.time()
 if left<=1:return None
 ss,XX,dt=rs.fq(fq,str(D/'tmp'),s,X,flags,timeout=min(100,left));return (ss,XX) if ss is not None else None
s,X=rs.normalize(rs.load(str(R/'cc0/365.csv'),{365})[365]);sc,C=rs.normalize(rs.load(str(R/'cc0/control-seed365.csv'),{365})[365]);assert len(X)==len(C)==365
# Compare actual public input to the known control geometry, with a rejecting perturbation.
d=max(cKDTree(C).query(X)[0].max(),cKDTree(X).query(C)[0].max());bad=X.copy();bad[0,0]+=.01;negative=cKDTree(C).query(bad)[0].max();assert d<2e-7 and negative>1e-4
print('CONTROL public365 matches known seed geometry within',d,'negative perturbation distance',negative,flush=True)
a=rb.fault(s,X,8,14,'BR',.15,None);b=rb.fault(sc,C,8,14,'BR',.15,None);assert a is not None and b is not None and len(a[0])==len(b[0])==365
faultdiff=max(cKDTree(b[0]).query(a[0])[0].max(),cKDTree(a[0]).query(b[0])[0].max());assert faultdiff<2e-6;print('CONTROL fault BR8:14 reproduces known start within',faultdiff,flush=True)
best=None
for flag in ['alm0','def']:
 q=quench(s,a[0],rs.FLAGSETS[flag])
 if q and (best is None or q[0]<best[0]):best=q
assert best is not None;s,X=best;save(s,X,'fault')
print('CONTROL known fault side19.610439666; got',s,'difference',s-19.610439666,flush=True)
for label,wanted in [('flip10',{'r10-10p','r10-10m'}),('flip3-10',{'r3-10m'})]:
 options=[(tag,Y) for tag,Y in rh.flips(s,X,8) if tag in wanted];best=(s,X)
 for tag,Y in options:
  q=quench(s,Y,rs.FLAGSETS['alm0'])
  if q and q[0]<best[0]:best=q
 s,X=best
 q=quench(s,X,rs.FLAGSETS['pol'])
 if q and q[0]<s:s,X=q
 save(s,X,label)
(D/'result.json').write_text(json.dumps(dict(n=365,side=s,control_input_distance=float(d),control_fault_distance=float(faultdiff),source=source,licence='CC0: Public Domain; own mathematical transformations',output=str(D/'365-flip3-10.csv')),indent=2))
print('DONE licensed365',s,flush=True)
