from pathlib import Path
import sys,traceback
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit
p='$SCRATCH/bounties-squares/take-forensics-r35/920.csv'
try:
 A=mlp.load(p,{920})[920];c=credit(920,A,p);print(bool(c))
except Exception:traceback.print_exc()
