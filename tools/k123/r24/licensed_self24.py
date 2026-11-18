import pathlib,sys,json,subprocess,math,time

def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));import methods_lp as m,k123_join as k,family_step as fs
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');fq=str(pathlib.Path.home()/'scratch/squares-base/fq');D=R/'out/cc0-self228';D.mkdir(exist_ok=True);P=m.load(str(R/'cc0/581-certified.csv'),{581})[581];Q,L=k.norm(P);X=k.Lay(581,Q,L,'581');Y=k.Lay(581,k.rot(Q,L),L,'581r');F,LL=k.join(X,Y,5,7,-9,0.0);assert len(F)==228;fs.write_rows(str(D/'start.csv'),228,F);print('CONTROL self581 ->228 count',len(F),'gap',m.min_gap(F),'side',LL,flush=True)
 bars={int(w[0]):float(w[1]) for l in (R/'bars.tsv').read_text().splitlines() if (w:=l.split('\t'))}
 with open(D/'turn.log','w') as h:subprocess.run([PY,'-I','lane/k123_turn.py',str(D/'start.csv'),'228',str(D),fq,'--turns=0','--modes','self','--loosen','1.001','--bar',str(bars[228]),'--keep'],stdout=h,stderr=h,check=True,timeout=180)
 rows=list((D/'raw').glob('*.csv'));(D/'result.json').write_text(json.dumps(dict(tag='581-581r-j5-7-s-9',parents=['cc0/581-certified.csv'],raw=[str(p) for p in rows],licence='CC0: Public Domain; own mathematical transformations'),indent=2));print('DONE licensed self228',[(str(p),m.side(m.load(str(p),{228})[228])) for p in rows],flush=True)
