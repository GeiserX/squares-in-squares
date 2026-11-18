"""Freeze an already closed graph whose every leaf is a verified submitted row."""
import pathlib,json,re,hashlib,shutil,time
W=pathlib.Path(__file__).resolve().parent

def freeze(p,n,ancestry):
 from held32 import resolve
 graph=json.load(open(ancestry));nodes=graph.get('nodes',{})
 if not graph.get('ok')or graph.get('policy')!='strict28v1'or graph.get('n')!=n:return None
 leaves=[v for v in nodes.values()if not v.get('parents')]
 if not leaves:return None
 roots=[];own_roots=[]
 for node in leaves:
  m=re.match(r'our own construction: submitted held row n=(\d+), accepted (\S+) sha256 ([0-9a-f]{64});',node['source'])
  if not m:
   own=re.fullmatch(r'our own design; direct original Samanyu best-fit row n=(\d+); source (\S+) sha256 ([0-9a-f]{64})',node['source'])
   if not own:return None
   from held32 import S
   original=pathlib.Path(own[2])
   if original!=S/'seeds/samanyu_bestfit.csv'or not original.is_file()or hashlib.sha256(original.read_bytes()).hexdigest()!=own[3]:return None
   own_roots.append(dict(n=int(own[1]),path=str(original),sha256=own[3]));continue
  root=resolve(dict(n=int(m[1]),path=m[2],sha256=m[3]))
  if not root or node['record'].split(' n=')[0]!=root['ledger']:return None
  roots.append(root)
 if any(parent not in nodes for v in nodes.values()for parent in v.get('parents',[])):raise ValueError('missing graph parent')
 refs={str(p),str(ancestry)}
 for node in nodes.values():
  record=node.get('record','').split(' n=')[0]
  if pathlib.Path(record).is_file():refs.add(record)
  for ref in re.findall(r'($DATA/(?:scratch/bounties-squares|repos/personal/bounties)/[^\s";,<>]+?\.(?:csv|json|tsv))',node['source']):
   if pathlib.Path(ref).is_file():refs.add(ref)
 for root in roots:refs.add(root['path']);refs.add(root['ledger'])
 for root in own_roots:refs.add(root['path'])
 for ref in list(refs):
  path=pathlib.Path(ref)
  if path.suffix=='.json':
   try:d=json.load(open(path))
   except (OSError,ValueError):continue
   if isinstance(d,dict):
    full=d.get('full_ancestry')
    if isinstance(full,dict)and full.get('path')and full.get('sha256'):
     fp=pathlib.Path(full['path'])
     if not fp.is_file()or hashlib.sha256(fp.read_bytes()).hexdigest()!=full['sha256']:raise ValueError('changed origin full ancestry')
     refs.add(str(fp))
 pinroot=W/'pins';pinroot.mkdir(exist_ok=True);snapshots=[];texts=[]
 for ref in sorted(refs):
  path=pathlib.Path(ref);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();dest=pinroot/(digest+path.suffix)
  if not dest.exists():dest.write_bytes(raw)
  if dest.read_bytes()!=raw:raise ValueError('changed content-addressed pin')
  snapshots.append(dict(original=ref,path=str(dest),sha256=digest,original_mtime_ns=path.stat().st_mtime_ns))
  if path.suffix=='.json':texts.append((ref,raw.decode()))
 key=hashlib.sha256((hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()+hashlib.sha256(pathlib.Path(ancestry).read_bytes()).hexdigest()+'submitted-held32-v1').encode()).hexdigest()
 evidence=dict(policy='submitted-owned33-v1',public_first=False,clean=True,hits=[],time=time.strftime('%FT%TZ',time.gmtime()),input_sha256=hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest(),n=n,share=0.0,texts=texts,snapshots=snapshots,ancestry=str(ancestry),ancestry_sha256=hashlib.sha256(pathlib.Path(ancestry).read_bytes()).hexdigest(),submitted_roots=roots,own_seed_roots=own_roots)
 out=W/'evidence'/(key+'.json')
 if not out.exists():out.write_text(json.dumps(evidence,separators=(',',':')))
 return dict(clean=True,hits=[],path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest())
