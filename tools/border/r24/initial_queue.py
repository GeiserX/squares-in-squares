from pathlib import Path
import csv,json,math,shutil,hashlib,sys
from provenance import audit,metadata
S=Path('$SCRATCH/bounties-squares');old=S/'take-border-r23/work'
names={992:'992-raw-992-b1-931-428be8c8-q0-v2-0d9aae44af',929:'929-raw-929-b1-870-4e959a66-q0-v2-4ce79ed86d',851:'851-raw-851-b1-794-23a3f2c3-q0-v7-cefc0a0fa0'}
def initialize(g,ready=False):
 if not ready:return
 W=g['W'];T=g['T'];b=g['bs'];L=g['L'];log=g['log']
 base_sources=g['sources']
 def sources(initial=False):
  current=base_sources(False)
  if initial:
   for p in (S/'take-forensics-r23/near').glob('*.csv'):current.append((p,None,False))
   for p in S.glob('take-*-r23/take.tsv'):
    for r in csv.DictReader(open(p),delimiter='\t'):
     if int(r['n']) in __import__('provenance').changed:
      f=p.parent/(r['n']+'.csv')
      if f.exists():current.append((f,r,False))
  return current
 g['sources']=sources
 if (W/'initialized').exists():return
 # Recover raw-feed ancestry from a sibling with the same own-design recipe.
 p=S/'take-twoshort-r22/near/794-794a-s122.csv'
 override={str(p):json.load(open(p.with_name('794-794a-s122-t1-raw.json')))}
 override[str(S/'take-stair-c-r22/near/870-71949154-s.csv')]=json.load(open(S/'take-stair-c-r22/work/archive/s/raw-a/870-71949154.json'))
 (W/'provenance-overrides.json').write_text(json.dumps(override,indent=2))
 # Three explicit shell round trips. Cut one shell, restore one border, then quench.
 for N,name in names.items():
  p=S/'take-border-r23/near'/(name+'.csv')
  if not audit(p):log('named round-trip deferred ancestry '+str(p));continue
  m,s,A=b.read_near(str(p));down=N-2*math.floor(s)+1
  for c in range(4):
   B=b.build('rev',A,s,down,c,0);ss,AA=b.normalize([(x,y,math.radians(a)) for x,y,a in B])
   rows=[dict(n=str(down),square_id=str(i),x=repr(float(x)),y=repr(float(y)),angle=repr(math.radians(a))) for i,(x,y,a) in enumerate(AA)]
   q=W/'donors'/f'{down}-trip-{N}-c{c}.csv';g['csvout'](q,rows)
   origin=f'shell down from {p}, corner {c}; '+b.near_source(p,m,s,L[m])
   q.with_suffix('.json').write_text(json.dumps(dict(source=origin,licence='ours on traced own modules; held source notices results/round23-best-2026-11-13.tsv')))
   # force all border orientations, with the historically productive corner first.
   pick=W/'trip-pick.tsv'
   with pick.open('w') as f:
    wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','donor','n','corner','side','margin','dropped','variant','near','near_source','donor_licence'])
    for v in [2,3,1,0]:wr.writerow(['b1',down,N,0,ss+1,ss+1-L[N],0,v,str(q),origin,'ours on recorded own module/held ancestry'])
   before={p.name for p in (W/'q').glob('*.start.txt')}
   a=g['NS'](held=str(W/'empty.csv'),details=str(W/'details.csv'),pairs=str(pick),dir=str(W/'q'),kinds='b1',max=1e9,min=-1e9,min_abs=0,no_grid=False,per_n=0,limit=100,vfrom=0,variants=4,gaps='',edge_min=0)
   b.cmd_starts(a)
   for st in (W/'q').glob('*.start.txt'):
    if st.name in before:continue
    ident=st.name.removesuffix('.start.txt');v=int(ident.rsplit('v',1)[1]);priority=-65+(0 if v==2 else 3)+list(names).index(N)
    st.with_name(ident+'.job.json').write_text(json.dumps(dict(start=st.name,priority=priority,named_trip=N)))
    g['queued'].add(hashlib.md5(st.read_bytes()).hexdigest())
  log(f'QUEUE shell roundtrip {N}->{down}->{N}, 4 cuts and 4 border orientations; common deadline22:15Z, boxC logs worker1/2.log')
 # Unstarted, frozen jobs: reuse exact starts and original donor snapshots.
 manifest={r['id']:r for r in csv.DictReader(open(old/'q/manifest.tsv'),delimiter='\t')}
 adopted=[]
 for entry in csv.DictReader(open(old/'unstarted.tsv'),delimiter='\t'):
  ident=entry['id'];r=manifest[ident];st=old/'q'/(ident+'.start.txt')
  if not st.exists() or not g['audit_manifest'](r):continue
  md=hashlib.md5(st.read_bytes()).hexdigest()
  if md in g['queued']:continue
  shutil.copyfile(st,W/'q'/st.name)
  if r.get('donor_copy'):shutil.copyfile(old/'q'/r['donor_copy'],W/'q'/r['donor_copy'])
  (W/'q'/(ident+'.job.json')).write_text(json.dumps(dict(start=st.name,priority=10+float(entry['margin']),adopted_r23=True)))
  adopted.append(r);g['queued'].add(md)
 if adopted:
  p=W/'q/manifest.tsv';cols=list(adopted[0]);exists=p.exists()
  with p.open('a') as f:
   wr=csv.DictWriter(f,fieldnames=cols,delimiter='\t')
   if not exists:wr.writeheader()
   wr.writerows(adopted)
 log(f'ADOPT {len(adopted)} clean unstarted r23 exact starts; remaining rejects work/source-rejections.jsonl. Fresh r24 jobs have priority over backlog.')

 (W/'initialized').write_text('initial queue completed')
