"""Round 26 base bar for the border lane.
The bar for each n is the details.csv of the gate dir named by the last 'main -> all: BASE ...' line of
handoff-r26.log. Before that line it is gate/cand-round25-1114b/details.csv (the brief's base bar).
Never the 1114a dir: it held a 982 the skeptic took out."""
from pathlib import Path
import csv,re,sys
csv.field_size_limit(16*1024*1024)
S=Path('$SCRATCH/bounties-squares');W=Path(__file__).parent
sys.path.insert(0,str(W))
_cache={}
DEFAULT=S/'gate/cand-round25-1114b/details.csv'
def base_line():
 h=S/'handoff-r26.log'
 if not h.exists():return None
 for line in reversed(h.read_text().splitlines()):
  if re.search(r'\bmain\s*->\s*all:\s*BASE\b',line):
   m=re.search(r'(?:$SCRATCH/bounties-squares/)?(gate/[A-Za-z0-9_.-]+)',line)
   if m and (S/m[1]/'details.csv').exists() and 'cand-round25-1114a' not in m[1]:return S/m[1]/'details.csv',line
 return None
def base():
 found=base_line()
 det=found[0] if found else DEFAULT
 key=str(det)
 if key in _cache:return _cache[key]
 held={int(r['n']):float(r['score']) for r in csv.DictReader(open(det))}
 out=(det,held,('main BASE line: ' if found else 'brief base bar: ')+str(det.relative_to(S)))
 _cache[key]=out
 return out
if __name__=='__main__':
 d,h,note=base();print(d,note,len(h),sum(h.values()))
