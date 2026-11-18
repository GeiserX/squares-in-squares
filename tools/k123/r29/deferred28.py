"""Scan omitted partners on current, newly pinned endpoints after each fresh pass."""
import pathlib,json,hashlib,time,sys
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from stage24 import stage,current,S,mlp
P,orig=current();began=time.time();sf=W/'deferred-progress28.json';progress=json.loads(sf.read_text()) if sf.exists() else {};count=0
for path in [W/'pre-admission-deferred27.jsonl',S/'take-k123-r28/work/pre-admission-deferred27.jsonl']:
 if not path.exists():continue
 for line in path.read_text().splitlines():
  if time.time()-began>25:break
  j=json.loads(line);sig=hashlib.sha256((str(path)+line).encode()).hexdigest();offset=progress.get(sig,0)
  chosen=set(j['selected']);remaining=[(a,b) for a,b in j['planned_pairs'] if a not in chosen or b not in chosen]
  if offset>=len(remaining):continue
  # This is a changed-current-end queue, not an exact replay of an absent frozen pool.
  # Every dispatched current array is byte-pinned by stage() before transfer.
  source=pathlib.Path(j['source']);pp=dict(P);oo=dict(orig)
  if source.is_file():
   try:
    q=mlp.load(str(source))
    if len(q)==1:
     n,A=next(iter(q.items()));pp[n]=A;oo[n]=str(source)
   except (ValueError,KeyError,OSError):pass
  batch=remaining[offset:offset+12];progress[sig]=offset+12
  batch=[(a,b) for a,b in batch if a in pp and b in pp]
  if not batch:continue
  tag='deferred29'+sig[:10]+'x'+str(offset)
  stage(tag,pp,oo,batch,'deferred-current',f'current endpoints of {j["source"]}; omitted partners from {path}, tag {j["tag"]}, offset {offset}')
  sf.write_text(json.dumps(progress));count+=1
  if count>=2:break
 if count>=2:break
sf.write_text(json.dumps(progress));print('deferred-current batches',count,'visited',len(progress),flush=True)
