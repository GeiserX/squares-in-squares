"""Compare completed coarse and finer trials only when their start settings match."""
import csv,hashlib,json,math,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from extend30 import verified_end
jobs=json.load(open(W/'jobs.json'));rows=[];pairs=[]

def read(job):
 path=W/job['start'];data=path.read_bytes()
 assert hashlib.sha256(data).hexdigest()==job['input_sha256'],'changed comparison input'
 points=list(csv.DictReader(data.decode().splitlines()));n=job['n'];assert len(points)==n
 bounds=[[],[]]
 for point in points:
  angle=float(point['angle']);h=.5*(abs(math.cos(angle))+abs(math.sin(angle)))
  for axis,key in enumerate(('x','y')):bounds[axis].append((float(point[key])-h,float(point[key])+h))
 start=max(max(hi for lo,hi in axis)-min(lo for lo,hi in axis)for axis in bounds)
 assert abs(start-job['side'])<1e-12
 folder=W/'boxE-raw'/job['id'];receipt=json.load(open(folder/'done.json'))if(folder/'done.json').exists()else{}
 status='pending';candidate=None
 if receipt:
  assert receipt['program']==job['program'],'comparison program differs from actual worker receipt'
  if receipt.get('error'):status='error'
  elif receipt.get('quench_from_certified'):
   verified_end(folder/'final'/f'{n}.csv',n,receipt,folder/'certin'/f'{n}.csv',folder/'quench'/f'{n}.done')
   candidate=(receipt['new']+1)*math.sqrt(n);status='certified'
  elif receipt.get('raw')==0:status='dry'
  else:status='incomplete'
 best=min(start,candidate)if candidate is not None else start
 tries=0
 for trace in folder.glob('slide-*.tsv'):
  for line in trace.read_text().splitlines():
   first=line.split('\t')[0]
   if first.isdigit():tries=max(tries,int(first))
 return dict(n=n,id=job['id'],program=job['program'],input_sha256=job['input_sha256'],seed=job['seed'],seconds=job['seconds'],fq=job['fq'],bar=job['bar'],options=json.dumps(job.get('options',[])),status=status,raw=receipt.get('raw'),tries=tries,start_side=start,candidate_side=candidate,best_side=best,side_gain=start-best,started=receipt.get('started'),ended=receipt.get('ended'))

for n in(539,598):
 finer=next((j for j in jobs if j['n']==n and j['kind']=='fineentry'),None)
 coarse=next((j for j in jobs if j['n']==n and j['kind']=='finebaseline'),None)
 if not finer or not coarse:continue
 c=read(coarse);f=read(finer);rows.extend((c,f))
 fields=('input_sha256','seed','seconds','fq','bar','options')
 mismatch=[key for key in fields if c[key]!=f[key]]
 complete=all(row['status']in('certified','dry')for row in(c,f))
 pairs.append(dict(n=n,complete=complete,matched=not mismatch,mismatch=mismatch,coarse=c,finer=f,finer_advantage=c['best_side']-f['best_side']if complete and not mismatch else None))
result=dict(ready=len(pairs)==2 and all(p['complete']for p in pairs),pairs=pairs)
out=W/'finer-comparison.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2));tmp.replace(out)
with(W/'finer-comparison.tsv').open('w',newline='')as stream:
 writer=csv.DictWriter(stream,fieldnames=list(rows[0])if rows else['n'],delimiter='\t');writer.writeheader();writer.writerows(rows)
print(json.dumps(dict(ready=result['ready'],pairs=[dict(n=p['n'],complete=p['complete'],matched=p['matched'],finer_advantage=p['finer_advantage'])for p in pairs])))
