"""Apply the round 24 handoff's separate reference for seed-free held counts."""
from pathlib import Path
import sys,csv
sys.path.insert(0,'.')
import forensics_policy as FP
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares')
def policy(source,licence):return FP.classify_text(source+' '+licence)
def label(source,licence):
 p=policy(source,licence)
 return licence+'; '+FP.label(p)
def bases():
 a={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round23-1113a/details.csv'))}
 h={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round22-1113b/details.csv'))}
 return a,h
def bars(exclude=None):
 a,h=bases();sam=dict(a);free={n:(h[n] if n in FP.RELAXED else a[n]) for n in a}
 for path in B.glob('take-*-r24/take.tsv'):
  if exclude is not None and path.parent==Path(exclude):continue
  for row in csv.DictReader(open(path),delimiter='\t'):
   try:n=int(row['n']);s=float(row['new'])
   except (KeyError,ValueError):continue
   p=policy(row.get('source',''),row.get('licence',''))
   sam[n]=min(sam[n],s)
   if n not in FP.RELAXED or p['status']=='none':free[n]=min(free[n],s)
 return a,h,sam,free
def reference(n,p,a,h):return FP.reference(n,p,a,h)
