"""Resolve harvest copies by exact producer hashes and notebook coordinates."""
import csv,hashlib,json,math,re
from pathlib import Path

def coords(path,n):
 out=[]
 for r in csv.DictReader(open(path)):
  k=int(r['n']) if 'n' in r else int(r['id'].split('_')[0])
  if k==n:
   sid=int(r.get('square_id',r.get('id','0_0').split('_')[-1]));out.append((sid,*[float(r[v].lstrip('s')) for v in ['x','y','angle']]))
 return [q[1:] for q in sorted(out)]
def exact_notebook(raw,public,n):
 a=coords(raw,n);b=coords(public,n);assert len(a)==len(b)==n
 err=max(abs(x-y) for p,q in zip(a,b) for x,y in zip(p,q));assert err<1e-10,('not an exact notebook row',err)
 return err

def resolve(path,n):
 p=Path(path);root=next((d for d in p.parents if re.match(r'take-harvest-r\d+$',d.name)),None)
 if root is None:return None
 pins=[]
 if '/collector/certified/' in str(p):
  receipts=[]
  for q in (root/'work/collector').glob('remote-*.json'):
   j=json.loads(q.read_text())
   if j.get('file')==str(p) and j.get('n')==n:receipts.append((q,j))
  assert len(receipts)==1,('ambiguous receipt',str(p),len(receipts));q,j=receipts[0];pins.append(q)
  wire=q.with_suffix('.csv');address=verify_receipt_name(p,wire,j)
  # The collector names the certified file by the raw wire hash, then dilates centres for floatsafe.
  aa=coords(p,n);wire_rows=coords(wire,n);preserved_input=hashlib.sha256(p.read_bytes()).hexdigest()==j['input_hash'];bb=aa if preserved_input else wire_rows;assert len(aa)==len(bb)==len(wire_rows)==n
  def extent(rows):
   hh=[.5*(abs(math.cos(a))+abs(math.sin(a))) for x,y,a in rows];return max(max(q[0]+h for q,h in zip(rows,hh))-min(q[0]-h for q,h in zip(rows,hh)),max(q[1]+h for q,h in zip(rows,hh))-min(q[1]-h for q,h in zip(rows,hh)))
  # Recover centre scale from the widest centre coordinate span.
  axis=max([0,1],key=lambda i:max(r[i] for r in bb)-min(r[i] for r in bb));lo=min(range(n),key=lambda k:bb[k][axis]);hi=max(range(n),key=lambda k:bb[k][axis]);scale=(aa[hi][axis]-aa[lo][axis])/(bb[hi][axis]-bb[lo][axis]);assert 1-1e-14<=scale<1+1e-9,scale
  offset=[aa[0][i]-scale*bb[0][i] for i in [0,1]];err=max(abs(u[i]-scale*v[i]-offset[i]) if i<2 else abs(math.remainder(u[i]-v[i],math.pi/2)) for u,v in zip(aa,bb) for i in range(3));assert err<1e-10,('certificate is not a uniform dilation',err)
  if address=='input':assert abs(extent(wire_rows)-float(j['remote_side']))<1e-9,('wire side differs from receipt',extent(wire_rows),j['remote_side'])
  pins.append(wire)
  jobs=[]
  for jp in (root/'work/jobs').glob('*'+j['input_hash']+'.json'):
   job=json.loads(jp.read_text())
   if job.get('n')==n and job.get('sha256')==j['input_hash']:jobs.append((jp,job))
  if not jobs:
   candidates=[q for q in (root/'work/starts').glob(str(n)+'-'+j['input_hash'][:16]+'*.csv') if hashlib.sha256(q.read_bytes()).hexdigest()==j['input_hash']]
   if len(candidates)==1:
    start=candidates[0];side=Path(str(start)+'.json');record=json.loads(side.read_text());assert record['n']==n and record.get('source') and record.get('licence');pins.extend([start,side])
    public=Path(record['src']);meta=public.parent/'meta.json';mj=json.loads(meta.read_text());entries=[v for v in mj['files'] if (v.get('file') if isinstance(v,dict) else v[0])==public.name];assert len(entries)==1
    entry=entries[0]
    if isinstance(entry,dict):assert hashlib.sha256(public.read_bytes()).hexdigest()==entry['sha256']
    else:assert public.stat().st_size==entry[1] and mj.get('session') and mj.get('lastRun')
    fit=verify_dilation(coords(start,n),coords(public,n));pins.extend([public,meta])
    return dict(source=record['source'],licence=record['licence'],pins=list(dict.fromkeys(str(q) for q in pins)),max_coordinate_error=fit['error'],certification_scale=fit['scale'],legacy_input_hash=j['input_hash'])
   start=root/'work/public/starts'/str(n)/f'{n}.csv';ledger=start.parent/'take.tsv'
   assert start.is_file() and hashlib.sha256(start.read_bytes()).hexdigest()==j['input_hash'],('legacy input hash differs',str(start))
   row=next(r for r in csv.DictReader(open(ledger),delimiter='\t') if int(r['n'])==n);pins.extend([start,ledger])
   return dict(source=row['source'],licence=row['licence'],pins=list(dict.fromkeys(str(q) for q in pins)),max_coordinate_error=None,legacy_input_hash=j['input_hash'])
  assert len(jobs)==1,('ambiguous input job',str(p));jp,job=jobs[0];inp=Path(job['path']);assert hashlib.sha256(inp.read_bytes()).hexdigest()==job['sha256'];pins.extend([jp,inp])
  if job.get('kind')!='fresh-public':
   assert job.get('source') and job.get('licence')
   return dict(source=job['source'],licence=job['licence'],pins=list(dict.fromkeys(str(q) for q in pins)),max_coordinate_error=err,metadata=job,first_source_public=job.get('public_first',False))
  side=Path(str(inp)+'.json');obj=json.loads(side.read_text());raw=Path(obj['original']);pins.extend([side,raw]);assert raw.is_file()
  src=job['source'];lic=job['licence']
 elif '/quick-starts/' in str(p):
  matches=[]
  for side in (root/'work/inputs').glob('*.csv.json'):
   obj=json.loads(side.read_text())
   if obj.get('original')==str(p) and obj.get('n')==n:matches.append((side,obj))
  assert len(matches)==1,('ambiguous quick row',str(p),len(matches));side,obj=matches[0]
  inp=Path(str(side)[:-5]);assert hashlib.sha256(inp.read_bytes()).hexdigest()==obj['queued_sha256'];pins.extend([side,inp,p]);src=obj['source'];lic=obj['licence'];raw=p
 else:return None
 m=re.search(r'raw file ([^;]+)',src);assert m,src
 public=Path(m[1]);meta=public.parent/'meta.json';mj=json.loads(meta.read_text());assert re.search(r'Apache|CC.?BY(?![- ]?SA)|CC0',mj['license'],re.I),mj['license']
 expected=next(q['sha256'] for q in mj['files'] if q['file']==public.name);assert hashlib.sha256(public.read_bytes()).hexdigest()==expected
 err=exact_notebook(raw,public,n);pins.extend([public,meta])
 return dict(source=src,licence=lic,pins=list(dict.fromkeys(str(q) for q in pins)),max_coordinate_error=err)


def verify_dilation(a,b):
 assert len(a)==len(b) and len(a)>1
 axis=max([0,1],key=lambda i:max(r[i] for r in b)-min(r[i] for r in b));lo=min(range(len(b)),key=lambda k:b[k][axis]);hi=max(range(len(b)),key=lambda k:b[k][axis]);scale=(a[hi][axis]-a[lo][axis])/(b[hi][axis]-b[lo][axis]);assert 1-1e-14<=scale<1+1e-9,scale
 offset=[a[0][i]-scale*b[0][i] for i in [0,1]];error=max(abs(u[i]-scale*v[i]-offset[i]) if i<2 else abs(math.remainder(u[i]-v[i],math.pi/2)) for u,v in zip(a,b) for i in range(3));assert error<1e-10,error
 return dict(scale=scale,error=error)


def verify_receipt_name(p,wire,j):
 wire_hash=hashlib.sha256(Path(wire).read_bytes()).hexdigest()
 if Path(p).stem==wire_hash:return 'wire'
 assert Path(p).stem==j['input_hash'],('neither wire nor input hash addresses certificate',str(p))
 assert j.get('remote_side') is not None,'input-addressed output lacks side receipt'
 return 'input'
