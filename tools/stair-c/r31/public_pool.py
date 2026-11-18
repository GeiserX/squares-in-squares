"""Read every harvested1105 coordinate version and retain its exact archive pins."""
import csv,hashlib,io,json,pickle,sys,zipfile
from pathlib import Path
import numpy as np
S=Path('$SCRATCH/bounties-squares');W=S/'take-stair-c-r31/work'
def pool():
 paths=sorted(set(S.glob('harvest*/ds/prvsiyan__squares-verified-best-of-1105/*.zip'))|set(S.glob('take-harvest-r*/work/*/data/ds/prvsiyan__squares-verified-best-of-1105/*.zip')))
 signature=[(str(p),p.stat().st_size,p.stat().st_mtime_ns)for p in paths]
 cache=W/'all-public-references.pkl'
 if cache.exists():
  old=pickle.load(cache.open('rb'))
  if old['signature']==signature:return old['rows']
 rows={};seen_files=set();seen_rows={};receipts=[]
 for p in paths:
  with zipfile.ZipFile(p)as z:
   for name in z.namelist():
    if not name.endswith('.csv'):continue
    raw=z.read(name);sha=hashlib.sha256(raw).hexdigest()
    if sha in seen_files:continue
    seen_files.add(sha);by={}
    for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
     k={str(a).strip().lower():v for a,v in r.items()}
     if 'x'not in k or 'y'not in k:continue
     n=str(k.get('n',str(k.get('id','')).split('_')[0])).lstrip('s')
     if n.isdigit():by.setdefault(int(n),[]).append((float(str(k['x']).lstrip('s')),float(str(k['y']).lstrip('s'))))
    included=[]
    for n,a in by.items():
     if len(a)!=n:continue
     a=np.asarray(a,float);a-=(a.min(0)+a.max(0))/2
     sort=np.lexsort((a[:,1],a[:,0]));key=hashlib.sha256(np.round(a[sort],11).tobytes()).hexdigest()
     if key in seen_rows.setdefault(n,set()):continue
     seen_rows[n].add(key);rows.setdefault(n,[]).append(a);included.append(n)
    if included:receipts.append(dict(archive=str(p),archive_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),member=name,member_sha256=sha,counts=included))
 value=dict(signature=signature,rows=rows);temp=cache.with_suffix('.tmp');pickle.dump(value,temp.open('wb'));temp.replace(cache)
 (W/'all-public-reference-receipt.json').write_text(json.dumps(dict(archives=len(paths),coordinate_members=receipts,counts=len(rows),versions=sum(map(len,rows.values()))),indent=2))
 return rows
if __name__=='__main__':
 rows=pool();print('REFERENCE POOL counts',len(rows),'per-count versions',sum(map(len,rows.values())),'972versions',len(rows.get(972,[])),flush=True)
