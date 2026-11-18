"""Try deeper physical cuts after the measured three-stack variants stayed dry."""
import hashlib,json,pickle,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
import expanded as E
W=Path(C.WORK);END=float((W/'box/search-deadline').read_text())
VARIANTS=[(4,0),(0,4),(4,1),(1,4),(4,4),(5,0),(0,5),(5,5)]
def main():
 receipt=W/'wide-stacks-control.json'
 while time.time()<END:
  r=subprocess.run(['rsync','-a','boxC:scratch/squares-stair-c/wide-stacks-control.json',str(receipt)],capture_output=True,timeout=35)
  if r.returncode==0:break
  time.sleep(20)
 else:return
 control=json.loads(receipt.read_text());assert control['passed']and len(control['variants'])==8
 assert control['helper_sha256']==hashlib.sha256((H/'corner_stacks.py').read_bytes()).hexdigest()
 n=805;p=W/'held31/805.csv';meta=json.loads(Path(str(p)+'.json').read_text());sha=hashlib.sha256(p.read_bytes()).hexdigest()
 meta['source']=str(p)+' immutable sha256 '+sha+'; '+meta['source']
 assert C.full_admission(str(p),n,meta)is not None
 d,why=C.M.cut(C.M.np.asarray(C.M.read_layouts(str(p))[n],float),n);assert d is not None,why
 mods=[];failed=[]
 for a,b in VARIANTS:
  try:
   e=E.expand(d,a,b)
   if min(e['s1'],e['s2'])<4:continue
   q,_,_=E.corner(e,meta['source']+'; deeper whole-stack corner cut '+str((a,b)),meta['licence'],f'r33wide-{n}-{sha[:12]}-{a}{b}')
   q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
  except(AssertionError,ValueError)as ex:failed.append(dict(variant=[a,b],reason=str(ex)))
 for start in range(0,len(mods),3):
  packet=W/'donors'/f'r33-priority-stacks-wide-805-{start}.pkl'
  pickle.dump(dict(mods=mods[start:start+3],lens={},origin='four/five-stack physical corner after dry three-stack builds'),packet.open('wb'))
  for host,_ in C.HOSTS:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
 result=dict(n=805,source_sha256=sha,modules=[q['id']for q in mods],failed=failed,control=str(receipt),recipe_owner805='boxC')
 (W/'wide-corners.json').write_text(json.dumps(result,indent=2));C.state(f'STAGE {len(mods)} four/five-stack805 corners after eight exact975 assembly controls. Changed scope from the dry three-stack model. Sparse tables retain the120s bound. One805 recipe owner boxC, default/polish fq before publish, numeric deadline00:15UTC.')
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
