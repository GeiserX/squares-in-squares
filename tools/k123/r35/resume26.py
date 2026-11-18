"""Resume unrun recipes with exact frozen inputs and rechecked source proofs."""
import pathlib,sys,json,csv,re,collections,hashlib,subprocess,tarfile,time,fcntl
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import S,mlp,key
from source25 import audit
O=S/'take-k123-r34/work';A=O/'boxE-final';log=(S/'handoff-r35.log').read_text()
def claimed(pool,line):
 return 'backlog ->' in line and bool(re.search(r'\bclaims?\b',line,re.I)) and 'take-k123-r34/' in line and pool in line
assert not claimed('fresh10090','backlog -> invent: claims follow:other')
assert claimed('fresh10090','backlog -> all: CLAIM saved take-k123-r34/work/fresh10090')
refused_recipes={(r['pool'],r['tag']) for l in (O/'records.jsonl').read_text().splitlines() if (r:=json.loads(l)).get('error')}
postponed_file=W/'resume-postponed32.json';postponed=json.load(postponed_file.open()) if postponed_file.exists() else {}
seenfile=W/'resume-seen26.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set();groups=collections.defaultdict(list)
for line in (A/'queue.tsv').read_text().splitlines():
 f=line.split('\t')
 if len(f)>=8:groups[f[7]].append(f)
history={tuple(z) for z in json.load(open(W/'completed-geometries26.json'))};began=time.time();count=0
for pool,rows in sorted(groups.items(),key=lambda z:(not z[0].startswith('fresh'),-max(float(r[6]) for r in z[1]))):
 if pool in seen or postponed.get(pool,0)>time.time():continue
 if any(claimed(pool,line) for line in log.splitlines()):
  seen.add(pool);print('skip exact claimed pool',pool,flush=True);continue
 if time.time()-began>15:break
 seen.add(pool);mp=A/f'sources-{pool}.json';cp=A/f'{pool}.csv'
 if not mp.exists() or not cp.exists():continue
 meta=json.load(open(mp));keep=[];proof={};refused=set();deferred=set()
 for f in rows:
  if (pool,f[1]) in refused_recipes:continue
  m=re.match(r'(\d+)r?-(\d+)r?-j',f[1])
  if not m:continue
  ns=m.groups()
  identity=tuple([f[1]]+[meta[n]['sha256_geometry'] for n in ns])
  if identity in history and identity+('loosen1.005-r30',) in history:continue
  for n in ns:
   if n not in proof and n not in refused:
    try:c=audit(meta[n])
    except __import__('admission_budget30').Deferred:
     refused.add(n);deferred.add(n);continue
    if c is None and n=='932' and (W.parent/'932.csv').exists():
     # The restored source can replace only an exactly equal frozen input array.
     import numpy as np
     from provenance24 import credit
     nn=int(n);own=mlp.load(str(W.parent/'932.csv'),{nn})[nn];old=mlp.load(str(cp),{nn})[nn]
     if np.array_equal(own,old) and key(nn,own)==meta[n]['sha256_geometry']:
      c=credit(nn,own,str(W.parent/'932.csv'))
      if c:
       c={**c,'rebound_exact_input':str(cp),'rebound_csv_sha256':hashlib.sha256(cp.read_bytes()).hexdigest()}
       with (W.parent/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA SOURCE REBIND932 in{pool}: exact-array positive control passed against restored certified932, same geometry hash; using its complete canonical source proof. Frozen pool untouched. Deadline16:25Z.\n')
    if c:proof[n]=c
    else:refused.add(n)
  if all(n in proof for n in ns):keep.append(f)
 if deferred:
  seen.discard(pool);postponed[pool]=time.time()+600;postponed_file.write_text(json.dumps(postponed))
  with (W/'resume-deferred31.jsonl').open('a') as h:h.write(json.dumps({'pool':pool,'parents':sorted(deferred),'retry_after':postponed[pool],'reason':'bounded source admission; full frozen inputs stay preserved'})+'\n')
  continue
 if not keep:continue
 tag='resume35'+pool;D=W/tag;D.mkdir(exist_ok=True);ns={int(n) for f in keep for n in re.match(r'(\d+)r?-(\d+)r?-j',f[1]).groups()};P=mlp.load(str(cp),ns)
 assert all(key(n,P[n])==meta[str(n)]['sha256_geometry'] for n in ns)
 with open(D/(tag+'.csv'),'w') as h:
  wr=csv.writer(h);wr.writerow(['n','square_id','x','y','angle'])
  for n in sorted(ns):wr.writerows((n,i,*q) for i,q in enumerate(P[n]))
 (D/('sources-'+tag+'.json')).write_text(json.dumps({str(n):proof[str(n)] for n in ns}))
 (D/('bars-'+tag+'.tsv')).write_text((W/'bars.tsv').read_text())
 for f in keep:f[7]=tag
 (D/'queue.tsv').write_text(''.join('\t'.join(f)+'\n' for f in keep))
 with open(W/'transfer.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  with tarfile.open(D/'send.tgz','w:gz') as t:
   for name in [tag+'.csv','sources-'+tag+'.json','bars-'+tag+'.tsv']:t.add(D/name,arcname=name)
   t.add(D/'queue.tsv',arcname='queue-'+tag+'.tsv')
  subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh',str(D/'send.tgz'),f'boxE:scratch/squares-k123/send-{tag}.tgz'],check=True)
  subprocess.run(['ssh','-S','/tmp/squares-k123-r35-ssh','boxE',f'cd $SCRATCH/squares-k123 && tar xzf send-{tag}.tgz && cat queue-{tag}.tsv >> queue.tsv && rm send-{tag}.tgz'],check=True)
 with (W.parent/'STATE.txt').open('a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA ADOPT {len(keep)} unrun exact r25 recipes as {tag}, refused parents {sorted(refused)}. Logs out/j22*/done.jsonl. Deadline16:25Z.\n')
 print('resume',pool,len(keep),flush=True);count+=1
 if count>=2:break
seenfile.write_text(json.dumps(sorted(seen)))
print('resume visited',len(seen),'staged',count,flush=True)
