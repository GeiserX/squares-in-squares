"""table21.py [OUT.tsv]: the midm take of round 21 against the round 19 file and against every other take dir.

One row per n of take-midm-r21/take.tsv: the held score (round 19 file), the new score, the gain, the lowest score of
the same n in every take-*-r20 dir (frozen, our own included) and every other take-*-r21 dir at the time of the call, the gain over that, the
dir the kick started from and the tag of the raw file. Prints both sums.
"""
import csv, glob, os, re, sys
B = '$SCRATCH/bounties-squares/'; T = B + 'take-midm-r21/'
low = {}
for d in sorted(glob.glob(B + "take-*-r20") + glob.glob(B + "take-*-r21")):
    if d.rstrip('/').endswith('take-midm-r21') or not os.path.exists(d + '/take.tsv'):
        continue
    for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
        try:
            n, v = int(r['n']), float(r['new'])
        except (KeyError, TypeError, ValueError):
            continue
        if n not in low or v < low[n][0]:
            low[n] = (v, os.path.basename(d))
tags = {}
if os.path.exists(T + 'work/TAGS.tsv'):
    tags = dict(l.rstrip('\n').split('\t')[:2] for l in open(T + 'work/TAGS.tsv') if l.strip())
out = ['n\theld\tnew\tgain_on_round19_file\tlowest_other\tlowest_other_dir\tgain_on_all\tstart_dir\ttag']
s1 = s2 = 0.0; n1 = n2 = 0
if os.path.exists(T + 'take.tsv'):
    for r in csv.DictReader(open(T + 'take.tsv'), delimiter='\t'):
        n = int(r['n']); held = float(r['held']); new = float(r['new'])
        lo, who = low.get(n, (held, 'round 19 file')); bar = min(held, lo)
        g2 = bar - new if new < bar - 1e-10 else 0.0
        m = re.search(r'in (take-[a-z0-9-]+)', r['source'])
        out.append('%d\t%r\t%r\t%.3e\t%r\t%s\t%.3e\t%s\t%s' % (n, held, new, held - new, lo, who, g2, m.group(1) if m else '', tags.get(str(n), '')))
        s1 += held - new; n1 += 1; s2 += g2; n2 += g2 > 0
if len(sys.argv) > 1:
    open(sys.argv[1], 'w').write('\n'.join(out) + '\n')
print('rows %d, below the round 19 file by %.4e; %d n below every other take dir too, by %.4e' % (n1, s1, n2, s2))
