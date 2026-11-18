import csv,json,pathlib,re,sys
W=pathlib.Path('$SCRATCH/bounties-squares/take-twoshort-r23/work');R=W/'boxE23';out=pathlib.Path(sys.argv[1]);rows=[]
def row(**kw):rows.append(kw)
for p in sorted(R.glob('done/*.json')):
 d=json.load(open(p))
 if 'start_side' in d:row(kind='lkick',tag=d['tag'],n=d['n'],seed=d['seed'],start=d['start_side'],best=d['best'],bar=d['bar'],tries=d['tries'],seconds=d['seconds_used'],source=d['source'])
for p in sorted(R.glob('q/*/run.log')):
 s=p.read_text();m=re.search(r'QUENCH ([\d.]+) -> ([\d.]+)',s);md=p.parent/'meta.json'
 if md.exists():
  d=json.load(open(md))
  if m:row(kind='quench',tag=p.parent.name,n=d['n'],start=m[1],best=m[2],bar=d['bar'],source=d['source'])
  else:
   mm=re.search(r'no certified gain on ([\d.]+)',s)
   if mm:row(kind='quench',tag=p.parent.name,n=d['n'],start=mm[1],best=mm[1],bar=d['bar'],source=d['source'])
for p in sorted(R.glob('designs/*/stair.log')):
 s=p.read_text();m=re.search(r'kept (\d+) corners of (\d+) settled, lowest loss ([\d.]+)',s)
 if m:row(kind='stair',tag=p.parent.name,count=m[2],best=m[3],source='kept '+m[1]+' corners; best is a corner loss in squares')
for p in sorted(R.glob('designs/*/*.hop.log'))+sorted(R.glob('designs/*/*.weak.log')):
 s=p.read_text();m=re.search(r'start .*?count (\d+).*?loss ([\d.]+)',s)
 if not m:continue
 vals=re.findall(r'DONE count (\d+).*?loss ([\d.]+)',s);best=vals[-1][1] if vals else ''
 start=m[2]
 if '.weak.' in p.name:
  hm=re.search(r'hops \d+ on count \d+ from loss ([\d.]+).*?: ([\d.]+)',s)
  if hm:start=hm[1];best=hm[2]
 row(kind='weak' if '.weak.' in p.name else 'hop',tag=p.parent.name,count=m[1],start=start,best=best,source=str(p.relative_to(R)))
for p in sorted(R.glob('designs/*/builds/*.json')):
 d=json.load(open(p));row(kind='build',tag=p.parent.parent.name,n=d['n'],start=d['predicted'],best=d.get('built'),bar=d['held'],source='; '.join(x['id'] for x in d.get('modules',[])))
for p in sorted(R.glob('designs/*/summary.json')):
 d=json.load(open(p));row(kind='screen',tag=p.parent.name,count=d.get('queue_rows',0),tries=d.get('built',0),source='queue rows and completed builds; see summary.json')
for p in sorted(R.glob('designs/*/joint-summary.json')):
 d=json.load(open(p));row(kind='joint',tag=p.parent.name,count=d['settled'],tries=d['attempted'],seconds=d['seconds'],source='joint column-height transfer and tilted-row offsets; count=settled starts')
for p in sorted(R.glob('designs/*/timeouts.log')):
 for line in p.read_text().splitlines():row(kind='timeout',tag=p.parent.name,seconds=120,source=line)
for p in sorted(R.glob('done/*.json')):
 d=json.load(open(p))
 if d.get('kind')=='design' and d.get('rc',0):row(kind='cancelled',tag=d['tag'],source='pipeline rc '+str(d['rc'])+'; worker.log and STATE.txt record cancelled leaves')
fields=['kind','tag','n','seed','count','start','best','bar','tries','seconds','source']
with open(out,'w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
print('rows',len(rows))
