"""Change the physical corner scope after the earlier two-stack compositions dried."""
import hashlib,json,pickle,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
import expanded as E
W=Path(C.WORK);END=float((W/'box/search-deadline').read_text());CONTROL=W/'three-stacks-control.json'
def main():
 while time.time()<END:
  r=subprocess.run(['rsync','-a','boxC:scratch/squares-stair-c/three-stacks-control.json',str(CONTROL)],capture_output=True,timeout=35)
  if r.returncode==0:break
  time.sleep(20)
 else:return
 j=json.loads(CONTROL.read_text());assert j['passed']and len(j['variants'])==9
 assert j['helper_sha256']==hashlib.sha256((H/'corner_stacks.py').read_bytes()).hexdigest()
 results=[]
 for n in [805,812,997]:
  p=W/'held31'/f'{n}.csv'
  if not p.exists():continue
  meta=json.loads(Path(str(p)+'.json').read_text());meta['source']=str(p)+' immutable sha256 '+hashlib.sha256(p.read_bytes()).hexdigest()+'; '+meta['source']
  proof=C.full_admission(str(p),n,meta)
  if proof is None:results.append(dict(n=n,refused='source proof'));continue
  d,why=C.M.cut(C.M.np.asarray(C.M.read_layouts(str(p))[n],float),n)
  if d is None:results.append(dict(n=n,refused=why));continue
  mods=[];fail=[]
  for a,b in[(1,2),(2,1),(3,0),(0,3),(3,1),(1,3),(3,2),(2,3),(3,3)]:
   try:
    e=E.expand(d,a,b)
    if min(e['s1'],e['s2'])<4:continue
    q,_,_=E.corner(e,meta['source']+'; coupled three-stack corner '+str((a,b)),meta['licence'],f'r33coupled-{n}-{a}{b}')
    q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
   except(AssertionError,ValueError)as ex:fail.append(dict(variant=[a,b],reason=str(ex)))
  for start in range(0,len(mods),3):
   packet=W/'donors'/f'r33-priority-stacks-coupled-{n}-{start}.pkl'
   pickle.dump(dict(mods=mods[start:start+3],lens={},origin='new coupled physical corner scope'),packet.open('wb'))
   for host,_ in C.HOSTS:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
  results.append(dict(n=n,modules=[q['id']for q in mods],failed=fail))
  C.state(f'STAGE coupled physical corners n={n} states{len(mods)} after nine exact975 controls. The change transfers up to three complete stacks on both arms. Fresh-only workers retain all prior completed recipe keys.')
 (W/'coupled-corners.json').write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
