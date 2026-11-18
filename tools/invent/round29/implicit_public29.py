"""Pin first-public archive rows named by the captured held-source resolver."""
import csv,hashlib,json,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r29/work'
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def capture(source,n):
 match=re.search(r'([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\s*::\s*([^ |;]+\.csv)',source)
 if not match:raise ValueError('held public source lacks its original file: '+source[:180])
 ref,filename=match.groups();filename=pathlib.Path(filename).name;folders=[S/'harvest'/kind/ref.replace('/','__')for kind in('nb','ds')];folder=next((p for p in folders if(p/filename).is_file()),None)
 if folder is None:raise ValueError('missing captured original public archive: '+ref+' :: '+filename)
 archive=folder/filename;meta=folder/'meta.json';st=archive.stat();mst=meta.stat();key=hashlib.sha256((str(archive)+':'+str(n)).encode()).hexdigest();index=W/'public-archive-index'/(key+'.json');index.parent.mkdir(exist_ok=True)
 stamp=[st.st_mtime_ns,st.st_size,mst.st_mtime_ns,mst.st_size]
 if index.exists():
  old=json.load(open(index))
  if old['stamp']==stamp and all(pathlib.Path(p['path']).is_file()and sha(p['path'])==p['sha256']for p in old['pins']if p['kind']!='full'):return old
 notice=json.load(open(meta));assert notice['ref']==ref
 pins=[];dest=W/'public-archive-pins';dest.mkdir(exist_ok=True)
 for kind,path in [('full',archive),('notice',meta)]:
  digest=sha(path);p=dest/(digest+path.suffix)
  if not p.exists():p.write_bytes(path.read_bytes())
  if sha(p)!=digest:raise ValueError('changed archived public pin')
  pins.append(dict(kind=kind,original=str(path),path=str(p),sha256=digest))
 full=pathlib.Path(next(pin['path']for pin in pins if pin['kind']=='full'))
 with full.open()as stream:
  reader=csv.DictReader(stream);fields=reader.fieldnames;rows=[]
  for row in reader:
   count=row.get('n',row.get('id','').split('_')[0]).lstrip('s')
   if count.isdigit()and int(count)==n:
    row=dict(row,n=str(n));row.update({k:str(row[k]).lstrip('s')for k in('x','y')});rows.append(row)
 if len(rows)!=n:raise ValueError('missing per-count public archive row '+ref+' n='+str(n))
 import io
 stream=io.StringIO(newline='');fields=list(dict.fromkeys(fields+['n']));writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows);payload=stream.getvalue().encode();digest=hashlib.sha256(payload).hexdigest();p=dest/(digest+'.csv')
 if not p.exists():p.write_bytes(payload)
 pins.append(dict(kind='subset',original=str(archive)+' n='+str(n),path=str(p),sha256=digest));upstream=[]
 for name in('per_n_source_table.csv','per_n.csv','sources.csv'):
  path=folder/name
  if not path.is_file():continue
  with path.open()as stream:upstream += [row for row in csv.DictReader(stream)if row.get('n')==str(n)]
  digest=sha(path);q=dest/(digest+'.csv')
  if not q.exists():q.write_bytes(path.read_bytes())
  pins.append(dict(kind='upstream',original=str(path),path=str(q),sha256=digest))
 if not all(pathlib.Path(pin['path']).is_file()and sha(pin['path'])==pin['sha256']for pin in pins):raise ValueError('changed supplemental public archive pin')
 out=dict(stamp=stamp,n=n,source=ref+' :: '+filename,licence=notice.get('license',''),original=str(archive),path=str(p),sha256=digest,pins=pins,upstream=upstream)
 # The subset hash is distinct from any later upstream table hash.
 out['sha256']=sha(p);tmp=index.with_suffix('.tmp');tmp.write_text(json.dumps(out));tmp.replace(index);return out
