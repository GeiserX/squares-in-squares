from pathlib import Path
import json
R=Path.home()/'scratch/squares-k123';timed=set()
for p in (R/'out').glob('j22*/done.jsonl'):
 for l in p.read_text().splitlines():
  r=json.loads(l)
  if not r.get('raw') and (r.get('code')==-2 or r.get('fq2code')==-2):timed.add(f'{r["pool"]}-{r["n"]}-{r["tag"]}')
removed=[]
for p in (R/'claims').glob('*/owner.json'):
 j=json.load(p.open())
 if j['jobkey'] in timed:p.unlink();p.parent.rmdir();removed.append(j)
(R/'load-timeouts-reopened34.json').write_text(json.dumps(removed,indent=2));print(json.dumps({'reopened':len(removed)}))
