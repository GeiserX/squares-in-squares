"""Round 24 take against the candidate and other live round 24 takes."""
import csv
csv.field_size_limit(16 * 1024 * 1024)
import glob
import json
from pathlib import Path
import re
import sys

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r24'
base={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round23-1113a/details.csv'))}
free_counts={228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}
low = {}; low_free={}
for pat in ('take-*-r24',):
    for name in sorted(glob.glob(str(B / pat))):
        d = Path(name)
        if d == T or not (d / 'take.tsv').exists():
            continue
        for r in csv.DictReader((d / 'take.tsv').open(), delimiter='\t'):
            try:
                n, v = int(r['n']), float(r['new'])
            except (KeyError, TypeError, ValueError):
                continue
            text=(r.get('source','')+' '+r.get('licence','')).lower()
            if 'samanyu-dev/squares_in_squares' not in text and (n not in low_free or v<low_free[n][0]):low_free[n]=(v,d.name)
            if n not in low or v < low[n][0]:
                low[n] = (v, d.name)
tags = {}
if (T / 'work/TAGS.tsv').exists():
    tags = dict(l.split('\t')[:2] for l in (T / 'work/TAGS.tsv').read_text().splitlines())
out = ['n\theld\tnew\tgain_on_round23_file\tlowest_other\tlowest_other_dir\tgain_on_all\tstart_dir\ttag\tsource\tlicence']
s1 = s2 = accepted_gain = 0.0
n1 = n2 = 0
if (T / 'take.tsv').exists():
    for r in csv.DictReader((T / 'take.tsv').open(), delimiter='\t'):
        n, accepted, new = int(r['n']), float(r['held']), float(r['new'])
        held=base[n]
        accepted_gain+=accepted-new
        source_free='samanyu-dev/squares_in_squares' not in (r.get('source','')+' '+r.get('licence','')).lower()
        comparison=low_free if n in free_counts and source_free else low
        lo, who = comparison.get(n, (accepted, 'accepted bar'))
        bar = min(accepted,lo)
        g2 = bar - new if new < bar - 1e-10 else 0.0
        m = re.search(r'in (take-[a-z0-9-]+)', r['source'])
        out.append('%d\t%r\t%r\t%.12g\t%r\t%s\t%.12g\t%s\t%s\t%s\t%s' % (
            n, held, new, held - new, lo, who, g2, m[1] if m else '', tags.get(str(n), ''),r.get('source','').replace('\t',' ').replace('\n',' '),r.get('licence','').replace('\t',' ').replace('\n',' ')))
        s1 += held - new
        s2 += g2
        n1 += 1
        n2 += g2 > 0
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text('\n'.join(out) + '\n')
print(json.dumps(dict(rows=n1, gain_round23=s1, gain_accepted_bars=accepted_gain, live_rows=n2, gain_all=s2), sort_keys=True))
