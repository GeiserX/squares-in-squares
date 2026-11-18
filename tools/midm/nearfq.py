# quench every near composition once with fq (default, then deep flags) and report against the held side
import sys, glob, os, csv, math
sys.path.insert(0,'.')
import numpy as np, methods_lp as mlp
from midm_scan import to_fq, from_fq, quench, POLISH
d, heldf, fq = sys.argv[1], sys.argv[2], sys.argv[3]
files = sorted(glob.glob(d + '/near/*.csv')); ns = {int(os.path.basename(f).split('-')[0]) for f in files}
held = {n: mlp.side(P) for n, P in mlp.load(heldf, ns).items()}
os.makedirs(d + '/raw', exist_ok=True); os.makedirs(d + '/tmp', exist_ok=True); wins = 0; tot = 0
for f in files:
    n = int(os.path.basename(f).split('-')[0]); tag = os.path.basename(f)[:-4].split('-')[1]
    P = mlp.load(f, {n})[n]; s, X = to_fq(P); s0 = s
    for fl in (('--loosen', '1.0'), (), POLISH):
        s2, X2 = quench(fq, d + '/tmp', s, X, fl)
        if s2 is not None and s2 < s - 1e-10: s, X = s2, X2
    tot += 1; ok = s < held[n] - 1e-9; wins += ok
    print('%d %s start %.9f -> %.9f held %.9f %s' % (n, tag, s0, s, held[n], 'BELOW %.3e' % ((held[n] - s) / math.sqrt(n)) if ok else ''), flush=True)
    if ok:
        Q = from_fq(X)
        with open('%s/raw/%d-%s.csv' % (d, n, tag), 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for i, (x, y, a) in enumerate(Q): w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(a))])
print('quenched', tot, 'below held', wins)
