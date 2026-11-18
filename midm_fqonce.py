#!/usr/bin/env python3
"""midm: the fq quench of every certified per-n file of a dir (default flags, then the deep flags, up to three
rounds, the loop of engine_polish.py). A lower side is written to OUTDIR/<n>-fq+<TAG>.csv as raw rows.

Usage: midm_fqonce.py INDIR OUTDIR FQ TAKE.tsv
  INDIR     <n>.csv, the certified files of a first midm_take.py pass
  TAKE.tsv  the take.tsv of that pass; the tag of each n is read from its source column through TAGS.tsv beside it
"""
import csv, glob, hashlib, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402
from midm_scan import to_fq, from_fq, quench, POLISH, remaining_timeout  # noqa: E402


def mark_complete(path, out, n):
    digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    dest = os.path.join(out, str(n) + '.done')
    with open(dest + '.tmp', 'w') as f:
        f.write(digest + '\n')
    os.replace(dest + '.tmp', dest)


def completed(path, out, n):
    dest = os.path.join(out, str(n) + '.done')
    return os.path.exists(dest) and open(dest).read().strip() == hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    ind, out, fq = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True); tmp = out + '/tmp'; os.makedirs(tmp, exist_ok=True)
    open(out + '/PER_FILE', 'a').close()
    deadline=float(open('deadline').read()) if os.path.exists('deadline') else math.inf
    tags = {}
    if os.path.exists(ind + '/TAGS.tsv'):
        tags = dict(l.rstrip('\n').split('\t')[:2] for l in open(ind + '/TAGS.tsv') if l.strip())
    for p in sorted(glob.glob(ind + '/*.csv')):
        n = int(os.path.basename(p)[:-4]); P = mlp.load(p, {n})[n]
        if completed(p, out, n):
            print('n=%d already quenched certified input' % n, flush=True)
            continue
        s, X = to_fq(P); s0 = s
        successful = False
        for rnd in range(3):
            improved = False
            for fl in ((), POLISH):
                budget=remaining_timeout(deadline)
                if budget<=0:
                    break
                s2, X2 = quench(fq, tmp, s, X, fl, timeout=budget)
                successful = successful or s2 is not None
                if s2 is not None and s2 < s - 3e-9:
                    s, X, improved = s2, X2, True
            if not improved:
                break
        if not successful:
            raise RuntimeError('fq returned no completed quench for n=%d' % n)
        print('n=%d fq %.12f -> %.12f gain of score %.3e' % (n, s0, s, (s0 - s) / math.sqrt(n)), flush=True)
        if s < s0 - 3e-9:
            Q = from_fq(X)
            with open('%s/%d-fq+%s.csv' % (out, n, tags.get(str(n), 'x')), 'w', newline='') as h:
                w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for i, (x, y, a) in enumerate(Q):
                    w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(a))])
        mark_complete(p, out, n)


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
