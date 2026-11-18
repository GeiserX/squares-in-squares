import pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from base25 import current
from stage24 import stage,kj
from classes26 import read
from provenance24 import credit
P,o=current();n=910
assert credit(n,P[n],o[n]),o[n]
t=read(n,P[n],kj);pairs=[]
for nn,A in P.items():
 if nn<100:continue
 tt=read(nn,A,kj)
 if tt and t&tt:pairs.append((n,nn))
stage('licensed40000',P,o,pairs,'licensed-new-910','new licensed midm910, bare972 start resolved by bytes and full licence proof')
