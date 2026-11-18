import pathlib,shutil,json,csv,datetime,sys,re,hashlib,collections
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-k123-r24/work';O=S/'take-k123-r23/work';R=pathlib.Path('.')
(W/'lane').mkdir(exist_ok=True)
for f in R.glob('*.py'):shutil.copy(f,W/'lane'/f.name)
for name in ['fq2.py','board.tsv','sel21.py','cert_once22.py','geometry23.py','thin23.py']:
 shutil.copy(O/name,W/name)
for name in ['qrun22.py','third22.py','collect22.py']:
 s=(O/name).read_text().replace('round21-1113a','round23-1113a').replace('handoff-r23','handoff-r24').replace('held round21 (results/round21-best','candidate round23 (results/round23-best').replace('deadline18:30Z','deadline22:15Z')
 if name=='collect22.py':
  s=s.replace("list(S.glob('take-*-r23/take.tsv'))+list(S.glob('take-*-r22/take.tsv'))","list(S.glob('take-*-r24/take.tsv'))")
  # Mandatory source audit is added below before either raw certification or publication.
  s=s.replace("lic='own join or step; each donor source and licence is in the named round table or take.tsv'", "manifest=json.load(open(W/('sources-'+r['pool']+'.json'))) if (W/('sources-'+r['pool']+'.json')).exists() else json.load(open(W/r['pool']/('sources-'+r['pool']+'.json')))\n credits=[manifest[str(nn)] for nn in donors]\n if not all(c.get('clean') for c in credits):\n  state[key]={'status':'source-refused','n':n};continue\n source+='; pinned donor ancestry: '+json.dumps(credits,separators=(',',':'))\n lic='ours, on: '+' | '.join(c['licence'] for c in credits)")
  s=s.replace("'out/j22*/done.jsonl out/steps/done.jsonl", "'out/j22*/done.jsonl out/steps/done.jsonl")
 if name=='qrun22.py':
  start=s.index(' first={}');end=s.index(' for l in sorted(queue,key=priority):',start)
  s=s[:start]+''' finished={}
 for fp in (R/'out').glob('j22*/done.jsonl'):
  for line in fp.read_text().splitlines():
   try:
    nn=json.loads(line)['n'];finished[nn]=finished.get(nn,0)+1
   except (ValueError,KeyError):pass
 first={}
 for line in queue:
  f=line.split('\\t');first.setdefault((f[7],f[0]),f[1])
 def priority(line):
  f=line.split('\\t');pool=f[7];fresh=pool.startswith('fresh')
  if worker=='j22b':return (fresh,finished.get(int(f[0]),0),-float(f[6]),-float(f[5]))
  return (not fresh,finished.get(int(f[0]),0),-int(pool[5:]) if fresh else 0,-float(f[5]))
''' + s[end:]
  s=s.replace("jobdeadline=time.time()+(120 if '--once' in sys.argv and not (pool in hot and first[(pool,w[0])]==tag) else 300)","jobdeadline=time.time()+180")
 if name=='third22.py':s=s.replace("'--mmin','15'","'--mmin','10'")
 (W/name).write_text(s)
(W/'deadline').write_text(str(datetime.datetime(2026,11,13,22,15,tzinfo=datetime.timezone.utc).timestamp()))
(W.parent/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
