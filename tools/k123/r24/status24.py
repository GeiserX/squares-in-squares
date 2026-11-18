import pathlib,json,collections,csv,subprocess,time
W=pathlib.Path(__file__).resolve().parent;T=W.parent
rows=[]
p=W/'records.jsonl'
if p.exists():
 for l in p.read_text().splitlines():
  try:rows.append(json.loads(l))
  except ValueError:pass
state=json.load(open(W/'collect-state.json')) if (W/'collect-state.json').exists() else {}
report=dict(time=time.strftime('%FT%TZ',time.gmtime()),attempts=len(rows),counts=len({r['n'] for r in rows}),raw=sum(bool(r.get('raw')) for r in rows),errors=collections.Counter(r.get('error') for r in rows if r.get('error')),timeouts=sum(r.get('code')==-2 for r in rows),certification=collections.Counter(r['status'] for r in state.values()))
take=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));report['take']=[(int(r['n']),float(r['gain'])) for r in take]
print(json.dumps(report,separators=(',',':')))
