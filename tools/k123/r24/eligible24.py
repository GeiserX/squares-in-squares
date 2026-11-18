import csv,pathlib
from provenance24 import W,S
SPECIAL={228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}
A=S/'gate/cand-round23-1113a/details.csv';B=S/'gate/cand-round22-1113b/details.csv';E=W/'details-eligible24.csv'
if not E.exists():
 rows=list(csv.DictReader(open(A)));old={int(r['n']):r for r in csv.DictReader(open(B))}
 with open(E,'w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(old[int(r['n'])] if int(r['n']) in SPECIAL else r for r in rows)
BARS={int(r['n']):float(r['L']) for r in csv.DictReader(open(B)) if int(r['n']) in SPECIAL}
