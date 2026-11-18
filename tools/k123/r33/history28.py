"""Close completed geometry signatures without changing a frozen round."""
from pathlib import Path
import json,re,time
W=Path(__file__).resolve().parent;p=W/'completed-geometries26.json';old={tuple(x) for x in json.loads(p.read_text())};all_seen=set(old);missing=[];cache={};records=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()]
for r in records:
 match=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not match:continue
 pool=r['pool']
 if pool not in cache:
  q=W/pool/('sources-'+pool+'.json');cache[pool]=json.loads(q.read_text()) if q.exists() else None
 try:all_seen.add((r['tag'],*(cache[pool][nn]['sha256_geometry'] for nn in match.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
 except (TypeError,KeyError):missing.append({'pool':pool,'tag':r['tag']})
assert not missing,missing
p.with_suffix('.tmp').write_text(json.dumps(sorted(all_seen)));p.with_suffix('.tmp').replace(p)
report={'old':len(old),'new':len(all_seen)-len(old),'total':len(all_seen),'records':len(records),'missing_source_manifests':missing};(W/'history28.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA CLOSE completed geometry history: {report}; immutable exact source manifests retained. Deadline00:15Z.\n')
