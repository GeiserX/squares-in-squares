import pathlib,json,csv,re,collections,sys,shutil
from provenance24 import W,S,mlp,credit
O=S/'take-k123-r23/work';A=O/'boxE-final';lines=(O/'pending-final.tsv').read_text().splitlines();pools={};done=collections.Counter()
for f in (A/'out').glob('j22*/done.jsonl'):
 for line in f.read_text().splitlines():
  try:done[json.loads(line)['n']]+=1
  except (ValueError,KeyError):pass
for line in lines:
 w=line.split('\t');pools.setdefault(w[7],[]).append(w)
rows=[];refused=[];summ=[]
for pool,q in pools.items():
 inp=next((p for p in [O/pool/(pool+'.csv'),O/(pool+'.csv'),A/(pool+'.csv')] if p.exists()),None)
 bp=next((p for p in [O/pool/('bars-'+pool+'.tsv'),O/('bars-'+pool+'.tsv'),A/('bars-'+pool+'.tsv')] if p.exists()),None)
 if not inp or not bp:continue
 origins={int(w[0]):w[3] for l in bp.read_text().splitlines() if len(w:=l.split('\t'))>=4};P=mlp.load(str(inp));manifest={};keep=[];need=set()
 for w in q:
  m=re.match(r'(\d+)r?-(\d+)r?-j',w[1]);ns=set(map(int,m.groups()))
  for n in ns:
   if n not in manifest:manifest[n]=credit(n,P[n],origins.get(n))
  if all(manifest[n] for n in ns):keep.append(w);need|=ns
  else:refused.append(w)
 if not keep:continue
 D=W/pool;D.mkdir(exist_ok=True)
 with open(D/(pool+'.csv'),'w') as f:
  wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
  for n in sorted(need):wr.writerows((n,i,*r) for i,r in enumerate(P[n]))
 shutil.copy(bp,D/('bars-'+pool+'.tsv'));(D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):manifest[n] for n in need}))
 rows+=keep;summ.append((pool,len(keep),len(need)))
rank=collections.Counter();ordered=[]
for w in rows:
 n=int(w[0]);ordered.append(((done[n]+rank[n],-float(w[6]),-float(w[5])),w));rank[n]+=1
ordered.sort(key=lambda x:x[0]);(W/'queue.tsv').write_text(''.join('\t'.join(w)+'\n' for _,w in ordered))
(W/'resume-audit.json').write_text(json.dumps(dict(pending=len(lines),accepted=len(rows),refused=len(refused),pools=summ,previous_trials=dict(done)),indent=2));(W/'resume-refused.tsv').write_text(''.join('\t'.join(w)+'\n' for w in refused))
print('accepted',len(rows),'of',len(lines),'pools',len(summ),'counts',len(rank),flush=True)
