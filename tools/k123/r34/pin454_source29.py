"""Bind the454 source to its queued412 version, preserving every packing byte."""
from pathlib import Path
import json,csv,hashlib,re,sys,shutil,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
D=W/'pin454-source29';D.mkdir(exist_ok=True);m=json.load((W/'fresh10542/sources-fresh10542.json').open());c=m['412'];origin=c['origin'];snap=Path(c['input_file_snapshot']);data=snap.read_bytes();assert hashlib.sha256(data).hexdigest()==c['input_file_sha256']
records=c['input_record_snapshots'];record=records[origin+'.json'];body=Path(record['snapshot']).read_bytes();assert hashlib.sha256(body).hexdigest()==record['sha256'];json.loads(body)
alias=D/('412-'+c['input_file_sha256']+'.csv');alias.write_bytes(data);Path(str(alias)+'.json').write_bytes(body)
M={origin:str(alias),origin+'.json':str(alias)+'.json',str(snap):str(alias)}
pool=W/'fresh10542/fresh10542.csv';poolalias=D/('pool-'+hashlib.sha256(pool.read_bytes()).hexdigest()+'.csv');poolalias.write_bytes(pool.read_bytes());pooljob=json.load(pool.with_suffix('.json').open());pooljob['source']=str(alias);Path(str(poolalias)+'.json').write_text(json.dumps(pooljob));M[str(pool)]=str(poolalias);M[str(pool.with_suffix('.json'))]=str(poolalias)+'.json'
cache={};active=set();edits=[];RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
def transform(text):
 for a,b in sorted(M.items(),key=lambda z:-len(z[0])):text=text.replace(a,b)
 for a in set(RX.findall(text)):
  b=proof(a)
  if a!=b:
   text=text.replace(a,b)
   if re.fullmatch(r'[0-9a-f]{64}',Path(a).stem):text=text.replace(Path(a).stem,Path(b).stem)
 return text

def proof(name):
 if name in cache:return cache[name]
 if name in active or name.startswith(str(D)):return name
 p=Path(name)
 if not p.exists() or p.stat().st_size>20_000_000:return name
 active.add(name)
 try:
  before=p.read_text();after=transform(before)
  if before==after:cache[name]=name;return name
  json.loads(after);sha=hashlib.sha256(after.encode()).hexdigest();out=W/'ancestry'/(sha+'.json');out.write_text(after);cache[name]=str(out);edits.append([name,str(out)]);return str(out)
 finally:active.remove(name)

row=next(r for r in csv.DictReader((W.parent/'take.tsv').open(),delimiter='\t') if r['n']=='454');original_source=row['source'];row['source']=transform(original_source)
raw=W.parent/'454.csv';out=D/'454.csv';shutil.copy(raw,out);Path(str(out)+'.json').write_text(json.dumps(row));(D/'row.json').write_text(json.dumps(row))
from publication_source26 import check
result=check(out,row);note={'clean':result['clean'],'hits':result['hits'],'files':result['files'],'input_sha256':c['input_file_sha256'],'producer_record_sha256':record['sha256'],'current_parent_sha256':hashlib.sha256(Path(origin).read_bytes()).hexdigest(),'unchanged_certificate_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'map':M,'proof_edits':edits}
(D/'binding-proof29.json').write_text(json.dumps(note,indent=2));print(json.dumps(note),flush=True)
