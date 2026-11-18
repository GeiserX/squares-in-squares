"""Run the full fq loop from certified bytes before final certification."""
import pathlib,sys,os,json,hashlib
R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'))
import methods_lp as mlp
from midm_scan import to_fq,from_fq,quench,POLISH
import family_step as fs
ind,out,fq=sys.argv[1:4];out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True);(out/'tmp').mkdir(exist_ok=True)
for p in pathlib.Path(ind).glob('*.csv'):
 n=int(p.stem);P=mlp.load(str(p),{n})[n];s,X=to_fq(P);initial=s;steps=[]
 for rnd in range(3):
  moved=False
  for name,flags in [('default',()),('polish',POLISH)]:
   s2,X2=quench(fq,str(out/'tmp'),s,X,flags,timeout=180)
   steps.append(dict(round=rnd,flags=name,before=s,after=s2,completed=s2 is not None))
   if s2 is None:
    (out/f'{n}-quench.json').write_text(json.dumps(dict(n=n,before=initial,completed=False,steps=steps)));sys.exit(2)
   if s2<s-3e-9:s,X,moved=s2,X2,True
  if not moved:break
 result=dict(n=n,before=initial,after=s,completed=True,full_fq_loop=True,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),steps=steps)
 (out/f'{n}-quench.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
 fs.write_rows(str(out/f'{n}-fq-tight.csv'),n,from_fq(X))
