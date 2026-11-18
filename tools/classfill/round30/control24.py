import sys
from pathlib import Path
sys.path.insert(0,str(Path('lane').resolve()))
import engine_fq,numpy as np
engine_fq.FQ=str(Path('fq').resolve())
s,Q,dt=engine_fq.quench(2.5,np.array([[.5,.5,0.],[2.,.5,0.]]),timeout=45)
assert s is not None and abs(s-2)<1e-7,(s,dt)
print('FQ_POSITIVE_CONTROL_PASS side 2.5 ->',repr(s),'seconds',dt,flush=True)
