"""One bounded bar-side kick on changed rectangle geometry."""
import csv,json,time
from pathlib import Path
import numpy as np
import midm_scan as ms


def run(fq, root, side, x, target, deadline, seed, seconds=900):
    root=Path(root);root.mkdir(exist_ok=True)
    requested_target=target
    live_file=root.parents[1]/'bar-sides34.json'
    live_sha=None
    if live_file.exists() and time.time()-live_file.stat().st_mtime<120:
        import hashlib
        payload=live_file.read_bytes();live=json.loads(payload)
        target=min(target,float(live.get(str(len(x)),target)))
        live_sha=hashlib.sha256(payload).hexdigest()
        (root/'bar-input.json').write_bytes(payload)
    limit=min(deadline,time.time()+seconds)
    rng=np.random.default_rng(seed)
    best=side;answer=None;current=x.copy();records=[];turn=0
    while time.time()<limit-.2:
        moved=current.copy()
        flags=['--loosen','1.0']
        if turn%2:
            flags+=['--kick',str(rng.choice([.003,.01,.02,.04]))]
        elif turn:
            centre=int(rng.integers(len(moved)))
            radius=float(rng.choice([1.2,1.8,2.5]));sigma=float(rng.choice([.03,.06,.12]))
            mask=np.linalg.norm(moved[:,:2]-moved[centre,:2],axis=1)<radius
            moved[mask,:2]+=rng.normal(0,sigma,(int(mask.sum()),2))
            moved[mask,2]+=rng.normal(0,20*sigma,int(mask.sum()))
        # Every leg begins with the smaller of the live bar and best measured side.
        start=min(target,best)
        end,y=ms.quench(fq,str(root),start,moved,flags,timeout=min(180,limit-time.time()))
        records.append(dict(turn=turn,input_side=start,end=end,flags=flags))
        if y is not None and end<best:
            best=end;answer=y;current=y.copy()
            np.savetxt(root/'best-fq.csv',current,delimiter=',')
            (root/'best-side.json').write_text(json.dumps(dict(side=best,seed=seed,turn=turn)))
        turn+=1
        (root/'bar-kick-progress.json').write_text(json.dumps(dict(seed=seed,target=target,start=side,end=best,tries=records)))
        if time.time()>limit-seconds+120 and not any(r['end'] is not None and r['end']<min(side,target)-max(1e-9,1e-10*len(x)**.5) for r in records):
            break
    (root/'bar-kick.json').write_text(json.dumps(dict(seed=seed,target=target,requested_target=requested_target,live_bars_sha256=live_sha,start=side,end=best,tries=records)))
    return (best,answer) if answer is not None else (None,None)
