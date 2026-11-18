from common28 import *
from light28 import load,side
base,live,_=bar();scanned=set(read(W/'scanned.json',[]))
for rnd in [25,26,27]:scanned.update(read(S/f'take-classfill-r{rnd}/work/scanned.json',[]))
seen=read(W/'intake-seen.json',{});h=[l for l in (S/'handoff-r28.log').read_text().splitlines() if re.search(r'backlog ->[^:]*: claims ',l)];found=[];counts={};began=time.time()
for path in read(W/'reopen-unseen-unclaimed.json',[]):
 if time.time()-began>90:break
 p=Path(path)
 try:
  n=int(re.match(r'\d+',p.name)[0]);sha=hashlib.sha256(p.read_bytes()).hexdigest()
  if n<100 or sha in scanned or any(sha[:12] in l for l in h):reason='previously scanned or claimed'
  else:
   excess=side(load(str(p),{n})[n])-(1+live[n])*math.sqrt(n);reason='outside allowance' if excess>0.0005 else 'eligible'
   if reason=='eligible':found.append(dict(path=path,n=n,sha256=sha,side_excess=excess))
  counts[reason]=counts.get(reason,0)+1
 except Exception as e:counts['read error']=counts.get('read error',0)+1
found.sort(key=lambda q:q['side_excess']);atomic(W/'reopen-ranked.json',dict(time=now(),examined=sum(counts.values()),counts=counts,candidates=found));atomic(W/'REOPEN_BEST.json',[r['path'] for r in found[:12]]);note('RANK_REOPENED '+json.dumps(dict(examined=sum(counts.values()),counts=counts,best=found[:6])));print(json.dumps(dict(counts=counts,best=found[:12]),indent=1),flush=True)
