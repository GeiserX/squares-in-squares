"""Check original builds and starts near the live bar, including those a kick did not improve."""
import csv,json,math,pathlib,sys
B=pathlib.Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r22';W=T/'work';R=W/'boxE22'
sys.path.insert(0,str(W));from shape974 import load
sys.path.insert(0,'.');import floatsafe
bar={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round20-1113a/details.csv'))}
for p in list(B.glob('take-*-r21/take.tsv'))+list(B.glob('take-*-r22/take.tsv')):
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
  except (ValueError,KeyError):pass
out=[];qual=[]
for p in sorted(list(R.glob('designs/*/builds/*.csv'))+list(R.glob('starts/*.csv'))):
 try:
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))];n=int(rows[0]['n'])
  if len(rows)!=n:continue
  _,side=load(p)
  if side>(1+bar[n])*math.sqrt(n)+1e-7:continue
  _,fr,score,err=floatsafe.work((n,rows));wins=fr is not None and score<bar[n]-1e-10
  out.append(dict(n=n,side=side,score=score,bar=bar[n],wins=wins,reason=err,path=str(p)))
  if wins:qual.append(out[-1])
 except Exception as ex:out.append(dict(path=str(p),reason=repr(ex)))
with open(W/'audit22.tsv','w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['n','side','score','bar','wins','reason','path'],delimiter='\t');w.writeheader();w.writerows(out)
(W/'audit22-qualified.json').write_text(json.dumps(qual,indent=2))
print('near-bar originals checked',len(out),'qualifying untouched layouts',len(qual))
for r in qual:print(json.dumps(r))
