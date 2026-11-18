"""One tight fq quench from a certified file; final certification stays local."""
import pathlib,sys,os,csv,json
R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'))
import methods_lp as mlp
from midm_scan import to_fq,from_fq,quench
import family_step as fs
ind,out,fq=sys.argv[1:4];out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
for p in pathlib.Path(ind).glob('*.csv'):
 n=int(p.stem);P=mlp.load(str(p),{n})[n];s,X=to_fq(P)
 s2,X2=quench(fq,str(out/'tmp'),s,X,['--loosen','1.0'],timeout=180)
 result=dict(n=n,before=s,after=s2,completed=s2 is not None)
 (out/f'{n}-quench.json').write_text(json.dumps(result))
 print(json.dumps(result),flush=True)
 if s2 is None:sys.exit(2)
 fs.write_rows(str(out/f'{n}-fq-tight.csv'),n,from_fq(X2))
