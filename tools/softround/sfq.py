#!/usr/bin/env python3
"""sfq.py N TAG [MAX]: the fq quench of the soft-free members of an island (round 28).

The round 28 islands on quenched near files reached soft-free states 2e-4 to 6e-4 of side below the legal side, with no
legal packing out of the island's own exact repair (ladder and reclose): 0 finds in 50,000 to 100,000 children each.
This step hands each soft-free member that methods_soft.py kept (--keep-softfree 1, run/N-TAG/softfree/N-*-box*.csv) to
fq quench (default flags, then the polish flags), largest box first, up to MAX members (default 12). A result whose side
is more than 3e-9 below the start side is written to run/N-TAG/raw/N-sfq-K.csv as raw rows. Nothing is certified here:
collect certifies on boxA (floatsafe at 2.2e-11)."""
import csv, glob, math, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import methods_lp as mlp
from bestof import best
from fqjob import normalize, quench, POLISH


def main():
    n, tag = int(sys.argv[1]), sys.argv[2]
    cap = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    run = '%s/run/%d-%s' % (HERE, n, tag); out = run + '/raw'; os.makedirs(out, exist_ok=True)
    os.makedirs(HERE + '/tmp', exist_ok=True)
    dl = float(open(HERE + '/fqdeadline').read())
    L0, p0 = best(n, tag)
    members = []
    for p in glob.glob('%s/softfree/%d-*-box*.csv' % (run, n)):
        m = re.search(r'-box([0-9.]+)\.csv$', p)
        if m:
            members.append((float(m[1]), p))
    members.sort(reverse=True)
    print('SFQ n=%d tag=%s start side %.12f members %d (trying %d)' % (n, tag, L0, len(members), min(cap, len(members))), flush=True)
    k = len(glob.glob('%s/%d-sfq-*.csv' % (out, n))); tried = 0; ok = 0; bestL = L0
    for box, p in members[:cap]:
        if time.time() > dl - 30:
            print('SFQ n=%d deadline' % n, flush=True); break
        P = mlp.load(p, {n})[n]
        s0, X = normalize([tuple(r) for r in P])
        inp, cur = s0, None          # the member's bounding side is not a legal side: only quench answers count
        for name, fl in (('default', ()), ('polish', POLISH)):
            if time.time() > dl - 30:
                break
            s2, X2, dt = quench(inp, X, fl, timeout=min(240, max(1, dl - time.time())))
            tried += 1; ok += s2 is not None
            print('SFQ n=%d box %.9f bound %.12f %s -> %r %.0fs' % (n, box, s0, name, s2, dt), flush=True)
            if s2 is not None and (cur is None or s2 < cur):
                cur, X, inp = s2, X2, s2
        if cur is not None and cur < bestL - 3e-9:
            k += 1; bestL = cur
            tmp = '%s/.%d-sfq-%d.tmp' % (out, n, k)
            with open(tmp, 'w', newline='') as h:
                w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for i, (x, y, a) in enumerate(X):
                    w.writerow([n, i, repr(float(x)), repr(float(y)), repr(math.radians(float(a)))])
            os.rename(tmp, '%s/%d-sfq-%d.csv' % (out, n, k))
            print('SFQFIND n=%d box %.9f side %.12f (start %.12f, gain of score %.3e)' % (n, box, cur, L0, (L0 - cur) / math.sqrt(n)), flush=True)
    print('SFQEND n=%d tag=%s tried %d quenches, %d answered, best %.12f -> %.12f gain of score %.3e' % (
        n, tag, tried, ok, L0, bestL, (L0 - bestL) / math.sqrt(n)), flush=True)


if __name__ == '__main__':
    main()
