import pathlib,json,csv,math,re,sys
sys.path.insert(0,".")
from invent_rest import plateau_stop
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r22/work');js=json.load(open(W/'jobs.json'));tests=[]
for j in js:
 p=W/'boxE-raw'/j['id'];logs=list(p.glob('slide-*.tsv'))
 if not logs or not(p/'done.json').exists()or j['kind']=='control':continue
 lines=logs[0].read_text().splitlines();m=re.search('start=([0-9.]+)',lines[0]);start=float(m[1]);rr=[]
 for l in lines:
  a=l.split('\t')
  if a[0].isdigit()and len(a)>4:
   try:rr.append((float(a[4]),float(a[5])))
   except ValueError:pass
 if len(rr)<6:continue
 d=json.load(open(p/'done.json'));side=(d['new']+1)*math.sqrt(j['n'])if'new'in d else start
 returned=sum(abs(v-start)<5e-9 for v,t in rr[:6]);early=min(v for v,t in rr[:6]);stop=plateau_stop([v for v,t in rr[:6]],start)
 assert stop==(sum(abs(v-early)<5e-9 for v,t in rr[:6])>=3 and early>=start-1e-8)
 tests.append(dict(id=j['id'],n=j['n'],kind=j['kind'],returned=returned,early_step=start-early,final_step=start-side,stop=stop,seconds_saved=sum(t for v,t in rr[6:])if stop else 0))
O=pathlib.Path(__file__).resolve().parent
(O/'plateau-audit23.json').write_text(json.dumps(tests,indent=2))
stopped=[r for r in tests if r['stop']];lost=[r for r in stopped if r['final_step']>1e-8]
print('eligible',len(tests),'would_stop',len(stopped),'seconds_freed',sum(r['seconds_saved']for r in stopped),'moves_lost',len(lost))
for r in lost:print(r)
positive=[r for r in tests if r['final_step']>1e-8][:10]
print('first10 moved controls preserved',sum(not r['stop']for r in positive),'/',len(positive))

assert len(positive)==10 and all(not r['stop']for r in positive)
assert plateau_stop([30.]*6,30.)
assert plateau_stop([30.00000002]*6,30.)
assert not plateau_stop([30.,30.,30.,29.999,30.,30.],30.)
print('PASS actual predicate replay and synthetic controls')
