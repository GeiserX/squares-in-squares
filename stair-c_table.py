#!/usr/bin/env python3
"""The long-arm slice (m 28 to 31, k 17 to 45): the loss a side allows for every pair of arm sizes, and which pairs
a new corner could make pay.

  stair-c_table.py need   LIBWORK DETAILS.csv GAP.tsv [--m 28-31] [--k 17-45] [--c 6-15] [--span 0.05] [--out TSV]
  stair-c_table.py pairs  NEED.tsv [--line 0.3]

need   For every n of the slice and every pair (c1 <= c2): the loss the held side and the board's side allow
       (k_flush - k of modules.py), the cheapest far zone of each arm that the library holds within --span of that f,
       and so the corner loss that would tie the held side: need = allowed - far1 - far2. Beside it the library's
       cheapest corner of the pair within --span of f (narrower arm first, moved with twoshort.flip_cost), and the
       line through the staircase corners that the twoshort lane measured (0.55 (c1 + c2) - 6.3 + 1.2 (f - 0.70)).
pairs  The pairs by what a corner at the line would give: n with a margin above --line, and the best margin.

Our own code. Reads the library pickle and the tables as data only. Imports modules.py and twoshort.py of this lane.
"""
import argparse, collections, csv, math, os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from modules import flush_tilt, k_flush
from twoshort import flip_cost, span

LINE = (0.55, -6.3, 1.2, 0.70)        # staircase corners of the twoshort lane: loss = 0.55 (c1 + c2) - 6.3 + 1.2 (f - 0.70)


def line(c1, c2, f):
    return LINE[0] * (c1 + c2) + LINE[1] + LINE[2] * (f - LINE[3])


def library(work):
    """-> far[c] = [(f0, loss, count, id)], cor[(c1, c2)] = [(f0, loss, count, id)] with c1 <= c2"""
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    far = collections.defaultdict(list); cor = collections.defaultdict(list)
    for q in lib['mods']:
        try: loss = float(q['loss0']); f0 = float(q['f0'])
        except (TypeError, ValueError): continue
        if not math.isfinite(loss): continue
        if q['kind'] == 'far':
            if len(q.get('miss', [])) == 0: far[q['c']].append((f0, loss, q['count'], q['id']))
        else:
            c1, c2 = q['c1'], q['c2']
            if c1 > c2: c1, c2, loss = c2, c1, loss - flip_cost(c2, c1, f0)
            cor[(c1, c2)].append((f0, loss, q['count'], q['id']))
    return far, cor


def low(rows, f, sp):
    """the lowest loss of rows within sp of f -> (loss, id) or (None, '')"""
    sel = [r for r in rows if abs(r[0] - f) <= sp]
    if not sel: return None, ''
    b = min(sel, key=lambda r: r[1]); return b[1], b[3]


def cmd_need(a):
    far, cor = library(a.lib)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.details))}
    board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(a.gap), delimiter='\t')}
    ms, ks, cs = span(a.m), span(a.k), span(a.c)
    out = []
    for n in sorted(held):
        m = math.isqrt(n - 1); k = n - m * m
        if not (ms[0] <= m <= ms[1] and ks[0] <= k <= ks[1]): continue
        fh, fb = held[n] - m, board[n] - m
        for c1 in range(cs[0], cs[1] + 1):
            for c2 in range(c1, cs[1] + 1):
                f1, i1 = low(far[c1], fh, a.span); f2, i2 = low(far[c2], fh, a.span)
                if f1 is None or f2 is None: continue
                ah = k_flush(m, fh, c1, c2) - k; ab = k_flush(m, fb, c1, c2) - k
                lc, ic = low(cor[(c1, c2)], fh, a.span)
                out.append(dict(n=n, m=m, k=k, fh=fh, fb=fb, c1=c1, c2=c2, allow_h=ah, allow_b=ab, far1=f1, far2=f2, need=ah - f1 - f2,
                                need_b=ab - f1 - f2, lib=lc, lib_id=ic, line=line(c1, c2, fh), score_gap=(held[n] - board[n]) / math.sqrt(n)))
    w = sys.stdout if not a.out else open(a.out, 'w')
    w.write('n\tm\tk\theld_f\tboard_f\tc1\tc2\tallowed_held\tallowed_board\tfar1\tfar2\tcorner_to_tie_held\tcorner_to_tie_board\tlibrary_corner\tlibrary_id\tline_corner\tmargin_library\tmargin_line\tscore_gap\n')
    for o in out:
        w.write('%d\t%d\t%d\t%.4f\t%.4f\t%d\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%s\t%s\t%.3f\t%s\t%.3f\t%.3e\n' % (
            o['n'], o['m'], o['k'], o['fh'], o['fb'], o['c1'], o['c2'], o['allow_h'], o['allow_b'], o['far1'], o['far2'], o['need'], o['need_b'],
            '' if o['lib'] is None else '%.3f' % o['lib'], o['lib_id'], o['line'], '' if o['lib'] is None else '%.3f' % (o['need'] - o['lib']),
            o['need'] - o['line'], o['score_gap']))
    if a.out: w.close(); print('wrote %s: %d rows on %d n' % (a.out, len(out), len({o['n'] for o in out})))


def cmd_pairs(a):
    R = list(csv.DictReader(open(a.need), delimiter='\t'))
    by = collections.defaultdict(list)
    for r in R: by[(int(r['c1']), int(r['c2']))].append(r)
    print('pair\tn with far zones\tlibrary corner on\tbest margin, library (n)\tn above %.1f, library\tbest margin, line (n)\tn above %.1f, line\tn above, line, and no library corner' % (a.line, a.line))
    for p in sorted(by):
        v = by[p]; L = [r for r in v if r['library_corner']]
        bl = max(L, key=lambda r: float(r['margin_library'])) if L else None
        bn = max(v, key=lambda r: float(r['margin_line']))
        print('%dx%d\t%d\t%d\t%s\t%d\t%+.2f (%s)\t%d\t%d' % (p[0], p[1], len(v), len(L), '-' if bl is None else '%+.2f (%s)' % (float(bl['margin_library']), bl['n']),
              sum(float(r['margin_library']) > a.line for r in L), float(bn['margin_line']), bn['n'], sum(float(r['margin_line']) > a.line for r in v),
              sum(float(r['margin_line']) > a.line and not r['library_corner'] for r in v)))
    best = {}
    for r in R:
        n = int(r['n']); mg = float(r['margin_line'])
        if n not in best or mg > best[n][0]: best[n] = (mg, r)
    print('n\tk\theld f\tscore gap\tbest pair at the line\tmargin\tlibrary margin of that pair\tbest library pair')
    for n in sorted(best, key=lambda n: -float(best[n][1]['score_gap'])):
        mg, r = best[n]; L = [q for q in R if int(q['n']) == n and q['library_corner']]
        bl = max(L, key=lambda q: float(q['margin_library'])) if L else None
        print('%d\t%s\t%s\t%s\t%sx%s\t%+.2f\t%s\t%s' % (n, r['k'], r['held_f'], r['score_gap'], r['c1'], r['c2'], mg, r['margin_library'] or '-',
              '-' if bl is None else '%sx%s %+.2f' % (bl['c1'], bl['c2'], float(bl['margin_library']))))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('need'); p.add_argument('lib'); p.add_argument('details'); p.add_argument('gap'); p.add_argument('--m', default='28-31')
    p.add_argument('--k', default='17-45'); p.add_argument('--c', default='6-15'); p.add_argument('--span', type=float, default=0.05); p.add_argument('--out'); p.set_defaults(fn=cmd_need)
    p = sub.add_parser('pairs'); p.add_argument('need'); p.add_argument('--line', type=float, default=0.3); p.set_defaults(fn=cmd_pairs)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
