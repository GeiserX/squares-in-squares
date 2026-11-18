#!/usr/bin/env python3
"""A block chain plus a row chain: the pair forensics_match.py does not try.

forensics_match.py tries a row chain  p/C + q T + a C + b S = c + d f  (p rows of an arm advance along
the wall, pitch 1/C, slide T) only on top of a slot or a short L chain. The arms we hold sit on a block
chain instead, (i + f) C + (j + f) S = w: rows of w squares between two staircases. This tool takes the
chain that forensics_curve.py read from a held layout, puts the board's side on it (that gives the
angle), and looks for a row chain there, along either wall (1/C with tan, or 1/S with cot).

  ctl    positive: a point planted on a block chain and a row chain must give the row chain back from
         the digits of f alone. Negative: the same f moved by a few 1e-6 must give nothing.
  scan   every row of the curve file, at the board's f and at the held f. A hit is kept when the two
         chains together give an f within the tolerance. A row chain without f is a relation of the
         angle alone: at an angle with a square root form such relations always exist.

Usage:
  forensics_rowlock.py ctl
  forensics_rowlock.py scan CURVE.tsv BOARD.json HELD_DETAILS.csv OUT.tsv [--tol 3e-10] [--held-tol 3e-9]
  forensics_rowlock.py values VALUES.tsv OUT.tsv [--imax 14] [--hmax 14] [--only LABEL,KIND,...]   every block chain
"""
import sys, re, math, csv, random, argparse
import numpy as np

P_MAX, Q_MAX, A_MAX = 6, 6, 14
D_SET = (-2, -1, 0, 1, 2)


def parse(text):
    """A chain as (i, d, j, e, a, g):  (i + d f) C + (j + e f) S = a + g f."""
    v = [int(x) for x in re.findall(r'-?\d+', text.replace('+', ' ').replace('- ', '-'))]
    if text.strip().startswith('('):
        i, d, j, e, a = v[:5]
        return (i, d, j, e, a, 0)
    a, b, c, d = v[:4]
    return (a, 0, b, 0, c, d)


def res1(ch, t, f):
    i, d, j, e, a, g = ch
    return (i + d * f) * math.cos(t) + (j + e * f) * math.sin(t) - a - g * f


def angle_on(ch, f, deg0):
    t = math.radians(deg0)
    for _ in range(60):
        h = 1e-7
        r = res1(ch, t, f)
        dr = (res1(ch, t + h, f) - res1(ch, t - h, f)) / (2 * h)
        if abs(dr) < 1e-12:
            return None
        t2 = t - r / dr
        if abs(t2 - t) < 1e-15:
            t = t2; break
        t = t2
    return t if abs(res1(ch, t, f)) < 1e-12 and 0.5 < math.degrees(t) < 89.5 else None


def res2(row, t, f):
    kind, p, q, a, b, c, d = row
    C, S = math.cos(t), math.sin(t)
    u, v = (1 / C, S / C) if kind == 'C' else (1 / S, C / S)
    return p * u + q * v + a * C + b * S - c - d * f


def joint(ch, row, t, f):
    """The f where both chains hold, by Newton from (t, f). None when the pair fixes nothing."""
    for _ in range(40):
        h = 1e-7
        r = np.array([res1(ch, t, f), res2(row, t, f)])
        J = np.array([[(res1(ch, t + h, f) - res1(ch, t - h, f)) / (2 * h), (res1(ch, t, f + h) - res1(ch, t, f - h)) / (2 * h)],
                      [(res2(row, t + h, f) - res2(row, t - h, f)) / (2 * h), (res2(row, t, f + h) - res2(row, t, f - h)) / (2 * h)]])
        if abs(np.linalg.det(J)) < 1e-3:                 # the pair does not fix f: one chain is the other in disguise
            return None
        dt, df = np.linalg.solve(J, -r)
        t += dt; f += df
        if abs(dt) + abs(df) < 1e-15:
            break
    return (t, f) if abs(res1(ch, t, f)) + abs(res2(row, t, f)) < 1e-11 else None


def rows_at(ch, f, deg0, tol):
    t = angle_on(ch, f, deg0)
    if t is None:
        return None, []
    C, S = math.cos(t), math.sin(t)
    a = np.arange(-A_MAX, A_MAX + 1)
    AA, BB = np.meshgrid(a, a, indexing='ij')
    base = AA * C + BB * S
    out = []
    for kind, u, v in (('C', 1 / C, S / C), ('S', 1 / S, C / S)):
        for p in range(1, P_MAX + 1):
            for q in range(-Q_MAX, Q_MAX + 1):
                for d in D_SET:
                    x = p * u + q * v + base - d * f
                    r = np.abs(x - np.rint(x))
                    for ia, ib in zip(*np.nonzero(r < 30 * tol)):
                        row = (kind, p, q, int(a[ia]), int(a[ib]), int(round(float(x[ia, ib]))), d)
                        sol = joint(ch, row, t, f)
                        if sol is None or abs(sol[1] - f) > tol:
                            continue
                        out.append((max(p, abs(q), abs(row[3]), abs(row[4])), row, sol[1] - f))
    out.sort(key=lambda h: (h[0], abs(h[2])))
    return t, out


def show(row):
    kind, p, q, a, b, c, d = row
    u, v = ('1/C', 'T') if kind == 'C' else ('1/S', '1/T')
    return '%d %s %+d %s %+d C %+d S = %d %+d f' % (p, u, q, v, a, b, c, d)


FORMS = P_MAX * (2 * Q_MAX + 1) * (2 * A_MAX + 1) ** 2 * len(D_SET) * 2


def cmd_ctl():
    ok = True
    ch = (4, 1, 3, 1, 6, 0)
    planted = ('C', 2, 1, 3, 0, 5, 1)
    sol = joint(ch, planted, math.radians(42.0), 0.72)
    t0, f0 = sol
    print('positive: planted %s on (4 + f) C + (3 + f) S = 6 at t %.6f, f %.12f' % (show(planted), math.degrees(t0), f0))
    t, hits = rows_at(ch, round(f0, 12), math.degrees(t0), 3e-10)
    got = [h for h in hits if h[1] == planted]
    print('   returned %d forms, the planted one %s' % (len(hits), 'is there' if got else 'IS MISSING')); ok &= bool(got)
    rng = random.Random(7); bad = 0
    for _ in range(12):
        g = f0 + rng.choice((-1, 1)) * rng.uniform(1e-6, 9e-6)
        bad += len(rows_at(ch, g, math.degrees(t0), 3e-10)[1])
    print('negative: 12 shifted copies return %d forms (must be 0)' % bad); ok &= bad == 0
    print('forms per value %d, expected by chance at 3e-10: %.4f' % (FORMS, FORMS * 6e-10))
    print('CONTROL', 'GREEN' if ok else 'RED')
    return 0 if ok else 1


def cmd_scan(curve, board, details, out, tol, held_tol):
    """The curve file rounds f to 1e-9, so the sides come from the board file and the gate's details file."""
    import json
    B = {int(r['n']): float(r['L']) for r in json.load(open(board))}
    D = {int(r[0]): float(r[1]) for r in csv.reader(open(details)) if r[0].isdigit()}
    rows = list(csv.DictReader(open(curve), delimiter='\t'))
    done = 0; lines = []; hit = {'board': set(), 'held': set()}
    for r in rows:
        if not r['chain']:
            continue
        ch = parse(r['chain']); n = int(r['n']); m = int(r['m'])
        done += 1
        for where, f, deg0, tl in (('board', B[n] - m, float(r['board_deg']), tol), ('held', D[n] - m, float(r['held_deg']), held_tol)):
            t, hits = rows_at(ch, f, deg0, tl)
            for h, row, off in hits[:3]:
                hit[where].add(n)
                lines.append([where, r['n'], r['m'], r['k'], '%.12f' % f, r['chain'], '%.6f' % math.degrees(t), show(row),
                              'yes' if row[6] else 'no', str(h), '%.1e' % off])
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['point', 'n', 'm', 'k', 'f', 'held_chain', 'deg', 'row_chain', 'has_f', 'height', 'f_off'])
        w.writerows(lines)
    print('%d chains read. Row chain at the board side: %d n (by chance %.2f in all). At the held side: %d n (by chance %.2f in all).' % (
        done, len(hit['board']), done * FORMS * 2 * tol, len(hit['held']), done * FORMS * 2 * held_tol))
    for l in lines:
        print('   %-5s n %s (%s,%s) f %s on %s at %s: %s  h=%s off %s' % (l[0], l[1], l[2], l[3], l[4], l[5], l[6], l[7], l[9], l[10]))


def block_angles(f, imax):
    """Every block chain (i + f) C + (j + f) S = w with a root at 45 degrees or less."""
    for i in range(0, imax + 1):
        for j in range(0, imax + 1):
            R = math.hypot(i + f, j + f); t_top = math.atan2(j + f, i + f)
            for w in range(max(1, int(math.floor(i + f)) - 1), int(math.floor(R)) + 1):
                if w > R or w < 1:
                    continue
                for sg in (-1, 1):
                    t = t_top + sg * math.acos(w / R)
                    if math.radians(1.0) < t <= math.radians(45.0) + 1e-9:
                        yield (i, 1, j, 1, w, 0), t


def cmd_values(values, out, imax, only, hmax):
    """Block chain plus row chain for a list of values (the file forensics_match.py values writes)."""
    rows = [r for r in csv.DictReader(open(values), delimiter='\t') if not only or r['label'] in only or r['kind'] in only]
    lines = []; tally = {}
    for r in rows:
        f = float(r['f']); tol = max(float(r['prec']), 3e-12); best = []      # an exact team still keeps a margin near 1e-12
        seen = set()
        for ch, t0 in block_angles(f, imax):
            t, hits = rows_at(ch, f, math.degrees(t0), tol)
            for h, row, off in hits:
                if row[6] == 0 or h > hmax:              # a row chain without f says nothing about f
                    continue
                key = (round(math.degrees(t), 5), row)
                if key in seen:
                    continue
                seen.add(key); best.append((h + max(ch[0], ch[2], ch[4]) / 100.0, ch, t, row, off))
        best.sort(key=lambda b: b[0])
        t_ = tally.setdefault(r['kind'], [0, 0]); t_[0] += 1; t_[1] += bool(best)
        for score, ch, t, row, off in best[:3]:
            lines.append([r['label'], r['kind'], '%.12f' % f, '(%d + f) C + (%d + f) S = %d' % (ch[0], ch[2], ch[4]), '%.6f' % math.degrees(t), show(row), str(int(score)), '%.1e' % off, r['members'][:70]])
            print('   %-16s %s  %s at %s with %s  h=%s off %s  %s' % tuple(lines[-1][i] for i in (0, 2, 3, 4, 5, 6, 7, 8)), flush=True)
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['label', 'kind', 'f', 'block_chain', 'deg', 'row_chain', 'height', 'f_off', 'members'])
        w.writerows(lines)
    for kind, (n, k) in sorted(tally.items()):
        print('%-10s %3d values, %3d with a block chain and a row chain of height %d or less' % (kind, n, k, hmax))


if __name__ == '__main__':
    if sys.argv[1] == 'ctl':
        sys.exit(cmd_ctl())
    if sys.argv[1] == 'values':
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd'); ap.add_argument('values'); ap.add_argument('out'); ap.add_argument('--imax', type=int, default=14)
        ap.add_argument('--only', default=''); ap.add_argument('--hmax', type=int, default=14)
        a = ap.parse_args()
        cmd_values(a.values, a.out, a.imax, set(a.only.split(',')) if a.only else set(), a.hmax)
        sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('curve'); ap.add_argument('board'); ap.add_argument('details'); ap.add_argument('out')
    ap.add_argument('--tol', type=float, default=3e-10); ap.add_argument('--held-tol', type=float, default=3e-9)
    a = ap.parse_args()
    cmd_scan(a.curve, a.board, a.details, a.out, a.tol, a.held_tol)
