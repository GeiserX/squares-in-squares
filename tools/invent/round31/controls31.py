"""Exercise ownership, public roots and versioned withdrawals before production."""
import hashlib,json,pathlib,sys
W=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(W))
import source_gate28 as G
import public_roots29 as P
from historical756 import resolve
G.refresh_walker()
assert G.Q.LIVE=='31'
assert G.declares_withdrawal('2026-11-15T12:00:00Z x -> all: WITHDRAW n910 sha256 aabbccddeeff')
assert not G.declares_withdrawal('2026-11-15T12:00:00Z x -> all: keeps n910, not the withheld n911')
assert G.lifted_policy('WITHDRAW layout through Samanyu-dev/squares_in_squares seed')
assert G.banned('prvsiyan/squares-verified-best-of-1105')
assert resolve(756,8)
assert resolve(756,7) is None
m=json.load(open(W/'historical756-proof.json'));m['pins'][0]['sha256']='0'*64
assert resolve(756,8,m) is None
folder=W/'controls30';folder.mkdir(exist_ok=True)
def fixture(name,payload,n,source,licence,public):
 p=folder/(name+'.csv');p.write_bytes(payload);h=hashlib.sha256(payload).hexdigest()
 q=folder/(name+'-graph.json');q.write_text(json.dumps(dict(root='root',nodes={'root':dict(source=source,licence=licence)})))
 e=folder/(name+'-evidence.json');e.write_text(json.dumps(dict(snapshots=[dict(path=str(p),original=str(p),sha256=h)],input_sha256=h,n=n,public_first=public)))
 return e,q
own=b'n,x,y,a\n2,0,0,0\n2,1.1,0,0\n'
e,q=fixture('owned',own,2,'own construction: ownership control','our own construction',False)
public=P.P.reader();saved=public.share
public.share=lambda *a,**k:(_ for _ in ()).throw(AssertionError('owned packing received share gate'))
r=P.audit(e,q)
assert r['clean'] and not r['public_roots']
public.share=saved
archive=G.S/'take-harvest-r28/work/ancestry-inputs/harvest-416-6bb3721a-2d91e8a6f7f45e33.csv'
e,q=fixture('public416',archive.read_bytes(),416,'public control/source :: captured file','Apache 2.0',True)
r=P.audit(e,q)
assert not r['clean'] and r['public_roots'][0]['share1e3']>=.4
pin=pathlib.Path(json.load(open(e))['snapshots'][0]['path']);pin.write_bytes(own)
try:P.audit(e,q)
except ValueError:changed=True
else:raise AssertionError('changed frozen public bytes accepted')
G.refresh_walker()
assert G.Q.LIVE=='31'
result=dict(live_round=G.Q.LIVE,owned_without_share=True,public416_share=r['public_roots'][0]['share1e3'],public416_excluded=True,changed_pin_refused=changed,retention_note_preserved=True,historical756_valid=True,historical756_wrong_round_and_hash_refused=True)
(W/'controls31.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
