from common29 import *
while time.time()<END+950:
 r=read(T/'report.json',{})
 state=(T/'STATE.txt').read_text().splitlines();recent=[l for l in state if any(s in l for s in ['CERTIFIED','START_QUEUE','DROP ancestor','FINAL','ERROR','WITHDRAW','FIRST_SCAN'])]
 statuses=[read(p,{}) for host in ['boxE','boxD'] for p in (W/host/'out').glob('x*-status.json')]
 print(json.dumps(dict(time=now(),jobs=len(list((W/'jobs').glob('x*.json'))),completed=len(statuses),returncodes={str(c):sum(j.get('returncode')==c for j in statuses) for c in {j.get('returncode') for j in statuses}},take=[int(q['n']) for q in rows(T/'take.tsv')],prospective=len(list((W/'prospective').glob('*.json'))),last=recent[-1][:450] if recent else '',report=bool(r))),flush=True)
 if r:print(json.dumps(r),flush=True);break
 time.sleep(60)
