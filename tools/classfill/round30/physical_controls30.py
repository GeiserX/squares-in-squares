from common29 import *
from light29 import load
from physical30 import key
P=[(.5,.5,0),(1.6,.5,math.pi/4)];Q=[(x,y,a+math.pi/2)for x,y,a in P]
assert key(P)==key(Q)
bad=list(Q);x,y,a=bad[0];bad[0]=(x+.01,y,a);assert key(P)!=key(bad)
checks=[]
for n,tag in [(653,'x92c938ec5de1'),(602,'x2287ebd66b30'),(741,'x8b029eff2a3f'),(902,'x4792122c22c7')]:
 raw=W/'inputs'/f'{n}-{tag}.csv';out=next(iter((W/'boxE/out').glob(f'near-{tag}/{n}.csv')),None)
 if out:checks.append(dict(n=n,changed=key(load(raw,{n})[n])!=key(load(out,{n})[n])))
print(json.dumps(checks),flush=True)
atomic(W/'physical-controls30.json',dict(passed=True,quarter_turn_invariant=True,changed_coordinate_distinct=True,actual_endpoints=checks))
note('CONTROL physical endpoint hash: quarter-turn-equivalent square angles agree, changed coordinate differs; actual endpoint results '+json.dumps(checks)+'. Legacy queue hashes retained for historical closure.')
