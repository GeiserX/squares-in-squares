from pathlib import Path
import csv,json,sys,re,math,io
csv.field_size_limit(16*1024*1024)
W=Path(__file__).parent;T=W.parent
sys.path.insert(0,'.');sys.path.insert(0,str(W))
import border_sweep as b
b.lib();import floatsafe
import finesafe as floatsafe  # r28: the driver and lpfeed certify with finesafe.work since 02:30Z
import hashlib

def rows_bytes(fr):
 f=io.StringIO();wr=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);wr.writeheader();wr.writerows({k:r[k] for k in wr.fieldnames} for r in fr);return f.getvalue().encode()

def converted(n,txt):
 _,A=b.read_txt(str(txt));rows=[dict(n=str(n),square_id=str(i),x=repr(x),y=repr(y),angle=repr(math.radians(a))) for i,(x,y,a) in enumerate(A)]
 return floatsafe.work((n,rows))

for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);target=(T/f'{n}.csv').read_bytes();matched=False
 ids=list(dict.fromkeys(re.findall(r'certified-file fq ([^\s;]+) on boxC',row['source'])))
 for uid in reversed(ids):
  p=W/'final'/f'{uid}.job.json';done=W/'final'/f'{uid}.job.done';staged=W/'staged'/f'{uid}.csv'
  if not(p.exists() and done.exists() and staged.exists()):continue
  meta=json.load(open(p));proof=json.load(open(done))
  if meta['n']!=n or proof['side'] is None:continue
  _,fr,sc,_=converted(n,W/'final'/proof['output'])
  if fr is None:continue
  if sc>meta['certified_before']:fr=list(csv.DictReader(open(staged)))
  if rows_bytes(fr)!=target:continue
  recipe=meta['manifest']
  if recipe['kind']=='win':
   import wfeed_rows
   rows=wfeed_rows.window_rows(recipe['near'],recipe['window']['a'],recipe['window']['b'],recipe['window']['s'],n)
   _,fr0,sc0,_=floatsafe.work((n,rows));assert fr0 is not None and abs(sc0-meta['certified_before'])<1e-14,'window rebuild differs'
   assert rows_bytes(fr0)==(W/'staged'/f'{uid}.csv').read_bytes(),'window rebuild bytes differ'
   assert proof['input']==meta['input'] and proof['output']==meta['output']
   print(n,uid,'window recipe, certified input and published result byte exact',flush=True);matched=True;break
  if recipe['kind'] in ('lp','kick'):  # r31 (r30 next item 5): a kick row has the same proof shape: pinned start copy, certified raw find, polish fq
   # r28: LP and self-follow jobs. The pinned donor copy is the recorded bytes, the staged input certifies to the recorded
   # score, the fq input is that staged file rendered, and the certified fq output (or the retained input) is the row.
   assert hashlib.sha256(Path(recipe['near']).read_bytes()).hexdigest()==recipe['start_sha256'],'pinned donor copy changed'
   before=list(csv.DictReader(open(staged)));_,fb,before_score,_=floatsafe.work((n,before))
   assert fb is not None and abs(before_score-meta['certified_before'])<1e-14,'certified input score differs'
   ss,A=b.normalize([(float(r['x']),float(r['y']),float(r['angle'])) for r in before]);render=W/'control'/f'{n}-proof-input.txt'
   render.parent.mkdir(exist_ok=True);b.write_txt(str(render),ss,A)
   assert render.read_bytes()==(W/'final'/meta['input']).read_bytes(),'certified input changed'
   assert proof['input']==meta['input'] and proof['output']==meta['output']
   print(n,uid,recipe['kind']+' (or self-follow) job: pinned start, certified input and published result byte exact',flush=True);matched=True;break
  b.check_start(str(W/'q'),recipe)
  m,donor_side,donor=b.read_near(recipe['near']);assert m==int(recipe['donor'])
  built=b.build(recipe['kind'],donor,donor_side,n,b.recipe_corner(recipe),int(recipe['variant']))
  ss,A=b.normalize([(float(x),float(y),math.radians(float(a))) for x,y,a in built])
  rebuilt=W/'control'/f'{n}-proof-start.txt';b.write_txt(str(rebuilt),ss+1e-10,A)
  assert rebuilt.read_bytes()==(W/'q'/f"{recipe['id']}.start.txt").read_bytes(), 'donor recipe changed'
  before=list(csv.DictReader(open(staged)));_,_,before_score,why=floatsafe.work((n,before))
  assert why is not None and abs(before_score-meta['certified_before'])<1e-14
  ss,A=b.normalize([(float(r['x']),float(r['y']),float(r['angle'])) for r in before]);render=W/'control'/f'{n}-proof-input.txt';b.write_txt(str(render),ss,A)
  assert render.read_bytes()==(W/'final'/meta['input']).read_bytes(), 'certified input changed'
  assert proof['input']==meta['input'] and proof['output']==meta['output']
  print(n,uid,'donor recipe, certified input and published result byte exact',flush=True);matched=True;break
 assert matched, 'no matching completed certified-input quench for '+str(n)
print('all published proof chains pass',flush=True)
