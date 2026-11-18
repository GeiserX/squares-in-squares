"""Round 22 take against the held file, frozen round 21 and live round 22 takes."""
import csv
import glob
import json
from pathlib import Path
import re
import sys

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r22'
low = {}
for pat in ('take-*-r21', 'take-*-r22'):
    for name in sorted(glob.glob(str(B / pat))):
        d = Path(name)
        if d == T or not (d / 'take.tsv').exists():
            continue
        for r in csv.DictReader((d / 'take.tsv').open(), delimiter='\t'):
            try:
                n, v = int(r['n']), float(r['new'])
            except (KeyError, TypeError, ValueError):
                continue
            if n not in low or v < low[n][0]:
                low[n] = (v, d.name)
tags = {}
if (T / 'work/TAGS.tsv').exists():
    tags = dict(l.split('\t')[:2] for l in (T / 'work/TAGS.tsv').read_text().splitlines())
out = ['n\theld\tnew\tgain_on_round20_file\tlowest_other\tlowest_other_dir\tgain_on_all\tstart_dir\ttag']
s1 = s2 = 0.0
n1 = n2 = 0
if (T / 'take.tsv').exists():
    for r in csv.DictReader((T / 'take.tsv').open(), delimiter='\t'):
        n, held, new = int(r['n']), float(r['held']), float(r['new'])
        lo, who = low.get(n, (held, 'round20 file'))
        bar = min(held, lo)
        g2 = bar - new if new < bar - 1e-10 else 0.0
        m = re.search(r'in (take-[a-z0-9-]+)', r['source'])
        out.append('%d\t%r\t%r\t%.12g\t%r\t%s\t%.12g\t%s\t%s' % (
            n, held, new, held - new, lo, who, g2, m[1] if m else '', tags.get(str(n), '')))
        s1 += held - new
        s2 += g2
        n1 += 1
        n2 += g2 > 0
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text('\n'.join(out) + '\n')
print(json.dumps(dict(rows=n1, gain_round20=s1, live_rows=n2, gain_all=s2), sort_keys=True))
