"""Round 29 base bar for the border lane: round29-briefs/bar29.tsv (the lower of the held round 27 b file and the
best certified round 28 take row, per n). Written once as a details-style csv (n,score) in this work dir.
A later 'main -> all: BASE ...' line in handoff-r29.log naming a gate dir lowers the bar further (min per n)."""
from pathlib import Path
import csv,re,sys
csv.field_size_limit(16*1024*1024)
S=Path('$SCRATCH/bounties-squares');W=Path(__file__).parent
BAR=S/'round29-briefs/bar29.tsv';DET=W/'bar29-details.csv'
_cache={}
def base_line():
 h=S/'handoff-r29.log'
 if not h.exists():return None
 for line in reversed(h.read_text().splitlines()):
  if re.search(r'\bmain\s*->\s*all:\s*BASE\b',line):
   m=re.search(r'(?:$SCRATCH/bounties-squares/)?(gate/[A-Za-z0-9_.-]+)',line)
   if m and (S/m[1]/'details.csv').exists() and 'cand-round25-1114a' not in m[1]:return S/m[1]/'details.csv',line
 return None
def base():
 found=base_line();key=str(found[0]) if found else ''
 if key in _cache:return _cache[key]
 held={int(r['n']):float(r['bar']) for r in csv.DictReader(open(BAR),delimiter='\t')}
 note='brief bar: round29-briefs/bar29.tsv'
 if found:
  for r in csv.DictReader(open(found[0])):
   n=int(r['n']);held[n]=min(held[n],float(r['score']))
  note+=' and main BASE line: '+str(found[0].relative_to(S))
 import os;tmp=DET.with_name(f'{DET.stem}.{os.getpid()}.tmp')
 with open(tmp,'w') as f:
  w=csv.writer(f);w.writerow(['n','score']);w.writerows((n,repr(held[n])) for n in sorted(held))
 tmp.replace(DET)
 out=(DET,held,note);_cache[key]=out
 return out
if __name__=='__main__':
 d,h,note=base();print(d,note,len(h),sum(h.values()))
