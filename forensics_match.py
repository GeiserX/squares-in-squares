#!/usr/bin/env python3
"""Match a side fraction f to rigid designs with small whole coefficients.

A design is a set of contact chains that fixes the tilt t of the tilted squares and f
(side = m + f). With C = cos t, S = sin t, T = tan t, a chain is one of:

  L  a*C + b*S = c + d*f              corners of tilted squares on grid lines (x or y extent)
  B  (i + d*f)*C + (j + e*f)*S = a    grid corners on the sides of a tilted block
  P  p/C + q*T + a*C + b*S = c + d*f  p rows of an arm advance along the wall (pitch 1/C, slide T).
                                      Two arms that close along a wall are this chain too: the other
                                      arm adds its slot width c2 + f, so d changes by one.
  S  (c+1)*C + S = c + f              the slot of an arm of rows of c+1 squares (an L chain)

Families:
  rat   f = p/q
  tanL  one L chain at its extreme angle:  hypot(a, b) = c + d*f      (the rigid 45 degree block is a = b, d = 2)
  tanB  one B chain at its extreme angle:  hypot(i + d*f, j + e*f) = a
  two   two independent chains at one angle (L, B or S first, then L, B or P)

Usage:
  forensics_match.py values BOARD.json OUT.tsv            repeated board values, controls and decoys
  forensics_match.py scan VALUES.tsv OUT.jsonl [I N]       scan the rows with index % N == I
  forensics_match.py report VALUES.tsv OUT.jsonl [...]     matches per value, with the decoy rate
"""
import sys, math, json, random
import numpy as np

TOL = 1e-9          # a design is kept when its f is within TOL of the value
TOP = 4             # two-chain designs printed per value, lowest height first
RAW = 5e-9          # collection tolerance on the residual of the second chain
HL, HB, HP = 24, 16, 40
SLOT_MAX = 40
D_L = (-1, 0, 1, 2)


def res(v):
    return np.abs(v - np.rint(v))


# ---------------------------------------------------------------- single-chain families
def fam_rat(f, out):
    for q in range(2, 61):
        p = round(f * q)
        if math.gcd(p, q) == 1 and abs(f - p / q) < TOL:
            out.append(dict(fam='rat', h=q, form='f = %d/%d' % (p, q), resid=abs(f - p / q), t=None))


def fam_tan(f, out):
    for a in range(1, 61):
        for b in range(a, 61):
            if math.gcd(a, b) != 1 and a != b:
                continue
            R = math.hypot(a, b)
            for d in (1, 2):
                v = R - d * f
                r = abs(v - round(v))
                if r < TOL and round(v) >= 0:
                    out.append(dict(fam='tanL', h=b, form='hypot(%d,%d) = %d + %d f' % (a, b, round(v), d),
                                    resid=r / d, t=math.degrees(math.atan2(b, a))))
    for i in range(0, 61):
        for j in range(i, 61):
            for d, e in ((1, 1), (1, 0), (0, 1)):
                R = math.hypot(i + d * f, j + e * f)
                r = abs(R - round(R))
                if r < TOL and round(R) > 0:
                    out.append(dict(fam='tanB', h=j, form='hypot(%d%+d f, %d%+d f) = %d' % (i, d, j, e, round(R)),
                                    resid=r, t=math.degrees(math.atan2(j + e * f, i + d * f))))


# ---------------------------------------------------------------- stage A: angles from one chain with f in it
def stage_a(f):
    """Yield (t, kind, coefs, h): every angle in (0, pi/2) that one chain gives at this f."""
    ts, meta = [], []
    for c in range(1, SLOT_MAX + 1):                       # S: (c+1) C + S = c + f
        R = math.hypot(c + 1, 1); z = (c + f) / R
        if abs(z) <= 1:
            t = math.atan2(1, c + 1) + math.acos(z)
            if 1e-6 < t < math.pi / 2 - 1e-6:
                ts.append(t); meta.append(('S', (c,), 1))
    lim = math.pi / 4 + 1e-9
    for a in range(0, HL + 1):                             # L: a C + b S = c + d f
        for b in range(-HL, HL + 1):
            if a == 0 and b <= 0:
                continue
            R = math.hypot(a, b); ph = math.atan2(b, a)
            for d in (-1, 1, 2):
                if math.gcd(math.gcd(a, abs(b)), abs(d)) != 1:
                    continue
                for c in range(math.ceil(-R - d * f), math.floor(R - d * f) + 1):
                    z = (c + d * f) / R
                    w = math.acos(max(-1.0, min(1.0, z)))
                    for t in (ph + w, ph - w):
                        if 1e-6 < t <= lim:
                            ts.append(t); meta.append(('L', (a, b, c, d), max(a, abs(b))))
    for i in range(-HB, HB + 1):                           # B: (i + d f) C + (j + e f) S = a
        for j in range(-HB, HB + 1):
            for d in (-1, 0, 1):
                for e in (-1, 0, 1):
                    if d == 0 and e == 0:
                        continue
                    X = i + d * f; Y = j + e * f
                    R = math.hypot(X, Y); ph = math.atan2(Y, X)
                    for a in range(0, int(R) + 1):
                        w = math.acos(max(-1.0, min(1.0, a / R)))
                        for t in (ph + w, ph - w):
                            if 1e-6 < t <= lim:
                                ts.append(t); meta.append(('B', (i, j, d, e, a), max(abs(i), abs(j), a)))
    return np.array(ts), meta


# ---------------------------------------------------------------- stage B: a second chain at that angle
_LA = np.arange(0, HL + 1)[:, None]
_LB = np.arange(-HL, HL + 1)[None, :]
_BI = np.arange(-HB, HB + 1)
_PP = np.arange(0, HP + 1)[:, None]
_PQ = np.arange(-HP, HP + 1)[None, :]
_PAB = [(a, b) for a in range(-2, 3) for b in range(-2, 3)]            # after an L chain
_PAB_S = [(a, b) for a in range(-1, 3) for b in range(-HP, HP + 1)]     # after a slot: b up to the row length


def grad(kind, co, t, f):
    """(dg/dt, dg/df) of one chain written as g(t, f) = 0."""
    C, S = math.cos(t), math.sin(t)
    if kind == 'S':
        return -(co[0] + 1) * S + C, -1.0
    if kind == 'L':
        a, b, _, d = co
        return -a * S + b * C, -float(d)
    if kind == 'B':
        i, j, d, e = co[:4]
        return -(i + d * f) * S + (j + e * f) * C, d * C + e * S
    p, q, a, b, _, d = co
    return p * S / C ** 2 + q / C ** 2 - a * S + b * C, -float(d)


def f_error(ka, coa, kb, cob, t, f, r2):
    """The first chain holds exactly at (t, f). The second misses by r2. Return how far f is from the
    f of the design that satisfies both, to first order: r2 * |dA/dt| / |det|. A chain that holds for
    every f at this angle, a multiple of the first chain and a chain at a double root all give a
    singular pair, and None."""
    at, af = grad(ka, coa, t, f)
    bt, bf = grad(kb, cob, t, f)
    det = at * bf - af * bt
    if abs(det) < 1e-9 * (1 + abs(at) + abs(bt)):
        return None
    return abs(r2 * at / det)


def stage_b(f, ts, meta, out, tol=RAW):
    C = np.cos(ts); S = np.sin(ts)
    n = len(ts)
    # L checks, all angles: a C + b S - d f
    step = 4000
    for s in range(0, n, step):
        c_ = C[s:s + step, None, None]; s_ = S[s:s + step, None, None]
        base = _LA[None] * c_ + _LB[None] * s_
        for d in D_L:
            r = res(base - d * f)
            for it, ia, ib in zip(*np.nonzero(r < tol)):
                a = int(_LA[ia, 0]); b = int(_LB[0, ib])
                if a == 0 and b <= 0:
                    continue
                k, co, h = meta[s + it]
                cc = int(round(a * C[s + it] + b * S[s + it] - d * f))
                fe = f_error(k, co, 'L', (a, b, cc, d), ts[s + it], f, float(r[it, ia, ib]))
                if fe is None or fe > TOL:
                    continue
                out.append(dict(fam='two', kind=k + 'L', A=co, B=(a, b, cc, d), h=max(h, a, abs(b)),
                                resid=fe, t=math.degrees(ts[s + it])))
    # B checks, all angles: (i + d f) C + (j + e f) S
    xs = [(i, d) for i in _BI for d in (-1, 0, 1)]
    X = np.array([i + d * f for i, d in xs]); Y = X.copy()
    step = 3000
    for s in range(0, n, step):
        val = (C[s:s + step, None] * X[None, :])[:, :, None] + (S[s:s + step, None] * Y[None, :])[:, None, :]
        r = res(val)
        for it, ix, iy in zip(*np.nonzero(r < tol)):
            i, d = xs[ix]; j, e = xs[iy]
            if d == 0 and e == 0:
                continue                                   # that is an L check with d = 0
            if (i, d, j, e) < (-i, -d, -j, -e):
                continue                                   # one sign of each chain
            k, co, h = meta[s + it]
            a = int(round(val[it, ix, iy]))
            fe = f_error(k, co, 'B', (int(i), int(j), int(d), int(e), a), ts[s + it], f, float(r[it, ix, iy]))
            if fe is None or fe > TOL:
                continue
            out.append(dict(fam='two', kind=k + 'B', A=co, B=(int(i), int(j), int(d), int(e), a),
                            h=max(h, abs(int(i)), abs(int(j))), resid=fe, t=math.degrees(ts[s + it])))
    # P checks, only for slots and for L chains of height <= 3
    sel = [x for x in range(n) if meta[x][0] == 'S' or (meta[x][0] == 'L' and meta[x][2] <= 3)]
    for x in sel:
        c_, s_ = C[x], S[x]
        base = _PP / c_ + _PQ * (s_ / c_)
        for a, b in (_PAB_S if meta[x][0] == 'S' else _PAB):
            for d in D_L:
                r = res(base + a * c_ + b * s_ - d * f)
                for ip, iq in zip(*np.nonzero(r < tol)):
                    p = int(_PP[ip, 0]); q = int(_PQ[0, iq])
                    if p == 0 and q == 0:
                        continue
                    if p == 0 and q < 0:
                        continue
                    k, co, h = meta[x]
                    cc = int(round(p / c_ + q * s_ / c_ + a * c_ + b * s_ - d * f))
                    fe = f_error(k, co, 'P', (p, q, a, b, cc, d), ts[x], f, float(r[ip, iq]))
                    if fe is None or fe > TOL:
                        continue
                    out.append(dict(fam='two', kind=k + 'P', A=co, B=(p, q, a, b, cc, d), h=max(h, p, abs(q), abs(b)),
                                    resid=fe, t=math.degrees(ts[x])))


def match(f):
    out = []
    fam_rat(f, out)
    fam_tan(f, out)
    ts, meta = stage_a(f)
    stage_b(f, ts, meta, out)
    return out, len(ts)


# ---------------------------------------------------------------- the values to explain
CONTROLS = [('ctl45-a5', 0.535533905932738), ('ctl45-a15', 0.606601717798213), ('ctl45-a8', 0.656854249492381),
            ('ctl45-a13', 0.692388155425118), ('ctl45-a6', 0.742640687119285), ('ctl45-strip', 0.707106781186548),
            ('ctl-n18', 0.822875655532295), ('ctl-n54', 0.846667192843490)]


def cmd_values(board, out):
    d = json.load(open(board))
    rows = []
    for x in d:
        L = float(x['L']); m = int(L + 1e-9); f = L - m
        if f > 1e-6:
            rows.append((f, x['n'], m, x['n'] - m * m, x['team']))
    rows.sort()
    groups, cur = [], [rows[0]]
    for r in rows[1:]:
        if r[0] - cur[-1][0] < 1e-9:
            cur.append(r)
        else:
            groups.append(cur); cur = [r]
    groups.append(cur)
    rnd = random.Random(17)
    with open(out, 'w') as h:
        h.write('label\tf\tprec\tkind\tmembers\n')
        vals = []
        for g in groups:
            if len(g) < 2:
                continue
            fs = [r[0] for r in g]
            spread = max(fs) - min(fs)
            prec = max(3e-13, 3 * spread) if spread < 1e-12 else max(2e-10, 3 * spread)
            f = min(fs)
            lab = 'b%.4f' % f
            vals.append((lab, f, prec))
            h.write('%s\t%.15f\t%.1e\tboard\t%s\n' % (lab, f, prec, ' '.join('%d(%d,%d)' % (r[1], r[2], r[3]) for r in g)))
        for lab, f in CONTROLS:
            h.write('%s\t%.15f\t%.1e\tcontrol\t-\n' % (lab, f, 3e-13))
            h.write('%s-shift\t%.15f\t%.1e\tnegative\t-\n' % (lab, f + 3e-7, 3e-13))
        for i in range(40):
            lab, f, prec = vals[i % len(vals)]
            h.write('decoy%02d\t%.15f\t%.1e\tdecoy\t%s\n' % (i, f + rnd.choice((-1, 1)) * rnd.uniform(1e-6, 9e-6), prec, lab))


def read_values(path):
    rows = []
    for ln in open(path).read().splitlines()[1:]:
        lab, f, prec, kind, mem = ln.split('\t')
        rows.append((lab, float(f), float(prec), kind, mem))
    return rows


def cmd_scan(values, out, i=0, n=1):
    rows = read_values(values)
    with open(out, 'a') as h:
        for idx, (lab, f, prec, kind, mem) in enumerate(rows):
            if idx % n != i:
                continue
            hits, nt = match(f)
            for x in hits:
                x['label'] = lab
                h.write(json.dumps(x) + '\n')
            h.write(json.dumps(dict(label=lab, done=True, angles=nt, hits=len(hits))) + '\n')
            h.flush()
            print(lab, f, 'angles', nt, 'hits', len(hits), flush=True)


def show(x):
    if x['fam'] != 'two':
        return '%s h=%d %s' % (x['fam'], x['h'], x['form'])
    A, B = x['A'], x['B']
    k = x['kind']
    sa = {'S': lambda: 'slot c=%d' % A[0],
          'L': lambda: '%d C %+d S = %d %+d f' % tuple(A),
          'B': lambda: '(%d%+d f) C + (%d%+d f) S = %d' % (A[0], A[2], A[1], A[3], A[4])}[k[0]]()
    sb = {'L': lambda: '%d C %+d S = %d %+d f' % tuple(B),
          'B': lambda: '(%d%+d f) C + (%d%+d f) S = %d' % (B[0], B[2], B[1], B[3], B[4]),
          'P': lambda: '%d/C %+d T %+d C %+d S = %d %+d f' % tuple(B)}[k[1]]()
    return 'two/%s h=%d t=%.6f  [%s] and [%s]' % (k, x['h'], x['t'], sa, sb)


def cmd_report(values, outs):
    rows = read_values(values)
    hits = {}
    done = set()
    for p in outs:
        for ln in open(p):
            x = json.loads(ln)
            if x.get('done'):
                done.add(x['label']); continue
            hits.setdefault(x['label'], []).append(x)
    decoys = [r for r in rows if r[3] == 'decoy' and r[0] in done]
    nd = max(1, len(decoys))

    def rate(fam, kind, h, prec):
        """Mean number of decoy matches of this family at height <= h and residual <= prec."""
        c = 0
        for lab, _, _, _, _ in decoys:
            for x in hits.get(lab, []):
                if x['fam'] == fam and x.get('kind') == kind and x['h'] <= h and x['resid'] <= prec:
                    c += 1
        return c / nd

    print('decoys scanned', len(decoys))
    for lab, f, prec, kind, mem in rows:
        if kind == 'decoy':
            continue
        hs = [x for x in hits.get(lab, []) if x['resid'] <= prec]
        hs.sort(key=lambda x: (x['h'], x['resid']))
        print('\n%s f=%.12f prec=%.0e %s %s %s' % (lab, f, prec, kind, mem, '' if lab in done else '(not scanned)'))
        seen = set()
        two = 0
        for x in hs:
            key = (x['fam'], None if x['t'] is None else round(x['t'], 6))
            if key in seen or (x['fam'] == 'two' and two >= TOP):
                continue
            seen.add(key)
            two += x['fam'] == 'two'
            r = rate(x['fam'], x.get('kind'), x['h'], prec)
            print('   %s  f off by %.1e  decoy rate %.3f %s' % (show(x), x['resid'], r, 'MATCH' if r < 0.05 else ''))
        if not seen:
            print('   no design within the precision')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'values':
        cmd_values(sys.argv[2], sys.argv[3])
    elif cmd == 'scan':
        cmd_scan(sys.argv[2], sys.argv[3], *(int(v) for v in sys.argv[4:6]))
    elif cmd == 'report':
        cmd_report(sys.argv[2], sys.argv[3:])
