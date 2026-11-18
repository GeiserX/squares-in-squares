"""Light status for the supervising implementation run."""
from common29 import *
state=(T/'STATE.txt').read_text().splitlines();started=sum('START_QUEUE ' in q for q in state);done=sum('WORKER_EVENT ' in q and ' DONE ' in q for q in state)
cert=[q for q in state if 'CERTIFIED ' in q];prosp=len(list((W/'prospective').glob('*.json')));take=rows(T/'take.tsv')
heartbeat=read(W/'heartbeat.json',{});out=dict(utc=now(),started=started,completed=done,retained=[int(r['n'])for r in take],prospective=prosp,collector=heartbeat.get('time_utc'),latest=state[-1] if state else '')
print(json.dumps(out),flush=True)
