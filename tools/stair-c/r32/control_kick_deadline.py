"""Bound a late kick separately from table search and reserve its final quench."""
import pathlib,sys
H=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[2])]
from kick_whole import kick_end
assert kick_end(100,2000,3000)==1000
assert kick_end(100,700,3000)==700
assert kick_end(100,2000,900)==750
assert kick_end(1000,700,3000)==700
start=11*3600+25*60;phase=11*3600+38*60;numeric=11*3600+45*60
assert kick_end(start,phase,numeric)==phase and phase>start
print('CONTROL kick deadline: fifteen-minute cap, phase cap,150-second final-quench reserve and expired phase respected; late follow can outlive table search')
