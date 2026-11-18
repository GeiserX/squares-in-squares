#!/usr/bin/env python3
"""Design census of the two-arm layouts of a file, and the slide of each design along k at its own m.

A stack is a row of c tilted squares in a strip of width c - 1 + f; its tilt t solves c cos t + sin t = c - 1 + f
and an arm of such stacks gains g = f - sin t squares per unit of wall. The census reads the two arm sizes of a
layout from its two most common tilts and computes the end loss
    E = (m - c2 + 1) g(c1, f) + (m - c1 + 1) g(c2, f) - k.
slide: for every n of the same m, the f at which a held design would hold that n with its own E.

Usage: invent_census.py SUB.csv GAP.tsv OUT.tsv [m_lo m_hi]
  SUB.csv  a submission file (id,n,square_id,x,y,angle) or raw rows (n,square_id,x,y,angle)
  GAP.tsv  n, m, k, ours_L, board_L, ... (main-r17/gap-by-n.tsv)
"""
import collections, csv, math, sys


def tilt(c, f):
    """the root of c cos t + sin t = c - 1 + f beyond the maximum of the left side"""
    lo, hi = math.atan(1.0 / c), math.pi / 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if c * math.cos(mid) + math.sin(mid) > c - 1 + f: lo = mid
        else: hi = mid
    return lo


def g(c, f):
    return f - math.sin(tilt(c, f))


def flush(m, c1, c2, f):
    return (m - c2 + 1) * g(c1, f) + (m - c1 + 1) * g(c2, f)


def f_for(m, c1, c2, E, k):
    """the f in (0.3, 1) at which the design holds k squares over the grid with end loss E"""
    lo, hi = 0.30, 0.9999
    if flush(m, c1, c2, hi) - E < k or flush(m, c1, c2, lo) - E > k: return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if flush(m, c1, c2, mid) - E < k: lo = mid
        else: hi = mid
    return hi


def read_design(sq, f):
    """(c1, c2, t1, t2, share) from the two most common tilts, or None when the layout is not two arms of flush stacks"""
    ang = []
    for x, y, a in sq:
        d = math.degrees(a) % 90.0
        if d > 45: d -= 90
        if abs(d) > 1.0: ang.append(d)
    if len(ang) < 40: return None
    cnt = collections.Counter(round(d, 2) for d in ang)
    # the two most common tilts that differ by more than 0.3 degrees (signed)
    top = []
    for d, q in cnt.most_common():
        if all(abs(d - e) > 0.3 for e, _ in top):
            top.append((d, sum(v for w, v in cnt.items() if abs(w - d) <= 0.3)))
        if len(top) == 2: break
    if len(top) == 1 or top[1][1] < 0.25 * top[0][1]:
        top = [top[0], top[0]]                      # both arms at one signed tilt
    out = []
    for d, q in top:
        t = math.radians(abs(d))
        c = (math.sin(t) + 1 - f) / (1 - math.cos(t))
        if abs(c - round(c)) > 0.12 or round(c) < 4: return None
        out.append((int(round(c)), d, q))
    share = (out[0][2] + (out[1][2] if top[0] is not top[1] else 0)) / len(ang)
    if share < 0.7: return None
    (c1, t1, _), (c2, t2, _) = sorted(out, key=lambda v: -v[0])
    return c1, c2, t1, t2, share


def main():
    sub, gapf, outp = sys.argv[1:4]
    mlo, mhi = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (28, 31)
    gap = {}
    for l in open(gapf):
        a = l.rstrip('\n').split('\t')
        if a[0] == 'n': continue
        gap[int(a[0])] = (int(a[1]), int(a[2]), float(a[3]), float(a[4]))
    rows = collections.defaultdict(list)
    for a in csv.DictReader(open(sub)):
        n = int(a['n'])
        if n in gap and mlo <= gap[n][0] <= mhi:
            rows[n].append((float(a['x']), float(a['y']), float(a['angle'])))
    des = {}
    for n in sorted(rows):
        m, k, L, B = gap[n]
        if k < 1: continue
        f = L - m
        d = read_design(rows[n], f)
        if d is None: continue
        c1, c2, t1, t2, share = d
        des[n] = dict(m=m, k=k, f=f, c1=c1, c2=c2, t1=t1, t2=t2, share=share, E=flush(m, c1, c2, f) - k,
                      sign='same' if t1 * t2 > 0 else 'mirror')
    print('two-arm layouts read: %d of %d' % (len(des), sum(1 for n in rows if gap[n][1] >= 1)))
    cls = collections.defaultdict(list)
    for n, d in des.items(): cls[(d['m'], d['c1'], d['c2'])].append(n)
    print('class (m, c1, c2): n held, E min..max')
    for key in sorted(cls):
        E = [des[n]['E'] for n in cls[key]]
        print('  m=%d c=%d,%d  %2d n  E %.2f..%.2f  k %s' % (key + (len(E), min(E), max(E), ' '.join(str(des[n]['k']) for n in cls[key]))))
    # the slide: every donor design on every n of its own m
    with open(outp, 'w') as h:
        h.write('n\tm\tk\theld_f\tboard_f\tdonor\tdonor_k\tc1\tc2\tsign\tE\tpred_f\theld_minus_pred\tsquares\n')
        best = {}
        for n in sorted(gap):
            m, k, L, B = gap[n]
            if not (mlo <= m <= mhi) or k < 1: continue
            for dn, d in des.items():
                if d['m'] != m: continue
                pf = f_for(m, d['c1'], d['c2'], d['E'], k)
                if pf is None: continue
                step = pf - (f_for(m, d['c1'], d['c2'], d['E'], k - 1) or pf)   # one square's worth of f for this design
                sqs = (L - m - pf) / step if step > 0 else 0.0
                h.write('%d\t%d\t%d\t%.6f\t%.6f\t%d\t%d\t%d\t%d\t%s\t%.3f\t%.6f\t%.6f\t%.2f\n' % (
                    n, m, k, L - m, B - m, dn, d['k'], d['c1'], d['c2'], d['sign'], d['E'], pf, L - m - pf, sqs))
                if dn != n and (n not in best or sqs > best[n][0]): best[n] = (sqs, dn, d, pf)
    return des, best, gap


if __name__ == '__main__':
    des, best, gap = main()
    print('n m k | held f board f | design held | best other donor: n k c1,c2 sign E -> pred f (squares below held)')
    for n in sorted(best):
        m, k, L, B = gap[n]
        sqs, dn, d, pf = best[n]
        own = des.get(n)
        print('%d %d %2d | %.4f %.4f | %s | %d k=%d c=%d,%d %s E=%.2f -> %.4f (%+.2f)' % (
            n, m, k, L - m, B - m, ('c=%d,%d %s E=%.2f' % (own['c1'], own['c2'], own['sign'], own['E'])) if own else '-          ',
            dn, d['k'], d['c1'], d['c2'], d['sign'], d['E'], pf, sqs))
