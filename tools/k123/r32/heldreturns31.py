"""Return changed held-kick endpoints as source-bound join or rectangle donors."""
from pathlib import Path
import sys,json,hashlib,shutil,time
import numpy as np
from scipy.spatial import cKDTree
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
import methods_lp as mlp,k123_join as kj
from source25 import audit
from compact_source28 import credits
from publication_source26 import check

def drift(A,B):
 C=A[:,:2]-A[:,:2].mean(0);D=B[:,:2]-B[:,:2].mean(0);tree=cKDTree(C);v=np.c_[np.cos(B[:,2]),np.sin(B[:,2])];best=float('inf')
 for M in [np.array(q) for q in [[[1,0],[0,1]],[[0,-1],[1,0]],[[-1,0],[0,-1]],[[0,1],[-1,0]],[[1,0],[0,-1]],[[0,1],[1,0]],[[-1,0],[0,1]],[[0,-1],[-1,0]]]]:
  distance,ids=tree.query(D@M.T);u=v@M.T;theta=np.arctan2(u[:,1],u[:,0]);angle=(theta-A[ids,2]+np.pi/4)%(np.pi/2)-np.pi/4
  best=min(best,max(float(distance.max()),float(np.abs(angle).max())))
 return best

def main():
 measure=json.load((W/'held-return-drift31.json').open());assert measure['control458']>1e-7 and measure['negative_self']<1e-12
 admitted=[];declined=[]
 for entry in measure['outputs']:
  r=entry['record'];n=r['n'];p=Path(entry['csv']);A=mlp.load(str(p),{n})[n];assert len(A)==n and abs(mlp.side(A)-r['side'])<1e-9
  if n==651:assert len(A)!=n+1;print('raw receipt control',n,len(A),mlp.side(A),float(mlp.min_gap(A)),flush=True)
  if entry['drift']<=1e-7 or mlp.min_gap(A)<-1e-8:declined.append((n,'no changed valid geometry'));continue
  try:chains=len(kj.Lay(n,*kj.norm(A),str(n)).G)
  except Exception:chains=0
  digest=hashlib.sha256(p.read_bytes()).hexdigest();out=W.parent/'near'/f'{n}-heldreturn31-{digest[:16]}.csv'
  if out.exists():admitted.append({'n':n,'csv':str(out),'sha256':digest,'drift':entry['drift'],'chains':chains});continue
  pool=r['pool'];meta=json.load((W/pool/('sources-'+pool+'.json')).open());c=audit(meta[str(n)])
  if not c:declined.append((n,'source-deferred'));continue
  D=W/'held-return-inputs31'/str(n);D.mkdir(parents=True,exist_ok=True);q=D/f'{n}.csv';q.write_bytes(p.read_bytes());(D/'receipt.json').write_text(json.dumps(r))
  src='midm_scan.py held900s probe output, used as a changed geometry donor; first120s probe, seed'+str(310000+n)+'; numerical receipt '+str(D/'receipt.json')+'; pose drift '+str(entry['drift'])+'; immutable input pool '+str(W/pool/(pool+'.csv'))+'; pinned donor ancestry: '+credits([c])
  row={'n':str(n),'source':src,'licence':'own held-kick descendant; terms in the pinned donor ancestry','numeric_csv_sha256':digest,'numeric_job':'steps-'+pool+'-'+r['tag']};Path(str(q)+'.json').write_text(json.dumps(row));proof=check(q,row)
  if not proof['clean']:declined.append((n,'source-refused'));continue
  Path(str(out)+'.json.tmp').write_text(json.dumps(row));Path(str(out)+'.json.tmp').replace(Path(str(out)+'.json'));shutil.copy(q,str(out)+'.tmp');Path(str(out)+'.tmp').replace(out);admitted.append({'n':n,'csv':str(out),'sha256':digest,'drift':entry['drift'],'chains':chains})
  scope='changed seams' if chains>=10 else 'rectangle or other methods; outside k123 join slice'
  line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: changed held-kick donor n={n}, side={mlp.side(A):.14g}, pose drift={entry["drift"]:.6g}, no counted kick gain; {scope}, {out}\n'
  with (W.parent.parent/'handoff-r32.log').open('a') as f:f.write(line)
  with (W.parent/'STATE.txt').open('a') as f:f.write(line.rstrip()+'; cutoff17:15Z.\n')
  print('returned held endpoint',n,chains,flush=True)
 (W/'held-return-export31.json').write_text(json.dumps({'admitted':admitted,'declined':declined},indent=2))
if __name__=='__main__':main()
