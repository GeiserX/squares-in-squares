"""Summarize round 22 kick jobs, with the same-file sigma pairs kept separate."""
import csv
import json
from pathlib import Path
import sys

W = Path('$SCRATCH/bounties-squares/take-midm-r22/work')
done = [json.loads(p.read_text()) for p in (W / 'boxE/done').glob('*.json')]
rawkeys = {int(p.stem[1:]) for p in W.glob('r*.tsv') if 'new-design raw start:' in p.read_text()}
groups = {}
for j in done:
    kind = 'leg' if j.get('leg', 0) else ('new-design raw' if (j.get('raw_design') or j['k'] in rawkeys) else ('r22' if j['source'].endswith('-r22') else j['source'][-3:]))
    a = groups.setdefault(kind, dict(scans=0, seconds=0, gain=0, finds=0))
    a['scans'] += 1
    a['seconds'] += j['elapsed']
    a['gain'] += j.get('gain', 0)
    a['finds'] += j.get('finds', 0)
pairs = {}
for j in done:
    if j.get('ab'):
        pairs.setdefault((j['source'], j['n'], j['seed'], j['sub']), {})[str(j['sigma'])] = j
out = ['source\tn\tseed\tfile\tsigma\tscans\tseconds\tfinds\tgain_before_cert\tclass']
for key, pair in sorted(pairs.items()):
    for sigma, j in sorted(pair.items()):
        out.append('%s\t%d\t%d\t%s\t%s\t1\t%.3f\t%d\t%.12g\t%s' % (
            *key, sigma, j['elapsed'], j.get('finds', 0), j.get('gain', 0),
            'repeat-kick control' if j['k'] in (200, 201) else j.get('phase', 'fresh pair')))
(W / 'ab22.tsv').write_text('\n'.join(out) + '\n')
print(json.dumps(dict(groups=groups, paired_files=len(pairs), complete_pairs=sum(len(p) == 2 for p in pairs.values()),
                      completed_jobs=len(done)), sort_keys=True))
