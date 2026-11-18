"""Check actual extra-box trials against the disjoint signature assignment."""
from pathlib import Path
import json,hashlib,re,collections,time
W=Path(__file__).resolve().parent;rows=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines() if l.strip()];extra=[r for r in rows if r['worker'] in ['j22e','j22f','j22g','j22h']];assert extra,'no extra-box completion copied yet'
keys=[];cache={}
for r in extra:
 pool=r['pool'];p=W/pool/('sources-'+pool+'.json')
 if pool not in cache:cache[pool]=json.load(p.open())
 meta=cache[pool];ns=re.match(r'(\d+)r?-(\d+)r?-j',r['tag']).groups();roots=[(n,meta[n]['sha256_geometry'],meta[n].get('ancestry_sha256','')) for n in ns]
 # This is the byte string the numerical worker claimed. The measured start d is in its frozen queue row.
 q=W/'boxD-bridge33/boxCD-export33.tgz'
 import tarfile
 with tarfile.open(q) as a:queue=a.extractfile('queue.tsv').read().decode().splitlines()
 matches=[l.split('\t') for l in queue if len(l.split('\t'))>=8 and l.split('\t')[7]==pool and l.split('\t')[1]==r['tag'] and int(l.split('\t')[0])==r['n']];assert matches,(r['worker'],pool,r['tag'])
 for f in matches:
  mechanism=r.get('mechanism');raw=[r['tag'],f[3],roots]+([mechanism] if mechanism else []);signature=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest();assert int(signature[:8],16)%2==1,(r,signature)
  keys.append((pool,r['tag'],mechanism))
assert len(keys)==len(set(keys)),('duplicate extra-box completions',collections.Counter(keys))
record={'time':time.strftime('%FT%TZ',time.gmtime()),'extra_completions':len(extra),'unique_trials':len(set(keys)),'all_in_extra_partition':True,'workers':dict(collections.Counter(r['worker'] for r in extra))};(W/'partition-audit33.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
