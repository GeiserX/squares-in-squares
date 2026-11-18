import pathlib,json,csv,math,sys,time,hashlib,os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
W=pathlib.Path(__file__).parent;S=W.parents[1];sys.path.insert(0,str(W));import ancestry28 as A
from invent_shape22 import fingerprint
import numpy as np
seen=set(json.load(open(W/'historical-fingerprints.json')));bar={int(v['n']):float(v['bar'])for v in csv.DictReader(open(S/'round30-briefs/bar30.tsv'),delimiter='\t')}
paths=[]
for lane in ('forensics','k123','stair-c','modules'):
 paths.extend((S/f'take-{lane}-r29/near').glob('**/*.csv'))
paths.sort(key=lambda p:p.stat().st_mtime_ns,reverse=True)
candidates=[]
for p in paths[:350]:
 try:
  rows=list(csv.DictReader(open(p)));n=len(rows)
  if n not in bar:continue
  a=np.array([[float(r['x']),float(r['y']),float(r['angle'])]for r in rows]);h=.5*(np.abs(np.cos(a[:,2]))+np.abs(np.sin(a[:,2])));L=float(((a[:,:2]+h[:,None]).max(0)-(a[:,:2]-h[:,None]).min(0)).max());delta=L-(bar[n]+1)*math.sqrt(n)
  if delta>.002 or delta<-.02:continue
  fp=fingerprint(a)
  if fp in seen:continue
  src,lic,rec=A.metadata(p,n)
  if not src or not lic:continue
  lane=p.relative_to(S).parts[0].split('-r')[0]
  candidates.append(dict(id='late29-'+p.stem,start=str(p),n=n,source=src,licence=lic,record=rec,kind='saved',fq=lane=='take-forensics',seconds=900 if lane=='take-forensics'else 420,seed=123,delta=delta))
  seen.add(fp)
 except (OSError,ValueError,KeyError):pass
candidates.sort(key=lambda j:j['delta']);candidates=candidates[:20]
p=W/'audit-ready.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(candidates));q.replace(p)
print(json.dumps([{'n':j['n'],'delta':j['delta'],'path':j['start']}for j in candidates]),flush=True)
with (W.parent/'STATE.txt').open('a')as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' LATE29 '+str(len(candidates))+' unfinished canonical forensics/join/module candidates repriced within .002 side. Geometry that completed stays closed; current r30 fresh priority. Full source admission remains required by collector.\n')
