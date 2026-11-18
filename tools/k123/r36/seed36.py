"""Stage the held round 35 rows that changed, at their lowest current geometry."""
from pathlib import Path
import sys,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from base25 import current
from stage24 import stage,kj
from classes26 import read
P,o=current();classes={n:read(n,A,kj) for n,A in P.items() if n>=100}
for n in [747, 803, 861, 860, 920, 693, 812, 869, 871, 806, 925, 864, 790, 546, 594, 808, 554, 809, 865, 807, 549, 746, 653, 702]:
 if (W/f'licensed36{n:04}'/f'licensed36{n:04}.json').exists():continue
 if not classes.get(n):print('no class',n,flush=True);continue
 partners=[nn for nn in classes if classes[nn] and classes[n]&classes[nn]]
 stage(f'licensed36{n:04}',P,o,[(n,nn) for nn in partners],'fresh-lowest-live',f'round36 lowest live changed row n={n}, source={o[n]}')
 print('seeded',n,len(partners),flush=True)
