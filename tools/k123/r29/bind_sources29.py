"""Make certificate source edges use exact queued packing and producer records."""
from pathlib import Path
import sys,json,csv,hashlib,re,shutil,time,fcntl
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from source25 import atomic_text
from publication_source26 import check
states=json.load((W/'collect-state.json').open());rows=list(csv.DictReader((W.parent/'take.tsv').open(),delimiter='\t'));results=[]
RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for row in rows:
 n=int(row['n']);raw=W.parent/f'{n}.csv';digest=sha(raw);matches=[(k,r) for k,r in states.items() if r.get('status')=='published' and r['n']==n and (W/'certs'/k/'final'/f'{n}.csv').exists() and sha(W/'certs'/k/'final'/f'{n}.csv')==digest]
 assert matches,n
 key,state=matches[-1];pool=state['pool'];meta=json.load((W/pool/f'sources-{pool}.json').open());D=W/'bound-sources29'/str(n);D.mkdir(parents=True,exist_ok=True);M={};pins=[]
 for donor in state['donors']:
  c=meta[str(donor)];origin=c.get('origin','');snap=c.get('input_file_snapshot');expected=c.get('input_file_sha256')
  if not snap:continue
  # No fetched-public file is reclassified by this own-input binding.
  assert not re.search(r'/take-harvest-|/(?:public|public2|collector)/',origin),origin
  p=Path(snap);assert sha(p)==expected,(n,donor,'packing snapshot')
  records=c.get('input_record_snapshots',{});data=None;original_record=None
  for candidate in [origin+'.json',str(Path(origin).with_suffix('.json'))]:
   if candidate in records:
    rr=records[candidate];q=Path(rr['snapshot']);assert sha(q)==rr['sha256'];data=q.read_bytes();json.loads(data);original_record=candidate;record_sha=rr['sha256'];break
  if data is None:
   ledger=str(Path(origin).parent/'take.tsv');rr=records.get(ledger);assert rr,(n,donor,'no pinned producer record');q=Path(rr['snapshot']);assert sha(q)==rr['sha256'];producer=next(z for z in csv.DictReader(q.open(),delimiter='\t') if z['n']==str(donor));data=json.dumps(producer).encode();original_record=ledger;record_sha=rr['sha256']
  alias=D/f'{donor}-{expected}-{hashlib.sha256(data).hexdigest()[:16]}.csv';alias.write_bytes(p.read_bytes());Path(str(alias)+'.json').write_bytes(data);M[origin]=str(alias);M[str(p)]=str(alias)
  if original_record.endswith('.json'):M[original_record]=str(alias)+'.json'
  pins.append({'donor':donor,'origin':origin,'snapshot':snap,'sha256':expected,'producer_record':original_record,'producer_record_sha256':record_sha,'alias':str(alias),'sidecar_sha256':hashlib.sha256(data).hexdigest()})
 if not M:continue
 poolcsv=W/pool/f'{pool}.csv';poolalias=D/('pool-'+sha(poolcsv)+'.csv');poolalias.write_bytes(poolcsv.read_bytes());jobfile=W/pool/f'{pool}.json';job=json.load(jobfile.open()) if jobfile.exists() else {'source':state['source']}
 for a,b in M.items():
  if isinstance(job.get('source'),str):job['source']=job['source'].replace(a,b)
 Path(str(poolalias)+'.json').write_text(json.dumps(job));M[str(poolcsv)]=str(poolalias);M[str(jobfile)]=str(poolalias)+'.json'
 cache={};active=set();edits=[]
 def transform(text):
  for a,b in sorted(M.items(),key=lambda z:-len(z[0])):text=text.replace(a,b)
  for a in set(RX.findall(text)):
   b=proof(a)
   if b!=a:
    text=text.replace(a,b)
    if re.fullmatch('[0-9a-f]{64}',Path(a).stem):text=text.replace(Path(a).stem,Path(b).stem)
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
   json.loads(after);out=W/'ancestry'/(hashlib.sha256(after.encode()).hexdigest()+'.json');atomic_text(out,after);cache[name]=str(out);edits.append([name,str(out)]);return str(out)
  finally:active.remove(name)
 new=dict(row);new['source']=transform(row['source']);out=D/f'{n}.csv';shutil.copy(raw,out);Path(str(out)+'.json').write_text(json.dumps(new));result=check(out,new)
 rec={'n':n,'key':key,'certificate_sha256':digest,'clean':result['clean'],'hits':result['hits'],'files':result['files'],'pins':pins,'proof_edits':edits,'row':new};results.append(rec);(D/'binding-proof29.json').write_text(json.dumps(rec,indent=2));print(n,result['clean'],result['files'],result['hits'],flush=True)
(W/'all-source-bindings29.json').write_text(json.dumps(results,indent=2))
assert all(r['clean'] for r in results),'source binding failed; take unchanged'
lock=(W/'collect.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
current=list(csv.DictReader((W.parent/'take.tsv').open(),delimiter='\t'));states=json.load((W/'collect-state.json').open());applied=[]
for item in results:
 n=item['n'];r=next((r for r in current if r['n']==str(n)),None)
 if r is None or sha(W.parent/f'{n}.csv')!=item['certificate_sha256']:continue
 r['source']=item['row']['source'];states[item['key']]['source']=r['source'];states[item['key']]['source_binding_proof']=str(W/'bound-sources29'/str(n)/'binding-proof29.json');applied.append(n)
 from replacements25 import register
 register(W.parent/f'{n}.csv',r)
p=W.parent/'take.tsv.tmp'
with p.open('w',newline='') as f:
 wr=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(current)
p.replace(W.parent/'take.tsv');p=W/'collect-state.tmp';p.write_text(json.dumps(states));p.replace(W/'collect-state.json')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA BIND immutable queue-time geometry and producer records for retained rows '+str(applied)+'. All full source walks green; certified CSVs unchanged. Per-row proofs work/bound-sources29; live producer rewrites cannot change these parent edges. Deadline11:45Z.\n')
print('source bindings applied',applied,flush=True)
