"""Tabulate one module in a process that the serial worker can stop."""
import os,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import corner_guard as G
import corner_stacks as K
G.install();K.install()
source,target=sys.argv[1:3]
q=pickle.load(open(source,'rb'))
use_sparse=q['kind']=='corner' and q.get('extra_stacks') and abs(q['f0']-.83867)<.035
if use_sparse:
 import hashlib,json
 assert json.load(open('sparse-control.json'))['helper_sha256']==hashlib.sha256(Path('sparse_table.py').read_bytes()).hexdigest()
 from sparse_table import tabulate
 table=tabulate(q)
else:table=M.tabulate(q)
p=Path(target);temp=p.with_name(p.name+'.tmp');temp.write_bytes(pickle.dumps(table));temp.replace(p)
print('TABLE RESULT',q['id'],flush=True)
