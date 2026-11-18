import pathlib,sys,json,csv,math,hashlib,shutil,time
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import controller23 as c
seen=set(json.load(open(W/'seen-r23-v2.json')));bar={int(r['n']):float(r['score'])for r in csv.DictReader(open(c.S/'gate/cand-round21-1113a/details.csv'))}
for p in list(c.S.glob('take-*-r22/take.tsv'))+list(c.S.glob('take-*-r23/take.tsv')):
 for r in csv.DictReader(open(p),delimiter='\t'):bar[int(r['n'])]=min(bar[int(r['n'])],float(r['new']))
out=[];D=W/'unadmitted-fresh';D.mkdir(exist_ok=True)
for table in c.S.glob('take-*-r23/take.tsv'):
 lane=table.parent.name[5:-4]
 if lane not in c.TRACK:continue
 for r in csv.DictReader(open(table),delimiter='\t'):
  src=r['source']
  if src.startswith(('fq kick','one fq quench','fq quench of invent_rest','fq quench of fq kick and quench','midm_scan.py','invent_rest.py','$SCRATCH/bounties-squares/take-')):continue
  p=table.parent/(r['n']+'.csv')
  if not p.exists():continue
  try:n,L,fp=c.shape(p)
  except Exception:continue
  if fp in seen or n not in bar or L>(bar[n]+1)*math.sqrt(n)+.0031:continue
  data=p.read_bytes();bytekey=hashlib.sha256(data).hexdigest();q=D/f'{n}-{fp[:12]}-{bytekey[:12]}.csv';q.write_bytes(data);n,L,actualfp=c.shape(q)
  if actualfp!=fp:continue
  if abs(L/math.sqrt(n)-1-float(r['new']))>1e-10:continue
  out.append(dict(n=n,start=str(q.relative_to(W)),original=str(p),source=table.parent.name+'/take.tsv: '+src,licence=r['licence'],side=L,bar=(bar[n]+1)*math.sqrt(n),gap=L-(bar[n]+1)*math.sqrt(n),fq=src.startswith('rectangle windows'),shape=fp,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),captured=time.strftime('%FT%TZ',time.gmtime())))
out.sort(key=lambda r:(r['gap'],r['n']));c.atomic(W/'unadmitted-fresh.json',out)
print(json.dumps({'unadmitted_snapshots':len(out),'n':sorted(set(r['n']for r in out))}))
