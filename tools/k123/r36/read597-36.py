from pathlib import Path
import sys,json
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
import k123_join as kj
from classes26 import read
p=W.parent/'597.csv';A=mlp.load(str(p),{597})[597];X=kj.Lay(597,*kj.norm(A),'597');print({'n':597,'chains':len(X.G),'class':str(read(597,A,kj)),'in_fresh_seen':str(p) in json.load(open(W/'fresh-seen.json'))})
