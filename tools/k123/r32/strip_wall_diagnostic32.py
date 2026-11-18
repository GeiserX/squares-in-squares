"""Measure which border cells the finite parent domains can put inside the box."""
from pathlib import Path
import json,math,numpy as np
W=Path(__file__).resolve().parent;s=json.load((W/'strip-feed32.json').open());out=[]
def cluster(v):
 r=[]
 for x in sorted(v):
  if not r or abs(x-r[-1])>1e-7:r.append(float(x))
 return np.array(r)
for j in s['jobs']:
 r=j.get('result',{})
 if j.get('learned_control') or not r.get('learned_reference'):continue
 ref=r['learned_reference'];S=np.array(ref['S']);R=np.array(ref['R']);theta=math.pi/4+math.radians(j['phi']);step=2**.5*math.sin(math.radians(j['phi']));u=np.array([math.cos(theta),math.sin(theta)]);v=np.array([-u[1],u[0]]);L=r['L'];O=np.array(ref['O'])+(L-ref['side'])/2;h=(abs(u[0])+abs(u[1]))/2;aa=r['a'];bb=r['b']
 for shifts,label in [([-1/3,0,1/3],'existing'),([-1,-1/3,0,1/3,1],'extended')]:
  sl=cluster(np.concatenate([S+x*step for x in shifts]));rl=cluster(np.concatenate([R+x*step for x in shifts]))
  for choices in [7,0]:
   feasible=[]
   for ii in range(aa):
    for jj in range(bb):
     if 1<=ii<aa-1 and 1<=jj<bb-1:continue
     if ii not in j['free_columns32'] and jj not in j['free_rows32']:continue
     ss=sl[np.argsort(abs(sl-S[jj]))[:choices]] if choices and jj in j['free_rows32'] else sl if jj in j['free_rows32'] else sl[[int(np.argmin(abs(sl-S[jj])))]]
     rr=rl[np.argsort(abs(rl-R[ii]))[:choices]] if choices and ii in j['free_columns32'] else rl if ii in j['free_columns32'] else rl[[int(np.argmin(abs(rl-R[ii])))]]
     C=O+(ii-(aa-1)/2+ss[:,None,None])*u+(jj-(bb-1)/2+rr[None,:,None])*v;count=int(np.all((C>=h-2e-9)&(C<=L-h+2e-9),axis=2).sum())
     if count:feasible.append([ii,jj,count])
   out.append({'tag':j['tag'],'domains':label,'choices':choices,'border_cells_with_wall_feasible_states':len(feasible),'states':feasible})
(W/'strip-wall-diagnostic32.json').write_text(json.dumps(out,indent=2));print(json.dumps([{k:v for k,v in r.items() if k!='states'} for r in out]))
