from common29 import *
from public_review30 import review,review_ref
ref='jazivxt/boxed-in-sub';n=793;archive=S/'take-harvest-r27/work/public02/data/nb/jazivxt__boxed-in-sub/submission.csv'
root=review_ref(ref,n,[str(archive)]);row=root['variants'][0]['row'];p=W/'controls-pinned/793-public.csv';p.parent.mkdir(exist_ok=True);p.write_bytes(Path(row['snapshot']).read_bytes());meta=Path(str(p)+'.json');atomic(meta,dict(source=ref+' :: submission.csv',licence='Apache 2.0',public_first=True,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
proof=W/'pinned-root-control-proof.json';a=dict(source='control',snapshots=[blob(p),blob(meta)],expanded=dict(history=dict(public=[[ref,n]])));atomic(proof,a)
r=review(proof);assert r['complete'] and not r['excluded'] and r['roots'][0].get('binding'),r
broken=dict(a);broken['snapshots']=[dict(a['snapshots'][0],sha256='0'*64),a['snapshots'][1]];bad=W/'pinned-root-broken-proof.json';atomic(bad,broken);negative=review(bad);assert not negative['complete'] and negative['ancestor']['errors']
atomic(W/'pinned-controls30.json',dict(passed=True,positive='exact public-first793 pin accepted despite changing archive versions',negative='altered packing hash rejected',source_proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest()))
note('CONTROL exact public-first row binding PASS: pinned793 accepted despite differing archive versions; altered pin rejected. Own sources remain exempt. No archive inferred from descendant geometry.')
print('PINNED_PUBLIC_ROOT_CONTROL_PASS',flush=True)
