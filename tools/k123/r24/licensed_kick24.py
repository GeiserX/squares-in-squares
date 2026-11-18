import pathlib,sys,json,subprocess,time,math
import numpy as np
def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));import methods_lp as mlp,rigidsoft as rs,rigidsoft_hop as rh,family_step as fs
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');fq=str(pathlib.Path.home()/'scratch/squares-base/fq');D=R/'out/cc0-rebuild365';K=D/'kick';K.mkdir(exist_ok=True);end=float((R/'deadline').read_text());start=D/'365-fault.csv'
 subprocess.run([PY,'-I','lane/midm_scan.py','--n','365','--sub',str(start),'--out',str(K),'--fq',fq,'--seconds','300','--seed','19','--modes','kick,lkick','--deadline',str(R/'deadline')],check=True)
 files=[start,*list((K/'raw').glob('*.csv'))];best=min(files,key=lambda p:mlp.side(mlp.load(str(p),{365})[365]));s,X=rs.normalize(mlp.load(str(best),{365})[365]);print('licensed kick best',s,best,flush=True)
 for tag,Y in list(rh.flips(s,X,8)):
  if tag!='r3-10m':continue
  ss,XX,dt=rs.fq(fq,str(D/'tmp'),s,Y,rs.FLAGSETS['alm0'],timeout=max(1,min(100,end-time.time())))
  if ss is not None and ss<s:s,X=ss,XX
 ss,XX,dt=rs.fq(fq,str(D/'tmp'),s,X,rs.FLAGSETS['pol'],timeout=max(1,min(80,end-time.time())))
 if ss is not None and ss<s:s,X=ss,XX
 P=X.copy();P[:,2]=np.radians(P[:,2]);out=D/'365-licensed-kick.csv';fs.write_rows(str(out),365,P);meta=dict(n=365,side=s,source='rigidsoft fault BR8:14, 300s midm kick seed19 and flip r3-10m, from actual samanyu1808/sis-final-packings :: data.zip!submission.csv input365',licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no',public_parent='cc0/365.csv')
 pathlib.Path(str(out)+'.json').write_text(json.dumps(meta,indent=2));(D/'kick-result.json').write_text(json.dumps(meta,indent=2));print('DONE licensed365 kick',s,out,flush=True)
