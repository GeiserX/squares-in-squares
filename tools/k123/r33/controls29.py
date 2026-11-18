from pathlib import Path
import sys,csv,json,hashlib,io
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from producer_guard28 import same_producer_records
from policy27 import banned
from provenance24 import mlp,credit,S
p=S/'take-k123-r28/756.csv';A=mlp.load(str(p),{756})[756];assert credit(756,A,str(p))
assert banned('recorded ancestry from prvsiyan/squares-verified-best-of-1105')
assert banned('recorded ancestry from penguin069/squares-joegun-boxed-certified-union')
body=(p.parent/'take.tsv').read_bytes();records={str(p.parent/'take.tsv'):body}
rows=list(csv.DictReader(io.StringIO(body.decode()),delimiter='\t'))
def pack(rows):
 out=io.StringIO();wr=csv.DictWriter(out,rows[0].keys(),delimiter='\t');wr.writeheader();wr.writerows(rows);return out.getvalue().encode()
assert same_producer_records(records,records,756)
changed=[dict(r) for r in rows];next(r for r in changed if r['n']=='756')['source']='changed target source'
assert not same_producer_records(records,{str(p.parent/'take.tsv'):pack(changed)},756)
changed=[dict(r) for r in rows];next(r for r in changed if r['n']!='756')['source']='unrelated count update'
assert same_producer_records(records,{str(p.parent/'take.tsv'):pack(changed)},756)
result={'own756_accepted':True,'excluded_public_ancestry_rejected':True,'stable_producer_accepted':True,'changed_target_rejected':True,'unrelated_target_accepted':True,'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(W/'controls29.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
