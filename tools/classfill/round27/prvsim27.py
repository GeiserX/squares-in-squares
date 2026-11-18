"""Round 27 share guard. Uses the greatest match share across all eight symmetries."""
import sys,json,hashlib,zipfile,csv,io,os
from pathlib import Path
from sharelight27 import share
W=Path(__file__).parent
PRV=Path('$SCRATCH/bounties-squares/take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip')
cache_dir=W/'prvcheck';cache_dir.mkdir(exist_ok=True)
ALL=None
def baseline():
 global ALL
 if ALL is None:
  ALL={}
  with zipfile.ZipFile(PRV) as z:
   for name in z.namelist():
    if name=='submission.csv':
     for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
      n=int(r['n']) if 'n' in r else int(r['id'].split('_')[0]);ALL.setdefault(n,[]).append([float(r['x'].lstrip('s')),float(r['y'].lstrip('s'))])
     break
 return ALL
def centres(path,n):
 a=[]
 for r in csv.DictReader(open(path)):
  k=int(r['n']) if 'n' in r else int(r['id'].split('_')[0])
  if k==n:a.append([float(r['x'].lstrip('s')),float(r['y'].lstrip('s'))])
 return a
def check(path,n):
 data=Path(path).read_bytes();sha=hashlib.sha256(data).hexdigest();cache=cache_dir/(str(n)+'-'+sha+'.json')
 if cache.exists():
  old=json.loads(cache.read_text())
  if old.get('policy')=='submission-v2':return old
 b=baseline().get(n,[]);a=centres(path,n);assert len(a)==n,(path,n,len(a))
 assert len(b)==n,('missing prvsiyan submission row',n,len(b))
 value=share(a,b)
 r=dict(policy='submission-v2',n=n,input_sha256=sha,share=value,excluded=value>=.4,baseline_sha256=hashlib.sha256(PRV.read_bytes()).hexdigest());tmp=cache.with_name(cache.name+'.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(r)+'\n');os.replace(tmp,cache);return r
if __name__=='__main__':
 if sys.argv[1:] == ['--control']:
  a=[[0.,0.],[1.,0.],[2.,0.],[4.,0.]]
  assert share(a,a)==1
  assert share(a,[[0.,0.],[0.,3.],[2.,1.],[9.,4.]])<.4
  print('SHARE_CONTROL_PASS identical=1.0 changed<0.4')
 else:
  for spec in sys.argv[1:]:
   n,p=spec.split(':',1);print(json.dumps(check(p,int(n))))
