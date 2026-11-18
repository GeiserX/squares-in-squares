"""Round 26 base (gate/cand-round25-1114b) and live scores from source-admitted round 26 takes."""
from pathlib import Path
import sys,csv,re,json,os
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r26/work'
sys.path.insert(0,str(W))
sys.path.insert(0,'.');import forensics_policy as FP
from source26 import allowed

def policy(source,licence):return FP.classify_text(source+' '+licence)
def label(source,licence):return licence+'; Samanyu ancestry: none (recorded public/own roots)'
def base():
 gate=B/'gate/cand-round25-1114b/details.csv'
 # The main session posts the base in the handoff log. Only a newer round 25+ gate may replace it.
 hp=B/'handoff-r26.log'
 if hp.exists():
  for line in hp.read_text().splitlines():
   if 'main -> all: BASE ' not in line:continue
   for p in re.findall(r'(?:$DATA/[^\s,;]+|gate/[^\s,;]+)',line):
    q=Path(p) if p.startswith('/') else B/p
    q=q/'details.csv' if q.is_dir() else q
    if q.name=='details.csv' and q.exists() and 'cand-round2' in str(q) and not q.parent.name.endswith('1114a'):gate=q
 cache=W/'base-cache.json';key=str(gate)+':'+str(gate.stat().st_mtime_ns)+':v26'
 if cache.exists():
  try:
   data=json.load(open(cache))
   if data['key']==key:return {int(n):v for n,v in data['scores'].items()}
  except (ValueError,KeyError):pass
 a={int(r['n']):float(r['score']) for r in csv.DictReader(open(gate))}
 tmp=cache.with_suffix('.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(dict(key=key,gate=str(gate),scores=a)));tmp.replace(cache)
 return a
def bars(exclude=None):
 a=base();live=dict(a)
 # A result counts only below the base and below every live round 26 take with clean source cells.
 for p in B.glob('take-*-r26/take.tsv'):
  if exclude is not None and p.parent==Path(exclude):continue
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   if not allowed(r.get('source','') or '',r.get('licence','') or ''):continue
   if n in live:live[n]=min(live[n],s)
 return a,a,live,live
def reference(n,p,a,h):return a[n]
