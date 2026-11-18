#!/usr/bin/env python3
"""Far zones for the dear count classes from the far zones we hold: one or two rows of uprights under a zone.

  farend_rows.py make LIBWORK NEWWORK OUT.tsv [--c 8,9] [--rows 1,2] [--margin 0.03] [--per 2]
  farend_rows.py show LIBWORK C F              the lowest loss of every class at F, with and without the rows

A row of c - 1 uprights on the end wall under a far zone of an arm of c gives a far zone of the class below. It adds
c - 1 squares and one unit of length, so the loss rises by g = c cos t - (c - 1), which is 0.29 squares for an arm
of 8 at f = 0.70. The lattice count of zone_search.py holds such rows for lattice tapers only. A far zone that was
cut from a built layout is often 0.2 to 0.35 squares under the taper of its class, and the library holds no copy of
it with a row under it. `make` adds those copies where they are below what the library holds in the class at some f:

  for every arm size, every f of a grid and every class, the lowest loss the library holds (from the tabulated
  lengths of lens.pkl); a zone with R rows is kept when it is --margin or more below that at one f or more, the
  --per best of each (arm size, class, f).

The new module is the old one moved up by R with the rows under it. Its length at every f is the old length plus R,
so its table is copied and no LP runs. Ids: old id + '+rR'. NEWWORK gets library.pkl, lens.pkl and farend-ids.txt
(the list for `modules.py queue --need`).

Our own code. Reads the library pickles of modules.py as data and changes neither file.
"""
import collections, math, os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M

FS = np.round(np.arange(0.60, 0.9901, 0.01), 2)


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


def plain_far(lib, lens, cs):
    """-> [(module, fs, lengths)] for the far zones a row can go under: tabulated, no slide and no cells of the rest"""
    out = []
    for q in lib['mods']:
        if q.get('kind') != 'far' or q['c'] not in cs: continue
        t = lens.get(q['id'])
        if t is None or t.get('knots') is None: continue
        if q['id'].endswith('~') or q.get('poke') or q.get('slide') is not None or q['miss'] or q.get('walk'): continue
        if not M.usable(q): continue
        out.append((q, np.asarray(t['knots'][0], float), np.asarray(t['knots'][1], float)))
    return out


def loss_table(far, c):
    """-> (zones of arm c, loss[zone, f] with nan outside the table of a zone, g[f])"""
    Z = [z for z in far if z[0]['c'] == c]
    cost = np.array([c * math.cos(M.flush_tilt(c, float(f))) for f in FS])
    A = np.full((len(Z), len(FS)), np.nan)
    for i, (q, fs, ls) in enumerate(Z):
        ok = (FS >= fs[0] - 1e-9) & (FS <= fs[-1] + 1e-9)
        if ok.any(): A[i, ok] = cost[ok] * np.interp(FS[ok], fs, ls) - q['count']
    return Z, A, cost - (c - 1)


def with_rows(q, R):
    """the module q with R rows of c - 1 uprights under it"""
    c = q['c']; P = np.array(q['P'], float); P[:, 1] += R
    rows = np.array([(0.5 + i, 0.5 + r, 0.0) for r in range(R) for i in range(c - 1)])
    v = dict(q)
    v['P'] = np.vstack([P, rows]); v['grp'] = np.r_[np.asarray(q['grp'], int), np.zeros(len(rows), int)]
    v['count'] = q['count'] + R * (c - 1); v['len0'] = q['len0'] + R
    v['loss0'] = c * math.cos(math.radians(q['tilt0'])) * v['len0'] - v['count']
    head, _, tail = q['sig'].partition('|u')
    up, _, more = tail.partition('|')
    v['sig'] = '%s|u%d%s' % (head, int(up) + len(rows), '|' + more if more else '')
    v['id'] = '%s+r%d' % (q['id'], R)
    v['src'] = 'farend_rows.py: %d row(s) of %d uprights under far zone %s <%s>' % (R, c - 1, q['id'], q['src'])
    v['how'] = 'rows'
    return v


def cmd_make(a):
    work, new, out = a[:3]
    cs = [int(x) for x in _opt(a, '--c', '8,9', str).split(',')]
    Rs = [int(x) for x in _opt(a, '--rows', '1,2', str).split(',')]
    margin = _opt(a, '--margin', 0.03); per = _opt(a, '--per', 2, int)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    far = plain_far(lib, lens, cs)
    have = set(q['id'] for q in lib['mods'])
    made = {}; lines = []
    for c in cs:
        Z, A, g = loss_table(far, c)
        cls = np.array([q['count'] % c for q, _, _ in Z])
        low = np.full((c, len(FS)), np.inf)
        for r in range(c):
            if (cls == r).any(): low[r] = np.nanmin(np.where(np.isnan(A[cls == r]), np.inf, A[cls == r]), axis=0)
        for R in Rs:
            B = A + R * g[None, :]                                  # the loss with R rows
            tcls = (cls + R * (c - 1)) % c
            for r in range(c):
                rows = np.nonzero(tcls == r)[0]
                if not len(rows): continue
                for j in range(len(FS)):
                    col = B[rows, j]
                    order = [rows[k] for k in np.argsort(np.where(np.isnan(col), np.inf, col))[:per]]
                    for i in order:
                        if not np.isfinite(B[i, j]) or B[i, j] > low[r, j] - margin: continue
                        q = Z[i][0]; vid = '%s+r%d' % (q['id'], R)
                        if vid in have: continue
                        gain = low[r, j] - B[i, j]
                        if vid not in made or gain > made[vid][1]: made[vid] = (i, gain, float(FS[j]), R, c, float(B[i, j]), float(low[r, j]))
    ids = []
    for vid in sorted(made, key=lambda k: -made[k][1]):
        i, gain, f, R, c, ls, lw = made[vid]
        Z, _, _ = loss_table(far, c)
        q, fs, lsn = Z[i]
        v = with_rows(q, R)
        t = lens[q['id']]
        lib['mods'].append(v)
        lens[vid] = dict(id=vid, own=None if t.get('own') is None else t['own'] + R, knots=(np.array(fs), np.array(lsn) + R), lock=t['lock'])
        ids.append(vid)
        lines.append('%d\t%d\t%d\t%s\t%d\t%.2f\t%.3f\t%.3f\t%+.3f\t%.4f\t%.4f' % (c, v['count'] % c, v['count'], vid, R, f, ls, lw, -gain, fs[0], fs[-1]))
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    open(new + '/farend-ids.txt', 'w').write(''.join(i + '\n' for i in ids))
    with open(out, 'w') as h:
        h.write('c\tclass\tcount\tid\trows\tf_of_largest_gain\tloss_there\tlibrary_lowest_there\tless_library\ttable_from_f\ttable_to_f\n')
        h.write('\n'.join(lines) + '\n')
    print('zones with rows added: %d (library now %d modules)' % (len(ids), len(lib['mods'])))
    by = collections.Counter((int(l.split('\t')[0]), int(l.split('\t')[1])) for l in lines)
    print('by arm and class:', ' '.join('%d/%d: %d' % (k[0], k[1], v) for k, v in sorted(by.items())))
    return 0


def cmd_show(a):
    work, c, f = a[0], int(a[1]), float(a[2])
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    far = plain_far(lib, lens, [c])
    Z, A, g = loss_table(far, c)
    j = int(np.argmin(np.abs(FS - f)))
    cls = np.array([q['count'] % c for q, _, _ in Z])
    print('arm %d at f = %.2f, one row costs %.3f squares' % (c, FS[j], g[j]))
    print('class\tlowest\tzone\twith 1 row\tfrom\twith 2 rows\tfrom')
    col = np.where(np.isnan(A[:, j]), np.inf, A[:, j])
    for r in range(c):
        cell = []
        for R in (0, 1, 2):
            rows = np.nonzero((cls + R * (c - 1)) % c == r)[0]
            if not len(rows) or not np.isfinite(col[rows]).any(): cell += ['-', '-']; continue
            i = rows[int(np.argmin(col[rows]))]
            cell += ['%.3f' % (col[i] + R * g[j]), Z[i][0]['id']]
        print('%d\t%s' % (r, '\t'.join(cell)))
    return 0


if __name__ == '__main__':
    cmd = {'make': cmd_make, 'show': cmd_show}.get(sys.argv[1] if len(sys.argv) > 1 else '')
    if cmd is None: print(__doc__); sys.exit(2)
    sys.exit(cmd(sys.argv[2:]))
