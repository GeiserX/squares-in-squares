import pathlib,json,sys,shutil
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A
p=A.S/'take-forensics-r28/work/feed/warm-partners/416-b8ac2c6463a40e33ae791c16.csv';o=pathlib.Path(str(p)+'.origin.json');value=json.load(open(o))
raw=A.forensics_sources.compact_ancestry(value['ancestry'],o);clean=A.forensics_sources.compact_ancestry(A.ancestry_only(value['ancestry']),o)
assert len(clean['roots'])==1 and clean['roots'][0]['path'].endswith('gather/round23-2026-11-13a.csv')
src,lic,record=A.pinned_origin_metadata(p,416);assert 'pinned_snapshot_roots'in src and lic
bad=W/'altered-origin416.csv';bad.write_bytes(p.read_bytes()+b'\n');shutil.copy(o,pathlib.Path(str(bad)+'.origin.json'))
assert 'input hash or count mismatch'in A.pinned_origin_metadata(bad,416)[0]
assert 'input hash or count mismatch'in A.pinned_origin_metadata(p,417)[0]
result=dict(raw_roots=len(raw['roots']),actual_roots=len(clean['roots']),valid_bound_origin_accepted=True,changed_bytes_refused=True,wrong_count_refused=True)
(W/'origin-controls.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
