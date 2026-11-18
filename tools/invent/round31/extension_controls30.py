"""Exercise endpoint receipt failures before extending source evidence."""
import json,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from extend30 import extend,verified_end
jobs=json.load(open(W/'jobs.json'));parent=next(j for j in jobs if j['id']=='fresh30x547x2cccb240668c')
folder=W/'boxE-raw'/parent['id'];p=folder/'final/547.csv';receipt=json.load(open(folder/'done.json'))
cert=folder/'certin/547.csv';marker=folder/'quench/547.done'
assert verified_end(p,547,receipt,cert,marker)==receipt['sha256']
for bad in (dict(receipt,sha256='0'*64),dict(receipt,quench_input_sha256='0'*64),dict(receipt,quench_from_certified=False),dict(receipt,new=float('nan'))):
 try:verified_end(p,547,bad,cert,marker);raise AssertionError('bad endpoint receipt accepted')
 except ValueError:pass
try:verified_end(p,546,receipt,cert,marker);raise AssertionError('wrong count accepted')
except ValueError:pass
assert not extend(dict(parent,evidence_sha256='0'*64),p,547,parent['ancestry'])['clean']
first=extend(parent,p,547,parent['ancestry']);second=extend(parent,p,547,parent['ancestry'])
assert first['clean']and first==second
(W/'extension-controls30.json').write_text(json.dumps(dict(certified_endpoint=True,wrong_end_hash_refused=True,wrong_quench_input_refused=True,unfinished_quench_refused=True,nan_refused=True,wrong_count_refused=True,wrong_parent_evidence_refused=True,replay_identical=True,result=first),indent=2))
print('CONTROL complete endpoint and source walk accepted; bad endpoint, quench-input, parent-evidence and count identities refused; unfinished/NaN refused; replay identical')
