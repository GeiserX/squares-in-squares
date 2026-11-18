"""Pin newly permitted own original roots for fresh join scans."""
from pathlib import Path
import sys,json,csv,hashlib,time
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
D=W/'reopened';D.mkdir(exist_ok=True);src=S/'seeds/merged0.csv';raw=src.read_bytes();sha=hashlib.sha256(raw).hexdigest();snap=W/'input-snapshots'/('seed-merged0-'+sha+'.csv')
if not snap.exists():snap.write_bytes(raw)
P=mlp.load(str(snap),{503,801,983});made=[]
for n,A in P.items():
 p=D/f'{n}-own-original-root28.csv'
 with p.open('w') as f:
  wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle']);wr.writerows((n,i,*a) for i,a in enumerate(A))
 record=dict(n=n,source=f'original seed: n = {n} of Samanyu-dev/squares_in_squares matching own independently discovered packing; main00:19:03Z rule permits this own original root; seeds/merged0.csv',licence='own independently discovered mathematical layout; main round28 00:19:03Z',original_packing_snapshot=str(snap),original_packing_sha256=sha)
 Path(str(p)+'.json').write_text(json.dumps(record));made.append(str(p))
marker=W/'reopened-inputs27.txt';old=marker.read_text().splitlines();marker.write_text('\n'.join(dict.fromkeys(made+old))+'\n')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA REOPEN explicit own original roots503/801/983; whole merged0 byte snapshot SHA256{sha}, per-n records under work/reopened. Fresh endpoint queue; other remaining source exclusions still apply. Deadline16:25Z.\n')
print('original roots',made,flush=True)
