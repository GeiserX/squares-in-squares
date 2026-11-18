"""Apply live withdrawals to the original bytes behind a bound input alias."""
from pathlib import Path
import json,re,functools
W=Path(__file__).resolve().parent;S=str(W.parent.parent)+'/'
@functools.lru_cache(4)
def _read(stamp):
 out={};p=W/'input-aliases30.jsonl'
 if p.exists():
  for line in p.read_text().splitlines():
   try:r=json.loads(line);out[r['alias']]=r
   except (ValueError,KeyError):pass
 return out

def hit(record,path,line,withdraw_time):
 origin=record['origin'].replace(S,'');path=path.replace(S,'')
 if origin!=path:return False
 # An explicit byte withdrawal applies only to the pin it names.
 tail=line.split(path,1)[-1] if path in line else line
 m=re.search(r'sha256\s*[:=]?\s*([0-9a-fA-F]{12,64})',tail[:300])
 if m:return record['sha256'].startswith(m[1].lower())
 return record['origin_mtime']<=withdraw_time(line)

def withdrawal_hits(seen,lines,withdraw_time):
 p=W/'input-aliases30.jsonl';records=_read(p.stat().st_mtime_ns if p.exists() else 0);out=[]
 for alias in seen:
  if alias not in records:continue
  r=records[alias]
  for path,line in lines:
   if hit(r,path,line,withdraw_time):out.append('withdrawn queue-time input bytes: '+line[:200])
 return out
