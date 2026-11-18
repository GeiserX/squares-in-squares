"""Round 26 final numbers for report.json: gain on the base bar and gain beyond the other live take-*-r30 rows."""
from pathlib import Path
import csv, json, sys
csv.field_size_limit(16000000)
W = Path(__file__).parent; T = W.parent; B = T.parent
rows = list(csv.DictReader(open(T / 'take.tsv'), delimiter='\t'))
others = {}
for tp in B.glob('take-*-r30/take.tsv'):
    if tp.parent == T:
        continue
    for r in csv.DictReader(open(tp), delimiter='\t'):
        try:
            others.setdefault(int(r['n']), []).append((float(r['new']), tp.parent.name))
        except (KeyError, ValueError):
            pass
out = []
for r in rows:
    n, held, new = int(r['n']), float(r['held']), float(r['new'])
    live = min(others.get(n, []), default=None)
    floor = min(held, live[0]) if live else held
    out.append(dict(n=n, held=held, new=new, gain=held - new, beyond=floor - new, live=live))
print(json.dumps(dict(rows=out, improved_n=[o['n'] for o in out], gain=sum(o['gain'] for o in out),
                      beyond=sum(o['beyond'] for o in out),
                      all_below_live=all(o['beyond'] > 0 for o in out)), indent=1))
