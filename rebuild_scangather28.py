import csv, glob, math, sys
import numpy as np
S = '$SCRATCH/bounties-squares/'
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'round28-briefs/bar28.tsv'), delimiter='\t')}
out = open(sys.argv[1], 'w')
for p in sorted(glob.glob(S + 'gather/*.csv')):
    try:
        pz = {}
        with open(p) as h:
            rd = csv.DictReader(h)
            if 'angle' not in rd.fieldnames: continue
            for r in rd:
                pz.setdefault(int(r['n']), []).append((float(r['x']), float(r['y']), float(r['angle'])))
        for n, L in pz.items():
            if len(L) != n or n not in bar: continue
            A = np.array(L); t = A[:, 2]; hh = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
            side = max((A[:, 0] + hh).max() - (A[:, 0] - hh).min(), (A[:, 1] + hh).max() - (A[:, 1] - hh).min())
            sc = side / math.sqrt(n) - 1
            if sc < bar[n] - 1e-10:
                out.write('%d\t%.12f\t%.4e\t%s\n' % (n, side, bar[n] - sc, p.replace(S, ''))); out.flush()
    except Exception as e:
        out.write('#err %s %s\n' % (p, e))
out.write('DONE\n')
