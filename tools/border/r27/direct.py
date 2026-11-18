"""Round 27 item 2, direct path (boxA, light). Frozen r22-r26 take, near and withdrawn layouts of other lanes
and the re-opened seed split whose raw side is below the bar27 side (below_scan.py -> below.tsv) are re-checked
under the r27 gate: provenance.audit walk, then floatsafe. Every one that certifies below the live bar by more than
1e-10 gets a certified-file fq job in final/ with a 'direct' manifest; the driver publishes it through the source
policy, the prvsiyan share test and the live-take check, like every other row. Per n the best three files that pass
the walk are staged. One pass; log lines go to STATE.txt."""
import os,sys,time,json,csv,math,hashlib,collections
from pathlib import Path
W=Path(__file__).parent;S=W.parent.parent;T=W.parent
src=(W/'driver.py').read_text()
src=src[:src.index("log('start round27 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_direct','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs'];floatsafe=ns['floatsafe'];audit=ns['audit'];metadata=ns['metadata'];csvout=ns['csvout'];log=ns['log'];refresh=ns['refresh']
refresh();L=ns['L']
d=collections.defaultdict(list)
for l in open(W/'below.tsv'):
 g,n,p=l.rstrip('\n').split('\t')
 if float(g)<-1e-9:d[int(n)].append((float(g),p))
summary=[]
for n in sorted(d,key=lambda n:min(d[n])[0]):
 took=0;why=collections.Counter()
 for g,p in sorted(d[n]):
  if took>=3:break
  p=Path(p)
  row=None
  if p.stem.isdigit() and (p.parent/'take.tsv').exists():
   row=next((r for r in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t') if r['n']==p.stem),None)
  before=len(ns['metadata'].__globals__['rejected'])
  if not audit(p,row):
   rj=[w for (q,w) in ns['metadata'].__globals__['rejected'] if q==str(p)]
   why[(rj[-1] if rj else 'audit')[:60]]+=1;continue
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
  for r in rows:r['n']=str(n)
  _,fr,sc,e=floatsafe.work((n,rows))
  if fr is None:why['no cert']+=1;continue
  if not (sc+1)*math.sqrt(n)<L[n]-math.sqrt(n)*1e-10:why['cert above live bar']+=1;continue
  data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
  copy=W/'donors'/f'{n}-{digest[:16]}.csv'
  if not copy.exists():copy.write_bytes(data)
  dsrc=f'{p}'+(f', from {p.parent}/take.tsv: {row["source"]}' if row else ', '+bs.near_source(str(p),n,(sc+1)*math.sqrt(n),L[n]))
  lic=row.get('licence','ours') if row else bs.near_metadata(str(p)).get('licence') or 'ours (near layout of another lane)'
  md=metadata(p)
  if md:
   dsrc+='; recorded ancestry '+json.dumps(md,sort_keys=True);lic=md.get('licence') or lic
  uid=f'{n}-direct-{digest[:8]}-'+hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
  if (W/'final'/f'{uid}.job.json').exists():took+=1;continue
  ss,AA=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
  man=dict(id=uid,kind='direct',donor=str(n),n=str(n),corner='0',variant='0',dropped='0',near=str(copy),donor_source=dsrc,donor_licence=lic,built_L=repr(ss),start_sha256=digest)
  csvout(W/'staged'/f'{uid}.csv',fr)
  bs.write_txt(str(W/'final'/f'{uid}.input.txt'),ss,AA)
  job=dict(input=f'{uid}.input.txt',output=f'{uid}.output.txt',n=n,manifest=man,certified_before=sc,
           chain={'mode':'re-opened layout (r27 item 2), certified directly','s_start':ss,'log':[]})
  (W/'final'/f'{uid}.job.json').write_text(json.dumps(job))
  log(f'direct {n}: re-opened {p} (sha256 {digest[:16]}) certifies at score {sc:.16g}, {(sc+1)*math.sqrt(n)-L[n]:.3e} of side vs the live bar; queued certified-file fq {uid}')
  took+=1
 summary.append((n,took,dict(why)))
for n,took,why in summary:print(n,took,why,flush=True)
