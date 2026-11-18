from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
import policy27
from provenance24 import mlp,credit
from source25 import retry_origin
p=W/'reopened/982-final-own-r25.csv';A=mlp.load(str(p),{982})[982]
retry_origin(str(p));accepted=bool(credit(982,A,str(p)));assert accepted
leaf='take-stair-c-r17/near/921-29e12ff3.csv';old=policy27.lines
try:
 policy27.lines=lambda:[(leaf,'2026-11-15T05:00:00Z source -> all: WITHDRAW '+leaf+'; overlapping input')]
 new_withdrawal=policy27.banned('$SCRATCH/bounties-squares/'+leaf)
 assert new_withdrawal
 excluded_file=policy27.banned('prvsiyan/squares-verified-best-of-1105')
 assert excluded_file
finally:policy27.lines=old
r={'old982_full_credit':accepted,'later_overlap_withdrawal_refused':new_withdrawal,'excluded_publication_refused':excluded_file}
(W/'seed-withdrawal-controls28.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
