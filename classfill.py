#!/usr/bin/env python3
"""Which far zone would serve the most trailing n: the table of (arm size, count class) cells at a high side fraction.

  classfill.py table  LIBWORK DETAILS.csv BOARD.json OUT.pkl [--flo 0.85] [--eps 0] [--part I/K]   the break-even loss of every cell
  classfill.py cells  OUT.pkl[,OUT.pkl...] CELLS.tsv [--near 0.30]          the cells ranked by the n they would serve
  classfill.py pairs  LIBWORK DETAILS.csv BOARD.json OUT.tsv [--flo 0.85]   the (c1, c2) table: the board's loss, ours,
                                                                            and the library's best sum with a free class
  classfill.py drop   LIBWORK NEWWORK ID [ID ...]                           a library without these modules (the control)
  classfill.py taper  C F OUTDIR LO HI [STEP]                               zone_search's taper enumeration with a key
                                                                            that also holds arms of 11 and 12
  classfill.py have   LIBWORK C F                                           the library's best far zone of every class of a
                                                                            c-arm at F
  classfill.py fresh  QUEUE.tsv[,...] RESULTS_DIR DETAILS.csv OUT.tsv [--takes DIR ...]   the queue rows that no earlier
                                                                            round built, against the bar of every take
  classfill.py builds OUT.tsv RAWDIR [RAWDIR ...]                           one row per build record of `modules.py job`
  classfill.py sweeps LOGDIR LIST.txt OUT.tsv                               one row per hop search at the f of an n
  classfill.py base   LIBWORK OUT.pkl F C                                   the start zones of a search, our own zones too
  classfill.py sweepall BASE.pkl OUTDIR [--classes 4,7] [--top 5] [--seconds 90]   the kind sweep on the best zones of every class
  classfill.py wide   CELLS.tsv [--short 0.25] [--gap 2e-5]                 the (arm, f, classes) lines for `sweepall`
  classfill.py own    LIBWORK OUTDIR IDS.txt [--seconds 120] [--part I/K] [--no-twins] [--control]
                                                                            the kind sweep on far zones at the f of their
                                                                            own layout (the recipe of 703); a zone whose
                                                                            layout holds its slid twin is swept as the twin
  classfill.py twins  LIBWORK BAR.csv OUT.txt                               the far zones whose layout holds their slid twin
                                                                            and is the bar of its n
  classfill.py owns   OUT.tsv LOG [LOG ...]                                 one row per zone of the logs of `own`

The idea. A two-arm layout of n squares in a side m + f holds a corner zone, two far zones and whole flush stacks.
modules.Library.fit says a choice (corner C, far zones F1 and F2, s1 and s2 stacks) fits at f when

  Y(C) + s1 p1 + L(F1) <= m + f   and   X(C) + s2 p2 + L(F2) <= m + f

and the count is n = (m - c1 + 1)(m - c2 + 1) + count(C) + count(F1) + s1 c1 + count(F2) + s2 c2.

Take a corner C in one of its states, and a real far zone F2 with s2 stacks that fits on arm 2. Then arm 1 must hold
T1 = n - rest - count(C) - count(F2) - s2 c2 squares beyond the corner, in a length of m + f - Y(C). A far zone of the
class T1 mod c1 does that if and only if its loss is at most

  break-even loss = c1 cos t1 (m + f - Y(C)) - T1

because the loss of a far zone is c cos t * length - count and whole flush stacks leave it alone. The largest
break-even loss over every corner, state, far zone and stack count is what a NEW far zone of that arm size and class
has to reach for n to fit at f. We take it at the held f (a zone below it wins n) and at the board's f (a zone below it
reaches the board's side). The library's best far zone of the same class at the same f is what we hold. A cell
(arm size, class) where the held zone is above the break-even loss of several n is a zone that serves all of them.

Our own code. Imports modules.py and zone_search.py of this lane and changes neither.
"""
import csv, json, math, os, pickle, sys, time, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M

NEG = -1e9


def _lib(work):
    return M.Library(work, only=(lambda q: q['tag'] in ('h', 'z') or q.get('ours') or any(k in q['licence'] for k in M.OK_LICENCE)))


def _at(arr, f):
    """arr[..., FF] at f by linear interpolation between the two knots of FF around it (nan if either is nan)."""
    i = int(np.searchsorted(M.FF, f) - 1); i = max(0, min(len(M.FF) - 2, i))
    w = (f - M.FF[i]) / (M.FF[i + 1] - M.FF[i])
    return arr[..., i] * (1 - w) + arr[..., i + 1] * w


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


class Table:
    """The library as arrays, by arm size and by pair of arm sizes."""

    def __init__(self, lib):
        self.lib = lib
        self.far = {}
        for c, Fs in lib.far.items():
            self.far[c] = dict(F=Fs, L=np.array([F['L'] for F in Fs]), lean=np.array([F['lean'] for F in Fs]),
                               sym=np.array([F['sym'] for F in Fs], bool), g=np.array([F['g'] for F in Fs], float),
                               count=np.array([F['count'] for F in Fs], int))
        by = collections.defaultdict(list)
        for C in lib.corners:
            if '^' in C['id']: continue                 # grant variants: a new zone does not poke, so the plain corner is never worse
            by[(C['c1'], C['c2'])].append(C)
        self.cor = {}
        for key, Cs in by.items():
            self.cor[key] = dict(C=Cs, Y=np.array([C['Y'] for C in Cs]), X=np.array([C['X'] for C in Cs]),
                                 count=np.array([C['count'] for C in Cs], int), lean1=np.array([C['lean1'] for C in Cs]),
                                 lean2=np.array([C['lean2'] for C in Cs]), g1=np.array([C['g1'] for C in Cs], float),
                                 g2=np.array([C['g2'] for C in Cs], float))

    def have(self, c, f):
        """The library's lowest far loss of every class of a c-arm at f. -> ([loss or inf], [id or None])"""
        out = [math.inf] * c; ids = [None] * c
        if c not in self.far: return out, ids
        A = self.far[c]; L = _at(A['L'], f); loss = c * math.cos(M.flush_tilt(c, f)) * L - A['count']
        for i in np.nonzero(np.isfinite(loss))[0]:
            a = int(A['count'][i] % c)
            if loss[i] < out[a]: out[a] = float(loss[i]); ids[a] = A['F'][i]['id']
        return out, ids

    def breakeven(self, n, f):
        """{(c, class): (break-even loss, corner id, state, other far id, other stacks, arm of the new zone)} for n at f."""
        m = math.isqrt(n - 1); best = {}
        for (c1, c2), G in self.cor.items():
            if m - c1 + 1 < 5 or m - c2 + 1 < 5: continue
            if c1 not in self.far or c2 not in self.far: continue
            Y = _at(G['Y'], f); X = _at(G['X'], f)                       # (corners, states)
            Q = n - (m - c1 + 1) * (m - c2 + 1) - G['count']             # squares of the two arms beyond the corner
            for arm in (1, 2):                                           # the arm that gets the new zone
                cn, co = (c1, c2) if arm == 1 else (c2, c1)              # its stack size, and the other arm's
                mine, other = (Y, X) if arm == 1 else (X, Y)
                A = self.far[co]
                need = G['lean2'] if arm == 1 else -G['lean1']           # the lean a far zone of the other arm must have
                gc = G['g2'] if arm == 1 else G['g1']
                Lo = _at(A['L'], f); po = M.pitch(co, f)
                sel = (A['sym'][None, :] | (A['lean'][None, :] == need[:, None])) & (A['g'][None, :] <= gc[:, None] + 2e-3) & np.isfinite(Lo)[None, :]
                with np.errstate(invalid='ignore'):
                    smax = np.floor((m + f - other[:, :, None] - np.nan_to_num(Lo, nan=1e9)[None, None, :]) / po)
                T = np.where(sel[:, None, :] & (smax >= 1) & np.isfinite(other)[:, :, None], A['count'][None, None, :] + co * smax, NEG)
                cls = A['count'] % co
                cc = cn * math.cos(M.flush_tilt(cn, f))
                room = cc * (m + f - mine)                               # (corners, states): squares of flush stacks the new arm has room for
                for b in range(co):
                    cols = np.nonzero(cls == b)[0]
                    if not len(cols): continue
                    Tb = T[:, :, cols]; j = Tb.argmax(axis=2); Tbest = np.take_along_axis(Tb, j[:, :, None], 2)[:, :, 0]
                    for i in range(1 if cn == co else cn):               # stacks fewer on the other arm: other classes of the new arm
                        To = Tbest - i * co
                        Tn = Q[:, None] - To
                        ok = (Tbest > NEG / 2) & (To >= co) & (Tn >= 2 * cn) & np.isfinite(room)
                        if not ok.any(): continue
                        le = np.where(ok, room - Tn, NEG); an = np.where(ok, Tn % cn, -1).astype(int)
                        for a in np.unique(an[ok]):
                            v = np.where(an == a, le, NEG); q = int(v.argmax()); ci, st = divmod(q, v.shape[1])
                            val = float(v[ci, st]); key = (cn, int(a))
                            if key not in best or val > best[key][0]:
                                F = A['F'][int(cols[j[ci, st]])]
                                best[key] = (val, G['C'][ci]['id'], st, F['id'], int((To[ci, st] - F['count']) // co), arm)
        return best


    def corner_cells(self, n, f):
        """The same for a NEW corner of two equal arms: with real far zones F1 and F2 and s1 and s2 stacks, the corner
        has count Nc = n - rest - T1 - T2 and the caps A1 = m + f - s1 p - L1 and A2 likewise on its two lengths. Its
        loss is then at most c cos t (A1 + A2 - W) - Nc (the break-even loss; a corner needs both caps, so this is an
        upper bound of what it may lose). -> {(c, class of Nc): (break-even loss, far 1 id, far 2 id, Nc, A1, A2)}
        and {(c, class): (the library's lowest corner loss of that class at f, id)}"""
        m = math.isqrt(n - 1); best = {}; have = {}
        for c in sorted(self.far):
            if (c, c) not in self.cor or m - c + 1 < 5: continue
            A = self.far[c]; L = _at(A['L'], f); p = M.pitch(c, f); cc = c * math.cos(M.flush_tilt(c, f)); W = c - 1 + f
            ok = np.nonzero(np.isfinite(L) & A['sym'])[0]
            if not len(ok): continue
            loss = cc * L[ok] - A['count'][ok]; cls = A['count'][ok] % c
            fl = {}                                                      # the lowest far loss of every class, with its zone
            for i in np.argsort(loss):
                fl.setdefault(int(cls[i]), (float(loss[i]), A['F'][int(ok[i])]['id']))
            budget = M.k_flush(m, f, c, c) - (n - m * m)                 # the three losses together, when both arms fit with no slack
            for a1, (l1, i1) in fl.items():
                for a2, (l2, i2) in fl.items():
                    if a2 < a1: continue
                    cl = (n - (m - c + 1) ** 2 - a1 - a2) % c
                    v = budget - l1 - l2
                    if (c, cl) not in best or v > best[(c, cl)][0]: best[(c, cl)] = (v, i1, i2)
            G = self.cor[(c, c)]; Y = _at(G['Y'], f); X = _at(G['X'], f)
            cl0 = cc * (Y + X - W) - G['count'][:, None]
            with np.errstate(invalid='ignore'):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore'); lo = np.nanmin(cl0, axis=1)
            for i in np.nonzero(np.isfinite(lo))[0]:
                key = (c, int(G['count'][i] % c))
                if key not in have or lo[i] < have[key][0]: have[key] = (float(lo[i]), G['C'][i]['id'])
        return best, have


def _targets(details, board, flo):
    held = {int(r['n']): (float(r['L']), float(r['score'])) for r in csv.DictReader(open(details))}
    brd = {int(r['n']): float(r['L']) for r in json.load(open(board))}
    out = []
    for n in sorted(held):
        m = math.isqrt(n - 1)
        if n < 260 or held[n][0] >= m + 1 - 1e-9: continue
        fb, fh = brd[n] - m, held[n][0] - m
        if fb < flo or brd[n] > held[n][0] - 1e-7: continue
        out.append(dict(n=n, m=m, k=n - m * m, fh=fh, fb=fb, gap=(held[n][0] - brd[n]) / math.sqrt(n)))
    return out


def cmd_table(a):
    work, details, board, out = a[:4]
    flo = _opt(a, '--flo', 0.85); part = tuple(map(int, _opt(a, '--part', '0/1', str).split('/')))
    eps = _opt(a, '--eps', 0.0)      # the fit is tested at the held f plus this: the rigid tables miss a held layout by about 2e-4
    tg = _targets(details, board, flo)[part[0]::part[1]]
    print('%d trailing n with a board f of %.2f and more' % (len(tg), flo), flush=True)
    T = Table(_lib(work)); t0 = time.time(); rows = []
    for q, r in enumerate(tg):
        fh = min(r['fh'] + eps, M.FF[-1]); fb = r['fb']
        r['held'] = T.breakeven(r['n'], fh); r['board'] = T.breakeven(r['n'], fb)
        r['have'] = {c: T.have(c, fh) for c in sorted(T.far)}
        r['have_b'] = {c: T.have(c, fb) for c in sorted(T.far)}
        r['cc'] = T.corner_cells(r['n'], fh)
        rows.append(r)
        d = [(r['have'][c][0][cl] - v[0], c, cl) for (c, cl), v in r['held'].items()]
        print('%d/%d n=%d f held %.4f board %.4f: nearest cell %s (%.0f s)' % (q + 1, len(tg), r['n'], r['fh'], r['fb'],
              '%+.3f for c=%d class %d' % min(d) if d else 'none', time.time() - t0), flush=True)
        if q % 10 == 9 or q == len(tg) - 1:
            pickle.dump(rows, open(out + '.tmp', 'wb')); os.replace(out + '.tmp', out)
    return 0


def cmd_cells(a):
    """The cells ranked. A cell is (arm size, class, band of held f of width 0.03). For every n: the break-even loss at
    the held f, the library's best loss of that class there (what we hold), and the difference (what a search must gain)."""
    rows = []
    for p in a[0].split(','): rows += pickle.load(open(p, 'rb'))
    near_ = _opt(a, '--near', 0.30)
    cell = collections.defaultdict(list)
    with open(a[1], 'w') as h:
        h.write('n\tm\tk\tf_held\tf_board\tscore_gap\tc\tclass\tbreak_even_held\tbreak_even_board\twe_hold\twe_hold_id\tshort\tbest_class_of_c\tcorner\tstate\tother_far\tother_stacks\tarm\n')
        for r in rows:
            for (c, cl), v in sorted(r['held'].items()):
                hv, hid = r['have'][c][0][cl], r['have'][c][1][cl]
                fl = min(r['have'][c][0])
                vb = r['board'].get((c, cl))
                short = hv - v[0]
                h.write('%d\t%d\t%d\t%.4f\t%.4f\t%.3e\t%d\t%d\t%.3f\t%s\t%s\t%s\t%s\t%.3f\t%s\t%d\t%s\t%d\t%d\n' % (
                    r['n'], r['m'], r['k'], r['fh'], r['fb'], r['gap'], c, cl, v[0], '%.3f' % vb[0] if vb else '-',
                    '%.3f' % hv if math.isfinite(hv) else '-', hid or '-', '%+.3f' % short if math.isfinite(short) else 'none',
                    fl, v[1], v[2], v[3], v[4], v[5]))
                band = round(math.floor(r['fh'] / 0.03) * 0.03, 2)
                cell[(c, cl, band)].append((short, r['n'], r['gap'], v[0], hv, vb[0] if vb else math.nan, fl))
    # a cell counts an n when a zone no worse than the arm's best class would win it (the break-even loss is at or
    # above the library's best far loss of any class of that arm at the n's f): only a zone better than every zone we
    # hold could serve the others
    print('cell (arm, class, band of held f)\tn a zone at our best level would win\tshort by 0.10 or less\tby 0.20\tby 0.35\tno zone held\tscore gap of the n\tbreak-even\twe hold\tbest class of the arm\tthe n (short)')
    rank = []
    for key, v in cell.items():
        w = [x for x in v if x[3] >= x[6]]
        if w: rank.append((-len(w), -sum(x[2] for x in w), key, sorted(w, key=lambda x: x[1])))
    for _, _, key, w in sorted(rank):
        fin = [x for x in w if math.isfinite(x[0])]; hv = [x[4] for x in fin]
        print('c=%d class %d f %.2f\t%d\t%d\t%d\t%d\t%d\t%.2e\t%.2f to %.2f\t%s\t%.2f\t%s' % (
            key[0], key[1], key[2], len(w), sum(x[0] <= 0.10 for x in fin), sum(x[0] <= 0.20 for x in fin), sum(x[0] <= 0.35 for x in fin),
            len(w) - len(fin), sum(x[2] for x in w), min(x[3] for x in w), max(x[3] for x in w),
            '%.2f to %.2f' % (min(hv), max(hv)) if hv else '-', np.median([x[6] for x in w]),
            ' '.join('%d(%s)' % (x[1], '%+.2f' % x[0] if math.isfinite(x[0]) else 'none') for x in w)))
    tot = collections.defaultdict(list)
    for key, v in cell.items():
        for x in v:
            if math.isfinite(x[0]): tot[x[1]].append((x[0], key[0], key[1]))
    near = sorted((min(v) + (n,)) for n, v in tot.items())
    print('nearest cell of every n (squares of loss a new zone must gain): ' + ' '.join('%d:%+.2f(c%d/%d)' % (n, s, c, cl) for s, c, cl, n in near if s <= near_))
    return 0


def cmd_ccells(a):
    """classfill.py ccells OUT.pkl[,OUT.pkl...] CCELLS.tsv [--near 0.30]   the corner cells of two equal arms: for
    every n the break-even loss of a new corner of each class, beside the library's best corner of that class."""
    rows = []
    for p in a[0].split(','): rows += pickle.load(open(p, 'rb'))
    near = _opt(a, '--near', 0.30)
    cell = collections.defaultdict(list)
    with open(a[1], 'w') as h:
        h.write('n\tm\tk\tf_held\tscore_gap\tc\tcorner_class\tbreak_even_held\twe_hold\twe_hold_id\tshort\tfar1\tfar2\n')
        for r in rows:
            best, have = r['cc']
            for (c, cl), v in sorted(best.items()):
                hv, hid = have.get((c, cl), (math.inf, None))
                short = hv - v[0]
                h.write('%d\t%d\t%d\t%.4f\t%.3e\t%d\t%d\t%.3f\t%s\t%s\t%s\t%s\t%s\n' % (r['n'], r['m'], r['k'], r['fh'], r['gap'], c, cl, v[0],
                        '%.3f' % hv if math.isfinite(hv) else '-', hid or '-', '%+.3f' % short if math.isfinite(short) else 'none', v[1], v[2]))
                band = round(math.floor(r['fh'] / 0.03) * 0.03, 2)
                cell[(c, cl, band)].append((short, r['n'], r['gap'], v[0], hv))
    print('cell (two c-arms, corner class, band of held f)\tn waiting\tn short by %.2f or less\tscore gap of those\tmedian break-even\tmedian we hold\tthe n (short)' % near)
    rank = []
    for key, v in cell.items():
        nr = [x for x in v if math.isfinite(x[0]) and x[0] <= near]
        if nr: rank.append((-sum(x[2] for x in nr), key, v, nr))
    for _, key, v, nr in sorted(rank):
        s = sorted(nr, key=lambda x: x[1])
        print('c=%d corner class %d f %.2f\t%d\t%d\t%.2e\t%.2f\t%.2f\t%s' % (key[0], key[1], key[2], len(v), len(nr), sum(x[2] for x in s),
              np.median([x[3] for x in s]), np.median([x[4] for x in s]), ' '.join('%d(%+.2f)' % (x[1], x[0]) for x in s)))
    return 0


def cmd_pairs(a):
    """For every trailing n and every ordered pair of arm sizes 6..12: the loss the board's count implies, the loss of
    our side, the class for equal arms, and the library's lowest sum of three zone losses with the class left free."""
    work, details, board, out = a[:4]
    flo = _opt(a, '--flo', 0.85)
    tg = _targets(details, board, flo); T = Table(_lib(work))
    agg = collections.defaultdict(list)
    with open(out, 'w') as h:
        h.write('n\tm\tk\tf_held\tf_board\tc1\tc2\tclass_if_equal\tboard_loss\tour_loss\tlibrary_free_sum_at_board_f\tfree_sum_minus_board\n')
        for r in tg:
            n, m, k, fb = r['n'], r['m'], r['k'], r['fb']; fh = min(r['fh'], 0.9995)
            for c1 in range(6, 13):
                for c2 in range(6, 13):
                    B = M.k_flush(m, fb, c1, c2) - k; H = M.k_flush(m, fh, c1, c2) - k
                    free = math.nan
                    G = T.cor.get((c1, c2))
                    if G is not None and c1 in T.far and c2 in T.far:
                        Y = _at(G['Y'], fb); X = _at(G['X'], fb)
                        cl = c1 * math.cos(M.flush_tilt(c1, fb)) * Y + c2 * math.cos(M.flush_tilt(c2, fb)) * (X - (c1 - 1 + fb)) - G['count'][:, None]
                        if np.isfinite(cl).any():
                            free = float(np.nanmin(cl)) + min(T.have(c1, fb)[0]) + min(T.have(c2, fb)[0])
                    cls = (k - 2 * m - 1) % c1 if c1 == c2 else -1
                    h.write('%d\t%d\t%d\t%.4f\t%.4f\t%d\t%d\t%s\t%.3f\t%.3f\t%s\t%s\n' % (n, m, k, r['fh'], fb, c1, c2, cls if cls >= 0 else '-', B, H,
                            '%.3f' % free if math.isfinite(free) else '-', '%+.3f' % (free - B) if math.isfinite(free) else '-'))
                    agg[(c1, c2)].append((B, H, free, cls, n))
    print('arms\tn\tmedian board loss\tmedian our loss\tn where the free sum is known\tn where it is at or below the board loss\tmedian free sum minus board')
    for key in sorted(agg):
        v = agg[key]; fr = [x for x in v if math.isfinite(x[2])]
        print('%dx%d\t%d\t%.2f\t%.2f\t%d\t%d\t%s' % (key[0], key[1], len(v), np.median([x[0] for x in v]), np.median([x[1] for x in v]), len(fr),
              sum(x[2] <= x[0] for x in fr), '%+.2f' % np.median([x[2] - x[0] for x in fr]) if fr else '-'))
    for c in range(6, 13):
        by = collections.defaultdict(list)
        for x in agg[(c, c)]: by[x[3]].append(x)
        print('two %d-arms by class: ' % c + '  '.join('%d: %d n, board %.2f, ours %.2f' % (cl, len(by[cl]), np.median([x[0] for x in by[cl]]),
              np.median([x[1] for x in by[cl]])) for cl in sorted(by)))
    return 0


def cmd_drop(a):
    work, new, ids = a[0], a[1], set(a[2:])
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    n0 = len(lib['mods']); lib['mods'] = [q for q in lib['mods'] if q['id'] not in ids]
    for i in ids: lens.pop(i, None)
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    print('dropped %d of %d modules' % (n0 - len(lib['mods']), n0))
    return 0


def cmd_have(a):
    T = Table(_lib(a[0])); c, f = int(a[1]), float(a[2])
    ls, ids = T.have(c, f)
    for cl in range(c): print('c=%d f=%.4f class %d: %s %s' % (c, f, cl, '%.4f' % ls[cl] if math.isfinite(ls[cl]) else 'none', ids[cl] or ''))
    return 0


# ----------------------------------------------------------------------------------------------- tapers of wide arms

def taper_best(c, f, lam):
    """zone_search.taper_best with the column heights kept as rows (np.unique) instead of one decimal key, so that an
    arm of 11 (20 columns) or 12 (22 columns) cannot put two states under one key."""
    import zone_search as Z
    t, p, W = Z.geom(c, f)
    S = Z.taper_sites(c, f, lam)
    fl = lambda v: np.where(np.isinf(v), 9, np.clip(np.floor(np.minimum(v, 8.0) + 1e-9), 0, 8)).astype(np.int8)
    caps = fl(S[0][0][3])[None, :]; cnt = np.zeros(1, int); idx = [np.zeros(1, int)]
    for opts in S[1:]:
        oc = fl(np.array([o[3] for o in opts])); on = np.array([o[1] - o[0] + 1 for o in opts])
        k = len(cnt)
        caps = np.minimum(caps[:, None, :], oc[None, :, :]).reshape(-1, caps.shape[1])
        cnt = (cnt[:, None] + on[None, :]).ravel()
        idx = [np.repeat(q, len(opts)) for q in idx] + [np.tile(np.arange(len(opts)), k)]
        half = caps.shape[1] // 2
        pw = 10 ** np.arange(half, dtype=np.int64)
        k1 = caps[:, :half].astype(np.int64) @ pw; k2 = caps[:, half:].astype(np.int64) @ pw[:caps.shape[1] - half]
        o = np.lexsort((-cnt, k2, k1))
        first = np.r_[True, (k1[o][1:] != k1[o][:-1]) | (k2[o][1:] != k2[o][:-1])]
        sel = o[first]
        caps, cnt, idx = caps[sel], cnt[sel], [q[sel] for q in idx]
    hts = np.where(caps >= 9, 0, caps).astype(int)
    m = c - 1; best = None
    for kl in range(m + 1):
        tot = cnt + hts[:, :kl].sum(1) + hts[:, m:m + (m - kl)].sum(1)
        q = int(np.argmax(tot))
        if best is None or tot[q] > best[0]: best = (int(tot[q]), q, kl)
    N, q, kl = best
    runs = []; sq = []
    for jj, opts in enumerate(S[1:]):
        o = opts[int(idx[jj + 1][q])]; runs.append((o[0], o[1]))
        sq += [(x, y, -math.degrees(t)) for x, y in o[2]]
    for i in range(kl): sq += [(i + 0.5, 0.5 + r, 0.0) for r in range(hts[q, i])]
    for i in range(m - kl): sq += [(W - 0.5 - i, 0.5 + r, 0.0) for r in range(hts[q, m + i])]
    return N, runs, np.array(sq), (kl, [int(v) for v in hts[q, :kl]], [int(v) for v in hts[q, m:m + m - kl]])


def cmd_taper(a):
    """zone_search.cmd_taper with the taper_best above. Same files, so `zone_search.py table` and `merge` read them."""
    import zone_search as Z
    Z.taper_best = taper_best
    return Z.cmd_taper(a)


def cmd_seed(a):
    """classfill.py seed BASE.pkl OUTDIR [--classes 4,6,7]   the base zones of zone_search.py as zone files, the
    shortest of every count, so that `zone_search.py search --moves resume,...` starts its hops from them."""
    import zone_search as Z
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    cls = [int(v) for v in _opt(a, '--classes', '', str).split(',') if v]
    best = {}
    for b in base:
        if cls and b['count'] % b['c'] not in cls: continue
        if b['count'] not in best or b['lam'] < best[b['count']]['lam']: best[b['count']] = b
    for n, b in sorted(best.items()):
        Z._save(outdir, 'zone-%d-s800' % n, dict(lam=b['lam'], gap=0.0, P=b['P'], how='library zone %s carried to f' % b['id'],
                                                 base=dict(id=b['id'], src=b['src'], licence=b['licence']), c=b['c'], f=b['f'], count=n, seed=800, cpu=0.0))
        print('count %d class %d: %s length %.6f loss %.4f' % (n, n % b['c'], b['id'], b['lam'], Z.loss_of(b['c'], b['f'], n, b['lam'])))
    return 0


def _zones(dirs):
    """the shortest zone of every (c, f, count) in the zone files of these dirs"""
    import glob
    best = {}
    for d in dirs:
        for p in sorted(glob.glob(d + '/zone-*.pkl')):
            r = pickle.load(open(p, 'rb')); key = (r['c'], round(r['f'], 4), r['count'])
            if key not in best or r['lam'] < best[key]['lam'] - 1e-9: best[key] = r
    return best


def cmd_report(a):
    """classfill.py report LIBWORK OUTDIR [OUTDIR ...]   the best zone of every class and f in the zone files, beside
    the library's best zone of that class at that f."""
    import zone_search as Z
    T = Table(_lib(a[0])); best = _zones(a[1:])
    by = collections.defaultdict(list)
    for (c, f, n), r in best.items(): by[(c, f, n % c)].append((Z.loss_of(c, f, n, r['lam']), n, r))
    print('c\tf\tclass\tbest loss here\tcount\tlength\tlibrary\tlibrary id\there minus library\thow')
    for (c, f, cl) in sorted(by):
        ls, n, r = min(by[(c, f, cl)], key=lambda t: t[0])
        hv, ids = T.have(c, f)
        print('%d\t%.4f\t%d\t%.4f\t%d\t%.6f\t%s\t%s\t%s\t%s' % (c, f, cl, ls, n, r['lam'], '%.4f' % hv[cl] if math.isfinite(hv[cl]) else '-', ids[cl] or '-',
              '%+.4f' % (ls - hv[cl]) if math.isfinite(hv[cl]) else 'new', r['how']))
    return 0


def cmd_merge(a):
    """classfill.py merge LIBWORK NEWWORK IDS.txt OUTDIR [OUTDIR ...] [--span 0.05] [--gain 0.005] [--tag cf]
    The zones of the zone files that lose at least --gain less than the library's best zone of their class at their
    f, as modules (a table on the grid of modules.py, and a dense twin walked by 0.001), added to the library."""
    import zone_search as Z
    work, new, idfile = a[:3]
    opt = [i for i, x in enumerate(a) if x.startswith('--')]
    dirs = a[3:opt[0]] if opt else a[3:]
    M.SPAN = _opt(a, '--span', 0.05); gain = _opt(a, '--gain', 0.005); tag = _opt(a, '--tag', 'cf', str)
    T = Table(_lib(work)); best = _zones(dirs)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    byid = {q['id']: q for q in lib['mods']}; have = set(byid); ids = []
    for (c, f, n) in sorted(best):
        r = best[(c, f, n)]; ls = Z.loss_of(c, f, n, r['lam']); hv = T.have(c, f)[0][n % c]
        if not ls < hv - gain: continue
        name = '%s%d-%df%04d%s' % (tag, c, n, round(f * 1e4), 's' if r.get('twin') else '')
        if name + ('.F1~' if r.get('twin') else '.F1') in have: continue
        b = byid.get(r['base']['id'])                   # a zone made from a module the generator may not use is not used either
        if not ((b is None and r['base']['licence'] == 'our own') or (b is not None and M.usable(b))):
            print(name, 'skipped: made from', r['base']['id'], r['base']['licence']); continue
        q = Z.as_module(r['P'], c, f, r['lam'], name + '.F1', r['how'], r['base']); q['ours'] = True
        if r.get('twin'):                               # a swept slid twin: the module of the twin with the new squares,
            tw = byid.get(r['twin'])                     # so it keeps its arm, its lean, its slide and its need
            if tw is None: print(name, 'skipped: the library does not hold the twin', r['twin']); continue
            sig, grp, rig = Z.signature(np.array(r['P'], float), c, f, tw['lean'])
            v = dict(tw); v.pop('walk', None); v.pop('walk_span', None)
            v.update(n=0, m=0, k=0, f0=float(f), tag='z', P=np.array(r['P'], float), grp=grp, rig=rig, count=len(r['P']),
                     len0=float(r['lam']), loss0=ls, tilt0=q['tilt0'], sig=sig, id=name + '.F1~', how=r['how'], src=q['src'],
                     licence=q['licence'], ours=True)
            q = v
        t = M.tabulate(q)
        if t.get('knots') is None: print(name, 'no table'); continue
        lib['mods'].append(q); lens[q['id']] = t; ids.append(q['id'])
        d = dict(q); d['id'] = name + ('.F1d~' if r.get('twin') else '.F1d'); d['walk'] = 0.001; d['walk_span'] = 0.03
        td = M.tabulate(d)
        if td.get('knots') is not None: lib['mods'].append(d); lens[d['id']] = td; ids.append(d['id'])
        print('%s count %d class %d f %.4f loss %.4f (library %s): table from f %.4f to %.4f' % (
            q['id'], n, n % c, f, ls, '%.4f' % hv if math.isfinite(hv) else 'none', t['lock'], t['knots'][0][-1]), flush=True)
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    open(idfile, 'w').write('\n'.join(ids) + '\n')
    print('%d modules added' % len(ids))
    return 0


def cmd_fresh(a):
    """classfill.py fresh QUEUE.tsv[,QUEUE.tsv...] RESULTS_DIR DETAILS.csv OUT.tsv [--takes TAKEDIR ...]
    The rows of a queue of modules.py that no earlier round built (RESULTS_DIR/modules-r*.tsv; a dense twin of a far
    zone counts as the same zone), with the predicted side less the bar: the lower of held and every take dir."""
    import glob
    qs, results, details, out = a[0].split(','), a[1], a[2], a[3]
    takes = a[a.index('--takes') + 1:] if '--takes' in a else []
    zid = lambda x: x[:-1] if x.endswith('d') else x
    built = collections.defaultdict(list)
    for p in sorted(glob.glob(results + '/modules-r*.tsv')):
        for r in csv.DictReader(open(p), delimiter='\t'):
            try: built[(int(r['n']), r['corner'], zid(r['far1']), zid(r['far2']), int(r['stacks1']), int(r['stacks2']))].append(r.get('built_minus_held', ''))
            except (KeyError, ValueError): pass
    bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}; who = {}
    for d in takes:
        if not os.path.exists(d + '/take.tsv'): continue
        for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
            if r['n'].isdigit() and float(r['new']) < bar.get(int(r['n']), 1e9): bar[int(r['n'])] = float(r['new']); who[int(r['n'])] = os.path.basename(d.rstrip('/'))
    rows = []; head = None; seen = set(); nb = 0
    for q in qs:
        for r in csv.DictReader(open(q), delimiter='\t'):
            head = head or list(r)
            key = (int(r['n']), r['corner'], zid(r['far1']), zid(r['far2']), int(r['stacks1']), int(r['stacks2']))
            if key in seen: continue
            seen.add(key)
            if key in built: nb += 1; continue
            n = key[0]; r['predicted_minus_bar'] = '%+.6f' % (float(r['predicted_side']) - (1 + bar[n]) * math.sqrt(n)); r['bar_from'] = who.get(n, 'held')
            rows.append(r)
    rows.sort(key=lambda r: float(r['predicted_minus_bar']))
    with open(out, 'w') as h:
        h.write('\t'.join(head + ['predicted_minus_bar', 'bar_from']) + '\n')
        for r in rows: h.write('\t'.join(str(r[k]) for k in head + ['predicted_minus_bar', 'bar_from']) + '\n')
    print('%d rows in the queue, %d built in an earlier round, %d fresh on %d n' % (len(seen), nb, len(rows), len({r['n'] for r in rows})))
    return 0


def cmd_builds(a):
    """classfill.py builds OUT.tsv RAWDIR [RAWDIR ...]   one row per build record (NAME.json of `modules.py job`)."""
    import glob
    rows = []
    for d in a[1:]:
        for p in sorted(glob.glob(d + '/*.json')):
            j = json.load(open(p)); ids = [q['id'] for q in j.get('modules', [])] + ['', '', '']
            rows.append((j['n'], os.path.basename(p)[:-5], ids[0], ids[1], ids[2], j['stacks'][0], j['stacks'][1], j['held'], j['predicted'], j.get('start'), j.get('built')))
    rows.sort()
    with open(a[0], 'w') as h:
        h.write('n\tname\tcorner\tfar1\tfar2\tstacks1\tstacks2\theld_side\tpredicted_side\tstart_side\tbuilt_side\tpredicted_minus_held\tbuilt_minus_held\n')
        for r in rows:
            b = r[10]
            h.write('%d\t%s\t%s\t%s\t%s\t%d\t%d\t%.9f\t%.6f\t%s\t%s\t%+.6f\t%s\n' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8],
                    '%.6f' % r[9] if r[9] else '', '%.9f' % b if b else '', r[8] - r[7], '%+.9f' % (b - r[7]) if b else ''))
    print('%d builds' % len(rows))
    return 0


def cmd_base(a):
    """classfill.py base LIBWORK OUT.pkl F C   the start states of `zone_search.py search`, as zone_search.cmd_base makes
    them, but from every far zone we may use: also the zones cut from our own takes and the lattice tapers. zone_search
    takes held and public zones only, so its base is empty at an f where the library has only our own zones."""
    import zone_search as Z
    work, out, f, c = a[0], a[1], float(a[2]), int(a[3])
    lib = pickle.load(open(work + '/library.pkl', 'rb'))
    res = []
    for q in lib['mods']:
        if q['kind'] != 'far' or q['c'] != c or q['miss'] or abs(q['f0'] - f) > 0.04: continue
        if not (q['tag'] in ('h', 'z') or q.get('ours') or any(k in q['licence'] for k in M.OK_LICENCE)): continue
        at = M.far_at(q, f)
        if at is None: continue
        lam, P = at
        if q['lean'] != -1: P = np.c_[c - 1 + f - P[:, 0], P[:, 1], -P[:, 2]]
        r = Z.compact(P, c, f, lam)
        if r is None: continue
        le = Z.length(r[1], c, f, r[0] + 1e-7)
        if le is None: continue
        res.append(dict(id=q['id'], src=q['src'], licence=q['licence'], sig=q['sig'], count=q['count'], c=c, f=f, lam=le[0], P=r[1]))
        print('%s %s count %d length %.6f loss %.4f' % (q['id'], q['sig'], q['count'], le[0], Z.loss_of(c, f, q['count'], le[0])), flush=True)
    pickle.dump(res, open(out, 'wb'))
    return 0


def cmd_sweeps(a):
    """classfill.py sweeps LOGDIR LIST.txt OUT.tsv   one row per hop search at the f of an n (LOGDIR/search-hNcCnK.log of
    `zone_search.py search`; LIST.txt has the lines `arm f squares n ...` the searches were started from). The loss
    at the start is the lowest loss of the seeds (library zones carried to f, lattice tapers); a search gains only
    when its last zone came out of the hops."""
    import glob, re
    logs, lst, out = a[:3]
    f = {}
    for l in open(lst):
        v = l.split()
        if len(v) >= 4: f[(int(v[3]), int(v[0]), int(v[2]))] = v[1]
    rows = []
    for p in sorted(glob.glob(logs + '/search-h*.log')):
        m = re.match(r'h(\d+)c(\d+)n(\d+)$', os.path.basename(p)[len('search-'):-4])
        if not m: continue
        n, c, cnt = map(int, m.groups())
        best = [l for l in open(p) if ' BEST ' in l]; done = [l for l in open(p) if ' DONE count ' in l]
        ff = f.get((n, c, cnt), '')
        if not best: rows.append((n, c, ff, cnt, '', '', '', 'no seed of this count', '')); continue
        loss = lambda l: float(re.search(r'loss ([\d.]+)', l).group(1))
        seeds = [loss(l) for l in best if 'then hops' not in l]
        end = loss((done or best)[-1]); hopped = 'then hops' in (done or best)[-1]
        how = re.search(r'how (.*?) cpu', done[-1]).group(1) if done else 'stopped before the end'
        sec = re.search(r'cpu (\d+) s', done[-1]).group(1) if done else ''
        rows.append((n, c, ff, cnt, '%.4f' % min(seeds), '%.4f' % end, '%.4f' % (min(seeds) - end) if hopped else '0.0000', how, sec))
    with open(out, 'w') as h:
        h.write('n\tarm\tf\tsquares\tclass\tbest_seed_loss\tloss_at_end\tgain_of_the_hops\thow\tcpu_seconds\n')
        for n, c, ff, cnt, s0, s1, g, how, sec in sorted(rows):
            h.write('%d\t%d\t%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n' % (n, c, ff, cnt, cnt % c, s0, s1, g, how, sec))
    seeded = [r for r in rows if r[4]]
    print('%d searches, %d with a seed, %d ran to the end, %d where the hops gained' % (
        len(rows), len(seeded), sum(1 for r in seeded if r[8]), sum(1 for r in seeded if float(r[6]) > 0.0005)))
    return 0


def cmd_sweepall(a):
    """classfill.py sweepall BASE.pkl OUTDIR [--classes 4,7] [--top 5] [--seconds 90] [--seed 810] [--deadline FILE]
    The kind sweep of zone_search.py (change the kind of every square in turn, keep what shortens the zone) on the
    --top zones of lowest loss of every class of BASE.pkl. `zone_search.py search` sweeps only the shortest zone of
    one count; a class holds zones of several counts, and a zone that is second before the sweep may be first after
    it. A zone that ends shorter than every base zone of its count is saved as a zone file for `report` and `merge`."""
    import zone_search as Z
    base = pickle.load(open(a[0], 'rb')); outdir = a[1]
    cls = [int(v) for v in _opt(a, '--classes', '', str).split(',') if v]
    top = _opt(a, '--top', 5, int); seconds = _opt(a, '--seconds', 90.0); seed = _opt(a, '--seed', 810, int)
    dl = _opt(a, '--deadline', None, str)
    if not base: print('empty base'); return 0
    c, f = base[0]['c'], base[0]['f']
    short = {}; by = collections.defaultdict(list)
    for b in base:
        short[b['count']] = min(short.get(b['count'], math.inf), b['lam'])
        by[b['count'] % c].append((Z.loss_of(c, f, b['count'], b['lam']), b))
    j = 0
    for cl in sorted(by):
        if cls and cl not in cls: continue
        v = sorted(by[cl], key=lambda t: t[0]); pick = []
        for ls, b in v:                                  # the same zone under two names is swept once
            if any(b['count'] == q['count'] and abs(b['lam'] - q['lam']) < 1e-5 for _, q in pick): continue
            pick.append((ls, b))
            if len(pick) >= top: break
        for ls, b in pick:
            if dl and os.path.exists(dl) and time.time() > float(open(dl).read().strip()) - seconds: return 0
            t0 = time.time(); cpu0 = time.process_time()
            lam, P, kept = Z.sweep(b['P'], c, f, b['lam'], until=t0 + seconds)
            le = Z.length(P, c, f, lam + 1e-7) if kept else None
            end = Z.loss_of(c, f, b['count'], le[0]) if le else ls
            print('c=%d f=%.4f class %d: %s count %d loss %.4f -> %.4f (%d kinds changed, %.0f s); best of the class %.4f%s' % (
                c, f, cl, b['id'], b['count'], ls, end, kept if le else 0, time.time() - t0, v[0][0],
                '  BELOW THE CLASS by %.4f' % (v[0][0] - end) if end < v[0][0] - 5e-4 else ''), flush=True)
            if le is None or not le[0] < short[b['count']] - 1e-9: continue
            j += 1
            Z._save(outdir, 'zone-%d-s%d' % (b['count'], seed + j), dict(
                lam=le[0], gap=le[1], P=P, how='library zone %s carried to f, then a sweep of the kinds' % b['id'],
                base=dict(id=b['id'], src=b['src'], licence=b['licence']), c=c, f=f, count=b['count'], seed=seed + j,
                cpu=time.process_time() - cpu0))
    return 0


def cmd_wide(a):
    """classfill.py wide CELLS.tsv [--short 0.25] [--gap 2e-5]   one line `arm f classes n,n,...` for every arm size
    and held f where a far zone of some class is at most --short squares above its break-even loss (the cells of
    `classfill.py cells`), for n that trail the board by --gap of score or more. The input of `sweepall`."""
    lim = _opt(a, '--short', 0.25); gap = _opt(a, '--gap', 2e-5)
    by = collections.defaultdict(lambda: (set(), set(), [math.inf]))
    for r in csv.DictReader(open(a[0]), delimiter='\t'):
        try: sh = float(r['short'])
        except ValueError: continue
        if sh > lim or float(r['score_gap']) < gap: continue
        cl, ns, best = by[(int(r['c']), '%.4f' % float(r['f_held']))]
        cl.add(int(r['class'])); ns.add(int(r['n'])); best[0] = min(best[0], sh)
    for (c, f), (cl, ns, best) in sorted(by.items(), key=lambda kv: kv[1][2][0]):
        print(c, f, ','.join(str(v) for v in sorted(cl)), ','.join(str(v) for v in sorted(ns)), '%.3f' % best[0])
    return 0


class _Slid:
    """zone_search.py holds the rest on the grid beside a far zone. Inside this block it holds the rest of a slid twin
    instead: the cells of the row beside the strip stand where the layout has them (the `slide` and `g` of the twin), as
    modules.far_state places them. `mod_of` hands that slide to the exact test and to the LP. The soft energy knows
    only walls and fixed squares, so it gets those cells as fixed squares, and its wall one cell further out, on the
    face of the next row of the rest, which is on the grid."""

    def __init__(self, Z, tw):
        self.Z = Z; self.sl = tw.get('slide'); self.g = float(tw.get('g', 0.0)); self.miss = [tuple(v) for v in tw['miss']]

    def __enter__(self):
        Z, sl, g, miss = self.Z, self.sl, self.g, self.miss
        self.old = (Z.mod_of, Z.soft)
        off = (lambda j: float(sl[j]) if j < len(sl) else g) if sl is not None else (lambda j: 0.0)
        Z.mod_of = lambda c, lean=-1: dict(c=c, lean=lean, miss=miss, rig=[], slide=sl, g=g)

        def soft(P, c, f, lam, lean=-1, delta=Z.DELTA, maxiter=200):
            t, p, W = Z.geom(c, f)
            J = int(math.ceil(lam + c * math.sin(t) + 2.5))
            cells = [(W + .5, .5 + j + off(j), 0.0) for j in range(J) if (0, j) not in miss]
            S = np.vstack([M.stack_squares(c, lean * math.degrees(t), W / 2, lam + p / 2), np.array(cells).reshape(-1, 3)])
            S[:, 2] = np.radians(S[:, 2])
            X = np.array(P, float); X[:, 2] = np.radians(X[:, 2]); nz = len(X)
            E0, _ = Z.soft_energy(X.ravel(), nz, S, W + 1.0, delta)
            if E0 <= Z.EPS: return np.array(P, float), E0
            r = Z.minimize(Z.soft_energy, X.ravel(), args=(nz, S, W + 1.0, delta), jac=True, method='L-BFGS-B',
                           options={'maxiter': maxiter, 'ftol': 1e-30, 'gtol': 1e-14})
            Q = r.x.reshape(nz, 3).copy(); Q[:, 2] = np.degrees(Q[:, 2])
            return Q, float(r.fun)
        Z.soft = soft
        return self

    def __exit__(self, *e):
        self.Z.mod_of, self.Z.soft = self.old


def cmd_own(a):
    """classfill.py own LIBWORK OUTDIR IDS.txt [--seconds 120] [--part I/K] [--deadline FILE] [--seed 830] [--no-twins] [--control] [--hops S] [--f F]
    The kind sweep on far zones at the f of their own layout. Every far module named in IDS.txt (one id per line, as
    `modules.py grow` writes them; corners and unknown ids are passed over) is carried to its own f0 as `base` does and
    swept with zone_search.sweep. This is the recipe that certified 703, for layouts that are new. A zone that ends
    shorter is saved as a zone file in OUTDIR/ID, for `merge`. --seconds is a limit on the clock: on a loaded box a sweep
    that reaches it has not tried every square, and its line says CUT.

    A zone whose layout holds its slid twin (ID~, the rest moved off the grid beside it) is swept as the twin: the
    start is the state of the twin, the slid cells stand beside it as fixed squares (_Slid), and its line says SLID
    TWIN. Its state on the grid is longer than the zone the layout holds, so a gain on the grid is not a gain of
    the layout (602 and 760 showed it). --no-twins passes such a zone over, as round 17 did.

    --control: before the sweep, the kind of one square is changed so that the zone is longer (a broken start). The
    sweep has to come back to the first length; the line says CONTROL and what it found.

    --hops S: zone_search.hops for S seconds in place of the sweep alone (its sweep first, then hops: a shake, one
    square to a pocket, a snap, a change of kind of one square or of two neighbours). The line says HOPS.

    --f F: sweep every zone at F in place of its own f0 (a library zone that a layout holds at another f, such as a
    near end of a block corner). The zone file keeps F, and `merge` tabulates around it."""
    import contextlib
    import zone_search as Z
    work, outdir, idfile = a[:3]
    seconds = _opt(a, '--seconds', 120.0); seed = _opt(a, '--seed', 830, int); dl = _opt(a, '--deadline', None, str)
    twins = '--no-twins' not in a; control = '--control' in a; hop_s = _opt(a, '--hops', 0.0); f_at = _opt(a, '--f', None, float)
    pi, pk = (int(v) for v in _opt(a, '--part', '0/1', str).split('/'))
    want = [l.strip() for l in open(idfile) if l.strip()]
    lib = pickle.load(open(work + '/library.pkl', 'rb')); byid = {q['id']: q for q in lib['mods']}
    far = [z for z in want if z in byid and byid[z]['kind'] == 'far' and not z.endswith('~')]
    for i, zid in enumerate(far):
        if i % pk != pi: continue
        if dl and os.path.exists(dl) and time.time() > float(open(dl).read().strip()) - seconds: break
        q = byid[zid]; c, f, n = q['c'], q['f0'], q['count']
        if f_at is not None: f = f_at
        head = '%s c=%d f=%.6f count %d class %d' % (zid, c, f, n, n % c)
        if q['miss']: print(head + ': holds cells of the rest, passed over', flush=True); continue
        tw = byid.get(zid + '~'); lean = -1; note = ''
        if tw is not None and (not twins or tw['miss'] or tw['count'] != n):   # the layout holds the slid twin; the strip state is longer
            print(head + ': the layout holds the slid twin of this zone (loss %.4f), passed over' % q['loss0'], flush=True); continue
        if tw is not None: lean = tw['lean']; note = '  SLID TWIN (as cut %.4f)' % q['loss0']
        with (_Slid(Z, tw) if tw is not None else contextlib.nullcontext()):
            st = None; at = M.far_at(tw if tw is not None else q, f)
            if at is not None:
                lam, P = at
                if tw is None and q['lean'] != -1: P = np.c_[c - 1 + f - P[:, 0], P[:, 1], -P[:, 2]]
                r = Z.compact(P, c, f, lam, lean)
                le = Z.length(r[1], c, f, r[0] + 1e-7, lean) if r is not None else None
                if le is not None: st = (le[0], r[1])
            if st is None: print(head + ': no state in the strip (the rest is not on the grid beside it)', flush=True); continue
            t0 = time.time(); cpu0 = time.process_time(); first = st
            if control:                                      # a broken start: one square of the other kind, the zone longer
                ft = lean * math.degrees(Z.geom(c, f)[0]); bad = None
                for j in np.argsort(-Z.slab(st[1], c, f, lean)):
                    Q = st[1].copy(); ang = ((Q[j, 2] + 45) % 90) - 45
                    Q[j, 2] = ft if abs(ang) < abs(ang - ft) else 0.0
                    r = Z.settle_zone(Q, c, f, st[0] + 0.12, lean)
                    if r is not None and r[0] > st[0] + 1e-3: bad = (r[0], r[1], int(j)); break
                if bad is None: print(head + ': CONTROL has no broken start (no single change makes the zone longer)', flush=True); continue
                st = bad[:2]
                note += '  CONTROL: square %d changed kind, start loss %.4f, the zone before it %.4f' % (bad[2], Z.loss_of(c, f, n, bad[0]), Z.loss_of(c, f, n, first[0]))
            if hop_s > 0:                                    # the sweep, then hops (shake, a square to a pocket, snap, flip) to the limit
                lam, P, tried, won = Z.hops(st[1], c, f, st[0], hop_s, np.random.default_rng(seed + i), lean)
                kept = sum(won.values()); note += '  HOPS %d tried, shorter by %s' % (tried, ','.join('%s:%d' % kv for kv in sorted(won.items())) or 'none')
            else:
                lam, P, kept = Z.sweep(st[1], c, f, st[0], lean=lean, until=t0 + seconds)
            le = Z.length(P, c, f, lam + 1e-7, lean) if kept else None
        a0 = Z.loss_of(c, f, n, st[0]); a1 = Z.loss_of(c, f, n, le[0]) if le else a0
        cut = '  CUT at the limit of %.0f s, the pass is not whole' % seconds if time.time() - t0 >= seconds - 0.5 and not hop_s else ''
        print('%s loss %.4f -> %.4f (%d kinds changed, %.0f s)%s%s%s' % (
            head, a0, a1, kept if le else 0, time.time() - t0, note, '  GAIN %.4f' % (a0 - a1) if a0 - a1 > 5e-4 and not control else '', cut), flush=True)
        if control or le is None or not le[0] < st[0] - 1e-9: continue
        rec = dict(lam=le[0], gap=le[1], P=P, how='library zone %s at %s, then a sweep of the kinds' % (zid, 'the f of its layout' if f_at is None else 'f %.6f' % f),
                   base=dict(id=zid, src=q['src'], licence=q['licence']), c=c, f=f, count=n, seed=seed, cpu=time.process_time() - cpu0)
        if tw is not None:
            rec.update(twin=tw['id'], how='library zone %s (the slid twin, the rest slid beside it) at the f of its layout, then a sweep of the kinds' % tw['id'],
                       base=dict(id=tw['id'], src=tw['src'], licence=tw['licence']))
        Z._save('%s/%s' % (outdir, zid), 'zone-%d-s%d' % (n, seed), rec)
    return 0


def cmd_twins(a):
    """classfill.py twins LIBWORK BAR.csv OUT.txt   the far zones whose layout holds their slid twin and is the bar of
    its n (its side within 2e-7 of the L of BAR.csv), smallest zone first, one id per line (the input of `own`)."""
    lib = pickle.load(open(a[0] + '/library.pkl', 'rb')); byid = {q['id']: q for q in lib['mods']}
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a[1]))}
    rows = []
    for l in lib['layouts']:
        for z in l.get('ids_slide') or []:
            q = byid.get(z)
            if q is None or q['kind'] != 'far' or not z.endswith('~') or z[:-1] not in byid: continue
            rows.append((l['s'] - bar[l['n']], q['count'], z[:-1], l['n'], q['c'], q['f0'], q.get('g', 0.0), bool(q['miss'])))
    keep = sorted((r for r in rows if abs(r[0]) < 2e-7 and not r[7]), key=lambda r: r[1])
    with open(a[2], 'w') as h: h.write(''.join(r[2] + '\n' for r in keep))
    for r in keep: print('%s n=%d arm %d f=%.6f count %d need %.4f' % (r[2], r[3], r[4], r[5], r[1], r[6]))
    print('%d far zones hold a slid twin; %d of them are in a layout that is the bar of its n (%d more hold cells of the rest)' % (
        len(rows), len(keep), sum(1 for r in rows if abs(r[0]) < 2e-7 and r[7])))
    return 0


def cmd_owns(a):
    """classfill.py owns OUT.tsv LOG [LOG ...]   one row per far zone that `own` swept (its log lines), the zones that
    moved most first."""
    import re
    pat = re.compile(r'^(\S+) c=(\d+) f=([\d.]+) count (\d+) class (\d+)(?: loss ([\d.]+) -> ([\d.]+) \((\d+) kinds changed, (\d+) s\)|: (.*))')
    rows = []
    for p in a[1:]:
        for l in open(p):
            m = pat.match(l.strip())
            if not m: continue
            z, c, f, n, cl, l0, l1, k, sec, why = m.groups()
            if 'CONTROL' in l: continue
            why = why or ('swept as the slid twin' if 'SLID TWIN' in l else '') + (' (cut at the limit)' if 'CUT at' in l else '')
            rows.append((z, int(c), f, int(n), int(cl), l0 or '', l1 or '', '%.4f' % (float(l0) - float(l1)) if l0 else '', k or '', sec or '', why.strip()))
    rows.sort(key=lambda r: (-float(r[7] or -1), r[0]))
    with open(a[0], 'w') as h:
        h.write('zone\tarm\tf\tsquares\tclass\tloss_before\tloss_after\tgain\tkinds_changed\tseconds\tnote\n')
        for r in rows: h.write('\t'.join(str(v) for v in r) + '\n')
    sw = [r for r in rows if r[5]]
    print('%d zones, %d swept, %d moved, %d by 0.002 squares or more' % (len(rows), len(sw), sum(1 for r in sw if int(r[8])), sum(1 for r in sw if float(r[7]) >= 0.002)))
    return 0


if __name__ == '__main__':
    cmds = dict(own=cmd_own, owns=cmd_owns, twins=cmd_twins, sweepall=cmd_sweepall, wide=cmd_wide, table=cmd_table, cells=cmd_cells, ccells=cmd_ccells, pairs=cmd_pairs, drop=cmd_drop, taper=cmd_taper, have=cmd_have, seed=cmd_seed,
                report=cmd_report, merge=cmd_merge, fresh=cmd_fresh, builds=cmd_builds, sweeps=cmd_sweeps, base=cmd_base)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]) or 0)
