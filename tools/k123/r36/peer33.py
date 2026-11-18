"""Retain only rows below bar33 and every live peer by more than 1e-10."""
from pathlib import Path
import json,csv,time,hashlib,fcntl
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;csv.field_size_limit(1<<28)
def refresh():
 bars={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round36-briefs/bar36.tsv').open(),delimiter='\t')};peer=dict(bars);pins={}
 for p in S.glob('take-*-r36/take.tsv'):
  if p.parent==T:continue
  raw=p.read_bytes();pins[str(p)]=hashlib.sha256(raw).hexdigest()
  import io
  for r in csv.DictReader(io.StringIO(raw.decode()),delimiter='\t'):
   try:n=int(r['n']);peer[n]=min(peer[n],float(r['new']))
   except (ValueError,KeyError):continue
 rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));keep=[];removed=[]
 for r in rows:
  n=int(r['n'])
  if float(r['new'])<min(bars[n],peer[n])-1e-10:keep.append(r);continue
  removed.append(r);p=T/f'{n}.csv';
  if not Path(str(p)+'.json').exists():Path(str(p)+'.json').write_text(json.dumps(r))
  D=W/'superseded33';D.mkdir(exist_ok=True);(D/f'{n}-{hashlib.sha256(p.read_bytes()).hexdigest()}.json').write_text(json.dumps(r))
 if removed:
  with (T/'take.tsv.tmp').open('w') as f:
   wr=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(keep)
  (T/'take.tsv.tmp').replace(T/'take.tsv')
  line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: SUPERSEDED own counts {[int(r["n"]) for r in removed]} by lower live takes. Source CSVs retained for pinned descendants; ancestry remains valid. {T}/take.tsv\n'
  with (T/'STATE.txt').open('a') as f:f.write(line)
  with (S/'handoff-r36.log').open('a') as f:f.write(line)
 (W/'final-peer33.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'kept':[int(r['n']) for r in keep],'removed':[int(r['n']) for r in removed],'peer_table_sha256':pins},indent=2))
 return len(keep)
if __name__=='__main__':
 with (W/'collect.lock').open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX);print(refresh())
