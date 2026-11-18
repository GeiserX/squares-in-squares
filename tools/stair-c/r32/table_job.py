"""Tabulate one module in a process that the serial worker can stop."""
import os,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_guard as G
import corner_stacks as K
G.install();K.install()
source,target=sys.argv[1:3]
q=pickle.load(open(source,'rb'));table=M.tabulate(q)
p=Path(target);temp=p.with_name(p.name+'.tmp');temp.write_bytes(pickle.dumps(table));temp.replace(p)
print('TABLE RESULT',q['id'],flush=True)
