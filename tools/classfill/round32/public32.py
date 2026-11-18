"""Apply the frozen round31 measure only beyond the owned-layout boundary."""
import csv,hashlib,importlib.util,json,sys
from pathlib import Path
W=Path(__file__).parent;S=Path('$SCRATCH/bounties-squares')
spec=importlib.util.spec_from_file_location('classfill_share32',S/'take-assemble-r31/scripts/share31.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
refs={}
owned_refs={}
def owned_layout(n,P):
 xy=P[:,:2]-(P[:,:2].min(0)+P[:,:2].max(0))/2
 own_policy.REFERENCE_ANGLES[id(xy)]=P[:,2]
 try:return own_policy.is_own_reference(n,xy)
 finally:own_policy.REFERENCE_ANGLES.pop(id(xy),None)

def references(n):
 if n not in refs:
  spec=importlib.util.spec_from_file_location('classfill_owned_reference32',Path('tools/harvest31/policy.py'))
  global own_policy
  if 'own_policy' not in globals():
   own_policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(own_policy)
  kept={};owned=[]
  for label,data in A.pub_rows({n}).items():
   if n not in data:continue
   P=data[n];is_own=owned_layout(n,P)
   if is_own:owned.append(label)
   else:kept[label]=data
  refs[n]=kept;owned_refs[n]=owned
 return refs[n],owned_refs[n]

def audit(path,n):
 targets,owned=references(n)
 if not targets and owned:return True,dict(allowed=True,reason='all harvested references are owned layouts',owned_references=owned)

 P=A.read_rows(Path(path).read_text(),{n})[n]
 if owned_layout(n,P):return True,dict(allowed=True,reason='owned Samanyu layout identity',owned_layout=True,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
 detail={k:A.share(P,v[n]) for k,v in targets.items() if n in v}
 ok=bool(detail) and all(max(v.values())<.4 for v in detail.values())
 proof=dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),allowed=ok,owned_references=owned,measure='frozen share31 bounding boxes and median ICP',comparisons=detail)
 return ok,proof
if __name__=='__main__':
 import numpy as np
 P=np.array([(i%10,i//10,0.) for i in range(100)])
 shifted=P.copy();shifted[:,:2]+=(.021,-.034)
 assert max(A.share(shifted,P).values())==1.
 spread=P.copy();spread[:,:2]*=1.37
 assert max(A.share(spread,P).values())<.4
 kept228,own228=references(228);kept972,own972=references(972)
 assert not kept228 and own228,(len(kept228),own228)
 assert kept972 and own972,(len(kept972),own972)
 reference=next(iter(kept972.values()))[972]
 assert not owned_layout(972,reference)
 assert max(A.share(reference,reference).values())==1.
 normal_share=A.share
 def forbidden_share(*args):raise AssertionError('share gate ran on an owned layout')
 A.share=forbidden_share
 try:
  ok,proof=audit(S/'seeds/samanyu_22249.csv',972)
  assert ok and proof.get('owned_layout'),proof
 finally:A.share=normal_share
 import tempfile
 with tempfile.TemporaryDirectory(dir=W) as td:
  p=Path(td)/'reference.csv'
  with p.open('w') as stream:
   writer=csv.writer(stream);writer.writerow(['n','square_id','x','y','angle']);writer.writerows((972,i,*row) for i,row in enumerate(reference))
  ok,proof=audit(p,972);assert not ok and max(max(v.values()) for v in proof['comparisons'].values())==1.,proof

 print('SHARE32_CONTROL_PASS translated copy1.0 refuses; changed spacing passes;228 all owned;972 retains unowned comparisons',len(kept972),'owned versions skipped',len(own972))
