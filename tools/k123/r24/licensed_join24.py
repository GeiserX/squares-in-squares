"""Compose and join actual CC0 descendants in the fourth numerical slot."""
import pathlib,subprocess,sys,json,time,shutil,csv,os
import numpy as np
def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));import methods_lp as m,family_step as fs
 from midm_scan import to_fq,from_fq,quench
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(pathlib.Path.home()/'scratch/squares-base/fq');D=R/'out/cc0-join';D.mkdir(exist_ok=True);(D/'tmp').mkdir(exist_ok=True);end=float((R/'deadline').read_text());x=R/'out/cc0-rebuild365/365-licensed-kick.csv'
 if not x.exists():x=R/'out/cc0-rebuild365/365-fault.csv'
 def call(args,log,timeout=150):
  with open(log,'w') as f:subprocess.run(args,stdout=f,stderr=f,check=True,timeout=min(timeout,max(1,end-time.time())))
 call([PY,'-I','lane/forensics_rect.py','details-eligible24.csv',str(D/'rect'),'--only','790','--no-single','--keep','12','--slack','.02','--per-n','8',str(R/'cc0/123.csv'),str(x)],D/'rect.log')
 paths=list((D/'rect').glob('790-*.csv'));print('CONTROL rectangle count790:',len(paths),'legal starts',flush=True)
 if not paths:return
 paths.sort(key=lambda p:m.side(m.load(str(p),{790})[790]));s0,P0=min(((m.side(m.load(str(p),{790})[790]),m.load(str(p),{790})[790]) for p in paths[:2]),key=lambda x:x[0]);best=(s0,P0)
 for p in paths[:2]:
  P=m.load(str(p),{790})[790];s,X=to_fq(P);ss,XX=quench(FQ,str(D/'tmp'),s,X,[],timeout=min(80,max(1,end-time.time())))
  if ss is not None and ss<best[0]:best=(ss,from_fq(XX))
 p790=D/'790-licensed.csv';fs.write_rows(str(p790),790,best[1]);pathlib.Path(str(p790)+'.json').write_text(json.dumps(dict(n=790,side=best[0],source='forensics_rect.py opposite rectangle windows from actual CC0 public123 and licensed365 reconstruction',licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no',parents=[str(R/'cc0/123.csv'),str(x)])))
 pool=D/'licensedjoin.csv'
 with open(pool,'w') as f:
  wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
  for n,p in [(365,x),(790,p790)]:wr.writerows((n,i,*row) for i,row in enumerate(m.load(str(p),{n})[n]))
 call([PY,'-I','lane/k123_join.py','scan',str(pool),'bars.tsv',str(D/'starts'),'365,790','--rmax','.3','--pmax','.3','--room','-.03','--mmin','10','--only','581'],D/'join-scan.log')
 starts=list((D/'starts').glob('581-*.csv'));print('CONTROL join count581:',len(starts),'legal starts; rectangle790 side',best[0],flush=True)
 starts.sort(key=lambda p:m.side(m.load(str(p),{581})[581]));bars={int(w[0]):float(w[1]) for l in (R/'bars.tsv').read_text().splitlines() if (w:=l.split('\t'))};done=[]
 for i,p in enumerate(starts[:2]):
  out=D/f'quench{i}';call([PY,'-I','lane/k123_turn.py',str(p),'581',str(out),FQ,'--turns=0','--modes','self','--loosen','1.001','--bar',str(bars[581]),'--keep'],D/f'quench{i}.log',150);done.extend(str(p) for p in (out/'raw').glob('*.csv'))
 result=dict(public_parent='samanyu1808/sis-final-packings :: data.zip!submission.csv',licence='CC0: Public Domain',licensed365=str(x),licensed790=str(p790),pool=str(pool),starts=[str(p) for p in starts],raw=done)
 (D/'result.json').write_text(json.dumps(result,indent=2));print('DONE CC0 rectangle/join',result,flush=True)
