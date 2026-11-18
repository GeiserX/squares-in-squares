import pathlib,sys,subprocess,json,time,os,csv

def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));import methods_lp as m,family_step as fs,family_readers as fr,k123_join as k
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');fq=str(pathlib.Path.home()/'scratch/squares-base/fq');D=R/'out/cc0-asbuilt';D.mkdir(exist_ok=True);P=m.load(str(R/'out/cc0-parts/847-licensed-parts.csv'),{847})[847];G,info=fr.band_step(P,847,2,'down');assert len(G)==734 and m.min_gap(G)>-1e-8;p734=D/'734-asbuilt-licensed.csv';fs.write_rows(str(p734),734,G);pathlib.Path(str(p734)+'.json').write_text(json.dumps(dict(n=734,side=info['side'],source='unpolished family_readers.band_step down2 from actual CC0-only847, count734 and nonnegative separation checked',licence='CC0: Public Domain; own mathematical transformation; Samanyu-dev seed ancestry: no')));print('ASBUILT734 count',len(G),'side',m.side(G),'gap',m.min_gap(G),flush=True)
 A=m.load(str(R/'cc0/630.csv'),{630})[630];AQ,AL=k.norm(A);BQ,BL=k.norm(G);X=k.Lay(630,k.rot(AQ,AL),AL,'630r');Y=k.Lay(734,BQ,BL,'734');F,L=k.join(X,Y,19,14,2,max(0,Y.f-X.f)+.02);print('JOIN new as-built734 count',len(F),'side',L,'gap',m.min_gap(F),flush=True);assert len(F)==847;fs.write_rows(str(D/'start847.csv'),847,F);bars={int(w[0]):float(w[1]) for l in (R/'bars.tsv').read_text().splitlines() if (w:=l.split('\t'))}
 with open(D/'turn.log','w') as h:subprocess.run([PY,'-I','lane/k123_turn.py',str(D/'start847.csv'),'847',str(D),fq,'--turns=0','--modes','self','--loosen','1.001','--bar',str(bars[847]),'--keep'],stdout=h,stderr=h,check=True,timeout=180)
 with open(D/'pool.csv','w') as f:
  w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
  for nn,Q in [(630,A),(734,G)]:w.writerows((nn,i,*row) for i,row in enumerate(Q))
 (D/'result.json').write_text(json.dumps(dict(n=847,tag='630r-734-j19-14-s2',raw=[str(p) for p in (D/'raw').glob('*.csv')],source='join actual Apache2.0 candidate630 with unpolished CC0-only734',licence='Apache2.0 and CC0: Public Domain'),indent=2));print('DONE asbuilt join',flush=True)
