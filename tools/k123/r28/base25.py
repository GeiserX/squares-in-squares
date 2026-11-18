"""Use the posted round25b bar and clean live round26 improvements."""
import csv,json,pathlib,re,subprocess,os
import numpy as np
from provenance24 import W,S,mlp,credit,key,base,R
_LAYOUT_CACHE={}
def loadpack(path,want=None):
 p=pathlib.Path(path);st=p.stat();t=(str(p),st.st_mtime_ns,st.st_size)
 if t not in _LAYOUT_CACHE:_LAYOUT_CACHE[t]=mlp.load(str(p))
 d=_LAYOUT_CACHE[t];return d if want is None else {n:d[n] for n in want if n in d}
def paths():return S/'gather/round26-2026-11-14b.csv',S/'gate/cand-round26-1114b/details.csv',True
_bound=False
def _current():
 global _bound
 p,det,_=paths();P=dict(loadpack(p));origins={n:'held' for n in P};rows={int(r['n']):r for r in csv.DictReader(open(det))};scores={n:float(r['score']) for n,r in rows.items()}
 scores={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round28-briefs/bar28.tsv'),delimiter='\t')}
 if not _bound:
  # Bind the exact posted layout to the assembler's per-n source table.
  tables_to_bind=[R/f'results/round{roundn}-best-2026-11-{day}.tsv' for roundn,day in [(24,'13'),(25,'14'),(26,'14')]]
  for table in tables_to_bind:
   if table.exists():
    for z in csv.DictReader(open(table),delimiter='\t'):
     n=int(z['n'])
     try:s=float(z.get('score',z.get('new','nan')))
     except ValueError:continue
     if not np.isfinite(s) or abs(s-float(rows[n]['score']))>1e-8:continue
     base()[key(n,P[n])]=dict(clean=True,n=n,origin='held round26b',table=str(table),source=z['source'],licence=z.get('licence',''),sha256_geometry=key(n,P[n]))
  base()[key(801,P[801])]=dict(clean=True,n=801,origin='held own801',source='held n = 801 of round 26; gather/round26-2026-11-14b.csv n = 801; historical source samanyu1808/sis-final-packings, CC0; held801 is allowed by the main round28 00:19:03Z rule',licence='own held mathematical layout; historical samanyu1808/sis-final-packings CC0; main round28 held801 allowance',sha256_geometry=key(801,P[801]))
  _bound=True
 for t in sorted([*S.glob('take-*-r27/take.tsv'),*S.glob('take-*-r28/take.tsv')]):
  for z in csv.DictReader(open(t),delimiter='\t'):
   try:
    n=int(z['n']);sc=float(z['new']);f=t.parent/f'{n}.csv'
    if sc>scores[n]+1e-12 or not f.exists():continue
    A=loadpack(f,{n})[n]
    if not credit(n,A,str(f)):continue
    P[n]=A;origins[n]=str(f);scores[n]=sc
   except (ValueError,KeyError,OSError):continue
 (W/'bars.tsv.tmp').write_text(''.join(f'{n}\t{(scores[n]+1)*n**.5:.14f}\t{scores[n]!r}\t{origins[n]}\n' for n in sorted(P)));(W/'bars.tsv.tmp').replace(W/'bars.tsv')
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r28-ssh','-q',str(W/'bars.tsv'),f'boxE:scratch/squares-k123/bars-{os.getpid()}.tmp'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r28-ssh','boxE',f'cd $SCRATCH/squares-k123 && mv bars-{os.getpid()}.tmp bars.tsv'],check=True)
 return P,origins

def current():
 import fcntl
 with open(W/'base.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  return _current()
