"""Read the announced base and every clean frozen or live improvement."""
import csv,json,pathlib,re,subprocess
from provenance24 import W,S,mlp,credit,key,base
import numpy as np
_LAYOUT_CACHE=globals().get('_LAYOUT_CACHE',{})
def loadpack(path,want=None):
 path=pathlib.Path(path);st=path.stat();token=(str(path),st.st_mtime_ns,st.st_size,st.st_ino)
 if token not in _LAYOUT_CACHE:
  _LAYOUT_CACHE[token]=mlp.load(str(path))
 P=_LAYOUT_CACHE[token]
 return P if want is None else {n:P[n] for n in want if n in P}


def paths():
 text=(S/'handoff-r25.log').read_text();lines=[l for l in text.splitlines() if 'main -> all: BASE ' in l]
 if lines:
  line=lines[-1];files=re.findall(r'(?:$SCRATCH/bounties-squares/)?(?:gather/[^\s,;]+\.csv|gate/[^\s,;]+)',line)
  full=[pathlib.Path(f) if f.startswith('/') else S/f for f in files]
  cand=next((p for p in full if p.suffix=='.csv' and 'gather' in str(p)),None);det=next((p if p.name=='details.csv' else p/'details.csv' for p in full if 'gate' in str(p)),None)
  if cand and det and det.exists():return cand,det,True
 return S/'gather/round23-2026-11-13b.csv',S/'gate/cand-round23-1113b/details.csv',False

def current():
 candidate,detail,posted=paths();P=dict(loadpack(candidate));origins={n:'held' for n in P};rows={int(r['n']):r for r in csv.DictReader(open(detail))};scores={n:float(r['score']) for n,r in rows.items()}
 if posted:
  for lp in sorted(S.glob('take-*-r24/take.tsv')):
   for row in csv.DictReader(open(lp),delimiter='\t'):
    try:
     n=int(row['n']);f=lp.parent/f'{n}.csv'
     if key(n,P[n]) in base() or abs(float(row['new'])-scores[n])>1e-9 or not f.exists():continue
     A=loadpack(f,{n})[n];c=credit(n,A,str(f))
     def ordered(X):return X[np.lexsort((X[:,2],X[:,1],X[:,0]))]
     if c and np.max(np.abs(ordered(A)-ordered(P[n])))<1e-7:
      origins[n]=str(f)
      base()[key(n,P[n])]={**c,'sha256_geometry':key(n,P[n]),'origin':'held posted round24'}
    except (KeyError,ValueError,OSError):continue
 # Frozen lower bars are independent of live takes. All files need complete source admission.
 for p in sorted(S.glob('take-*-r24/take.tsv'))+sorted(S.glob('take-*-r25/take.tsv')):
  if posted and '-r24/' in str(p):continue
  for row in csv.DictReader(open(p),delimiter='\t'):
   try:
    n=int(row['n']);score=float(row['new']);f=p.parent/f'{n}.csv'
    if score>=scores[n]-1e-12 or not f.exists():continue
    A=loadpack(f,{n})[n]
    if not credit(n,A,str(f)):continue
    P[n]=A;origins[n]=str(f);scores[n]=score
   except (ValueError,KeyError,OSError):continue
 frozen={n:dict(r) for n,r in rows.items()}
 if not posted:
  for p in sorted(S.glob('take-*-r24/take.tsv')):
   for row in csv.DictReader(open(p),delimiter='\t'):
    try:
     n=int(row['n']);score=float(row['new']);f=p.parent/f'{n}.csv'
     if score>=float(frozen[n]['score'])-1e-12 or not f.exists():continue
     A=loadpack(f,{n})[n]
     if credit(n,A,str(f)):frozen[n].update(score=repr(score),L=repr((score+1)*n**.5))
    except (ValueError,KeyError,OSError):continue
 with open(W/'details-base25.csv.tmp','w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(next(iter(frozen.values())).keys()));wr.writeheader();wr.writerows(frozen.values())
 (W/'details-base25.csv.tmp').replace(W/'details-base25.csv')
 (W/'bars.tsv.tmp').write_text(''.join(f'{n}\t{(scores[n]+1)*n**.5:.14f}\t{scores[n]!r}\t{origins[n]}\n' for n in sorted(P)));(W/'bars.tsv.tmp').replace(W/'bars.tsv')
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r25-ssh','-q',str(W/'bars.tsv'),'boxE:scratch/squares-k123/bars.tmp'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r25-ssh','boxE','cd $SCRATCH/squares-k123 && mv bars.tmp bars.tsv'],check=True)
 return P,origins
