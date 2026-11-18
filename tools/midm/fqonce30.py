#!/usr/bin/env python3
"""midm round 30: the certified-file quench with a contact LP.

midm_fqonce.py ran fq (default flags, then the polish flags, up to three rounds) and wrote a lower side only when fq
gained 3e-9 of side. Round 29 measured: our 504 ended 2.75e-11 of score short of the 1e-10 rule, and border measured
1.5e-10 to 5e-10 of score from the contact LP on raw layouts. So each file now gets:
  1. the fq rounds of midm_fqonce.py (written as <n>-fq+x.csv when the true side fell by more than 1e-13);
  2. the contact LP (methods_lp.slp: fixed-angle reclose, then the sequential LP that also turns the squares, iteration
     cap ITERS and a time cap LP_SECONDS) from the lower of the input and step 1, then one polish fq from the LP end;
     the lowest true side of the LP end and that polish is written as <n>-fq+lp.csv when it is below step 1 and the
     input by more than 1e-13.
The driver certifies every output with finesafe and keeps the lowest certified score.

Usage: fqonce30.py INDIR OUTDIR FQ TAG   (INDIR holds <n>.csv certified files; deadline file in the cwd)
"""
import csv, glob, hashlib, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402
from midm_scan import to_fq, from_fq, quench, POLISH, remaining_timeout  # noqa: E402

ITERS = int(os.environ.get('LP_ITERS', '30'))
LP_SECONDS = float(os.environ.get('LP_SECONDS', '240'))


def mark_complete(path, out, n):
    digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    dest = os.path.join(out, str(n) + '.done')
    with open(dest + '.tmp', 'w') as f:
        f.write(digest + '\n')
    os.replace(dest + '.tmp', dest)


def completed(path, out, n):
    dest = os.path.join(out, str(n) + '.done')
    return os.path.exists(dest) and open(dest).read().strip() == hashlib.sha256(open(path, 'rb').read()).hexdigest()


def write(path, n, Q):
    with open(path + '.tmp', 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, a) in enumerate(Q):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(a))])
    os.replace(path + '.tmp', path)


GAP_OK = -1e-10   # round 30 control: HiGHS meets the 4e-11 pair rows only to its 1e-10 tolerance (747: min gap
                  # -1.3e-11 and -3.0e-11 after one fixed-angle LP); finesafe certifies the end and keeps the lowest


def reclose(P, L, t_end):
    for _ in range(6):
        if time.time() > t_end:
            break
        Q = mlp.solve(P, 0.02, 0.0)
        if Q is None or mlp.min_gap(Q) < GAP_OK:
            break
        LQ = mlp.side(Q)
        if LQ >= L - 1e-13:
            break
        P, L = Q, LQ
    return P, L


def lp(P, t_end):
    """methods_lp.slp with a time cap and the relaxed gap check: reclose, then SLP steps while time is left."""
    P, L = reclose(P, mlp.side(P), t_end)
    tr_a = 2e-3; stall = 0
    for k in range(ITERS):
        if time.time() > t_end:
            break
        Q = mlp.solve(P, 0.02, tr_a)
        if Q is not None:
            Q, LQ = reclose(Q, mlp.side(Q), t_end)
        ok = Q is not None and mlp.min_gap(Q) >= GAP_OK and LQ < L - 1e-13
        if ok:
            stall = stall + 1 if L - LQ < 1e-10 else 0
            P, L = Q, LQ
            tr_a = min(tr_a * 1.5, 5e-3)
            if stall >= 3:
                break
        else:
            tr_a /= 4
            if tr_a < 2e-8:
                break
    return P, L


def main():
    ind, out, fq = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True); tmp = out + '/tmp'; os.makedirs(tmp, exist_ok=True)
    open(out + '/PER_FILE', 'a').close()
    deadline = float(open('deadline').read()) if os.path.exists('deadline') else math.inf
    for p in sorted(glob.glob(ind + '/*.csv')):
        n = int(os.path.basename(p)[:-4]); P0 = mlp.load(p, {n})[n]
        if completed(p, out, n):
            print('n=%d already quenched certified input' % n, flush=True)
            continue
        t0 = time.time()
        L0 = mlp.side(P0)
        s, X = to_fq(P0); s0 = s
        successful = False
        for rnd in range(3):
            improved = False
            for fl in ((), POLISH):
                budget = remaining_timeout(deadline)
                if budget <= 0:
                    break
                s2, X2 = quench(fq, tmp, s, X, fl, timeout=budget)
                successful = successful or s2 is not None
                if s2 is not None and s2 < s - 3e-9:
                    s, X, improved = s2, X2, True
            if not improved:
                break
        if not successful:
            raise RuntimeError('fq returned no completed quench for n=%d' % n)
        Pf = from_fq(X); Lf = mlp.side(Pf)
        if Lf < L0 - 1e-13 and s < s0:
            write('%s/%d-fq+x.csv' % (out, n), n, Pf)
        best_L = min(L0, Lf)
        # contact LP from the input and from the fq end (round 30 control, inflated 747: the LP from the input reached
        # 9e-9 of score below the fq end, and the LP from the fq end gained nothing), then one polish fq from the lower
        cand = []
        for P_, tag in ((P0, 'lp-in'), (Pf, 'lp-fq')):
            t_end = min(time.time() + LP_SECONDS / 2, deadline - 30)
            try:
                Pl, Ll = lp(P_.copy(), t_end)
                cand.append((Ll, Pl, tag))
            except Exception as ex:  # noqa: BLE001
                print('n=%d LP %s error %r' % (n, tag, ex), flush=True)
        if not cand:
            cand = [(best_L, Pf if Lf < L0 else P0, 'none')]
        Ll, Pl, tag = min(cand, key=lambda c: c[0])
        budget = remaining_timeout(deadline)
        if budget > 0 and Ll < best_L - 1e-13:
            sl, Xl = to_fq(Pl)
            s3, X3 = quench(fq, tmp, sl, Xl, POLISH, timeout=budget)
            if s3 is not None:
                P3 = from_fq(X3); cand.append((mlp.side(P3), P3, tag + '+polish'))
        Lc, Pc, how = min(cand, key=lambda c: c[0])
        if Lc < best_L - 1e-13:
            write('%s/%d-fq+lp.csv' % (out, n), n, mlp.normal(Pc))
        print('n=%d input %.13f fq %.13f lp %.13f (%s) gain of score fq %.3e lp %.3e %.0fs' % (
            n, L0, Lf, Lc, how, (L0 - Lf) / math.sqrt(n), (min(L0, Lf) - Lc) / math.sqrt(n), time.time() - t0), flush=True)
        mark_complete(p, out, n)


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
