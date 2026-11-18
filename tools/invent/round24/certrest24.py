import csv,glob,json,os,sys,pathlib,hashlib
csv.field_size_limit(16*1024*1024)
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r24/work')
sys.path.insert(0,str(W));sys.path.insert(0,'.')
from ancestry24 import clean
from policy24 import classify,annotate,bars,RELAXED,save_cache
T,specs=sys.argv[1],sys.argv[2:]
if len(specs)==1 and specs[0].startswith('@'):specs=json.load(open(specs[0][1:]))
held,held22,bar,freebar,who,freewho=bars(T)
# CONTROL_OVERRIDE
best={}
def bounds(n,src,lic):
 p=classify(src,lic);free=n in RELAXED and p['status']=='none'
 return p,(held22[n] if free else held[n]),(freebar[n] if free else bar[n]),free

def offer(n,score,rows,src,lic,path):
 if not clean(src,lic)[0]:return
 p,reference,limit,free=bounds(n,src,lic)
 if p['status']=='unknown' or not(score<reference-1e-10 and score<limit-1e-10):return
 if n in best:
  old=best[n];oldfree=bounds(n,old[2],old[3])[3]
  if oldfree and not free:return
  if oldfree==free and old[0]<=score:return
 src,lic=annotate(src,lic)
 best[n]=(score,rows,src,lic,path)
CF=pathlib.Path(__file__).parent/'fs-cache-policy.json'
try:cache=json.load(open(CF))
except (OSError,ValueError):cache={}
def read_offer(n,path,src,lic):
 mt=os.path.getmtime(path);digest=hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest();c=cache.get(path)
 if os.path.abspath(T)==str(W.parent) and not(c and len(c)>3 and c[2]==digest and c[3]):return
 if c and c[0]==mt and len(c)>2 and c[2]==digest:
  score=c[1]
  if score is None:return
  p,reference,limit,free=bounds(n,src,lic)
  if p['status']=='unknown' or not(score<reference-1e-10 and score<limit-1e-10):return
  if n in best:
   oldfree=bounds(n,best[n][2],best[n][3])[3]
   if (oldfree and not free) or (oldfree==free and best[n][0]<=score):return
 rows=[{k:r[k]for k in ('n','square_id','x','y','angle')}for r in csv.DictReader(open(path))]
 if len(rows)!=n:return
 if c and c[0]==mt and len(c)>3 and c[2]==digest and c[3]:
  offer(n,c[1],rows,src,lic,path);return
 import floatsafe
 _,fr,score,error=floatsafe.work((n,rows))
 same=fr is not None and all(all(float(x[k])==float(y[k]) for k in ('x','y','angle')) and int(x['n'])==int(y['n']) and int(x['square_id'])==int(y['square_id']) for x,y in zip(rows,fr))
 cache[path]=[mt,score if fr is not None else None,digest,same]
 CF.with_suffix('.tmp').write_text(json.dumps(cache));CF.with_suffix('.tmp').replace(CF)
 if fr is not None:offer(n,score,fr,src,lic,path)
if os.path.abspath(T)!=str(W.parent) and os.path.exists(T+'/take.tsv'):
 for r in csv.DictReader(open(T+'/take.tsv'),delimiter='\t'):
  n=int(r['n']);read_offer(n,f'{T}/{n}.csv',r['source'],r['licence'])
for spec in specs:
 raw,src,lic=spec.split('|');only=None
 if '#'in raw:raw,only=raw.split('#')[0],int(raw.split('#')[1])
 last={}
 for p in glob.glob(raw+'/*.csv'):
  parts=pathlib.Path(p).stem.split('-');key=tuple(parts[:2]) if len(parts)==3 and parts[2].isdigit() else tuple(parts);t=int(parts[2]) if len(parts)==3 and parts[2].isdigit() else 0
  if key not in last or t>last[key][0]:last[key]=(t,p)
 for _,p in last.values():
  n=int(pathlib.Path(p).stem.split('-')[0])
  if only is None or only==n:read_offer(n,p,src,lic)
CF.with_suffix('.tmp').write_text(json.dumps(cache));CF.with_suffix('.tmp').replace(CF)
rows=[];total=net=0
for n,(score,fr,src,lic,path) in sorted(best.items()):
 p,reference,limit,free=bounds(n,src,lic)
 dest=f'{T}/{n}.csv'
 if os.path.abspath(path)!=os.path.abspath(dest):
  with open(dest+'.tmp','w',newline='')as f:
   w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(fr)
  os.replace(dest+'.tmp',dest)
 rows.append(dict(n=n,held=reference,new=score,gain=reference-score,source=src,licence=lic))
 total+=held[n]-score;net+=limit-score
 print('keep',n,'original_candidate_gain',held[n]-score,'accepted_gain',reference-score,'over_bar',limit-score,p)
for p in glob.glob(T+'/*.csv'):
 if int(pathlib.Path(p).stem)not in best:os.remove(p)
with open(T+'/take.tsv.tmp','w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(rows)
os.replace(T+'/take.tsv.tmp',T+'/take.tsv')
save_cache()
print('kept',len(best),'gain',total,'over the bar',net)
