#!/usr/bin/env python3
"""The stair-b slice (m 24 to 27, k 4 to 20): the margin of every pair of arm sizes at every n, and the corners to build.

  stair-b_plan.py margins GAP.tsv ZONES.tsv FAR.tsv [--m 24-27] [--k 4-20] [--c 6-15] [--built 8x9@0.68=2.72,..]
                          [--span 0.06] [--out TSV] [--plan TSV] [--line 0.3]
  stair-b_plan.py bar     DETAILS.csv OUT.csv TAKEDIR ...     the bar of every n: the smaller of its held side and its side
                          in these take dirs (their take.tsv; score = L / sqrt(n) - 1), as n, L, score, who
  stair-b_plan.py rows    QUEUE.tsv ... [--bar BAR.csv] [--slack 0.003] [--need IDS.txt] [--out LIST] [--prefix s]
                          the generator rows of modules.py queue as a build list, largest score gap first

margins. The model is the one of twoshort.py: the loss a side allows for a pair is k_flush(m, f, c1, c2) - k, and the
margin is that loss less the cheapest far zone of each arm at that f and less a corner. Two things differ from
`twoshort.py pay`, because this slice runs from f = 0.57 to 0.87 where that one stays below 0.78:

  * a library corner counts for an n only within --span of the f it was found at (modules.py uses a corner within
    CSPAN = 0.06 of its f), so the table says where the library has no corner at all for a pair;
  * a corner we built counts the same way, at its own f.

Where neither holds a corner in reach, the corner is the lower line of twoshort.py, 0.55 (c1 + c2) - 6.3, and the row
is marked `line`: that is a corner nobody has built, and the place where a staircase corner can pay.

--plan writes one row for every (pair, f rounded to 0.02) whose margin is above --line on some n, with the n it
serves and the score gap of those n: the corners to build, largest score gap first.

Our own code. Reads tables as data only. Imports twoshort.py and modules.py of this lane and changes neither.
"""
import argparse, collections, csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import twoshort as T
from modules import k_flush


def corners_by_f(zones_path):
    """results/zones-*.tsv -> {(ca, cb) with ca <= cb: [(f, loss in that labelling, count, labelled)]}"""
    _, cor = T.zone_table(zones_path)
    out = collections.defaultdict(list)
    for (ca, cb), v in cor.items():
        for f, n, l in v:
            if ca <= cb: out[(ca, cb)].append((f, l, n, '%dx%d' % (ca, cb)))
            else: out[(cb, ca)].append((f, l - T.flip_cost(cb, ca, f), n, '%dx%d' % (ca, cb)))
    return out


def cmd_margins(a):
    rows = T.slice_rows(a.gap, T.span(a.m), T.span(a.k)); c0, c1 = T.span(a.c); cs = list(range(c0, c1 + 1))
    ft = T.far_table(a.far)
    far = {c: {f: min(v[0] for v in ft[c][f].values()) for f in ft[c]} for c in ft}
    zfar, _ = T.zone_table(a.zones)
    zf = collections.defaultdict(dict)
    for c, v in zfar.items():
        for f, cl, n, l in v: zf[c][f] = min(zf[c].get(f, 9e9), l)

    def far_at(c, f):
        out = []
        for tab in (far, zf):
            if c in tab and tab[c]:
                fs = sorted(tab[c]); out.append(float(np.interp(f, fs, [tab[c][x] for x in fs])))
        return min(out) if out else None

    lib = corners_by_f(a.zones)
    built = collections.defaultdict(list)             # --built 8x9@0.68=2.72: corners we built, narrower arm first
    for s in (a.built or '').split(','):
        if not s: continue
        pr, loss = s.split('='); pr, f = pr.split('@'); ca, cb = (int(x) for x in pr.split('x'))
        built[(ca, cb)].append((float(f), float(loss)))

    def corner(ca, cb, f):
        best = (T.CORNER_LINE[0] * (ca + cb) + T.CORNER_LINE[1], 'line'); got = False
        for ff, l, n, lab in lib.get((ca, cb), ()):
            if abs(ff - f) <= a.span and (not got or l < best[0]): best = (l, 'lib'); got = True
        for ff, l in built.get((ca, cb), ()):
            if abs(ff - f) <= a.span and (not got or l < best[0]): best = (l, 'built'); got = True
        return best

    out = []
    for r in rows:
        fb, fh = r['board'] - r['m'], r['ours'] - r['m']
        for ca in cs:
            for cb in cs:
                if cb < ca: continue
                fa_h, fb_h, fa_b, fb_b = far_at(ca, fh), far_at(cb, fh), far_at(ca, fb), far_at(cb, fb)
                if None in (fa_h, fb_h): continue
                co, how = corner(ca, cb, fh); cob, howb = corner(ca, cb, fb)
                allow_h = k_flush(r['m'], fh, ca, cb) - r['k']; allow_b = k_flush(r['m'], fb, ca, cb) - r['k']
                out.append(dict(n=r['n'], m=r['m'], k=r['k'], fh=fh, fb=fb, gap=r['gap'], ca=ca, cb=cb, how=how, corner=co,
                                allow_h=allow_h, allow_b=allow_b, mh=allow_h - fa_h - fb_h - co, mb=allow_b - fa_b - fb_b - cob))
    print('n\tm\tk\theld f\tboard f\tscore gap\tbest pair (margin on held, on the board, corner)\tbest pair with a line corner\tpairs above %.1f' % a.line)
    for r in rows:
        mine = [o for o in out if o['n'] == r['n']]
        if not mine: continue
        b = max(mine, key=lambda o: o['mh']); ln = [o for o in mine if o['how'] == 'line']
        w = max(ln, key=lambda o: o['mh']) if ln else None
        fm = lambda o: '-' if o is None else '%dx%d %+.2f %+.2f %s' % (o['ca'], o['cb'], o['mh'], o['mb'], o['how'])
        ab = ' '.join('%dx%d%s' % (o['ca'], o['cb'], '' if o['how'] != 'line' else '*') for o in sorted(mine, key=lambda o: -o['mh']) if o['mh'] > a.line)
        print('%d\t%d\t%d\t%.4f\t%.4f\t%.2e\t%s\t%s\t%s' % (r['n'], r['m'], r['k'], b['fh'], b['fb'], r['gap'], fm(b), fm(w), ab))
    print('pair\trows\tcorner by line on\tmedian margin on held\tbest (n)\tn above %.1f\tmedian on the board\tbest on the board' % a.line)
    for ca in cs:
        for cb in cs:
            mine = [o for o in out if o['ca'] == ca and o['cb'] == cb]
            if not mine: continue
            b = max(mine, key=lambda o: o['mh'])
            print('%dx%d\t%d\t%d\t%+.2f\t%+.2f (%d)\t%d\t%+.2f\t%+.2f' % (ca, cb, len(mine), sum(o['how'] == 'line' for o in mine),
                  float(np.median([o['mh'] for o in mine])), b['mh'], b['n'], sum(o['mh'] > a.line for o in mine),
                  float(np.median([o['mb'] for o in mine])), max(o['mb'] for o in mine)))
    if a.out:
        with open(a.out, 'w') as h:
            h.write('n\tm\tk\theld_f\tboard_f\tscore_gap\tc1\tc2\tallowed_held\tallowed_board\tmargin_held\tmargin_board\tcorner\tcorner_loss\n')
            for o in sorted(out, key=lambda o: (o['n'], o['ca'], o['cb'])):
                h.write('%d\t%d\t%d\t%.4f\t%.4f\t%.3e\t%d\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%s\t%.2f\n' % (
                    o['n'], o['m'], o['k'], o['fh'], o['fb'], o['gap'], o['ca'], o['cb'], o['allow_h'], o['allow_b'], o['mh'], o['mb'], o['how'], o['corner']))
    if a.plan:
        plan = collections.defaultdict(list)
        for o in out:
            if o['mh'] > a.line: plan[(o['ca'], o['cb'], round(round(o['fh'] / 0.02) * 0.02, 2))].append(o)
        with open(a.plan, 'w') as h:
            h.write('c1\tc2\tf\tn served\tscore gap of those n\tbest margin\tcorner now\tn\n')
            for key in sorted(plan, key=lambda q: -sum(o['gap'] for o in plan[q])):
                v = plan[key]
                h.write('%d\t%d\t%.2f\t%d\t%.3e\t%+.2f\t%s\t%s\n' % (key[0], key[1], key[2], len(v), sum(o['gap'] for o in v), max(o['mh'] for o in v),
                        '/'.join(sorted({o['how'] for o in v})), ' '.join(str(o['n']) for o in sorted(v, key=lambda o: -o['gap']))))
        print('plan: %d (pair, f) cells above %.1f -> %s' % (len(plan), a.line, a.plan))


def cmd_rows(a):
    """Generator rows -> a build list "HOW NAME N CORNER FAR1 FAR2 S1 S2 F", rows within --slack of the bar, one n after
    the other by the score gap of the n (largest first), the best row of every n before the second best of any, at
    most --per-n rows of an n. The rows predicted below the bar come first, then the rows up to --slack above it."""
    bar = {}
    if a.bar:
        bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.bar))}
    need = set(open(a.need).read().split()) if a.need else None
    gap = {}
    if a.gap:
        gap = {int(r['n']): float(r['score_gap']) for r in csv.DictReader(open(a.gap), delimiter='\t')}
    per = collections.defaultdict(list); seen = set()
    for q in a.queue:
        if not os.path.exists(q): continue
        for r in csv.DictReader(open(q), delimiter='\t'):
            if not r['n'].isdigit(): continue
            n = int(r['n']); ids = (r['corner'], r['far1'], r['far2']); st = (int(r['stacks1']), int(r['stacks2']))
            if (n, ids, st) in seen: continue
            if need is not None and not (set(ids) & need): continue
            d = float(r['predicted_side']) - bar.get(n, float(r['held_side']))
            if d > a.slack: continue
            seen.add((n, ids, st)); per[n].append((d, ids, st, r['f']))
    lines = []
    for tier in (0, 1):                               # rows predicted below the bar first, then the rows above it
        pt = {n: sorted(t for t in v if (t[0] > 0) == bool(tier)) for n, v in per.items()}; rank = 0
        while any(pt.values()):
            for n in sorted(pt, key=lambda n: (-gap.get(n, 0.0), n)):
                if not pt[n] or rank >= a.per_n: pt[n] = []; continue
                d, ids, st, f = pt[n].pop(0)
                lines.append('%s %d-%s%03d %d %s %s %s %d %d %s' % (a.how, n, a.prefix, len(lines), n, ids[0], ids[1], ids[2], st[0], st[1], f))
                if rank == 0: print('  %d %+.6f %s %s' % (n, d, '+'.join(ids), st))
            rank += 1
    if a.out:
        with open(a.out + '.tmp', 'w') as h: h.write('\n'.join(lines) + ('\n' if lines else ''))
        os.replace(a.out + '.tmp', a.out)
    print('rows %d on %d n' % (len(lines), len({ln.split()[2] for ln in lines})))


def cmd_bar(a):
    import math
    held = {int(r['n']): (float(r['L']), float(r['score'])) for r in csv.DictReader(open(a.details))}
    bar = {n: (v[0], v[1], 'held') for n, v in held.items()}
    for d in a.takes:
        p = os.path.join(d, 'take.tsv')
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p), delimiter='\t'):
            if not (r.get('n') or '').isdigit(): continue
            try: n, sc = int(r['n']), float(r['new'])
            except (ValueError, KeyError, TypeError): continue
            if n in bar and sc < bar[n][1]: bar[n] = ((1 + sc) * math.sqrt(n), sc, os.path.basename(d.rstrip('/')))
    with open(a.out + '.tmp', 'w') as h:
        h.write('n,L,score,who\n')
        for n in sorted(bar): h.write('%d,%r,%r,%s\n' % (n, bar[n][0], bar[n][1], bar[n][2]))
    os.replace(a.out + '.tmp', a.out)
    low = [n for n in bar if bar[n][2] != 'held']
    print('bar of %d n, %d lowered by a take' % (len(bar), len(low)))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('bar'); p.add_argument('details'); p.add_argument('out'); p.add_argument('takes', nargs='*'); p.set_defaults(fn=cmd_bar)
    p = sub.add_parser('margins'); p.add_argument('gap'); p.add_argument('zones'); p.add_argument('far')
    p.add_argument('--m', default='24-27'); p.add_argument('--k', default='4-20'); p.add_argument('--c', default='6-15')
    p.add_argument('--built'); p.add_argument('--span', type=float, default=0.06); p.add_argument('--out'); p.add_argument('--plan')
    p.add_argument('--line', type=float, default=0.3); p.set_defaults(fn=cmd_margins)
    p = sub.add_parser('rows'); p.add_argument('queue', nargs='+'); p.add_argument('--bar'); p.add_argument('--gap'); p.add_argument('--need')
    p.add_argument('--slack', type=float, default=0.003); p.add_argument('--out'); p.add_argument('--prefix', default='s'); p.add_argument('--how', default='family'); p.add_argument('--per-n', dest='per_n', type=int, default=2)
    p.set_defaults(fn=cmd_rows)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
