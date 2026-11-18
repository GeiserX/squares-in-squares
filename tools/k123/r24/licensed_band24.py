import pathlib,sys,json,subprocess,time,os
import numpy as np

def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));os.environ['SQ_FQ']=str(pathlib.Path.home()/'scratch/squares-base/fq');import methods_lp as m,family_step as fs,family_readers as fr,k123_join as k
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');fq=os.environ['SQ_FQ'];D=R/'out/cc0-band847';D.mkdir(exist_ok=True);end=float((R/'deadline').read_text());fs.FQ=fq;(D/'tmp').mkdir(exist_ok=True);os.environ['SQ_TMP']=str(D/'tmp');assert pathlib.Path(fs.FQ).exists();P=m.load(str(R/'out/cc0-parts/847-licensed-parts.csv'),{847})[847];G,info=fr.band_step(P,847,2,'down');print('CONTROL licensed847 banddown2 count',len(G),'side',info['side'],'gap',info['gap'],flush=True);assert len(G)==734
 back=fr.band_build(G,info['side'],2,'up',info['a0']);s,Q,_=fr.band_frame(P);a=np.array(sorted(map(tuple,np.round(back,8))));b=np.array(sorted(map(tuple,np.round(Q,8))));passed=len(back)==847 and np.allclose(a,b,atol=1e-7);print('MEASURE inverse cut restores847',passed,flush=True)
 C=m.load(str(R/'cc0/847-control.csv'),{847})[847];CG,CI=fr.band_step(C,847,2,'down');assert len(CG)==734
 fs.set_limit(min(180,max(1,end-time.time())));CX,CL,_=fs.squeeze(CG,iters=60,fq=False,stop=lambda:time.time()>=end);CX,CL=fs.finish(CX,CL,27.591378146832746,'down',.02,lambda:time.time()>=end);ok=abs(CL-27.591378146832746)<1e-5;print('CONTROL historical forward734',CL,'expected27.591378146833 passed',ok,flush=True);fs.set_limit(None);assert ok
 (D/'forward-control.json').write_text(json.dumps(dict(expected=27.591378146832746,actual=CL,passed=ok,inverse_identity=bool(passed))))
 fs.set_limit(min(180,max(1,end-time.time())));X,L,_=fs.squeeze(G,iters=60,fq=False,stop=lambda:time.time()>=end);bars={int(w[0]):float(w[1]) for l in (R/'bars.tsv').read_text().splitlines() if (w:=l.split('\t'))};X,L=fs.finish(X,L,bars[734],'down',.02,lambda:time.time()>=end);fs.set_limit(None);p734=D/'734-licensed-band.csv';fs.write_rows(str(p734),734,X);pathlib.Path(str(p734)+'.json').write_text(json.dumps(dict(n=734,side=L,source='family_readers.band_step down2 from actual licensed847, sequential LP and fq',licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no',parent='out/cc0-parts/847-licensed-parts.csv')));print('SAVED licensed734',L,flush=True)
 A=m.load(str(R/'cc0/630.csv'),{630})[630];AQ,AL=k.norm(A);BQ,BL=k.norm(X);u=k.Lay(630,k.rot(AQ,AL),AL,'630r');v=k.Lay(734,BQ,BL,'734');F,FL=k.join(u,v,19,14,2,max(0,v.f-u.f)+.02);print('CONTROL join630/734 count',len(F),'gap',m.min_gap(F),flush=True);assert len(F)==847;fs.write_rows(str(D/'start847.csv'),847,F)
 with open(D/'turn.log','w') as h:subprocess.run([PY,'-I','lane/k123_turn.py',str(D/'start847.csv'),'847',str(D),fq,'--turns=0','--modes','self','--loosen','1.001','--bar',str(bars[847]),'--keep'],stdout=h,stderr=h,check=True,timeout=min(180,max(1,end-time.time())))
 with open(D/'pool.csv','w') as f:
  import csv
  wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
  for nn,PP in [(630,A),(734,X)]:wr.writerows((nn,i,*r) for i,r in enumerate(PP))
 (D/'result.json').write_text(json.dumps(dict(n=847,tag='630r-734-j19-14-s2',raw=[str(p) for p in (D/'raw').glob('*.csv')],licensed734=str(p734),source='actual licensed847 -> banddown2 ->734, then join actual Apache2.0 candidate630',licence='CC0: Public Domain and Apache2.0; own mathematical transformations'),indent=2));print('DONE licensed847 band/join',flush=True)
