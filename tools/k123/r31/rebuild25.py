"""Prioritize the two recorded recipes on newly traced rebuild parents."""
import pathlib,json,re,csv,hashlib,subprocess
from provenance24 import W,S,mlp,credit,key
import os,sys
if (W/'restart-stage25').exists():
 (W/'restart-stage25').unlink()
 os.execv(sys.executable,[sys.executable,str(W/'resident25.py'),'stage'])
import stage24,importlib
importlib.reload(stage24)
from stage24 import stage,current
import runpy
runpy.run_path(str(W/'maintenance25.py'),run_name='__main__')
seenfile=W/'rebuild-seen25.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set();found={}
root=S/'take-rebuild-r25'
for p in list(root.glob('*.csv'))+list((root/'near').glob('*.csv')):
 try:
  P=mlp.load(str(p));n=next(iter(P))
  if len(P)!=1 or n not in (735,790):continue
  c=credit(n,P[n],str(p))
  if c and (n not in found or mlp.side(P[n])<mlp.side(found[n][1])):found[n]=(p,P[n],c)
 except (KeyError,ValueError,OSError):continue
parent968=W.parent/'968.csv'
if not parent968.exists():parent968=S/'take-rebuild-r25/968.csv'
if 790 in found and parent968.exists():
 A968=mlp.load(str(parent968),{968})[968];c968=credit(968,A968,str(parent968))
 token='child489:'+key(790,found[790][1])+':'+key(968,A968)
 if c968 and token not in seen:
  P,orig=current();P[790]=found[790][1];P[968]=A968;orig[790]=str(found[790][0]);orig[968]=str(parent968)
  tag=f'rebuildchild{len(seen)+1:05d}'
  if stage(tag,P,orig,[(790,968)],'rebuild-exact489','licensed968 child; recipe790-968-j9-17-s-9'):
   p=W/tag/'exact489.tsv';p.write_text(f'489\t790-968-j9-17-s-9\tscan{tag}\t0.043\t22.606602\t+0.005356\t+1.058e-04\t{tag}\n')
   subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r31-ssh','-q',str(p),'boxE:scratch/squares-k123/exact489.tsv'],check=True)
   subprocess.run(['ssh','-S','/tmp/squares-k123-r31-ssh','boxE','cd $SCRATCH/squares-k123 && cat exact489.tsv >> queue.tsv'],check=True)
   seen.add(token);seenfile.write_text(json.dumps(sorted(seen)))
if not all(n in found for n in (735,790)):raise SystemExit
sig=hashlib.sha256(json.dumps([(n,key(n,found[n][1]),found[n][2].get('ancestry_sha256')) for n in (735,790)]+['reader-fallback25']).encode()).hexdigest()
if sig in seen:raise SystemExit
P,orig=current()
for n,(p,A,c) in found.items():P[n]=A;orig[n]=str(p)
seq=len(seen)+1;tag=f'rebuildfix{seq:05d}'
if stage(tag,P,orig,[(735,790)],'rebuild-exact968','clean rebuilt735/790; recorded recipe735r-790-j21-16-s3'):
 # Append the historical exact seam ahead of the broad scan. The worker verifies its count.
 row=f'968\t735r-790-j21-16-s3\tscan{tag}\t0.040\t31.608713\t-0.025089\t+2.827e-04\t{tag}\n'
 p=W/tag/'exact968.tsv';p.write_text(row)
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r31-ssh','-q',str(p),'boxE:scratch/squares-k123/exact968.tsv'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r31-ssh','boxE','cd $SCRATCH/squares-k123 && cat exact968.tsv >> queue.tsv'],check=True)
 seen.add(sig);seenfile.write_text(json.dumps(sorted(seen)))
