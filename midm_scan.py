#!/usr/bin/env python3
"""midm: a wide fq search on one n from starts that are not the held layout.

Kinds of start (each try is one fq quench, all squares free):
  drop1  the layout of n+1 with one square removed (every square in turn, tilted ones and their neighbours first)
  drop2  the layout of n+2 with two squares removed (a square and one of its neighbours)
  grow1  the layout of n-1 with one square put into its widest hole
  kick   the layout of n with fq's --kick (sigma drawn from KICKS); after a find, the kicks start from the find
  lkick  the same layout with a kick of one neighbourhood only (radius 1.2 to 2.5, sigma 0.03 to 0.12)
  bkick  a large local kick: every square within 3 to 6 of one square moves by sigma 0.15 to 0.5 and takes a new
         angle, so that a whole patch packs again
  melt   the layout of n in a box 4 to 10 per cent larger (--loosen 1.04 to 1.1) with a kick of sigma 0.03 to 0.1:
         every square gets room to move before fq squeezes the box again
  hop    the layout of n with fq's --shrink --hops (its own basin hopping in a shrinking box)
With --stop6 a scan ends after 6 tries when 3 or more of them came back to the start side (within 5e-9) and none
found. With --bank FILE such a scan puts half of its unused seconds into FILE, and a scan that runs to its end takes
up to half of its own length from FILE and spends it on full kicks at sigma 0.04 (logged after a "# BANK04" line).
With --kicks 0.02,0.04 a full kick draws its sigma from that list instead of KICKS (round 20).
With --walk T the kicks walk: a kick result that is not a new best still becomes the next start when its side is
below the walker's side plus T times an exponential draw. After 60 tries with no new best the walker goes back to the best.
Flag sets rotate over the tries (FLAGSETS). A result below the incumbent side is written to OUT/raw/<n>-<tag>.csv
(raw rows; certification is methods_take.py on boxA). Every try is one line of OUT/scan-<n>-<seed>.tsv.

Usage: midm_scan.py --n N --sub HELD.csv [--donors FILE.csv] --out DIR --fq PATH [--seconds 600] [--seed 1]
                    [--modes drop1,drop2,grow1,kick,hop] [--ref SIDE] [--deadline FILE]
  --sub     the file whose layout of n is the incumbent (its side is the bar)
  --donors  the file the layouts of n+1, n+2 and n-1 come from (default: --sub)
  --ref     a second side to count hits against (a control: the side a public file reached)
Needs numpy, scipy and methods_lp.py beside it; fq is Evan Daniel's MIT quench binary, used by path.
"""
import argparse, csv, math, os, subprocess, sys, tempfile, time

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402

KICKS = (0.003, 0.01, 0.02, 0.04)
FLAGSETS = {
    'd': (),                                             # fq default: loosen 1.02, ALM, polish
    't': ('--loosen', '1.005'),                          # a tight start keeps the contact structure
    'k': ('--loosen', '1.005', '--kick', '0.005'),
    'K': ('--loosen', '1.02', '--kick', '0.02'),
}
POLISH = ('--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600')


def to_fq(P):
    """(x, y, radians) -> side and (x, y, degrees in (-45, 45]) in the box at the origin."""
    Q = mlp.normal(P); s = mlp.side(Q)
    d = np.degrees(Q[:, 2]) % 90.0
    d = np.where(d > 45, d - 90, d)
    return s, np.column_stack([Q[:, 0], Q[:, 1], d])


def from_fq(X):
    return np.column_stack([X[:, 0], X[:, 1], np.radians(X[:, 2])])


def remaining_timeout(deadline, cap=180):
    return max(0.0, min(cap, deadline-time.time()-.1))


def quench(fq, tmp, s, X, flags, timeout=180):
    d = tempfile.mkdtemp(prefix='fq', dir=tmp); a, b = d + '/a.txt', d + '/b.txt'
    with open(a, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, g in X:
            h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    out = (None, None)
    try:
        r = subprocess.run([fq, 'quench', '--in', a, '--out', b] + list(flags), capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            L = [l.split() for l in open(b) if l.strip() and not l.startswith('#')]
            n = int(L[0][0]); out = (float(L[0][1]), np.array([[float(v) for v in q[:3]] for q in L[1:n + 1]]))
    except subprocess.TimeoutExpired:
        pass
    for f in (a, b):
        if os.path.exists(f):
            os.remove(f)
    os.rmdir(d)
    return out


def tilted(P):
    d = np.degrees(P[:, 2]) % 90.0
    return np.minimum(d, 90 - d) > 1e-4


def drop_order(P, rng):
    """Every square once: the tilted ones and the squares within 1.6 of a tilted one first, each group shuffled."""
    t = tilted(P); n = len(P)
    near = np.zeros(n, bool)
    if t.any():
        tree = cKDTree(P[t, :2]); dist, _ = tree.query(P[:, :2]); near = (dist < 1.6) & ~t
    g1 = np.flatnonzero(t); g2 = np.flatnonzero(near); g3 = np.flatnonzero(~t & ~near)
    for g in (g1, g2, g3):
        rng.shuffle(g)
    return np.concatenate([g1, g2, g3])


def hole(P, L, rng, tries=4000):
    """A point of the box far from every centre (the widest of `tries` random points and of a coarse grid)."""
    tree = cKDTree(P[:, :2])
    pts = rng.uniform(0.5, L - 0.5, (tries, 2))
    d, _ = tree.query(pts)
    top = np.argsort(-d)[:8]
    return pts[top[int(rng.integers(len(top)))]]


def write_raw(out, n, P, tag):
    os.makedirs(out + '/raw', exist_ok=True)
    tmp = '%s/raw/.%d-%s.tmp' % (out, n, tag)
    with open(tmp, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, a) in enumerate(P):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(float(a))])
    os.rename(tmp, '%s/raw/%d-%s.csv' % (out, n, tag))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, required=True); ap.add_argument('--sub', required=True); ap.add_argument('--donors')
    ap.add_argument('--out', required=True); ap.add_argument('--fq', required=True)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--modes', default='drop1,drop2,grow1,kick,hop'); ap.add_argument('--ref', type=float, default=0.0)
    ap.add_argument('--flagsets', default='d,t,k,K'); ap.add_argument('--deadline')
    ap.add_argument('--max-tries', type=int, default=0); ap.add_argument('--walk', type=float, default=0.0)
    ap.add_argument('--stop6', action='store_true'); ap.add_argument('--bank')
    ap.add_argument('--kicks', help='comma list of the sigmas of a full kick (default %s)' % ','.join(map(str, KICKS)))
    a = ap.parse_args()
    kicks = tuple(float(x) for x in a.kicks.split(',')) if a.kicks else KICKS
    n = a.n; os.makedirs(a.out, exist_ok=True); tmp = a.out + '/tmp'; os.makedirs(tmp, exist_ok=True)
    rng = np.random.default_rng(a.seed * 7919 + n)
    held = mlp.load(a.sub, {n})[n]
    don = mlp.load(a.donors or a.sub, {n - 1, n + 1, n + 2})
    Lheld = mlp.side(held); best = Lheld; ref = a.ref; cur = held      # cur: the best layout so far (kick, lkick, hop start there)
    modes = [m for m in a.modes.split(',') if not ((m == 'drop1' and n + 1 not in don) or (m == 'drop2' and n + 2 not in don) or (m == 'grow1' and n - 1 not in don))]
    fsets = a.flagsets.split(',')
    orders = {}
    if 'drop1' in modes:
        orders['drop1'] = list(drop_order(don[n + 1], rng))
    if 'drop2' in modes:
        orders['drop2'] = list(drop_order(don[n + 2], rng)); tree2 = cKDTree(don[n + 2][:, :2])
    cnt = {m: [0, 0, 0, math.inf] for m in modes}      # tries, below held, at or below ref, lowest side
    lg = open('%s/scan-%d-%d.tsv' % (a.out, n, a.seed), 'a')
    lg.write('# n=%d held=%.12f ref=%.12f modes=%s seed=%d %s\n' % (n, Lheld, ref, ','.join(modes), a.seed, time.strftime('%H:%M:%S', time.gmtime())))
    t0 = time.time(); k = 0; finds = 0
    curL = Lheld; bestP = held; since = 0; moves = 0; back = 0      # the walker of --walk
    dl = float(open(a.deadline).read()) if a.deadline else math.inf
    back6 = 0; stopped = False; extra = 0.0; k1 = None      # --stop6 and --bank (round 19)
    while time.time() < dl and (not a.max_tries or k < a.max_tries):
        if time.time() - t0 >= a.seconds + extra:
            if extra or not a.bank or (a.stop6 and k < 6):
                break
            # the scan stayed open to its end: it takes seconds from the bank and spends them on full kicks at sigma 0.04
            bank = float(open(a.bank).read()) if os.path.exists(a.bank) else 0.0
            extra = min(bank, 0.5 * a.seconds, dl - time.time() - 5)
            if extra < 15:
                extra = 0.0; break
            open(a.bank + '.tmp', 'w').write('%.1f\n' % (bank - extra)); os.rename(a.bank + '.tmp', a.bank); k1 = k
            lg.write('# BANK04 after try %d: %.0f s of full kicks at sigma 0.04 (bank %.0f -> %.0f) best %.12f finds %d\n' % (k, extra, bank, bank - extra, best, finds)); lg.flush()
        if a.stop6 and k == 6 and not extra and back6 >= 3 and best > Lheld - 5e-9:
            stopped = True; saved = max(0.0, min(a.seconds - (time.time() - t0), dl - time.time())); bank = 0.0
            if a.bank:
                bank = float(open(a.bank).read()) if os.path.exists(a.bank) else 0.0
                open(a.bank + '.tmp', 'w').write('%.1f\n' % (bank + saved / 2)); os.rename(a.bank + '.tmp', a.bank)
            lg.write('# STOP6 %d of the first 6 tries came back to the start side: %.0f s saved, half to the bank (%.0f -> %.0f)\n' % (back6, saved, bank, bank + saved / 2)); lg.flush()
            break
        mode = modes[k % len(modes)]; fs = fsets[(k // len(modes)) % len(fsets)]; flags = list(FLAGSETS[fs]); what = ''
        if extra:
            mode = 'kick'
        if mode == 'drop1':
            if not orders['drop1']:
                orders['drop1'] = list(drop_order(don[n + 1], rng))
            i = orders['drop1'].pop(0); P = np.delete(don[n + 1], i, 0); what = str(i)
        elif mode == 'drop2':
            if not orders['drop2']:
                orders['drop2'] = list(drop_order(don[n + 2], rng))
            i = orders['drop2'].pop(0)
            _, nb = tree2.query(don[n + 2][i, :2], 7)
            j = int(nb[1 + int(rng.integers(len(nb) - 1))]); P = np.delete(don[n + 2], [i, j], 0); what = '%d+%d' % (i, j)
        elif mode == 'grow1':
            B = mlp.normal(don[n - 1]); c = hole(B, mlp.side(B), rng)
            P = np.vstack([B, [c[0], c[1], float(rng.uniform(0, math.pi / 2))]]); what = '%.2f,%.2f' % (c[0], c[1])
            if fs in ('t', 'k'):
                flags = ['--loosen', '1.03'] + (['--kick', '0.005'] if fs == 'k' else [])
        elif mode == 'kick':
            sg = kicks[int(rng.integers(len(kicks)))]; P = cur
            if extra:
                sg = 0.04
            what = 'sig%g' % sg
            flags = ['--loosen', '1.005' if fs in ('t', 'k') else '1.02', '--kick', repr(sg)]
        elif mode == 'lkick':
            P = mlp.normal(cur).copy(); t = tilted(P)
            c = int(rng.choice(np.flatnonzero(t))) if (t.any() and rng.random() < 0.7) else int(rng.integers(n))
            rad = float(rng.choice([1.2, 1.8, 2.5])); sg = float(rng.choice([0.03, 0.06, 0.12]))
            sel = np.hypot(P[:, 0] - P[c, 0], P[:, 1] - P[c, 1]) < rad
            P[sel, :2] += rng.normal(0, sg, (int(sel.sum()), 2)); P[sel, 2] += np.radians(rng.normal(0, 20 * sg, int(sel.sum())))
            what = 'c%d,r%g,s%g' % (c, rad, sg); flags = ['--loosen', '1.003' if fs in ('t', 'k') else '1.01']
        elif mode == 'melt':
            lo = float(rng.choice([1.04, 1.07, 1.1])); sg = float(rng.choice([0.03, 0.06, 0.1])); P = cur
            what = 'l%g,s%g' % (lo, sg); flags = ['--loosen', repr(lo), '--kick', repr(sg)]
        elif mode == 'bkick':
            P = mlp.normal(cur).copy(); t = tilted(P)
            c = int(rng.choice(np.flatnonzero(t))) if (t.any() and rng.random() < 0.7) else int(rng.integers(n))
            rad = float(rng.choice([3.0, 4.5, 6.0])); sg = float(rng.choice([0.15, 0.3, 0.5]))
            sel = np.hypot(P[:, 0] - P[c, 0], P[:, 1] - P[c, 1]) < rad; q = int(sel.sum())
            P[sel, :2] += rng.normal(0, sg, (q, 2)); P[sel, 2] = rng.uniform(0, math.pi / 2, q)
            what = 'c%d,r%g,s%g,q%d' % (c, rad, sg, q); flags = ['--loosen', '1.03' if fs in ('t', 'k') else '1.06']
        else:
            P = cur; hk = int(rng.choice([1, 3, 8])); hs = float(rng.choice([0.01, 0.03, 0.08])); what = 'k%d,s%g' % (hk, hs)
            flags = ['--shrink', '--hops', '30', '--hop-k', str(hk), '--hop-sigma', repr(hs), '--loosen', '1.002']
        seed = int(rng.integers(1, 1 << 30)); flags += ['--seed', str(seed)]
        s, X = to_fq(P); tq = time.time()
        budget=remaining_timeout(dl)
        if budget<=0:
            break
        s2, X2 = quench(a.fq, tmp, s, X, flags, timeout=budget)
        k += 1; c = cnt[mode]; c[0] += 1
        if s2 is None or not math.isfinite(s2):
            lg.write('%d\t%s\t%s\t%s\tnan\t%.1f\n' % (k, mode, fs, what, time.time() - tq)); continue
        c[3] = min(c[3], s2)
        if k <= 6 and abs(s2 - Lheld) <= 5e-9:
            back6 += 1
        if s2 < Lheld - 1e-9:
            c[1] += 1
        if ref and s2 <= ref + 1e-7:
            c[2] += 1
        lg.write('%d\t%s\t%s\t%s\t%.12f\t%.1f\n' % (k, mode, fs, what, s2, time.time() - tq)); lg.flush()
        if s2 < best - 1e-9:
            # squeeze the new best once more with the deep flags before it is written
            budget=remaining_timeout(dl)
            s3, X3 = quench(a.fq, tmp, s2, X2, POLISH, timeout=budget) if budget>0 else (None,None)
            if s3 is not None and s3 < s2:
                s2, X2 = s3, X3
            best = s2; finds += 1
            if mode in ('kick', 'lkick', 'bkick', 'melt', 'hop'):
                cur = from_fq(X2); bestP = cur; curL = best; since = 0
            write_raw(a.out, n, from_fq(X2), '%s-%d-%d' % (mode, a.seed, finds))
            lg.write('# FIND try %d mode %s flags %s what %s side %.12f (held %.12f, gain of score %.3e) t %.0f\n' % (
                k, mode, fs, what, best, Lheld, (Lheld - best) / math.sqrt(n), time.time() - t0)); lg.flush()
        elif a.walk and mode in ('kick', 'lkick'):
            since += 1
            if abs(s2 - curL) > 1e-9 and s2 < curL + a.walk * rng.exponential():
                cur = from_fq(X2); curL = s2; moves += 1
            if since >= 60:
                cur = bestP; curL = best; since = 0; back += 1
    if a.walk:
        lg.write('# WALK T %g moves %d back %d\n' % (a.walk, moves, back))
    if a.stop6 or a.bank:
        lg.write('# RULE stop6 %d stopped %d back6 %d bank_tries_from %s bank_seconds %.0f\n' % (a.stop6, stopped, back6, k1 if k1 is not None else '-', extra))
    tot = '  '.join('%s %d/%d/%d min %.9f' % (m, c[0], c[1], c[2], c[3]) for m, c in cnt.items())
    lg.write('# END n=%d tries %d finds %d best %.12f held %.12f seconds %.0f | tries/below held/at ref: %s\n' % (n, k, finds, best, Lheld, time.time() - t0, tot)); lg.close()
    print('n=%d tries %d finds %d best %.12f held %.12f gain %.3e | %s' % (n, k, finds, best, Lheld, (Lheld - best) / math.sqrt(n), tot), flush=True)


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
