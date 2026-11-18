"""Foreground wait loop, bounded to twenty minutes, with compact progress receipts."""
from pathlib import Path
import time,json,csv,collections,sys
W=Path(__file__).resolve().parent;end=time.time()+min(1200,float(sys.argv[1]) if len(sys.argv)>1 else 1200);csv.field_size_limit(1<<28)
while time.time()<end:
 time.sleep(min(50,max(0,end-time.time())))
 rs=[]
 for l in (W/'records.jsonl').read_text().splitlines():
  try:rs.append(json.loads(l))
  except ValueError:pass
 def read(n):
  p=W/n;return json.load(open(p)) if p.exists() else {}
 state=read('collect-state.json');near=read('near-state36.json')
 rows=[(r['n'],r['gain']) for r in csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t')]
 print(time.strftime('%FT%TZ',time.gmtime()),'attempts='+str(len(rs)),'n='+str(len({r['n'] for r in rs})),'raw='+str(sum(bool(r.get('raw')) for r in rs)),'take='+str(rows),'near='+str(sum(j['status']=='published' for j in near.values())),'queued='+str(sum(j['status']=='queued' for j in near.values())),'errors='+str(sum(bool(r.get('error')) for r in rs)),'guard='+str(read('guardian36.json').get('time')),'final_error='+str((W/'finalize36.error').exists()),flush=True)
