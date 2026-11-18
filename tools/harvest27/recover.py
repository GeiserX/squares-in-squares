"""Reopen the round 26 near-public starts excluded only for Samanyu ancestry."""
import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,W,setup,enqueue,state,hand,write_json
from policy import audit,control
setup();control()
old = S/'take-harvest-r26/work'
queue = {r['start']:r for r in csv.DictReader((old/'near-pub/queue-fresh-all.tsv').open(),delimiter='\t')}
measured = list(csv.DictReader((old/'near-pub/excl-share.tsv').open(),delimiter='\t'))
rows=[]
for r in measured:
    if not r['label'].startswith('samanyu'):
        continue
    q=queue[r['start']]; p=old/r['start'];rr=list(csv.DictReader(p.open()))
    ok,ev=audit(rr)
    record=dict(q,original_samanyu_share=float(r['share1e3']),allowed=ok,evidence=ev)
    rows.append(record)
    if not ok:
        continue
    source_file=str(old/q['file'])
    meta=dict(n=int(q['n']), kind='reopened-public', source=f"round27 reopened public start; source_file {source_file}; original update {q['updated']}; Samanyu ancestry exclusion lifted", licence=q['licence'], evidence=ev)
    job=enqueue(p,meta,0)
    state(f'QUEUE reopened Samanyu-only n={q["n"]} snapshot={json.loads(job.read_text())["path"]} deadline 23:45Z')
write_json(W/'reopened.json',rows)
allowed=[r for r in rows if r['allowed']]
state(f'RECOVER checked {len(rows)} formerly Samanyu-labelled starts; {len(allowed)} pass remaining share policy; {len(rows)-len(allowed)} still excluded')
hand(f'Reopened {len(allowed)} formerly Samanyu-only public near starts, immutable snapshots queued first for one fq; measurements {W}/reopened.json; original r26 dirs unchanged')
