"""Replace one missing historical producer with its exact byte-pinned CSV and ledger row."""
from pathlib import Path
import csv,json,re,hashlib,shutil,time,sys
W=Path(__file__).resolve().parent;S=W.parent.parent;csv.field_size_limit(1<<28)
OLD=str(S/'take-midm-r28/551.csv');SNAP=S/'take-k123-r28/work/input-snapshots/551-d02848915270cc38efe67cb1a657213913a184b1ce0de378501aee6d1614d495.csv';SHA='d02848915270cc38efe67cb1a657213913a184b1ce0de378501aee6d1614d495'
LEDGER=S/'take-k123-r28/work/input-snapshots/c39c34a38e0ffb48c242c17c1b47dc2874f73f2f261756046f3eb5424855b2ac.tsv';LSHA='c39c34a38e0ffb48c242c17c1b47dc2874f73f2f261756046f3eb5424855b2ac'
def verified_bytes(p,sha):
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha,(str(p),'snapshot hash mismatch');return raw
assert not Path(OLD).exists()
raw=verified_bytes(SNAP,SHA);verified_bytes(LEDGER,LSHA)
producer=next(r for r in csv.DictReader(LEDGER.open(),delimiter='\t') if r['n']=='551')
D=W/'normalized29';D.mkdir(exist_ok=True)
assert not (D/'FROZEN').exists(), 'source graph already frozen; use a new version directory'
fixed=D/('551-'+SHA+'.csv');fixed.write_bytes(raw)
row={'n':551,'source':producer['source'],'licence':producer['licence'],'producer_csv_snapshot':str(SNAP),'producer_csv_sha256':SHA,'producer_record_snapshot':str(LEDGER),'producer_record_sha256':LSHA,'historical_producer_lane':'midm round28','historical_producer_n':551}
Path(str(fixed)+'.json').write_text(json.dumps(row))
# Content-addressed proof copies retain each source and replace only resolvable CSV/proof edges.
RX=re.compile(r'$DATA/[^\s,;<>"\\]+\.(?:csv|json)')
cache={OLD:str(fixed)};active=set();edits=[];began=time.time();limit=240

def transform(text):
 if not isinstance(text,str):return text
 text=text.replace(OLD,str(fixed))
 text=re.sub(r'(?<![A-Za-z0-9/_-])take-midm-r28/551\.csv',str(fixed),text)
 changes={}
 for rel in set(re.findall(r'(?<![A-Za-z0-9/_-])(take-[a-z0-9-]+-r\d+/[^\s,;<>"\\]+\.csv)',text)):
  q=repair(str(S/rel))
  if q!=str(S/rel):text=text.replace(rel,q)
 for p in set(RX.findall(text)):
  q=repair(p)
  if q!=p:changes[p]=q
 for p,q in sorted(changes.items(),key=lambda z:-len(z[0])):
  text=text.replace(p,q)
  if re.search(r'/ancestry/[0-9a-f]{64}\.json$',p):text=text.replace(Path(p).stem,Path(q).stem)
 return text

def repair(name):
 if time.time()-began>limit:raise TimeoutError('bounded provenance reconstruction')
 if name in cache:return cache[name]
 if name in active:return name
 p=Path(name)
 if not p.exists():cache[name]=name;return name
 proof=p.suffix=='.json'
 take=p.suffix=='.csv' and bool(re.search(r'/take-[a-z0-9-]+-r\d+/',name))
 if not proof and not take:cache[name]=name;return name
 active.add(name)
 try:
  if proof:
   before=p.read_text();after=transform(before)
   if after==before:cache[name]=name;return name
   # The source is JSON. Any changed proof hash has been rebound in the referring text.
   json.loads(after);sha=hashlib.sha256(after.encode()).hexdigest();out=W/'ancestry'/(sha+'.json');out.write_text(after)
  else:
   ledger=p.parent/'take.tsv'
   if p.stem.isdigit() and ledger.exists():
    r=next((r for r in csv.DictReader(ledger.open(),delimiter='\t') if r['n']==p.stem),None)
   else:
    sidecars=[z for z in [Path(str(p)+'.json'),p.with_suffix('.json')] if z.exists()]
    r={'source_records':[json.load(z.open()) for z in sidecars]} if sidecars else None
   if not r:cache[name]=name;return name
   before=json.dumps(r);after=transform(before)
   if after==before:cache[name]=name;return name
   r=json.loads(after);data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();out=D/(p.stem+'-'+sha+'.csv')
   out.write_bytes(data);Path(str(out)+'.json').write_text(json.dumps(r))
  cache[name]=str(out);edits.append({'from':name,'to':str(out)});return str(out)
 finally:active.discard(name)

if __name__=='__main__':
 job=Path(sys.argv[1]);rows=list(csv.DictReader((job/'out/take.tsv').open(),delimiter='\t'));r=rows[0];r['licence']=sys.argv[2] if len(sys.argv)>2 else r['licence']
 before=r['source'];r['source']=transform(before)
 # Also repair the restored producer's own source graph if a nested take edge moved.
 pr=Path(str(fixed)+'.json');obj=json.load(pr.open());obj['source']=transform(obj['source']);pr.write_text(json.dumps(obj))
 out=job/'repair29';out.mkdir(exist_ok=True);shutil.copy(job/'out'/f'{r["n"]}.csv',out/f'{r["n"]}.csv');(out/'row.json').write_text(json.dumps(r));Path(str(out/f'{r["n"]}.csv')+'.json').write_text(json.dumps(r))
 from publication_source26 import check
 result=check(out/f'{r["n"]}.csv',r)
 proof={'clean':result['clean'],'hits':result['hits'],'edits':edits,'seconds':time.time()-began,'snapshot_sha256':SHA,'ledger_sha256':LSHA,'before_source_chars':len(before),'after_source_chars':len(r['source'])}
 (out/'repair-proof29.json').write_text(json.dumps(proof,indent=2));print(json.dumps(proof),flush=True)
