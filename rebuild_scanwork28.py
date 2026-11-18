"""scanwork28.py LIST OUT: side of every per-n csv in LIST (one path per line), lane format (n,square_id,x,y,angle in radians,
an optional id column first); writes the files whose score is below bar28 by more than 1e-10 (n, side, gain, path).
Duplicate bytes are read once (sha1)."""
import hashlib, math, sys, csv
import numpy as np
S = '$SCRATCH/bounties-squares/'
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'round28-briefs/bar28.tsv'), delimiter='\t')}
seen = set()
out = open(sys.argv[2], 'w')
k = 0
for p in open(sys.argv[1]):
    p = p.strip()
    k += 1
    try:
        b = open(p, 'rb').read()
        h = hashlib.sha1(b).digest()
        if h in seen:
            continue
        seen.add(h)
        lines = b.decode('utf-8', 'replace').split('\n')
        hd = lines[0].strip().split(',')
        if 'x' not in hd or 'angle' not in hd or 'n' not in hd:
            continue
        ix, iy, ia, i_n = hd.index('x'), hd.index('y'), hd.index('angle'), hd.index('n')
        rows = [l.split(',') for l in lines[1:] if l.strip()]
        ns = set(r[i_n] for r in rows)
        if len(ns) != 1:
            continue
        n = int(ns.pop())
        if len(rows) != n or n not in bar:
            continue
        A = np.array([[float(r[ix]), float(r[iy]), float(r[ia])] for r in rows])
        t = A[:, 2]; hh = 0.5 * (np.abs(np.cos(t)) + np.abs(np.sin(t)))
        side = max((A[:, 0] + hh).max() - (A[:, 0] - hh).min(), (A[:, 1] + hh).max() - (A[:, 1] - hh).min())
        sc = side / math.sqrt(n) - 1
        if sc < bar[n] - 1e-10:
            out.write('%d\t%.12f\t%.4e\t%s\n' % (n, side, bar[n] - sc, p.replace(S, ''))); out.flush()
    except Exception:
        pass
    if k % 20000 == 0:
        out.write('#progress %d\n' % k); out.flush()
out.write('DONE %d\n' % k)
