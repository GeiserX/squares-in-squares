from pathlib import Path
import sys,json
sys.path.insert(0,'.')
import quench_walk as w
W=Path(__file__).resolve().parent;D=W/'certs/j22a-fresh10238-551r-599-j8-10-s-1/repair29';x=w.check(str(D/'551.csv'));p='$SCRATCH/bounties-squares/take-midm-r28/551.csv';seen=set()
for i in range(20):
 print('VIA',p,flush=True)
 if p in seen:break
 seen.add(p);p=w.LAST_VIA.get(p)
 if not p:break
print(x['hits'],flush=True)
for p in [str(D/'row.json'),str(W/'normalized29/551-948244f7f48a25f9291e533e693fefd247c22290fc15c80c5a4d9fc338af222d.csv.json')]:
 t=Path(p).read_text();print('PATH',p,'backlog reference count',t.count('take-backlog-r29/551.csv'),'midm reference count',t.count('take-midm-r28/551.csv'))
