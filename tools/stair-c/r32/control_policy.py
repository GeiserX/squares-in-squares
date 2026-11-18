"""Exercise frozen public geometry, source boundaries and byte withdrawals."""
import csv,hashlib,json,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import public_roots as P
import withdrawals as W
P.control()
policy=P.geometry_policy();policy.control()
with tempfile.TemporaryDirectory()as d:
 p=Path(d)/'take-control-r32/805.csv';p.parent.mkdir();p.write_bytes(b'old')
 digest=hashlib.sha256(p.read_bytes()).hexdigest();cache={}
 line=f'2026-11-16T11:00:00Z control -> all: WITHDRAW exact bytes sha256 {digest}, {p}'
 out=W.tokens([line],cache,d)
 assert str(p)+' immutable sha256 '+digest in out
 p.write_bytes(b'changed')
 assert str(p)+' immutable sha256 '+hashlib.sha256(p.read_bytes()).hexdigest()not in W.tokens([line],cache,d)
print('CONTROL frozen source policy and withdrawal hashes passed',flush=True)
