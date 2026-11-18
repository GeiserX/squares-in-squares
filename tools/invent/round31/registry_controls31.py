"""Prove the submitted-row cut without reading a public archive beneath it."""
import pathlib,sys,json
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import public_branch30 as B
fixture=None
for p in(W/'evidence').glob('*.json'):
 d=json.load(open(p))
 if d.get('n')==541:fixture=(p,pathlib.Path(d['ancestry']));break
assert fixture
old=B.L.audit
B.L.audit=lambda *a,**k:(_ for _ in()).throw(AssertionError('tried public archive beneath a byte-verified held row'))
r=B.audit(*fixture);assert r['clean']and r['submitted_held_root']and not r['public_roots']
e=json.load(open(fixture[0]));e['input_sha256']='0'*64;bad=W/'registry-bad-evidence.json';bad.write_text(json.dumps(e))
try:B.audit(bad,fixture[1])
except (ValueError,AssertionError):pass
else:raise AssertionError('wrong input identity received held exemption')
B.L.audit=old
# The direct-public controls remain separate from the registry and cannot take its cut.
assert not any('take-harvest-r26/814.csv'in p for p in json.load(open(W/'held-registry31.json'))['rows'])
result=dict(actual541_held_root_without_archive=True,wrong_input_hash_refused=True,direct814_not_in_held_registry=True)
(W/'registry-controls31.json').write_text(json.dumps(result));print(json.dumps(result))
