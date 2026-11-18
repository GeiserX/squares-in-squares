import pathlib,json,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A
p=A.S/'take-stair-c-r22/near/863-0f92c19d-n.csv'
r=A.S/'take-stair-c-r22/work/boxcopy/n/raw-a/863-0f92c19d.json'
assert A.stair_record_matches(p,r,863)
assert not A.stair_record_matches(p,r,864)
wrong=W/'wrong-stair-record-control.csv';wrong.write_bytes(p.read_bytes()+b'\n')
assert not A.stair_record_matches(wrong,r,863)
src,lic,record=A.metadata(p,863);assert src and lic and record==str(r)
value=dict(exact_863_accepted=True,changed_input_refused=True,wrong_count_refused=True,record=str(r))
(W/'record-controls.json').write_text(json.dumps(value));print(json.dumps(value))
