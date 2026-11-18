from pathlib import Path
import time,json,csv,collections
W=Path(__file__).resolve().parent;end=float((W/'deadline').read_text())+605
while time.time()<end:
 try:
  rows=list(csv.DictReader((W.parent/'take.tsv').open(),delimiter='\t'));rs=[]
  for l in (W/'records.jsonl').read_text().splitlines():
   try:rs.append(json.loads(l))
   except ValueError:pass
  status={'utc':time.strftime('%H:%M:%SZ',time.gmtime()),'attempts':len(rs),'counts':len(set(r['n'] for r in rs)),'raw_crossings':sum(bool(r.get('raw')) for r in rs),'certified_n':[int(r['n']) for r in rows],'base_gain':sum(float(r['gain']) for r in rows),'held_probes':sum(r.get('kind')=='held-probe31' for r in rs)}
  (W/'monitor-status31.json').write_text(json.dumps(status));print(json.dumps(status),flush=True)
 except Exception as e:print(repr(e),flush=True)
 time.sleep(55)
