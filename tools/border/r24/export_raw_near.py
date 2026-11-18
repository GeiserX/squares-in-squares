from pathlib import Path
import json,csv,math,sys,hashlib,datetime,io
csv.field_size_limit(16*1024*1024)
W=Path(__file__).parent;T=W.parent;S=T.parent
sys.path.insert(0,'.');import border_sweep as b
b.lib();import floatsafe
bars=json.load(open(W/'bars.json'));man={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
cache=W/'raw-near-cache.json';seen=json.load(open(cache)) if cache.exists() else {}
hashes={hashlib.sha256(p.read_bytes()).hexdigest() for p in (T/'near').glob('*.csv')}
count=0
for p in (W/'q').glob('*.k0.json'):
 try:
  ident=p.name.removesuffix('.k0.json');j=json.load(open(p));r=man.get(ident)
  if not r or not j['log']:continue
  n=int(r['n']);margin=j['s_final']-bars[str(n)]
  if not 1e-8<margin<.015 or j['s_start']-j['s_final']<1e-4 or j['s_final']>=seen.get(ident,1e100)-1e-6:continue
  b.check_start(str(W/'q'),r)
  _,A=b.read_txt(str(W/'q'/j['best']))
  rows=[dict(n=str(n),square_id=str(i),x=repr(x),y=repr(y),angle=repr(math.radians(a))) for i,(x,y,a) in enumerate(A)]
  _,fr,sc,_=floatsafe.work((n,rows))
  if fr is None or (sc+1)*math.sqrt(n)>bars[str(n)]+.015:continue
  f=io.StringIO();wr=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);wr.writeheader();wr.writerows({k:q[k] for k in wr.fieldnames} for q in fr);data=f.getvalue().encode();digest=hashlib.sha256(data).hexdigest()
  seen[ident]=j['s_final']
  uid=ident+'-'+hashlib.md5(repr(sc).encode()).hexdigest()[:8]
  receipt=W/'final'/f'{uid}.job.done';staged=W/'staged'/f'{uid}.csv'
  if receipt.exists() and json.load(open(receipt)).get('side') is not None and staged.exists() and staged.read_bytes()==data:continue
  if digest in hashes:continue
  target=T/'near'/f'{n}-raw-{ident}-{digest[:10]}.csv';target.write_bytes(data)
  source=f"raw fq endpoint of border_sweep.py {r['kind']} from n={r['donor']}, corner {b.recipe_corner(r)}, variant {r['variant']}; {r['donor_source']}; record {p}; floatsafe passed, required certified-input quench not yet proved"
  target.with_suffix('.json').write_text(json.dumps(dict(source=source,licence='ours, on '+r['donor_licence'],manifest=r,chain=j,certified_score=sc,certified_input_quench=False),indent=2))
  hashes.add(digest);count+=1
  line=f"{datetime.datetime.now(datetime.timezone.utc).isoformat()} border -> all: float-safe raw fq near n={n}, side gap {(sc+1)*math.sqrt(n)-bars[str(n)]:.9g}; no certified-input proof yet, {target}"
  print(line,flush=True)
  with open(S/'handoff-r24.log','a') as o:o.write(line+'\n')
  with open(T/'STATE.txt','a') as o:o.write(line.replace('border -> all:', 'boxA EXPORT raw near; command work/export_raw_near.py, log work/raw-near.log, deadline22:15Z:')+'\n')
 except (OSError,ValueError,KeyError,TypeError) as e:print('transient raw source skipped',p.name,str(e),flush=True)
cache.write_text(json.dumps(seen,indent=2));print('raw near exports',count,flush=True)
