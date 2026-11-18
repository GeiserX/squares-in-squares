"""Round 27 bar (round29-briefs/bar29.tsv) and live scores from source-admitted round 27 takes."""
from pathlib import Path
import sys,csv,re,json,os
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r29/work'
sys.path.insert(0,str(W))
sys.path.insert(0,'.');import nosamanyu29
import forensics_policy as FP
from source29 import allowed

def policy(source,licence):return FP.classify_text(source+' '+licence)
def label(source,licence):return licence+'; round 29 walk (Samanyu-dev check lifted; rules a and b and withdrawals checked)'
def base():
 # Round 27: the bar is round29-briefs/bar29.tsv, the lower of the held round 25 b row and the best certified round 26 take row.
 a={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round29-briefs/bar29.tsv'),delimiter='\t')}
 return a
def bars(exclude=None):
 a=base();live=dict(a)
 # A result counts only below the bar and below every live round 27 take with clean source cells.
 for p in B.glob('take-*-r29/take.tsv'):
  if exclude is not None and p.parent==Path(exclude):continue
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   # Round 28: every live row counts, whatever its source cell says (backlog 743 has a 'see the record' licence cell).
   if n in live:live[n]=min(live[n],s)
 return a,a,live,live
def reference(n,p,a,h):return a[n]
