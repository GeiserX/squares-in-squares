"""Preserve source holds across path rewrites and distinguish explicit newer versions."""
import pathlib,json,hashlib,sys
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r28/work');sys.path.insert(0,str(W))
import source_gate28 as G
line='2026-11-15T03:41:06Z stair-c -> all: SOURCE-HOLD pending full ancestry repair for own raw near804-r28-e5f4576fae88-slp-n.csv, 995-r28-4e5a3ebbdf72-slp-s.csv and997-r28-fa32dc5d6ce6-m.csv under take-stair-c-r28/near/. Current producer walk finds missing source record.'
assert len(G.notice_paths(line))==3
path=W/'withdrawal-version-control.txt';path.write_text('replacement bytes')
snap=dict(original=str(path),sha256=hashlib.sha256(b'withdrawn old bytes').hexdigest())
assert G.withdrawal_applies(snap,line)
assert G.withdrawal_applies(dict(snap,original_mtime_ns=1),line)
assert not G.withdrawal_applies(dict(snap,original_mtime_ns=G.Q.withdraw_time(line)*1e9+1e9),line)
assert G.withdrawal_applies(snap,line+' sha256 '+snap['sha256'])
assert not G.withdrawal_applies(snap,line+' sha256 '+'0'*64)
result=dict(source_hold_refs=3,old_changed_path_still_held=True,older_snapshot_held=True,newer_snapshot_separate=True,explicit_hash_match_held=True,other_hash_unchanged=True)
(W/'withdrawal-version-controls.json').write_text(json.dumps(result));print(json.dumps(result))
