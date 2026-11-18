"""Quench a certified copy once, and always record the end before publication."""
import os, sys, time
from pathlib import Path
here = Path(__file__).resolve().parent
lane = here if (here / 'family_step.py').exists() else here.parents[1]
sys.path.insert(0, str(lane))
import family_step as fs
out = sys.argv[1] + '/raw'
os.makedirs(out, exist_ok=True)
for p in sys.argv[2:]:
    fn = os.path.basename(p); n = int(fn.split('-')[0])
    L, X = fs.canon(fs.load(p)[n]); L0 = L
    remaining = float(open('deadline').read()) - time.time()
    if remaining <= 0:
        break
    fs.set_limit(remaining)
    s2, Y = fs.fq_quench(L, X, (), timeout=min(240, remaining))
    if s2 is None:
        print('QUENCH INCOMPLETE', n, fn, 'no completed fq output; not eligible for publication', flush=True)
        continue
    if s2 < L - 1e-10:
        Lc, fr = fs.certify(n, Y)
        if Lc is not None and Lc < L:
            X, L = Y, Lc
    destination = sys.argv[1] + '/controls' if fn == '2-readers-positive-control.csv' else out
    os.makedirs(destination, exist_ok=True)
    tmp = destination + '/' + fn + '.tmp'
    fs.write_rows(tmp, n, X)
    os.replace(tmp, destination + '/' + fn)
    print(n, fn, '%.12f -> %.12f (%+.3e)' % (L0, L, L-L0), flush=True)
    if fn == '2-readers-positive-control.csv':
        print('CONTROL PASSES: fq shrank two separated squares below 2.01' if L < 2.01 and L0 > 2.9 else 'CONTROL FAILS: fq did not shrink the separated squares', flush=True)
