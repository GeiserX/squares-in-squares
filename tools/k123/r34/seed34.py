"""Stage the four productive endpoint counts at their lowest current geometry."""
from pathlib import Path
import sys,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from base25 import current
from stage24 import stage,kj
from classes26 import read
P,o=current();classes={n:read(n,A,kj) for n,A in P.items() if n>=100}
for n in [259,445,968,734]:
 if not classes.get(n):continue
 partners=[nn for nn in classes if classes[nn] and classes[n]&classes[nn]]
 stage(f'licensed34{n:04}',P,o,[(n,nn) for nn in partners],'fresh-lowest-live',f'round34 lowest live productive endpoint n={n}, source={o[n]}')
 print('seeded',n,flush=True)
