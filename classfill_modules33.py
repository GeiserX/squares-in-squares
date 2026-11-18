"""Make changed far zones from newly held poses, then quench the new layout."""
import sys,json,time,math,hashlib,contextlib,pickle
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path('lane').resolve()))
import modules as M
import classfill as C
import zone_search as Z
import methods_lp as L
import classfill_finish as F
import floatsafe as FS

def main(raw,n,tag,fq,deadline,source,licence):
 out=Path('out/finish-'+tag);out.mkdir(exist_ok=True)
 p=L.load(raw,{n})[n];start=L.side(p);sq=M.read_layouts(raw)[n];d,why=M.cut(sq,n)
 if d is None:
  (out/'module-result.json').write_text(json.dumps(dict(cut=False,reason=why)));print('MODULE_CUT_REFUSED',n,why,flush=True);return 0
 mods=M.modules_of(d,source,licence,'cf33');twins,_=M.slid(d,mods);by={q['id']:q for q in mods+twins};Q=d['X'].copy();moves=[]
 pickle.dump(dict(mods=mods+twins,layouts=[]),open(out/'modules.pkl','wb'))
 for q in mods:
  if q['kind']!='far' or q['miss']:continue
  native=q['P'];mask=d['zone']==('F1' if q['arm']==1 else 'F2')
  restored=np.c_[native[:,0],d['s']-native[:,1],-native[:,2]] if q['arm']==1 else np.c_[d['s']-native[:,1],native[:,0],native[:,2]]
  assert np.max(np.abs(restored-d['X'][mask]))<1e-10,'native zone reconstruction differs'
  tw=by.get(q['id']+'~');use=tw or q;c=use['c'];f=use['f0'];lean=tw['lean'] if tw else -1
  if tw and (tw['miss'] or tw['count']!=q['count']):continue
  with C._Slid(Z,tw) if tw else contextlib.nullcontext():
   st=M.far_at(use,f)
   if st is None:continue
   lam,A=st
   if not tw and q['lean']!=-1:A=np.c_[c-1+f-A[:,0],A[:,1],-A[:,2]]
   compact=Z.compact(A,c,f,lam,lean)
   if compact is None:continue
   lam,A=compact[:2];actual=Z.length(A,c,f,lam+1e-7,lean)
   if actual is None:continue
   first=actual[0];t=time.time();lam,A,kept=Z.sweep(A,c,f,first,lean=lean,until=min(t+90,deadline-150))
   final=Z.length(A,c,f,lam+1e-7,lean) if kept else None
  rec=dict(id=q['id'],before=first,after=final[0] if final else first,kept=kept,seconds=time.time()-t);moves.append(rec);print('MODULE_SWEEP',n,rec,flush=True)
  if not final or final[0]>=first-1e-8:continue
  # Undo the canonical zone reflection used by the kind sweep.
  if not tw and q['lean']!=-1:A=np.c_[c-1+f-A[:,0],A[:,1],-A[:,2]]
  mask=d['zone']==('F1' if q['arm']==1 else 'F2')
  if len(A)!=sum(mask):raise ValueError('zone square count changed')
  B=np.c_[A[:,0],d['s']-A[:,1],-A[:,2]] if q['arm']==1 else np.c_[d['s']-A[:,1],A[:,0],A[:,2]]
  Q[mask]=B
 changed=max((r['before']-r['after'] for r in moves),default=0)
 (out/'module-result.json').write_text(json.dumps(dict(cut=True,moves=moves,maximum_zone_gain=changed),indent=1)+'\n')
 if changed<=1e-8:return 0
 Q[:,2]=np.radians(Q[:,2]);rawnew=out/'new-geometry.csv';M.write_layout(str(rawnew),n,Q)
 cert=F.certify(rawnew,n)
 if cert is None:print('MODULE_NEW_GEOMETRY_REFUSED',n,flush=True);return 0
 result=out/(str(n)+'.csv');F.write(result,cert[1]);score=F.finish_quench(n,result,cert[0],fq,deadline,out)
 final=F.certify(result,n)
 if final is None:raise ValueError('module final certificate failed')
 score,rows=final;F.write(result,rows)
 target=Path('out/final-'+tag);target.mkdir(exist_ok=True);dest=target/(str(n)+'.csv');dest.write_bytes(result.read_bytes())
 direct,why=FS.check(n,rows);parsed=FS.via_pandas(rows);pd,why2=FS.check(n,parsed);gap=FS.clearance(rows);pgap=FS.clearance(parsed)
 audit=dict(input_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),direct=why,pandas=why2,direct_score=direct,pandas_score=pd,clearance=gap,pandas_clearance=pgap,passed=why==why2=='ok' and gap>=2e-11 and pgap>=2e-11)
 meta=dict(finish_score=score,finish_start_side=start,finish_quenched=True,finish_search_method='changed far-zone kind sweep',module_moves=moves,original_byte_audit=audit)
 (target/(str(n)+'.json')).write_text(json.dumps(meta,indent=1)+'\n');(target/'DONE').touch();print('MODULE_FINISHED',n,score,flush=True);return 0
