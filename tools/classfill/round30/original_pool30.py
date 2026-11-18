"""Fill spare boxE slots from direct owned catalogues at the current bar."""
from common29 import *
from light29 import load,key,side
assert read(W/'preq-control-result.json',{}).get('passed') and read(W/'original-source-control30.json',{}).get('passed')
base,live,_=bar();catalogue=S/'seeds/samanyu_bestfit.csv';C=load(catalogue);pin=blob(catalogue)
board={int(r['n']):float(r['board_L']) for r in rows(S/'main-r17/gap-by-n.tsv')}
closed=set()
# Jobs use n in their input names, so include already dispatched preparation legs.
for p in (W/'jobs').glob('*.json'):
 j=read(p,{})
 if j.get('prequench'):
  match=re.match(r'data/(\d+)',j.get('input',''))
  if match:closed.add(int(match[1]))
rank=[]
for n,P in C.items():
 if n<300 or n in closed:continue
 L=side(P);excess=L-(1+live[n])*math.sqrt(n)
 if excess>.0005 or abs(L-round(L))<1e-7:continue
 rank.append(((1+live[n])-board[n]/math.sqrt(n),n,P,excess))
paths=[];records=[]
for gap,n,P,excess in sorted(rank,reverse=True)[:24]:
 path=W/'preq-seeds'/f'{n}-owned-original.csv'
 with path.open('w',newline='') as h:
  wr=csv.writer(h);wr.writerow(CSV)
  for i,(x,y,a) in enumerate(P):wr.writerow([n,i,repr(x),repr(y),repr(a)])
 packing=blob(path);signature=key(P,8);assert key(load(path,{n})[n],8)==signature
 source=f'n = {n} of Samanyu-dev/squares_in_squares (GitHub), original owned seed'
 receipt=W/'seed-identity'/f'{n}.json'
 atomic(receipt,dict(n=n,source=source,licence='Own original seed, round30 override',canonical_relative_path='seeds/samanyu_bestfit.csv',canonical_snapshot=pin['snapshot'],canonical_sha256=pin['sha256'],packing_snapshot=packing['snapshot'],packing_sha256=packing['sha256'],full_geometry_sha256=signature,method='extract the requested complete catalogue row'))
 source+='; direct catalogue extraction; pinned receipt '+str(receipt)
 atomic(Path(str(path)+'.json'),dict(n=n,source=source,source_override=source,licence='Own original seed, round30 override',licence_override='Own original seed, round30 override',prequench=True,input_sha256=packing['sha256'],original_seed_receipt=str(receipt)))
 paths.append(str(path));records.append(dict(n=n,gap=gap,side_excess=excess,input_sha256=packing['sha256'],receipt=str(receipt)))
atomic(W/'original-pool30.json',dict(rows=records,already_dispatched=sorted(closed)))
atomic(W/'REOPEN_BEST.json',paths)
note('START direct owned original pool: '+str(len(paths))+' non-integer-side rows within5e-4 of current bar, excluding every n with a dispatched pre-quench leg. Extracted from pinned Samanyu bestfit catalogue; source control passed. boxE spare slots only, fresh queue priority higher, n2 preparation control passed.')
print(json.dumps(dict(count=len(paths),rows=records),indent=1),flush=True)
