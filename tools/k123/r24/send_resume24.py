import pathlib,json,csv,re,tarfile,subprocess,collections
from provenance24 import W,S,banned
O=S/'take-k123-r23/work';rows=[];pools=set();completed={tuple(x) for x in json.load(open(W/'old-completed.json'))}
for l in (O/'pending-final.tsv').read_text().splitlines():
 w=l.split('\t');p=w[7]
 if (int(w[0]),w[1]) in completed:continue
 mp=W/p/('sources-'+p+'.json')
 if not mp.exists():continue
 try:m=json.load(open(mp));ns=re.match(r'(\d+)r?-(\d+)r?-j',w[1]).groups()
 except (ValueError,AttributeError):continue
 if all(n in m and m[n].get('clean') and (m[n].get('origin')=='candidate round23' or not banned(json.dumps(m[n]))) for n in ns):rows.append(w);pools.add(p)
prior=collections.Counter()
for fp in (O/'boxE-final/out').glob('j22*/done.jsonl'):
 for l in fp.read_text().splitlines():
  try:prior[json.loads(l)['n']]+=1
  except (ValueError,KeyError):pass
rank=collections.Counter();ordered=[]
for w in rows:
 n=int(w[0]);ordered.append(((prior[n]+rank[n],-float(w[6]),-float(w[5])),w));rank[n]+=1
ordered.sort();(W/'queue-send.tsv').write_text(''.join('\t'.join(w)+'\n' for _,w in ordered));(W/'prior-trials.json').write_text(json.dumps(prior))
if not (W/'bars.tsv').exists():
 (W/'bars.tsv').write_text(''.join(f"{r['n']}\t{float(r['L']):.12f}\t{r['score']}\theld\n" for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))))
with tarfile.open(W/'resume-send.tgz','w:gz',compresslevel=1) as t:
 for p in sorted(pools):
  for name in [p+'.csv','bars-'+p+'.tsv','sources-'+p+'.json']:t.add(W/p/name,arcname=name)
 for name in ['bars.tsv','prior-trials.json','queue-send.tsv']:t.add(W/name,arcname=name)
print('snapshot',len(rows),'rows',len(pools),'pools',len(rank),'counts',flush=True)
subprocess.run(['scp','-q',str(W/'resume-send.tgz'),'boxE:scratch/squares-k123/'],check=True)
subprocess.run(['ssh','boxE','cd $SCRATCH/squares-k123 && tar xzf resume-send.tgz && $SCRATCH/squares-base/venv/bin/python -I append_queue24.py && rm resume-send.tgz queue-send.tsv'],check=True)
