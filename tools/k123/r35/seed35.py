"""Stage the held round 34 rows that changed, at their lowest current geometry."""
from pathlib import Path
import sys,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from base25 import current
from stage24 import stage,kj
from classes26 import read
P,o=current();classes={n:read(n,A,kj) for n,A in P.items() if n>=100}
for n in [790,808,735,683,640,582,489,653,998,928,995,811,753,687,925]:
 if not classes.get(n):print('no class',n,flush=True);continue
 partners=[nn for nn in classes if classes[nn] and classes[n]&classes[nn]]
 stage(f'licensed35{n:04}',P,o,[(n,nn) for nn in partners],'fresh-lowest-live',f'round35 lowest live changed row n={n}, source={o[n]}')
 print('seeded',n,len(partners),flush=True)
