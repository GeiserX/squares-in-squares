"""Bind an unpublished row to exact queue-time packing and producer records."""
from pathlib import Path
import json,csv,hashlib,re,os
RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
W=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):
 p.parent.mkdir(exist_ok=True,parents=True);q=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');q.write_bytes(data);q.replace(p)

def bind(row,manifest,donors,pool,key):
 D=W/'prepublish-bindings30'/key;D.mkdir(parents=True,exist_ok=True);M={};pins=[]
 from snapshot_nodes30 import credits
 all_credits=[manifest[str(n)] for n in donors]+credits({'source':row['source']})
 admitted_origins=set()
 for c in all_credits:
  donor=int(c['n']);origin=c.get('origin','');snap=c.get('input_file_snapshot');expected=c.get('input_file_sha256')
  if origin in admitted_origins:continue
  admitted_origins.add(origin)
  if not snap or re.search(r'/take-harvest-|/(?:public|public2|collector)/',origin):continue
  p=Path(snap);assert sha(p)==expected,(donor,'queue packing hash')
  records=c.get('input_record_snapshots',{});data=None;record_name=None
  for candidate in [origin+'.json',str(Path(origin).with_suffix('.json'))]:
   if candidate in records:
    rr=records[candidate];q=Path(rr['snapshot']);assert sha(q)==rr['sha256'];data=q.read_bytes();json.loads(data);record_name=candidate;break
  if data is None:
   record_name=str(Path(origin).parent/'take.tsv')
   if record_name not in records and c.get('ledger') in records:record_name=c['ledger']
   if record_name not in records:
    ledgers=[name for name in records if Path(name).name=='take.tsv'];assert len(ledgers)==1,(donor,'ambiguous queue producer ledger');record_name=ledgers[0]
   rr=records.get(record_name);assert rr,(donor,'queue producer record');q=Path(rr['snapshot']);assert sha(q)==rr['sha256'];r=next(r for r in csv.DictReader(q.open(),delimiter='\t') if r['n']==str(donor));data=json.dumps(r).encode()
  alias=D/f'{donor}-{expected}-{hashlib.sha256(data).hexdigest()[:16]}.csv';write(alias,p.read_bytes());M[origin]=str(alias);M[str(p)]=str(alias)
  if record_name.endswith('.json'):M[record_name]=str(alias)+'.json'
  origin_path=Path(origin)
  origin_mtime=c.get('input_file_mtime',origin_path.stat().st_mtime if origin_path.is_file() and sha(origin_path)==expected else p.stat().st_mtime)
  with (W/'input-aliases30.jsonl').open('a') as h:h.write(json.dumps({'alias':str(alias),'origin':origin,'sha256':expected,'origin_mtime':origin_mtime})+'\n')
  pins.append({'donor':donor,'origin':origin,'csv_snapshot':snap,'csv_sha256':expected,'record_name':record_name,'producer_sha256':rr['sha256'],'alias':str(alias)})
  write(Path(str(alias)+'.json'),data)
 if not M:return row
 P=W/pool;poolcsv=P/f'{pool}.csv'
 if poolcsv.exists():
  alias=D/f'pool-{sha(poolcsv)}.csv';write(alias,poolcsv.read_bytes());jobfile=P/f'{pool}.json';job=json.load(jobfile.open()) if jobfile.exists() else {'source':row['source']}
  if isinstance(job.get('source'),str):
   for a,b in M.items():job['source']=job['source'].replace(a,b)
  write(Path(str(alias)+'.json'),json.dumps(job).encode());M[str(poolcsv)]=str(alias);M[str(jobfile)]=str(alias)+'.json'
 cache={};active=set();csv_cache={}
 def transform(text):
  for a,b in sorted(M.items(),key=lambda z:-len(z[0])):text=text.replace(a,b)
  for name in set(re.findall(r'$DATA/[^\s,;<>"\\]+\.csv',text)):
   p=Path(name)
   if name.startswith(str(D)) or '/take-k123-' not in name or '/work/' not in name or not (p.stem==p.parent.name or p.stem.startswith('pool-')):continue
   if name not in csv_cache:
    sibling=Path(str(p)+'.json') if Path(str(p)+'.json').exists() else p.with_suffix('.json')
    if not p.is_file() or not sibling.is_file():continue
    rebound=proof(str(sibling))
    if rebound==str(sibling):continue
    body=Path(rebound).read_bytes();alias=D/f'pool-{sha(p)}-{hashlib.sha256(body).hexdigest()[:16]}.csv';write(alias,p.read_bytes());write(Path(str(alias)+'.json'),body);csv_cache[name]=str(alias)
   text=text.replace(name,csv_cache[name])
  for a in set(RX.findall(text)):
   b=proof(a)
   if a!=b:
    text=text.replace(a,b)
    if re.fullmatch('[0-9a-f]{64}',Path(a).stem) and Path(a).is_file() and sha(Path(a))==Path(a).stem:text=re.sub(r'(?<![\w/.-])'+re.escape(Path(a).stem)+r'(?![\w.-])',Path(b).stem,text)
  return text
 def proof(name):
  if name in cache:return cache[name]
  if name in active or name.startswith(str(D)):return name
  p=Path(name)
  if not p.is_file() or p.stat().st_size>20_000_000:return name
  active.add(name)
  try:
   before=p.read_text();after=transform(before)
   if before==after:cache[name]=name;return name
   json.loads(after);out=W/'ancestry'/(hashlib.sha256(after.encode()).hexdigest()+'.json');write(out,after.encode());cache[name]=str(out);return str(out)
  finally:active.remove(name)
 out={**row,'source':transform(row['source'])}
 # Rebind each exact producer sidecar too, without adding the mutable origin as an ancestry edge.
 for pin in pins:
  p=Path(pin['alias']+'.json');s=p.read_text();write(p,transform(s).encode())
 write(D/'binding-receipt.json',json.dumps({'pins':pins,'proofs':cache,'row':out},indent=2).encode())
 return out
