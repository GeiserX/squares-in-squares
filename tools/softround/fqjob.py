#!/usr/bin/env python3
"""fqjob.py N TAG: the fq quench of the smallest packing of N under run/N-TAG (default flags, then the deep
flags, up to three rounds, the loop of engine_polish.py). Every step that makes the side smaller is written to
run/N-TAG/raw/N-fq-K.csv as raw rows. Nothing is certified here: methods_take's rule runs on boxA."""
import csv, math, os, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np
import methods_lp as mlp
from bestof import best
FQ = HERE + '/fq'
POLISH = ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600']


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def normalize(sq):
    x0 = min(x - hw(a) for x, y, a in sq); y0 = min(y - hw(a) for x, y, a in sq)
    s = max(max(x - x0 + hw(a) for x, y, a in sq), max(y - y0 + hw(a) for x, y, a in sq))
    out = []
    for x, y, a in sq:
        d = math.degrees(a) % 90.0
        if d > 45: d -= 90
        out.append((x - x0, y - y0, d))
    return s, np.array(out)


def quench(s, X, flags=(), timeout=600):
    d = tempfile.mkdtemp(prefix='fq', dir=HERE + '/tmp'); a, b = d + '/a.txt', d + '/b.txt'
    with open(a, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, g in X: h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    t = time.time(); out = (None, None)
    try:
        r = subprocess.run([FQ, 'quench', '--in', a, '--out', b] + list(flags), capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            L = [l.split() for l in open(b) if l.strip() and not l.startswith('#')]
            n = int(L[0][0]); out = (float(L[0][1]), np.array([[float(v) for v in q[:3]] for q in L[1:n + 1]]))
    except subprocess.TimeoutExpired:
        pass
    for f in (a, b):
        if os.path.exists(f): os.remove(f)
    os.rmdir(d)
    return out[0], out[1], time.time() - t


def main():
    n, tag = int(sys.argv[1]), sys.argv[2]
    out = '%s/run/%d-%s/raw' % (HERE, n, tag); os.makedirs(out, exist_ok=True); os.makedirs(HERE + '/tmp', exist_ok=True)
    dl = float(open(HERE + '/fqdeadline').read())
    L0, p = best(n, tag)
    P = mlp.load(p, {n})[n]
    s0, X = normalize([tuple(r) for r in P]); cur = s0
    k = len([f for f in os.listdir(out) if f.startswith('%d-fq-' % n)])
    print('FQ n=%d tag=%s from %s side %.12f' % (n, tag, p, s0), flush=True)
    steps = 0; successful = 0
    for rnd in range(3):
        improved = False
        for name, fl in (('default', ()), ('polish', POLISH)):
            if time.time() > dl:
                print('FQ n=%d deadline' % n, flush=True); break
            s2, X2, dt = quench(cur, X, fl, timeout=min(600, max(1, dl - time.time())))
            successful += s2 is not None
            print('FQ n=%d round %d %s %r -> %r %.0fs' % (n, rnd, name, cur, s2, dt), flush=True)
            if s2 is not None and s2 < cur - 3e-9:
                k += 1; steps += 1
                tmp = '%s/.%d-fq-%d.tmp' % (out, n, k)
                with open(tmp, 'w', newline='') as h:
                    w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                    for i, (x, y, a) in enumerate(X2):
                        w.writerow([n, i, repr(float(x)), repr(float(y)), repr(math.radians(float(a)))])
                os.rename(tmp, '%s/%d-fq-%d.csv' % (out, n, k))
                cur, X, improved = s2, X2, True
        if not improved: break
    print('FQCHECK n=%d tag=%s successful %d' % (n, tag, successful), flush=True)
    print('FQEND n=%d tag=%s L %.12f -> %.12f gain of score %.3e steps %d' % (n, tag, s0, cur, (s0 - cur) / math.sqrt(n), steps), flush=True)
    sys.exit(0 if steps else 3)


if __name__ == '__main__':
    main()
