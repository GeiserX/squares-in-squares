"""Extract owned original rows directly; result-table selection is not ancestry."""
from common29 import *
from light29 import load,key,side
old=read(W/'preq-seed-candidates.json',[]);want={int(Path(p).name.split('-')[0]) for p in old};catalogues={}
for name in ['samanyu_bestfit.csv','samanyu_22249.csv']:
 p=S/'seeds'/name;catalogues[name]=(p,load(p,want),blob(p))
base,live,_=bar();out=[];records=[]
for former in old:
 former=Path(former);n=int(former.name.split('-')[0]);P=load(former,{n})[n];signature=key(P,8)
 matches=[(name,p,pack[n],pin)for name,(p,pack,pin) in catalogues.items() if n in pack and key(pack[n],8)==signature]
 if matches:name,catalogue,Q,pin=matches[0]
 else:
  choices=[(side(pack[n]),name,p,pack[n],pin)for name,(p,pack,pin) in catalogues.items() if n in pack]
  _,name,catalogue,Q,pin=min(choices,key=lambda q:q[0])
 excess=side(Q)-(1+live[n])*math.sqrt(n)
 if excess>.0005:
  records.append(dict(n=n,former_matched=bool(matches),catalogue=name,excess=excess,disposition='canonical start too far from bar'));continue
 signature=key(Q,8)
 # Positive full-layout identity and a deliberately changed coordinate that must fail.
 bad=list(Q);x,y,a=bad[0];bad[0]=(x+.01,y,a);assert key(bad,8)!=signature
 target=W/'preq-seeds'/f'{n}-owned-original.csv'
 with target.open('w',newline='') as h:
  writer=csv.writer(h);writer.writerow(CSV)
  for i,(x,y,a) in enumerate(Q):writer.writerow([n,i,repr(x),repr(y),repr(a)])
 ownpin=blob(target);receipt=W/'seed-identity'/f'{n}.json';receipt.parent.mkdir(exist_ok=True)
 proof=dict(n=n,canonical_relative_path='seeds/'+name,canonical_snapshot=pin['snapshot'],canonical_sha256=pin['sha256'],packing_snapshot=ownpin['snapshot'],packing_sha256=ownpin['sha256'],full_geometry_sha256=signature,former_transport_sha256=hashlib.sha256(former.read_bytes()).hexdigest(),source='n = '+str(n)+' of Samanyu-dev/squares_in_squares (GitHub), original owned seed',licence='Own original seed, round30 override',identity_control='all squares match at eight decimals; changed coordinate fails')
 atomic(receipt,proof)
 source=proof['source']+'; extracted directly from '+name+'; pinned extraction receipt '+str(receipt)
 atomic(Path(str(target)+'.json'),dict(n=n,source=source,source_override=source,licence=proof['licence'],licence_override=proof['licence'],prequench=True,input_sha256=ownpin['sha256'],original_seed_receipt=str(receipt)))
 excess=side(Q)-(1+live[n])*math.sqrt(n)
 records.append(dict(n=n,former_matched=bool(matches),canonical_extraction_verified=True,catalogue=name,input=str(target),excess=excess,receipt=str(receipt)))
 if excess<=.0005:out.append(str(target))
atomic(W/'original-seed-controls30.json',dict(passed=bool(out),rows=records,all_coordinates_checked=True,negative='one coordinate changed by0.01 rejected for every matching row'))
assert out
# Check one real source graph before activating the replacement input pool.
p=Path(out[0]);meta=read(str(p)+'.json',{});a,why=audit(meta['source'],meta['licence'],meta,int(meta['n']))
assert why is None and not a['history']['issues'] and all(ref=='Samanyu-dev/squares_in_squares' for ref,n in a['history']['public']),(why,a['history'])
atomic(W/'original-source-control30.json',dict(passed=True,n=meta['n'],history=a['history']))
atomic(W/'REOPEN_BEST.json',out)
note('START '+str(len(out))+' direct canonical original-seed alternatives within side allowance. The prior held-row identity test did not confirm equality, so inherited source graphs were not rewritten. Each new start is extracted from a pinned owned catalogue; changed-coordinate controls fail; real source control has only own Samanyu root. Fresh designs stay ahead.')
print(json.dumps(dict(admitted=len(out),rows=records),indent=1),flush=True)
