#!/usr/bin/env python3
"""rebuild_bars.py OUT.tsv [BASE_DETAILS.csv]: the base bar of the rebuild lane per n.

The bar is the lower of the base details.csv (default gate/cand-round25-1114b) and every row of the live
take-*-r<SQ_ROUND>/take.tsv files (SQ_ROUND in the environment, default 26) whose source and licence cells classify as free of Samanyu-dev seed ancestry
(forensics_policy.classify_text status 'none'), minus rows that name a WITHDRAWN parent. Writes n, score, side, origin. Our own code; it imports
forensics_policy and does not change it."""
import csv, glob, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_policy as fp  # noqa: E402

S = '$SCRATCH/bounties-squares'
csv.field_size_limit(1 << 28)
# Parents withdrawn in the handoff log although later rows still label them clean: k123 withdrew its near 927
# (548-927 join, defer00384) at 21:11 on 2026-11-13 as seed 811; the invent 927 of round 24 descends from it.
# The round 25 brief also withdraws the 735 tree of seed 365 with the 790 built on it: the border lane's frozen
# round 24 735 and 790 (k123, stair-c and midm read it the same way in handoff-r25.log).
WITHDRAWN = ('927-pending-j22a-defer00384', '927-reclassified-seed811', 'take-border-r24/735.csv', 'fq quench of rev on n=847')


def bars(base=S + '/gate/cand-round25-1114b/details.csv'):
    out = {int(r['n']): (float(r['score']), 'base') for r in csv.DictReader(open(base))}
    for t in sorted(glob.glob(S + '/take-*-r%s/take.tsv' % os.environ.get('SQ_ROUND', '26'))):
        for r in csv.DictReader(open(t), delimiter='\t'):
            if fp.classify_text(r['source'] + ' ' + r['licence'])['status'] != 'none':
                continue
            if any(w in r['source'] for w in WITHDRAWN):
                continue
            n, s = int(r['n']), float(r['new'])
            if s < out[n][0]:
                out[n] = (s, t.split('/')[-2])
    return out


if __name__ == '__main__':
    b = bars(*sys.argv[2:3])
    with open(sys.argv[1], 'w') as f:
        for n in sorted(b):
            s, o = b[n]
            f.write('%d\t%.17g\t%.15f\t%s\n' % (n, s, (s + 1) * math.sqrt(n), o))
