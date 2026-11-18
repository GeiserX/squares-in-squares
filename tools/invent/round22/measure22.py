import csv, json, math, pathlib, re, sys, statistics
W=pathlib.Path(__file__).resolve().parent
jobs=json.load(open(W/'jobs.json')); out=[]
for j in jobs:
 p=W/'boxE-raw'/j['id'];dp=p/'done.json';logs=list(p.glob('slide-*.tsv'))
 if not dp.exists() or not logs:continue
 d=json.load(open(dp));lines=logs[0].read_text().splitlines()
 h=re.search(r'n=(\d+) start=([\d.]+) bar=([\d.]+) seed=(\d+)',lines[0])
 if not h:continue
 start=float(h[2]);best=start;tries=0;secs=0
 for l in lines:
  a=l.split('\t')
  if not a[0].isdigit():continue
  tries+=1
  if len(a)>4:
   try:best=min(best,float(a[4]));secs+=float(a[5])
   except (ValueError,IndexError):pass
 post=(d['new']+1)*math.sqrt(j['n']) if 'new' in d else best
 out.append(dict(kind=j['kind'],name=j['id'],n=j['n'],fq=j['fq'],seed=j['seed'],start_side=start,best_side=best,final_side=post,kick_side_gain=start-best,final_side_gain=start-post,tries=tries,finds=d.get('raw',0),solve_seconds=secs,started=d['started'],ended=d['ended'],source=j['source'],licence=j['licence']))
if len(sys.argv)>1:
 with open(sys.argv[1],'w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(out[0]),delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(out)
print('Completed',len(out),'including',sum(r['kind']=='control'for r in out),'positive controls; tries',sum(r['tries']for r in out if r['kind']!='control'))
for k in ['near','fresh','leg']:
 for fq in [False,True]:
  rows=[r for r in out if r['kind']==k and r['fq']==fq]
  if not rows:continue
  moved=[r for r in rows if r['final_side_gain']>1e-8]
  print(k,'fq',fq,'runs',len(rows),'moved>1e-8',len(moved),'median',statistics.median(r['final_side_gain']for r in moved) if moved else 0,'max',max(r['final_side_gain']for r in rows),'tries',sum(r['tries']for r in rows))
print('Largest final steps:')
for r in sorted([r for r in out if r['kind']!='control'],key=lambda r:-r['final_side_gain'])[:10]:
 print(r['name'],r['n'],r['kind'],'%.9g'%r['final_side_gain'],r['source'][:100])
