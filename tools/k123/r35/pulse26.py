import pathlib,json,csv,collections,datetime
csv.field_size_limit(20000000)
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
R=[]
for l in (W/'records.jsonl').read_text().splitlines():
 try:R.append(json.loads(l))
 except ValueError:pass
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));others={}
for p in S.glob('take-*-r31/take.tsv'):
 if p.parent==T:continue
 try:
  for q in csv.DictReader(open(p),delimiter='\t'):
   n=int(q['n']);others[n]=min(others.get(n,float('inf')),float(q['new']))
 except (ValueError,KeyError):pass
print(datetime.datetime.now(datetime.timezone.utc).isoformat(),json.dumps(dict(attempts=len(R),counts=len({r['n'] for r in R}),raw=sum(bool(r.get('raw')) for r in R),errors=sum('error' in r for r in R),timeouts=sum(r.get('code')==-2 or r.get('fq2code')==-2 for r in R),certified=[int(r['n']) for r in rows],gain=sum(float(r['gain']) for r in rows),lowest=[int(r['n']) for r in rows if float(r['new'])<others.get(int(r['n']),float(r['held']))-1e-10],beyond=sum(max(0,min(float(r['held']),others.get(int(r['n']),float(r['held'])))-float(r['new'])) for r in rows))))
if (W/'collect-state.json').exists():print('cert',dict(collections.Counter(r['status'] for r in json.load(open(W/'collect-state.json')).values())))
print('staging', '\n'.join((W/'resident25.log').read_text().splitlines()[-2:]))
p=W/'handoff-offset26';off=int(p.read_text()) if p.exists() else 0;text=(S/'handoff-r35.log').read_text();lines=text[off:].splitlines();print('new handoffs',len(lines))
important=[l for l in lines if (' -> ' in l and 'k123' in l.split(' -> ',1)[1].split(':',1)[0]) or 'main ->' in l or any(z in l.lower() for z in ['withdraw','withdrew','ancestry note','ancestry fix'])]
for line in list(dict.fromkeys(important+lines[-6:])):print(line[:550])
p.write_text(str(len(text)))
