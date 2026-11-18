from common28 import *
from light28 import load,side
host='boxE';tag='xwidecontrol28c';status=read(W/host/'out'/(tag+'-status.json'),{})
assert status and status.get('returncode')==0,'control is incomplete'
paths=list((W/host/'out').glob('*-'+tag+'/2.json'));assert len(paths)==1
f=read(paths[0],{});out=paths[0].with_suffix('.csv');end=side(load(str(out),{2})[2]);start=f['finish_start_side']
assert abs(start-2.0004)<1e-12 and end<2.000000001,(start,end)
assert f.get('finish_quenched') and f['finish_kicks']=='0.08,0.12'
scans=list((W/host/'out'/('finish-'+tag)/'kick').glob('scan-*.tsv'));tries=sum(len([x for x in p.read_text().splitlines() if re.match(r'\d+\t',x)]) for p in scans);assert tries>0
q=dict(time=now(),passed=True,kicks=f['finish_kicks'],start_side=start,end_side=end,tries=tries,finish_quenched=True,output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),input_sha256=hashlib.sha256((W/'inputs'/('2-'+tag+'.csv')).read_bytes()).hexdigest())
atomic(W/'widekick-control.json',q);note('LARGER_KICK_CONTROL_PASS '+json.dumps(q));print(json.dumps(q))
