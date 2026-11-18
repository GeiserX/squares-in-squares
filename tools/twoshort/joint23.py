"""Change upright column heights and tilted row offsets together on a known corner."""
import json,math,os,pathlib,pickle,sys,time
import numpy as np
R=pathlib.Path.home()/'scratch/squares-twoshort';sys.path.insert(0,str(R/'lane'));import zone_corner as Z
f=float(sys.argv[1]);tag=sys.argv[2];D=R/'designs'/tag;D.mkdir(parents=True,exist_ok=True)
b=pickle.load(open(R/'reference/deep64.pkl','rb'));mod=Z.cmod(9,9)
P0=np.array(b['P']);y0=b['y0'];x0=b['x0'];before=Z.loss_of(mod,.64,len(P0),y0,x0)
# Rebuild the row positions from each row's centre, direction and within-row coordinates.
def rows(P):
 out=[]
 for sign in [-1,1]:
  ids=np.nonzero(P[:,2]*sign>5)[0]
  if not len(ids):continue
  a=math.radians(float(np.median(P[ids,2])));v=np.array([math.cos(a),math.sin(a)]);perp=np.array([-v[1],v[0]])
  values=P[ids,:2]@perp
  for value in sorted(values):
   ii=ids[np.abs(values-value)<1e-5]
   if len(ii)<2 or any(np.array_equal(ii,j) for j in out):continue
   out.append(ii)
 return out
rr=rows(P0);reconstructed=P0.copy()
for ids in rr:
 a=math.radians(float(np.median(P0[ids,2])));v=np.array([math.cos(a),math.sin(a)]);perp=np.array([-v[1],v[0]])
 reconstructed[ids,:2]=np.outer(P0[ids,:2]@v,v)+np.outer(P0[ids,:2]@perp,perp)
assert np.max(np.abs(reconstructed-P0))<1e-12
r=Z.settle_zone(reconstructed,mod,.64,y0+1e-6,x0+1e-6)
assert r is not None
control=Z.loss_of(mod,.64,len(P0),r[0],r[1]);assert abs(control-before)<1e-4,(control,before)
negative=reconstructed.copy();negative[1,:2]=negative[0,:2];g=Z.exact(negative,mod,.64,y0,x0);assert g[0]<-.5,g
(D/'control.json').write_text(json.dumps(dict(before=before,recovered=control,rows=len(rr),negative_gap=g[0]),indent=2))
print('CONTROL',before,control,'rows',len(rr),'negative',g[0],flush=True)
car=Z.carry(b,f,soft=True)
if car is None:raise RuntimeError('carry failed')
# carry returns lengths and points in the order used by settle_zone.
y,x,P,_=car
print('carry',y,x,Z.loss_of(mod,f,len(P),y,x),flush=True)
rr=rows(P);up=np.nonzero(np.abs(P[:,2])<1e-4)[0];cols={}
for idx in up:cols.setdefault(round(P[idx,0]-.5),[]).append(idx)
tops={k:max(v,key=lambda i:P[i,1]) for k,v in cols.items()};rng=np.random.default_rng(round(f*1e5)+23)
base=[];end=int(open(R/'deadline').read());t0=time.time()
# Simultaneous transfers of upright column heights and phase changes along whole tilted rows.
for k in range(48):
 if time.time()+100>end or time.time()-t0>900:break
 Q=P.copy();cfrom,cto=map(int,rng.choice(sorted(cols),2,replace=False));idx=tops[cfrom]
 Q[idx,:2]=[cto+.5,max(P[i,1] for i in cols[cto])+1]
 chosen=rng.choice(len(rr),size=min(2,len(rr)),replace=False)
 shifts=[]
 for ri in chosen:
  ids=rr[ri];a=math.radians(float(np.median(Q[ids,2])));delta=float(rng.choice([-.47,-.25,-.1,.1,.25,.47]))
  Q[ids,:2]+=delta*np.array([math.cos(a),math.sin(a)]);shifts.append((int(ri),delta))
 try:r=Z.settle_zone(Q,mod,f,y+.04,x+.04)
 except Exception as e:print(k,'ERROR',repr(e),flush=True);r=None
 if r is None:print(k,'no settle',cfrom,cto,shifts,flush=True);continue
 yy,xx,QQ=r;loss=Z.loss_of(mod,f,len(QQ),yy,xx)
 print(k,'SETTLED',loss,cfrom,cto,shifts,flush=True)
 base.append(dict(id=tag+'-'+str(k),src='twoshort joint column transfer and tilted row offset from deep64; '+b['src'],licence='our own',c1=9,c2=9,lean1=1,lean2=-1,f=f,count=len(QQ),y0=yy,x0=xx,P=QQ))
 tmp=D/'base.tmp';pickle.dump(base,open(tmp,'wb'));tmp.replace(D/'base.pkl')
(D/'joint-summary.json').write_text(json.dumps(dict(f=f,attempted=k+1,settled=len(base),seconds=time.time()-t0)))
