"""Replace old corner starts with whole-stack transfers from the current held row."""
import csv,datetime,hashlib,json,pickle,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;L=H.parents[2];sys.path[:0]=[str(H),str(L)]
import modules as M
import expanded as E
import held_driver as D
import held_proof as B
import provenance as P
from prepare import fingerprint
W=D.W

def main():
 while not(W/'coordinator.pid').exists():time.sleep(5)
 canonical='--canonical'in sys.argv
 counts=[int(x)for x in sys.argv[1:]if x.isdigit()]or[805,812,871,997]
 out=W/('held31'if canonical else'fresh-held-corners');out.mkdir(exist_ok=True)
 result=[]
 for n in counts:
  r=D.source(n);p=out/f'{n}.csv'
  with p.open('w')as f:
   w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(B.held_rows()[n])
  sha=hashlib.sha256(p.read_bytes()).hexdigest();rec=out/f'{n}-source.json';rec.write_text(json.dumps(r,sort_keys=True))
  origin=dict(n=n,held_path=str(B.HELD),held_sha256=B.held_sha(),snapshot=str(p),snapshot_sha256=sha,record=str(rec),record_sha256=hashlib.sha256(rec.read_bytes()).hexdigest())
  binding=B.check(origin)
  proof=out/f'{n}-binding.json';lic=r['licence'];src=f'own submitted held n={n} in {B.HELD}; inherited source notices retained inside the held binding; '+r['table']
  proof.write_text(json.dumps(dict(path=str(B.HELD),n=n,source=src,licence=lic,held31_origin=origin,binding=binding,original_source_record=r),sort_keys=True))
  metadata=dict(n=n,source=src,licence=lic,held31_origin=origin,modules=[dict(id=f'{n}-held-snapshot',source=src,licence=lic)])
  Path(str(p)+'.json').write_text(json.dumps(metadata))
  transport=dict(path=str(B.HELD),n=n,snapshot_sha256=sha,verified_ancestry=True,ancestry=dict(path=str(B.HELD),n=n,reason='exact submitted subset',held_binding=binding),full_ancestry=dict(path=str(proof),sha256=hashlib.sha256(proof.read_bytes()).hexdigest()),source=src,licence=lic)
  Path(str(p)+'.origin.json').write_text(json.dumps(transport))
  src=f'{p} immutable sha256 {sha}; ancestry proof {proof}; '+src
  if not P.clean(src,lic):result.append(dict(n=n,refused='source notices'));continue
  from public_roots import audit
  audit(dict(source=src,licence=lic))
  d,why=M.cut(M.np.asarray(M.read_layouts(str(p))[n],float),n)
  if d is None:result.append(dict(n=n,refused=why));continue
  mods=[];failed=[]
  if canonical:
   import coordinator as C
   assert C.full_admission(str(p),n,dict(metadata,source=src))is not None,'held canonical full source proof deferred'
   mods=M.modules_of(d,src,lic,f'r33heldcanonical{n}-{sha[:12]}')
  for a,b in ([]if canonical else[(1,0),(0,1),(1,1),(2,0),(0,2),(2,2)]):
   try:
    e=E.expand(d,a,b)
    if min(e['s1'],e['s2'])<4:continue
    q,_,_=E.corner(e,src+'; own whole-stack transfer '+str((a,b)),lic,f'r33stacks-{n}-{sha[:12]}-{a}{b}')
    q.update(turn=True,ours=True,extra_stacks=3);mods.append(q)
   except (AssertionError,ValueError)as ex:failed.append(dict(variant=[a,b],reason=str(ex)))
  for offset in range(0,len(mods),3):
   name=f'r33-live-held-canonical-{n}-{offset}.pkl'if canonical else f'r33-priority-stacks-current-{n}-{offset}.pkl'
   packet=out/name;pickle.dump(dict(mods=mods[offset:offset+3],lens={},origin='new current held geometry with full source binding'),packet.open('wb'))
   for host in ['boxC','boxD','boxE']:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
  result.append(dict(n=n,sha256=sha,modules=[dict(id=q['id'],fingerprint=fingerprint(q))for q in mods],failed=failed))
  kind='canonical modules'if canonical else'physical corners with following stacks'
  with(W.parent/'STATE.txt').open('a')as f:f.write(D.stamp()+' boxA STAGE fresh held '+kind+' '+str(n)+' current held sha '+sha+' states'+str(len(mods))+'. Replaces old cached source versions; controls975 precede dispatch. Logs worker.log; deadline00:15Z.\n')
  print('STAGED','canonical'if canonical else'physical',n,len(mods),flush=True)
 (W/('held-canonical-staged.json'if canonical else'fresh-held-corners.json')).write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
