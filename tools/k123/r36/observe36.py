from pathlib import Path
import json,csv,collections,subprocess,time
W=Path(__file__).resolve().parent;T=W.parent
rs=[]
for l in (W/'records.jsonl').read_text().splitlines():
 try:rs.append(json.loads(l))
 except ValueError:pass
state=json.load(open(W/'collect-state.json')) if (W/'collect-state.json').exists() else {};near=json.load(open(W/'near-state36.json')) if (W/'near-state36.json').exists() else {}
print(time.strftime('%FT%TZ',time.gmtime()),'attempts',len(rs),'counts',len({r['n'] for r in rs}),'raws',sum(bool(r.get('raw')) for r in rs),'errors',dict(collections.Counter(r['error'] for r in rs if r.get('error'))),'collect',dict(collections.Counter(r['status'] for r in state.values())),'near',dict(collections.Counter(r['status'] for r in near.values())))
print('take',[(r['n'],r['new'],r['gain']) for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')]);print('pids',json.load(open(W/'guardian36.json')))
for name in ['seed36.log','stage24.py.log','collect22.py.log','third-r36.log','finalize36-r36.log']:
 p=W/name
 if p.exists():print(name, '\n'.join(p.read_text().splitlines()[-2:]))
