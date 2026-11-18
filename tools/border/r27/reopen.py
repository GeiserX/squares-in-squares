"""Round 27 item 2: the re-opened pool for the border driver and wfeed (read only).
1. every layout the r26 border gate refused (take-border-r26/work/source-rejections.jsonl), Samanyu reasons first;
2. the withdrawn folders and withdrawn near files of the frozen r22-r26 take dirs of other lanes;
3. per-n files of the re-opened seeds (seeds/samanyu_bestfit.csv, seeds/samanyu_22249.csv) and the held 921,
   written once into work/seedsplit/<name>/<n>.csv with a .json record (source and licence of the r27 brief).
Each item is (path, take.tsv row or None). batch(k) hands out the next k items once each."""
from pathlib import Path
import json,csv,re
S=Path('$SCRATCH/bounties-squares');W=Path(__file__).parent;T=W.parent
csv.field_size_limit(1<<26)
SAM=re.compile(r'29e12ff3|amanyu|921|985|747r|735|790')
POOL=None;POS=0
_rows={}
def rows_of(t):
 if t not in _rows:_rows[t]=_rows_of(t)
 return _rows[t]
def _rows_of(t):
 try:return {r['n']:r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
 except (OSError,ValueError,KeyError):return {}
def seed_files():
 out=[]
 specs=[('samanyu_bestfit',S/'seeds/samanyu_bestfit.csv',None),('samanyu_22249',S/'seeds/samanyu_22249.csv',None),('held921',S/'gather/round25-2026-11-14b.csv',{921})]
 for name,src,only in specs:
  d=W/'seedsplit'/name;d.mkdir(parents=True,exist_ok=True)
  if not (d/'done').exists():
   P={}
   for r in csv.DictReader(open(src)):
    n=int(r['n'])
    if n<30 or (only and n not in only):continue
    P.setdefault(n,[]).append(r)
   for n,rr in P.items():
    with open(d/f'{n}.csv','w') as f:
     w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
     for i,r in enumerate(rr):w.writerow([n,i,r['x'],r['y'],r['angle']])
    lic='ours: the round 27 brief (item 2) records that our own code found the layouts that match the Samanyu-dev/squares_in_squares seed'
    (d/f'{n}.json').write_text(json.dumps(dict(source=f'{src.relative_to(S)} n={n} (re-opened in round 27, item 2 of the brief)',licence=lic)))
   (d/'done').write_text('ok')
  out+=sorted(d.glob('*.csv'),key=lambda p:-int(p.stem))
 return out
def pool():
 global POOL
 if POOL is not None:return POOL
 items=[];seen=set()
 def add(p,r=None):
  p=Path(p)
  if str(p) in seen or not p.exists() or p.suffix!='.csv' or '/take-border-' in str(p):return
  try:
   if p.stat().st_size>1500000:return
  except OSError:return
  seen.add(str(p));items.append((p,r))
 rej=[json.loads(l) for l in open(S/'take-border-r26/work/source-rejections.jsonl')]
 rej.sort(key=lambda d:(0 if SAM.search(d['why']) else 1,-d.get('time',0)))
 for d in rej:
  p=Path(d['path'])
  if not str(p).startswith(str(S/'take-')):continue
  r=rows_of(p.parent).get(p.stem) if p.stem.isdigit() else None
  add(p,r)
 for t in sorted(S.glob('take-*-r2[2-6]'),reverse=True):
  for p in list(t.glob('work/withdrawn/*.csv'))+list(t.glob('work/*/withdrawn/*.csv'))+list(t.glob('near/*withdrawn*.csv')):add(p)
 for p in seed_files():add(p)
 POOL=items
 return POOL
def batch(k):
 global POS
 P=pool();out=P[POS:POS+k];POS+=len(out)
 return out
if __name__=='__main__':
 P=pool();print(len(P),'items;',sum(1 for p,_ in P if 'seedsplit' in str(p)),'seed files')
 import collections;print(collections.Counter(p.parts[5] if len(p.parts)>5 else '' for p,_ in P).most_common(30))
