"""Transfer whole stacks into corners cut from newly certified kick returns."""
import hashlib,json,pickle,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
import expanded as E
W=Path(C.WORK);RECEIPT=W/'returned-stacks-control.json'
END=float((W/'box/search-deadline').read_text())
def main():
 while time.time()<END:
  result=subprocess.run(['rsync','-a','boxC:scratch/squares-stair-c/returned-stacks-control.json',str(RECEIPT)],capture_output=True,timeout=40)
  if result.returncode==0:break
  time.sleep(30)
 else:return
 control=json.loads(RECEIPT.read_text());assert control['passed']and len(control['variants'])==7
 assert control['helper_sha256']==hashlib.sha256((H/'corner_stacks.py').read_bytes()).hexdigest()
 out=[]
 for record in json.loads((W/'feedback-final-state.json').read_text()).values():
  if record.get('status')!='staged'or record['n']!=805:continue
  n=record['n'];p=None
  for candidate in (W/'donors').glob(f'{n}-feedback-*.csv'):
   if hashlib.sha256(candidate.read_bytes()).hexdigest()==record['sha256']:p=candidate;break
  assert p is not None,'returned snapshot bytes missing'
  meta=json.loads(p.with_suffix('.json').read_text());proof=C.full_admission(str(p),n,meta)
  if proof is None:C.state('DEFER returned stack source '+str(p));continue
  d,why=C.M.cut(C.M.np.asarray(C.M.read_layouts(str(p))[n],float),n);assert d is not None,why
  mods=[]
  for a,b in[(1,0),(0,1),(1,1),(2,0),(0,2),(2,2)]:
   e=E.expand(d,a,b)
   if min(e['s1'],e['s2'])<4:continue
   q,_,_=E.corner(e,meta['source']+'; returned whole-stack transfer '+str((a,b)),meta['licence'],f"r31returnstacks-{n}-{record['sha256'][:12]}-{a}{b}")
   q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
  for start in range(0,len(mods),3):
   packet=W/'donors'/f"r31-priority-stacks-return-{n}-{record['sha256'][:12]}-{start}.pkl"
   with packet.open('wb')as f:pickle.dump(dict(mods=mods[start:start+3],lens={},origin='changed certified return with following flush stacks'),f)
   for host,_ in C.HOSTS:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
  out.append(dict(n=n,sha256=record['sha256'],side=record['side'],source=str(p),proof=proof['proof'],modules=[q['id']for q in mods]))
  C.state(f"STAGE returned physical corners n={n} sha{record['sha256']} variants{len(mods)} after seven975 controls. Changed bytes replace the held corner input. Numerical searches remain on the three serial workers, deadline00:15Z.")
  print('RETURN STACKS',n,record['sha256'],len(mods),flush=True)
 (W/'returned-stacks-staged.json').write_text(json.dumps(out,indent=2))
if __name__=='__main__':main()
