"""Measure repeated physical starts in the existing boxE verification slot."""
from pathlib import Path
import json,sys,hashlib,collections,time
import numpy as np
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R/'lane')]
import methods_lp as mlp

def geometry(P):
 xy=P[:,:2]-(P[:,:2].min(0)+P[:,:2].max(0))/2
 axes=np.column_stack((np.cos(P[:,2]),np.sin(P[:,2])));out=[]
 for swap in (False,True):
  for sx in (-1,1):
   for sy in (-1,1):
    p=(xy[:,::-1] if swap else xy)*[sx,sy];u=(axes[:,::-1] if swap else axes)*[sx,sy]
    angle=np.arctan2(u[:,1],u[:,0])%(np.pi/2)
    angle=np.where(angle>np.pi/2-5e-12,0,angle)
    q=np.rint(np.column_stack((p,angle))*1e11).astype(np.int64)
    q=q[np.lexsort((q[:,2],q[:,1],q[:,0]))]
    out.append(hashlib.sha256(q.tobytes()).hexdigest())
 return min(out)

def main():
 t=time.time();records=[]
 for fp in (R/'out').glob('j22*/done.jsonl'):
  for line in fp.read_text().splitlines():
   try:records.append(json.loads(line))
   except ValueError:pass
 seen={};duplicates=[];missing=0;tested=0;control=None
 for r in records:
  p=R/'out'/r['worker']/(r['pool']+'-'+str(r['n'])+'-'+r['tag'])/'start.csv'
  if not p.exists():missing+=1;continue
  A=mlp.load(str(p),{r['n']})[r['n']]
  sig=geometry(A)
  if control is None:
   moved=A.copy();moved[:,0]=-moved[:,0]+2;moved[:,1]+=1;moved[:,2]=-moved[:,2]
   assert geometry(moved)==sig,'symmetry/translation control failed'
   changed=A.copy();changed[0,0]+=1e-6;assert geometry(changed)!=sig,'changed-coordinate control failed'
   control={'n':r['n'],'symmetry_translation_preserved':True,'changed_coordinate_rejected':True}
  identity=(r['n'],r.get('loosen',1.001),sig);tested+=1
  if identity in seen:duplicates.append({'record':r,'earlier':seen[identity],'geometry':sig})
  else:seen[identity]=r
 result={'completed_records':len(records),'starts_tested':tested,'missing_starts':missing,'unique_starts_by_finish':len(seen),'duplicate_starts':len(duplicates),'control':control,'seconds':time.time()-t,'rounding_decimals':11}
 (R/'geometry-audit31.json').write_text(json.dumps(result,indent=2));(R/'geometry-duplicates31.json').write_text(json.dumps(duplicates));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
