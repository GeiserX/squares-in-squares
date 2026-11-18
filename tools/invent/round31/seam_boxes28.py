"""Locate orientation junctions without running a packing optimizer."""
import csv,hashlib,json,math,os,pathlib,sys
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r31/work');sys.path.insert(0,str(W/'lane'))
import numpy as np
from scipy.spatial import cKDTree
import family_step as FS

def box(path,n):
 data=pathlib.Path(path).read_bytes();rows=list(csv.DictReader(data.decode().splitlines()))
 if len(rows)!=n:return None
 side,P=FS.canon(np.array([[float(v['x']),float(v['y']),float(v['angle'])]for v in rows]))
 angle=P[:,2]%(math.pi/2);bins=np.rint(angle/.08).astype(int);bins[np.minimum(angle,math.pi/2-angle)<.04]=0
 if len(np.unique(bins))<2:return None
 tree=cKDTree(P[:,:2]);best=None
 for i,near in enumerate(tree.query_ball_point(P[:,:2],3.2)):
  _,counts=np.unique(bins[near],return_counts=True);major=int((counts>=3).sum())
  if major<2:continue
  frac=counts/len(near);entropy=float(1-(frac*frac).sum());score=(major,entropy,len(near),-i)
  if best is None or score>best[0]:best=(score,i)
 if best is None:return None
 score,i=best;x,y=P[i,:2];bounds=[max(0,float(x)-3.5),max(0,float(y)-3.5),min(side,float(x)+3.5),min(side,float(y)+3.5)]
 return dict(n=n,input_sha256=hashlib.sha256(data).hexdigest(),cbox=','.join(f'{v:.10f}'for v in bounds),major_orientations=score[0],entropy=score[1],local_squares=score[2],side=side)

if __name__=='__main__':
 control=box(W/'starts/control907.csv',907);assert control and control['major_orientations']>=2
 inputs={}
 for j in json.load(open(W/'jobs.json')):
  if j['kind']not in('fresh','near','saved')or j.get('refused'):continue
  p=W/j['start'];data=box(p,j['n'])
  if data and data['input_sha256']==j.get('input_sha256'):inputs[data['input_sha256']]=data
 value=dict(policy='orientation-junction-box-v1',control=control,inputs=inputs)
 p=W/'seam-plan.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(value));q.replace(p)
 print(json.dumps(dict(control=control,eligible_inputs=len(inputs))),flush=True)
