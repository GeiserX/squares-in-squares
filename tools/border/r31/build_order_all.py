"""r31: the wider held-row kick list after held31/order.json. Classes: 0 = open (order.json), 1 = rows that round 30 c
added (results/round30-best-2026-11-15.tsv; their final bytes got no kick after the deadline certification: rebuild r30
593 moved 1.94e-3 of side that way), 2 = rows named by a kick or claim line of handoff-r29 only, 3 = rows named in
handoff-r30. Within a class the largest board gap first; board gap 1e-7 of score or more, side fraction not shared,
639 691 745 858 918 980 and rows whose table text names the prvsiyan file or CC BY-SA out."""
import json, csv, re
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent
info = {int(k): v for k, v in json.load(open(W / 'held31/info.json')).items()}
order = {int(k): v for k, v in json.load(open(W / 'held31/order.json')).items()}
new30 = {int(r['n']) for r in csv.DictReader(open('results/round30-best-2026-11-15.tsv'), delimiter='\t')}
out = []
for n, v in info.items():
    if v['bad'] or v['gap'] is None or v['rigid']: continue
    if n in order: cls = 0
    elif n in new30: cls = 1
    elif v['gap'] < 1e-7: continue
    elif v['named'] == 'handoff-r29.log': cls = 2
    else: cls = 3
    out.append((cls, -v['gap'], n))
out.sort()
(W / 'held31/order_all.json').write_text(json.dumps([[c, n, -g] for c, g, n in out]))
from collections import Counter
print(len(out), Counter(c for c, _, _ in out)); print([n for c, _, n in out if c == 1])
