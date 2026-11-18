"""Round 25 base and live scores from source-admitted rows."""
from pathlib import Path
import sys,csv,re,json
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r25/work'
sys.path.insert(0,str(W));from admit25 import store
sys.path.insert(0,'.');import forensics_policy as FP
from source25 import allowed

def policy(source,licence):return FP.classify_text(source+' '+licence)
def label(source,licence):return licence+'; Samanyu ancestry: none (recorded public/own roots)'
def base():
 gate=B/'gate/cand-round23-1113b/details.csv';posted=False
 for line in (B/'handoff-r25.log').read_text().splitlines():
  if 'main -> all: BASE ' not in line:continue
  paths=re.findall(r'(?:$DATA/[^\s,;]+|gate/[^\s,;]+)',line)
  for p in paths:
   q=Path(p) if p.startswith('/') else B/p
   q=q/'details.csv' if q.is_dir() else q
   if q.name=='details.csv' and q.exists():gate=q;posted=True
 cache=W/'base-cache.json';key=str(gate)+':'+str(gate.stat().st_mtime_ns)+':v25q-selected'
 if cache.exists():
  data=json.load(open(cache))
  if data['key']==key:return {int(n):v for n,v in data['scores'].items()}
 a={int(r['n']):float(r['score']) for r in csv.DictReader(open(gate))}
 if not posted:
  for p in B.glob('take-*-r24/take.tsv'):
   for r in csv.DictReader(open(p),delimiter='\t'):
    if not allowed(r.get('source',''),r.get('licence','')):continue
    ok,proof=store(dict(source=r['source'],licence=r['licence']),n=int(r['n']))
    missing_only=bool(proof['closure']['roots']) and bool(proof['closure']['errors']) and all(e[1] in ['missing recorded ancestor','missing source record'] for e in proof['closure']['errors'])
    if ok or missing_only:a[int(r['n'])]=min(a[int(r['n'])],float(r['new']))
 tmp=cache.with_suffix('.'+str(__import__('os').getpid())+'.tmp');tmp.write_text(json.dumps(dict(key=key,scores=a)));tmp.replace(cache)
 return a
def bars(exclude=None):
 a=base();live=dict(a)
 # Scores of every frozen row give a conservative search bound, including rows unusable as donors.
 for p in B.glob('take-*-r24/take.tsv'):
  for r in csv.DictReader(open(p),delimiter='\t'):
   live[int(r['n'])]=min(live[int(r['n'])],float(r['new']))
 for p in B.glob('take-*-r25/take.tsv'):
  if exclude is not None and p.parent==Path(exclude):continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   if not allowed(r.get('source',''),r.get('licence','')):continue
   live[int(r['n'])]=min(live[int(r['n'])],float(r['new']))
 return a,a,live,live
def reference(n,p,a,h):return a[n]
