#!/usr/bin/env python3
"""The border step as a sweep: every pair (donor m -> target n), near misses included, then the fq quench.

literature_border.py builds only the pairs where the bare step is already below the held side. This tool
lists every pair by its margin (side of the built packing minus the held side of n, in units of side) and
quenches the near misses, because the quench gives some of the margin back.

Steps, all from the held packing of a donor m with side s = L(m):
  b1   one border: a row of floor(s)+1 squares above and a column of floor(s) beside. Side s + 1,
       up to m + 2*floor(s) + 1 squares. A target below that count drops squares from the border.
  b2   two borders. Side s + 2, up to m + 4*floor(s) + 4 squares.
  rev  the reverse: keep the k squares of a donor that lie nearest one corner (a corner window), drop the
       rest. Side t_k = the window that holds them. Every corner, every k.
A single row or a single column gives a rectangle s by s + 1, whose square side is s + 1 with fewer
squares than b1, so b1 with dropped squares covers it.

  border_sweep.py base   HELD.csv DETAILS.csv OUT.csv OUT_DETAILS.csv [TAKE_DIR ...]
  border_sweep.py enum   HELD.csv DETAILS.csv PAIRS.tsv [--max 2e-3]
  border_sweep.py rank   HELD.csv DETAILS.csv PAIRS.tsv BOARD.json RANKED.tsv [--max 3e-2] [--edge-min 0]
                         [--wall-min 2] [--both-min 0] [--dist-min 0.01] [--kinds b1] [--per-n K] [--moved PREV.csv]
  border_sweep.py near   DETAILS.csv BOARD.json RANKED.tsv TAKE_DIR [TAKE_DIR ...] [--done SEEN.txt] [--max 3e-2]
                         [--kinds b1,b2] [--wall-min 2]
  border_sweep.py starts HELD.csv DETAILS.csv PAIRS.tsv DIR [--max 2e-3] [--min-abs 1e-8] [--kinds b1,b2,rev]
                         [--min M] [--no-grid] [--per-n K] [--variants V] [--vfrom V0] [--limit N] [--edge-min E]
                         [--gaps 0,1,end]
  border_sweep.py gaps   DIR PICK.tsv [--min 1e-3]
  border_sweep.py carry  DETAILS.csv PREFIX SRC_DIR ... [--tiers 7e-3,1.1e-2] [--split 2]
  border_sweep.py quench DIR [--jobs 3] [--cap 600] [--passes 6] [--kick 1e-3 --seeds K [--sfrom K0]] [--fq PATH]
                         [--until EPOCH]
  border_sweep.py cert   HELD.csv DETAILS.csv DIR TAKE_DIR [--takes DIR ...] [--submitted DETAILS.csv]
                         [--sources BEST.tsv ...]
  border_sweep.py report TAKE_DIR [--min 1e-5] [--board BOARD.json]

HELD.csv is the file the donors are read from, and DETAILS.csv has its n, L and score (the gate's
details.csv). To sweep on top of takes that are not submitted yet, base writes the submitted file with
the smallest take of each n in place (as engine_assemble.py does) and a details table with their sides.
A take that is not below the submitted score is left out: the submitted file already holds it.
Give those two to the other commands and name the same take dirs with --takes and the submitted table
with --submitted: cert then keeps an n only below both, writes the submitted score in the held column and
names the donor's source and licence. --sources names the lane's results tables (results/*-best-*.tsv
and the other tables with n, score or new, source and licence): a donor that is a held packing then
carries the source listed for it at the score nearest above the held one, and its licence.
base also writes, for each n it replaced, the take dir (with the time of the base), the source and the licence
into OUT_DETAILS.csv; starts copies the donor's into the manifest (donor_take, donor_source, donor_licence), and
cert names a take donor from there. So a donor that another lane replaces after starts keeps the source of the
packing the corner was built on. Only a manifest from before these columns reads the take dirs at cert time.
A donor that a take made smaller opens its border step and its corner windows as plain wins (a negative
margin): starts --max -3e-9 --min-abs 3e-9 builds exactly those.

enum    lists the pairs within --max, cheapest first. A margin within 1e-8 of zero is a tie: the held n
        already is that step.
rank    reads the pairs of enum and the board's side per n (results/per-puzzle-lb-*.json), and writes one
        line per border pair and corner whose donor is not a grid: the edge count of that corner, how far
        the held side of the target is above the board's side (dist), and the same for the donor. top and
        right are the edge count by wall: the border's row goes on the top wall, its column on the right
        wall. It keeps the corners with --wall-min tilted squares or more on at least one of the two walls
        (and --edge-min on both together, --both-min on each) and the targets at least --dist-min above the
        board. It sorts each wall on its own: by the larger of the two counts (each capped at 15) times
        dist, then by the other count. In round 14 the corner of 854 -> 913 with 0 tilted squares on the
        top wall and 9 on the right gave back 6 to 10 times more than the corner with 9 and 0, and a rule
        that asks for five on each wall left both out. --moved PREV_DETAILS.csv keeps the pairs whose donor
        or target has a smaller score than in PREV_DETAILS.csv (the n that moved since that file).
        The file has a variant column, so starts builds exactly those corners.
near    reads every near layout under the take dirs (TAKE_DIR/**/near/*.csv: a lane's build of an n that
        ended a little above the held side, so it is not a take, but its layout is new). Each distinct file
        (md5; the ones listed in --done are skipped and the new ones are added to it) is the donor of b1
        and b2 to the largest n they reach. It writes the rows of rank, one per corner that passes
        --wall-min, plus the near file (near) and what made it (near_source). starts builds them on the near
        layout instead of the held donor, keeps a copy of the file in DIR, and cert names it as the donor.
starts  builds the start of each chosen pair as DIR/<id>.start.txt (fq's text format) and DIR/manifest.tsv,
        variants V0 to V - 1 (for a border, variant % 4 is the corner and variant // 4 says where the
        border's free length goes: see build).
        Held donors have a content hash in the id, so a new packing of the same n gets a new start.
        The manifest records the start digest and the retained near-donor copy. cert refuses a changed start.
        --no-grid leaves out a start whose side is within 1e-4 of a whole number: it is a plain grid with
        holes, or a window that the quench only brings back to the grid. The manifest also has
        what could explain a give-back: the donor's side fraction (frac), the tilted squares, the squares
        the build leaves loose (fewer than three contacts with a wall or a square), and the tilted squares
        on the two walls the step works on (edge). --edge-min E leaves out a border start with fewer
        than E of those. A pairs file with a variant column (rank writes one) builds only that variant.
        --gaps G,... builds, for the corner c of each row, the variants 4 * g + c instead: g = 0 is the
        even spread, g = 1 the gap at the first tilted square of each wall, and end the gap at the last one
        (the end of the donor's tilted band on that wall; one value per wall when the counts differ).
gaps    the plain corners (variant < 4) in DIR whose best chain gave back more than --min, as rows for
        starts --gaps 1,end. The rows keep the near file of a near donor.
carry   the starts of earlier dirs (another round's included) that have no record or a cut one, with their
        margin against the new DETAILS.csv (built side minus the held side of n). Each goes, with its manifest
        line, its near donor copy and its record and packing, into PREFIX<tier><letter>: the tier by --tiers
        (margin below 7e-3 is tier 1), the letter dealing the starts of a tier over --split dirs, one per
        quench process, smallest margin first (order.txt). An id in two SRC dirs (a donor that moved between
        two polls) keeps the start with the smaller margin. The chains go on from their records.
quench  runs one chain of fq on every start: default flags (loosen 2 %, compress, polish), then the deep
        flags, up to --passes rounds while the side falls. --cap is fq's own deadline per call, in seconds;
        a call that reaches it counts as no result, so keep it long on a loaded box. It needs only the
        standard library and the fq binary, so it runs on a box with nothing else. A chain is deterministic.
        --kick SIGMA --seeds K runs K more chains from the start, each after a random kick (fq moves every
        centre by SIGMA and every angle by 20 * SIGMA degrees, Gaussian); the best chain is kept. --sfrom K0
        starts at seed K0, for a start whose plain chain (seed 0) ran before. A chain writes its record
        after every round, so a chain that was killed, or cut by --until (no new round after that epoch
        second), goes on from its best packing when quench runs again on the same DIR.
cert    floatsafe on every result that ends below the held side by the take's bar, then the take rule (more
        than 1e-10 below the score of DETAILS.csv). TAKE_DIR gets <n>.csv and take.tsv, and
        TAKE_DIR/work/sweep.tsv gets one line per run with the margin before and after the quench
        (cut = 1: the chain was still falling when it was stopped).
report  reads sweep.tsv, the best run of each start: per kind, how many starts the quench moved and where
        they ended; the border starts by their edge count; with --board, the border starts on donors that
        are not grids by edge count and by the distance of the held target from the board; then every
        border start whose donor is not a plain grid and every start that gave back more than --min.
Run everything with python -I.
"""
import argparse, csv, glob, json, math, os, subprocess, sys, time

LANE = os.path.dirname(os.path.abspath(__file__))
GAP = 3e-11
TIE = 1e-8
POLISH = ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600']    # engine_fq.POLISH
FQ = os.path.join(os.environ.get('SQ_BOX', '$SCRATCH/bounties-squares'),
                  'ext/evand/search/packer/target/release/fq')


def lib():
    """numpy and the lane's helpers; the quench stage does not need them."""
    global np, load, normalize, hw
    sys.path.insert(0, LANE)
    from engine_lib import load, normalize, hw, np


def held_L(details):
    R = list(csv.DictReader(open(details)))
    return {int(r['n']): float(r['L']) for r in R}, {int(r['n']): float(r['score']) for r in R}


def enum_border(L, mx):
    """(kind, m, n, 0, side, margin, dropped) for b1 and b2, every donor within mx, and the best per n."""
    out = []
    for kind, add in (('b1', 1), ('b2', 2)):
        for m in range(2, 1000):
            f = math.floor(L[m])
            cap = m + 2 * f + 1 + (2 * (f + 1) + 1 if add == 2 else 0)
            side = L[m] + add + add * GAP
            for n in range(m + 1, min(cap, 1000) + 1):
                out.append((kind, m, n, 0, side, side - L[n], cap - n))
    best = {}
    for c in out:   # the smallest margin of each (kind, n), for the report
        k = (c[0], c[2])
        if k not in best or c[5] < best[k][5]:
            best[k] = c
    return [c for c in out if c[5] <= mx], best


def corner(A, s, q):
    """rotate the packing q quarter turns, so that each corner comes to the origin in turn."""
    B = A.copy()
    for _ in range(q):
        B = np.column_stack([s - B[:, 1], B[:, 0], B[:, 2]])
    return B


def extents(B):
    h = np.array([hw(math.radians(d)) for d in B[:, 2]])
    return np.maximum(B[:, 0] + h, B[:, 1] + h)


def enum_rev(P, L, mx):
    out, best = [], {}
    for N in sorted(P):
        if N < 3:
            continue
        s, A = normalize(P[N])
        for q in range(4):
            e = np.sort(extents(corner(A, s, q)))
            for k in range(2, N):
                if e[k] - e[k - 1] < 1e-9:      # the window that holds k squares would hold k + 1
                    continue
                c = ('rev', N, k, q, float(e[k - 1]), float(e[k - 1]) - L[k], 0)
                if k not in best or c[5] < best[k][5]:
                    best[k] = c
                if c[5] <= mx:
                    out.append(c)
    return out, {('rev', k): v for k, v in best.items()}


def wall_points(B, side, tol=1e-6):
    """x of the top corner of each tilted square on the top wall, y of the right corner of each on the right wall."""
    xs, ys = [], []
    for x, y, d in B:
        t = math.radians(d); c, s = math.cos(t), math.sin(t)
        if abs(d) <= tol:
            continue
        if y + hw(t) > side - tol:
            a, b = max(((a, b) for a in (-1, 1) for b in (-1, 1)), key=lambda q: q[0] * s + q[1] * c)
            xs.append(x + 0.5 * (a * c - b * s))
        if x + hw(t) > side - tol:
            a, b = max(((a, b) for a in (-1, 1) for b in (-1, 1)), key=lambda q: q[0] * c - q[1] * s)
            ys.append(y + 0.5 * (a * s + b * c))
    return sorted(xs), sorted(ys)


def strip(count, length, free_at=None):
    """centres of count unit squares along [0, length]: spread evenly, or pushed to the two ends so that all
    the free length is one gap over the point free_at (when a gap can reach it)."""
    k = math.floor(free_at) if free_at is not None else -1
    if 0 <= k <= count and free_at - k <= length - count:
        return [0.5 + i for i in range(k)] + [length - (count - k) + 0.5 + i for i in range(count - k)]
    return [0.5 + i * (length - 1) / max(count - 1, 1) for i in range(count)]


def build(kind, A, s, n, q, variant=0):
    """the start packing of one pair, as an array (x, y, deg). variant % 4 picks the corner that gets the
    border. variant // 4 = g places the border's free length: 0 spreads the squares evenly; g >= 1 leaves
    one gap in the row over the g-th tilted square on the top wall and one in the column beside the g-th
    tilted square on the right wall (the ends of the donor's tilted band)."""
    B = corner(A, s, q if kind == 'rev' else variant % 4)
    if kind == 'rev':
        return B[np.argsort(extents(B), kind='stable')[:n]]
    side, g = s, variant // 4
    for _ in range(1 if kind == 'b1' else 2):
        f = math.floor(side)
        row, col = f + 1, f
        last = _ == (0 if kind == 'b1' else 1)
        drop = (len(B) + row + col - n) if last else 0
        assert drop >= 0
        dr = (drop + 1) // 2
        row, col = row - dr, col - (drop - dr)
        S = side + 1 + GAP
        xs, ys = wall_points(B, side) if g else ([], [])
        new = [(x, side + GAP + 0.5, 0.0) for x in strip(row, S, xs[(g - 1) % len(xs)] if xs else None)]
        new += [(side + GAP + 0.5, y, 0.0) for y in strip(col, side, ys[(g - 1) % len(ys)] if ys else None)]
        B = np.vstack([B, np.array(new).reshape(-1, 3)])
        side = S
    assert len(B) == n, (len(B), n)
    return B


def loose(A, s, tol=1e-7):
    """how many squares touch fewer than three things (a wall or another square) within tol."""
    t = np.radians(A[:, 2]); c, si = np.cos(t), np.sin(t)
    h = (np.abs(c) + np.abs(si)) / 2
    cnt = ((A[:, 0] - h < tol).astype(int) + (A[:, 1] - h < tol) + (s - A[:, 0] - h < tol) + (s - A[:, 1] - h < tol))
    U, V = np.stack([c, si], 1), np.stack([-si, c], 1)
    C = np.stack([A[:, :2] + 0.5 * (a * U + b * V) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))], 1)
    d = np.hypot(A[:, None, 0] - A[None, :, 0], A[:, None, 1] - A[None, :, 1])
    I, J = np.nonzero(np.triu(d < 1.41422, 1))
    ax = np.stack([U[I], V[I], U[J], V[J]], 1)                  # pairs, 4 axes, 2
    pi = np.einsum('pkd,pad->pak', C[I], ax); pj = np.einsum('pkd,pad->pak', C[J], ax)
    sep = np.maximum(pj.min(2) - pi.max(2), pi.min(2) - pj.max(2)).max(1)
    np.add.at(cnt, I[sep < tol], 1); np.add.at(cnt, J[sep < tol], 1)
    return int((cnt < 3).sum())


def edge(D, s, tol=1e-6):
    """how many tilted squares touch the top or the right wall: the two walls a border goes on (D is the
    donor, turned), or the two cut sides of a corner window (D is the window)."""
    h = np.array([hw(math.radians(d)) for d in D[:, 2]])
    return int(((np.abs(D[:, 2]) > tol) & ((D[:, 0] + h > s - tol) | (D[:, 1] + h > s - tol))).sum())


def walls(D, s, tol=1e-6):
    """the edge count by wall: the tilted squares on the top wall and those on the right wall."""
    h = np.array([hw(math.radians(d)) for d in D[:, 2]])
    t = np.abs(D[:, 2]) > tol
    return int((t & (D[:, 1] + h > s - tol)).sum()), int((t & (D[:, 0] + h > s - tol)).sum())


def cmd_enum(a):
    lib()
    L, _ = held_L(a.details); P = load(a.held)
    cb, bb = enum_border(L, a.max)
    cr, br = enum_rev(P, L, a.max)
    C = sorted(cb + cr, key=lambda c: c[5])
    with open(a.pairs, 'w') as h:
        h.write('kind\tdonor\tn\tcorner\tside\tmargin\tdropped\n')
        for c in C:
            h.write('%s\t%d\t%d\t%d\t%r\t%.6e\t%d\n' % c)
    for kind, best in (('b1', bb), ('b2', bb), ('rev', br)):
        v = sorted(c[5] for k, c in best.items() if k[0] == kind)
        cnt = lambda t: sum(1 for x in v if x <= t)
        print('%s: targets %d, best margin per n: min %.3e, median %.3e; n with margin <= 0: %d, <= 5e-4: %d, '
              '<= 1e-3: %d, <= 2e-3: %d, <= 5e-3: %d, <= 1e-2: %d' % (kind, len(v), v[0], v[len(v) // 2],
              cnt(0), cnt(5e-4), cnt(1e-3), cnt(2e-3), cnt(5e-3), cnt(1e-2)))
    print('pairs within %g: %d (b1 %d, b2 %d, rev %d), distinct n %d' % (a.max, len(C),
          sum(c[0] == 'b1' for c in C), sum(c[0] == 'b2' for c in C), sum(c[0] == 'rev' for c in C),
          len({c[2] for c in C})))
    for kind in ('b1', 'b2', 'rev'):
        v = [c for c in C if c[0] == kind and abs(c[5]) > TIE]
        print('%s, ties left out:' % kind, ', '.join('<= %g: %d pairs, %d n' % (
            t, sum(c[5] <= t for c in v), len({c[2] for c in v if c[5] <= t})) for t in (0, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2)))


def wall_key(top, right, dist):
    """the rank of a corner: each wall on its own. The larger count (capped at 15) times dist, then the other."""
    hi, lo = max(min(top, 15), min(right, 15)), min(min(top, 15), min(right, 15))
    return (-hi * dist, -lo)


RANK_COLS = 'kind\tdonor\tn\tcorner\tside\tmargin\tdropped\tvariant\tedge\tdist\tdonor_dist\ttop\tright'


def cmd_rank(a):
    lib()
    L, sc = held_L(a.details); P = load(a.held)
    B = {int(r['n']): float(r['L']) for r in json.load(open(a.board))}
    moved = None
    if a.moved:
        old = held_L(a.moved)[1]
        moved = {n for n in sc if sc[n] < old[n] - 1e-10}
    kinds, E, out, seen = a.kinds.split(','), {}, [], {}
    for r in csv.DictReader(open(a.pairs), delimiter='\t'):
        mg, side, m, n = float(r['margin']), float(r['side']), int(r['donor']), int(r['n'])
        if r['kind'] not in kinds or mg <= TIE or mg > a.max or abs(side - round(side)) < 1e-4 or L[n] - B[n] < a.dist_min:
            continue
        if moved is not None and m not in moved and n not in moved:
            continue
        if m not in E:
            s, A = normalize(P[m])
            E[m] = [(edge(corner(A, s, v), s),) + walls(corner(A, s, v), s) for v in range(4)]
        for v in range(4):
            e, top, right = E[m][v]
            if e >= a.edge_min and min(top, right) >= a.both_min and max(top, right) >= a.wall_min:
                out.append((r, v, e, L[n] - B[n], L[m] - B[m], top, right))
    out.sort(key=lambda c: wall_key(c[5], c[6], c[3]) + (float(c[0]['margin']),))
    with open(a.out, 'w') as h:
        h.write(RANK_COLS + '\n')
        for r, v, e, d, dm, top, right in out:
            k = (r['kind'], r['n'])
            seen[k] = seen.get(k, 0) + 1
            if a.per_n and seen[k] > a.per_n:
                continue
            h.write('\t'.join(r[c] for c in ('kind', 'donor', 'n', 'corner', 'side', 'margin', 'dropped')) +
                    '\t%d\t%d\t%.6f\t%.6f\t%d\t%d\n' % (v, e, d, dm, top, right))
    print('rank: %d corners of %d pairs on %d n (on one wall >= %d, on each >= %d, edge >= %d, dist >= %g, '
          'margin <= %g%s)' % (len(out), len({(c[0]['kind'], c[0]['donor'], c[0]['n']) for c in out}),
                              len({c[0]['n'] for c in out}), a.wall_min, a.both_min, a.edge_min, a.dist_min, a.max,
                              ', donor or target among the %d n that moved' % len(moved) if moved is not None else ''))


def near_files(dirs):
    """every near layout under the take dirs, oldest first"""
    F = set()
    for d in dirs:
        for root, sub, files in os.walk(d):
            if os.path.basename(root) == 'near':
                F.update(os.path.join(root, f) for f in files if f.endswith('.csv'))
    return sorted(F, key=lambda f: (os.path.getmtime(f), f))


def read_near(path):
    """-> (m, s, A) of a near layout file (n, square_id, x, y, angle in radians)"""
    R = list(csv.DictReader(open(path)))
    m = int(R[0]['n'])
    R = sorted((r for r in R if int(r['n']) == m), key=lambda r: int(r['square_id']))
    assert len(R) == m, (path, len(R), m)
    s, A = normalize([(float(r['x']), float(r['y']), float(r['angle'])) for r in R])
    return m, s, A


def near_metadata(path):
    """Source and licence supplied beside a near CSV, when the donor lane writes them."""
    path = os.fspath(path)
    j = None
    for sidecar in (os.path.splitext(path)[0] + '.json', path + '.json'):
        try:
            value = json.load(open(sidecar))
        except (OSError, ValueError):
            continue
        if isinstance(value, dict):
            j = value
            break
    if j is None:
        return {}
    out = {k: j[k].replace('\t', ' ').replace('\n', ' ') for k in ('source', 'licence')
           if isinstance(j.get(k), str) and j[k]}
    # The border collector writes its immutable recipe inside a manifest.
    # Keep explicit metadata first, then recover that recipe's donor ancestry.
    manifest = j.get('manifest')
    if isinstance(manifest, dict):
        source, licence = manifest.get('donor_source'), manifest.get('donor_licence')
        if 'source' not in out and isinstance(source, str) and source:
            recipe = 'border_sweep.py %s from n=%s, corner %s, variant %s' % (
                manifest.get('kind', '?'), manifest.get('donor', '?'),
                recipe_corner(manifest) if manifest.get('kind') in ('rev', 'b1', 'b2')
                and manifest.get('corner') is not None and manifest.get('variant') is not None else '?',
                manifest.get('variant', '?'))
            out['source'] = (recipe + '; ' + source).replace('\t', ' ').replace('\n', ' ')
        if 'licence' not in out and isinstance(licence, str) and licence:
            out['licence'] = licence.replace('\t', ' ').replace('\n', ' ')
    parts = j.get('parts')
    if isinstance(parts, dict):
        donors = [p for p in parts.values() if isinstance(p, dict)]
        if 'source' not in out and any(p.get('original_file') or p.get('source_record') for p in donors):
            out['source'] = ('%s %s' % (j.get('kind', 'composition'),
                             json.dumps(parts, sort_keys=True, separators=(',', ':')))).replace('\t', ' ').replace('\n', ' ')
        licences = list(dict.fromkeys(p['licence'] for p in donors if isinstance(p.get('licence'), str) and p['licence']))
        if 'licence' not in out and licences:
            out['licence'] = '; '.join(licences).replace('\t', ' ').replace('\n', ' ')
    return out


def near_source(path, m, s, held):
    """what made a near layout, for the take table: lane, file, file time, how far above the held side"""
    p = os.path.abspath(path)
    take = next((q for q in p.split(os.sep) if q.startswith('take-')), '')
    lane = take[len('take-'):].rsplit('-r', 1)[0] if take else 'another'
    rel = p[p.index(take):] if take else p
    t = time.strftime('%H:%M UTC', time.gmtime(os.path.getmtime(path)))
    src = 'a near layout of n=%d that the %s lane wrote (file time %s, %s, %.1e above the held %d side)' % (
        m, lane, t, rel, s - held, m)
    upstream = near_metadata(path).get('source')
    return src + ('; from ' + upstream if upstream else '')


def cmd_near(a):
    import hashlib
    lib()
    L, _ = held_L(a.details)
    B = {int(r['n']): float(r['L']) for r in json.load(open(a.board))}
    done = set(open(a.done).read().split()) if a.done and os.path.exists(a.done) else set()
    kinds, out, new, seen = a.kinds.split(','), [], [], set()
    for f in near_files(a.takes):
        h = hashlib.md5(open(f, 'rb').read()).hexdigest()
        if h in seen or h in done:
            continue
        seen.add(h); new.append(h)
        try:
            m, s, A = read_near(f)
        except (AssertionError, KeyError, ValueError, IndexError) as e:
            print('near: %s unreadable (%s)' % (f, e)); continue
        W = [(edge(corner(A, s, v), s),) + walls(corner(A, s, v), s) for v in range(4)]
        for kind in kinds:
            add = 1 if kind == 'b1' else 2
            fl = math.floor(s)
            t = m + 2 * fl + 1 + (2 * (fl + 1) + 1 if add == 2 else 0)
            side = s + add + add * GAP
            if t > 1000 or abs(side - round(side)) < 1e-4:
                continue
            mg = side - L[t]
            print('near %s %d -> %d (%s): %.1e above the held %d, margin %.3e, dist %.4f, walls by corner %s, %s' % (
                h[:8], m, t, kind, s - L[m], m, mg, L[t] - B[t], [w[1:] for w in W], f))
            if mg > a.max:
                continue
            for v in range(4):
                e, top, right = W[v]
                if max(top, right) >= a.wall_min:
                    out.append(([kind, str(m), str(t), '0', repr(side), '%.6e' % mg, '0'], v, e, L[t] - B[t], L[m] - B[m],
                                top, right, f, near_source(f, m, s, L[m]).replace('\t', ' ')))
    out.sort(key=lambda c: wall_key(c[5], c[6], c[3]) + (float(c[0][5]),))
    with open(a.out, 'w') as h:
        h.write(RANK_COLS + '\tnear\tnear_source\n')
        for r, v, e, d, dm, top, right, f, src in out:
            h.write('\t'.join(r) + '\t%d\t%d\t%.6f\t%.6f\t%d\t%d\t%s\t%s\n' % (v, e, d, dm, top, right, f, src))
    if a.done:
        with open(a.done, 'a') as g:
            g.writelines(x + '\n' for x in new)
    print('near: %d new files, %d corners within %g (on one wall >= %d)' % (len(new), len(out), a.max, a.wall_min))


def write_txt(path, s, X):
    with open(path, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, d in X:
            h.write('%r %r %r\n' % (float(x), float(y), float(d)))


def read_txt(path):
    T = [l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n = int(T[0][0])
    return float(T[0][1]), [[float(v) for v in q[:3]] for q in T[1:n + 1]]


def gap_list(spec, A, s, c):
    """the g values of --gaps for corner c: 0, 1, and end (the last tilted square of each wall)"""
    xs, ys = wall_points(corner(A, s, c), s)
    G = []
    for g in spec.split(','):
        G += [k for k in (len(xs), len(ys)) if k] if g == 'end' else [int(g)]
    return sorted({g for g in G if g == 0 or g >= 1 and (xs or ys)})


def cmd_starts(a):
    import hashlib, shutil
    lib()
    L, _ = held_L(a.details); P = load(a.held)
    os.makedirs(a.dir, exist_ok=True)
    kinds, seen, rows = a.kinds.split(','), {}, []
    for r in csv.DictReader(open(a.pairs), delimiter='\t'):
        mg = float(r['margin'])
        if r['kind'] not in kinds or mg > a.max or mg <= a.min or abs(mg) <= a.min_abs:
            continue
        if a.no_grid and abs(float(r['side']) - round(float(r['side']))) < 1e-4:
            continue
        k = (r['kind'], r['n'])
        seen[k] = seen.get(k, 0) + 1
        if a.per_n and seen[k] > a.per_n:
            continue
        rows.append(r)
    rows = rows[:a.limit]
    # the donor's origin as the base had it now: a take that another lane replaces later must not rename it at cert
    O = {int(r['n']): [r.get(k) or '' for k in ('take', 'source', 'licence')] for r in csv.DictReader(open(a.details))}
    cols = ['id', 'kind', 'donor', 'n', 'corner', 'variant', 'dropped', 'held_L', 'built_L', 'margin_before', 'frac',
            'tilted', 'loose', 'edge', 'donor_take', 'donor_source', 'donor_licence', 'near', 'donor_copy', 'start_sha256']
    man = os.path.join(a.dir, 'manifest.tsv'); fresh = not os.path.exists(man)
    if not fresh:                                   # a manifest written before the donor columns keeps its columns
        cols = open(man).readline().rstrip('\n').split('\t')
        if 'donor_take' not in cols:
            print('starts: %s has no donor columns; cert will read the donors from the take dirs' % man)
        if any(r.get('near') for r in rows) and 'near' not in cols:
            sys.exit('starts: %s has no near column; give near rows a new DIR' % man)
    with open(man, 'a') as h:
        if fresh:
            h.write('\t'.join(cols) + '\n')
        for r in rows:
            m, n, q = int(r['donor']), int(r['n']), int(r['corner'])
            tag, origin, keep = '', O[m], ''
            if r.get('near'):                       # a near layout of another lane is the donor, not the held m
                m2, s, A = read_near(r['near'])
                assert m2 == m, (r['near'], m2, m)
                tag = '-' + hashlib.md5(open(r['near'], 'rb').read()).hexdigest()[:8]
                keep = os.path.join(a.dir, 'donor-%d%s.csv' % (m, tag))     # the take stands alone
                if not os.path.exists(keep):
                    shutil.copyfile(r['near'], keep)
                meta = near_metadata(r['near'])
                src = r.get('near_source') or near_source(r['near'], m, s, L[m])
                if meta.get('source') and meta['source'] not in src:
                    src += '; from ' + meta['source']
                origin = ['', src, r.get('donor_licence') or meta.get('licence') or 'ours']
            else:
                s, A = normalize(P[m])
                # A new donor must not reuse the id of an older packing of the same n.
                tag = '-' + hashlib.sha256(A.tobytes()).hexdigest()[:12]
            V = [int(r['variant'])] if r.get('variant') else list(range(a.vfrom, a.variants))
            if a.gaps:
                V = [4 * g + c for c in sorted({v % 4 for v in V}) for g in gap_list(a.gaps, A, s, c)]
            for v in V:
                pid = '%d-%s-%d%s-q%d-v%d' % (n, r['kind'], m, tag, q, v)
                path = os.path.join(a.dir, pid + '.start.txt')
                if os.path.exists(path):
                    continue
                if r['kind'] != 'rev' and edge(corner(A, s, v % 4), s) < a.edge_min:
                    continue
                X = build(r['kind'], A, s, n, q, v)
                if v >= 4 and np.array_equal(X, build(r['kind'], A, s, n, q, v % 4)):
                    continue                        # no tilted square on those walls: the same start as v % 4
                s0, A0 = normalize([(x, y, math.radians(d)) for x, y, d in X])
                write_txt(path, s0 + 1e-10, A0)
                D, sd = (A0, s0) if r['kind'] == 'rev' else (corner(A, s, v % 4), s)
                row = dict(zip(['id', 'kind', 'donor', 'n', 'corner', 'variant', 'dropped', 'held_L', 'built_L',
                                'margin_before', 'frac', 'tilted', 'loose', 'edge', 'donor_take', 'donor_source',
                                'donor_licence', 'near', 'donor_copy', 'start_sha256'],
                               [pid, r['kind'], str(m), str(n), str(q), str(v), r['dropped'], repr(L[n]), repr(float(s0)),
                                '%.4e' % (s0 - L[n]), '%.4f' % (s - math.floor(s)), str(int((np.abs(A0[:, 2]) > 1e-6).sum())),
                                str(loose(A0, s0)), str(edge(D, sd))] + [x.replace('\t', ' ') for x in origin] +
                               [os.path.abspath(r['near']) if r.get('near') else '', os.path.basename(keep),
                                hashlib.sha256(open(path, 'rb').read()).hexdigest()]))
                h.write('\t'.join(row[c] for c in cols) + '\n')
    print('starts:', len(rows), 'pairs into', a.dir, '(variants: %s)' % ('gaps ' + a.gaps if a.gaps else 'as listed'
                                                                        if rows and rows[0].get('variant') else
                                                                        '%d to %d' % (a.vfrom, a.variants - 1)))


def cmd_gaps(a):
    """the plain corners of DIR that gave back more than --min, as rows for starts --gaps"""
    collect(a.dir)
    M = list(csv.DictReader(open(os.path.join(a.dir, 'manifest.tsv')), delimiter='\t'))
    out = []
    for r in M:
        f = os.path.join(a.dir, r['id'] + '.json')
        if r['kind'] == 'rev' or int(r['variant']) >= 4 or not os.path.exists(f):
            continue
        j = json.load(open(f))
        if j['s_start'] - j['s_final'] > a.min:
            out.append((j['s_start'] - j['s_final'], r))
    out.sort(key=lambda c: -c[0])
    with open(a.out, 'w') as h:
        h.write('kind\tdonor\tn\tcorner\tside\tmargin\tdropped\tvariant\tnear\tnear_source\n')
        for g, r in out:
            h.write('\t'.join([r['kind'], r['donor'], r['n'], r['corner'], r['built_L'], r['margin_before'], r['dropped'],
                               r['variant'], r.get('near') or '', r.get('donor_source', '') if r.get('near') else '']) + '\n')
            print('gaps: %s gave back %.3e' % (r['id'], g))
    print('gaps: %d corners of %s gave back more than %g' % (len(out), a.dir, a.min))


def cmd_carry(a):
    """the starts of earlier dirs that did not finish, re-margined on a new details table, into tier dirs"""
    import shutil
    L = held_L(a.details)[0]
    tiers = [float(t) for t in a.tiers.split(',')] if a.tiers else []
    best = {}                                       # id -> (new margin, src dir, manifest line)
    for src in a.src:
        lines = open(os.path.join(src, 'manifest.tsv')).readlines()
        cols = lines[0].rstrip('\n').split('\t')
        for l in lines[1:]:
            r = dict(zip(cols, l.rstrip('\n').split('\t')))
            stem = os.path.join(src, r['id'])
            if not os.path.exists(stem + '.start.txt'):
                continue
            rec = stem + '.k0.json'
            if os.path.exists(rec) and not json.load(open(rec)).get('cut'):
                continue                            # finished
            mg = float(r['built_L']) - L[int(r['n'])]
            if r['id'] not in best or mg < best[r['id']][0]:     # the same id on two donors: the smaller margin
                best[r['id']] = (mg, src, cols, l)
    rows = sorted(best.items(), key=lambda c: c[1][0])
    out = {}
    for i, (pid, (mg, src, cols, l)) in enumerate(rows):
        t = sum(mg >= x for x in tiers) + 1
        d = '%s%d%s' % (a.out, t, chr(ord('a') + sum(1 for q in rows[:i] if sum(q[1][0] >= x for x in tiers) + 1 == t) % a.split))
        os.makedirs(d, exist_ok=True)
        man = os.path.join(d, 'manifest.tsv')
        if not os.path.exists(man):
            open(man, 'w').write('\t'.join(cols) + '\n')
        head = open(man).readline().rstrip('\n').split('\t')
        r = dict(zip(cols, l.rstrip('\n').split('\t')))
        with open(man, 'a') as h:
            h.write('\t'.join(r.get(c, '') for c in head) + '\n')
        for f in [os.path.join(src, pid + '.start.txt')] + glob.glob(glob.escape(os.path.join(src, pid)) + '.k*.json'):
            shutil.copyfile(f, os.path.join(d, os.path.basename(f)))
            if f.endswith('.json'):
                b = os.path.join(src, json.load(open(f))['best'])
                if os.path.exists(b):
                    shutil.copyfile(b, os.path.join(d, os.path.basename(b)))
        if r.get('near'):
            keep = 'donor-%s-%s.csv' % (r['donor'], pid.split('-')[3])
            if os.path.exists(os.path.join(src, keep)):
                shutil.copyfile(os.path.join(src, keep), os.path.join(d, keep))
        with open(os.path.join(d, 'order.txt'), 'a') as h:
            h.write(pid + '\n')
        out.setdefault(d, []).append(mg)
    for d in sorted(out):
        v = out[d]
        print('carry: %s %d starts, margin %.2e to %.2e' % (d, len(v), v[0], v[-1]))


def fq_call(fq, inp, out, flags, cap):
    """one fq quench -> (side, seconds); the side is None when fq failed, ran out of time or left an overlap."""
    t = time.time()
    try:
        r = subprocess.run([fq, 'quench', '--in', inp, '--out', out, '--deadline', str(cap)] + flags,
                           capture_output=True, text=True, timeout=3 * cap + 120)
        j = json.loads(r.stdout.strip().splitlines()[0]) if r.returncode == 0 else {}
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        j = {}
    ok = (os.path.exists(out) and not j.get('deadline', True) and not j.get('diverged', True)
          and j.get('min_gap', -1) > -1e-9 and j.get('min_wall', -1) > -1e-9)
    return (read_txt(out)[0] if ok else None), time.time() - t


def quench_one(b):
    """one chain from a start: seed 0 as built, seed k > 0 after a random kick -> <stem>.k<k>.json, written
    after every round (cut = True while the side still falls), so a stopped chain goes on from its record."""
    start, fq, cap, passes, kick, k, until = b
    stem = start[:-len('.start.txt')]
    rec = '%s.k%d.json' % (stem, k)
    s0 = read_txt(start)[0]
    cur, best, log, t0, p0, used = s0, start, [], time.time(), 0, 0.0
    if os.path.exists(rec):
        j = json.load(open(rec))
        if os.path.exists(os.path.join(os.path.dirname(stem), j['best'])):
            cur, best, log, p0, used = j['s_final'], os.path.join(os.path.dirname(stem), j['best']), j['log'], j.get('round', 0), j['secs']

    def save(cut, p):
        res = {'s_start': s0, 's_final': cur, 'best': os.path.basename(best), 'log': log,
               'secs': round(used + time.time() - t0, 1), 'cut': cut, 'round': p}
        with open(rec + '.tmp', 'w') as h:
            json.dump(res, h)
        os.replace(rec + '.tmp', rec)
        return res
    cut, nxt = False, p0
    for p in range(p0, passes):
        if until and time.time() > until:
            cut = True
            break
        moved = False
        for name, flags in (('d', ['--kick', repr(kick), '--seed', str(k)] if k and p == 0 else []), ('p', POLISH)):
            out = '%s.k%d%s%d.txt' % (stem, k, name, p)
            if out == best:                 # a chain that was stopped inside this round, after this call
                out = out[:-4] + 'r.txt'
            s2, dt = fq_call(fq, best, out, flags, cap)
            log.append(['k%d%s%d' % (k, name, p), s2, round(dt, 1)])
            if s2 is not None and s2 < cur - 3e-9:
                old, cur, best, moved = best, s2, out, True
                save(True, p)               # the record names the new packing before the old one goes
                if old != start:
                    os.remove(old)
            elif os.path.exists(out):
                os.remove(out)
        if not moved:
            break
        nxt = p + 1
        save(True, nxt)
    else:
        cut = True                          # the rounds ran out while the side still fell
    res = save(cut, nxt)
    return os.path.basename(stem), k, s0, cur, res['secs'], log


def cmd_quench(a):
    from multiprocessing.pool import ThreadPool
    stems = [f[:-len('.start.txt')] for f in sorted(glob.glob(os.path.join(a.dir, '*.start.txt')))]
    order = os.path.join(a.dir, 'order.txt')        # optional: the ids in the order to run them
    rank = {l.strip(): i for i, l in enumerate(open(order))} if os.path.exists(order) else {}
    stems.sort(key=lambda s: (rank.get(os.path.basename(s), len(rank)), read_txt(s + '.start.txt')[0]))    # else small n first
    open_ = lambda f: not os.path.exists(f) or json.load(open(f)).get('cut', False)
    todo = [(s + '.start.txt', a.fq, a.cap, a.passes, a.kick, k, a.until) for k in range(a.sfrom, a.seeds + 1)
            for s in stems if open_('%s.k%d.json' % (s, k))]
    print('quench:', len(stems), 'starts,', len(todo), 'chains,', a.jobs, 'jobs, cap', a.cap, 's', flush=True)
    with ThreadPool(a.jobs) as pool:
        for pid, k, s0, s1, dt, log in pool.imap(quench_one, todo):
            first = log[0][1] if log else None
            print(pid, 'seed %d start %.9f first default %s final %.9f gave back %.3e %.0fs' % (
                k, s0, 'none' if first is None else '%.9f' % first, s1, s0 - s1, dt), flush=True)
    collect(a.dir, True)


def collect(d, clean=False):
    """the best chain of each start -> <stem>.json; clean removes the packings of the other finished chains."""
    for start in glob.glob(os.path.join(d, '*.start.txt')):
        s = start[:-len('.start.txt')]
        R = [json.load(open(f)) for f in sorted(glob.glob(glob.escape(s) + '.k*.json'))]
        if not R:
            continue
        best = min(R, key=lambda r: r['s_final'])
        for r in R:
            f = os.path.join(d, r['best'])
            if (clean and r is not best and r['best'] != best['best'] and not r.get('cut') and not f.endswith('.start.txt')
                    and os.path.exists(f)):
                os.remove(f)
        best = dict(best, log=[q for r in R for q in r['log']], secs=round(sum(r['secs'] for r in R), 1))
        with open(s + '.json.tmp', 'w') as h:
            json.dump(best, h)
        os.replace(s + '.json.tmp', s + '.json')


def cert_job(b):
    import floatsafe
    n, path = b
    _, X = read_txt(path)
    rows = [{'n': str(n), 'square_id': str(i), 'x': repr(x), 'y': repr(y), 'angle': repr(math.radians(d))}
            for i, (x, y, d) in enumerate(X)]
    _, fr, sc, _e = floatsafe.work((n, rows))
    return fr, sc


def recipe_corner(r):
    return int(r['corner']) if r['kind'] == 'rev' else int(r['variant']) % 4


def check_start(d, r):
    """Refuse a queue whose manifest and start came from different donors."""
    import hashlib
    path = os.path.join(d, r['id'] + '.start.txt')
    if abs(read_txt(path)[0] - float(r['built_L'])) > 1e-8:
        raise ValueError('manifest/start side mismatch: ' + path)
    if r.get('start_sha256') and hashlib.sha256(open(path, 'rb').read()).hexdigest() != r['start_sha256']:
        raise ValueError('manifest/start digest mismatch: ' + path)


def cmd_cert(a):
    sys.path.insert(0, LANE)
    from multiprocessing import Pool
    L, score = held_L(a.details)
    sub = held_L(a.submitted)[1] if a.submitted else None
    prior = {n: v[0] for n, v in best_takes(a.takes, sub).items()}    # n -> the take.tsv row of a take in HELD.csv
    origin = {}                                     # n -> (score, source, licence) of a held packing: the listed
    for f in a.sources or []:                       # score nearest above the held one (a lower one is not the held n)
        for r in csv.DictReader(open(f), delimiter='\t'):
            n, sc = int(r['n']), float(r.get('score') or r['new'])
            if sc > (sub or score)[n] - 1e-9 and (n not in origin or sc < origin[n][0]):
                origin[n] = (sc, r['source'], r['licence'])
    collect(a.dir)
    work = os.path.join(a.take, 'work'); os.makedirs(work, exist_ok=True)
    tsv = os.path.join(a.take, 'take.tsv')
    T = {int(r['n']): r for r in csv.DictReader(open(tsv), delimiter='\t')} if os.path.exists(tsv) else {}
    log = os.path.join(work, 'sweep.tsv')
    done = {(r['id'], r['quenched_L']) for r in csv.DictReader(open(log), delimiter='\t')} if os.path.exists(log) else set()
    M = [r for r in csv.DictReader(open(os.path.join(a.dir, 'manifest.tsv')), delimiter='\t')
         if os.path.exists(os.path.join(a.dir, r['id'] + '.json'))]
    for r in M:
        check_start(a.dir, r)
    R = {r['id']: json.load(open(os.path.join(a.dir, r['id'] + '.json'))) for r in M}
    M = [r for r in M if R[r['id']]['log'] and os.path.exists(os.path.join(a.dir, R[r['id']]['best']))]
    # left out: a chain that --until stopped before its first call, and one that runs now and has moved on
    M = [r for r in M if (r['id'], repr(R[r['id']]['s_final'])) not in done]    # a run already in the log is not read twice
    cand = [r for r in M if R[r['id']]['s_final'] < L[int(r['n'])] - 1e-10 * math.sqrt(int(r['n']))]    # the take's bar
    with Pool(a.jobs) as pool:
        C = dict(zip([r['id'] for r in cand],
                     pool.map(cert_job, [(int(r['n']), os.path.join(a.dir, R[r['id']]['best'])) for r in cand])))
    with open(log, 'a') as h:
        if not done:
            h.write('id\tkind\tdonor\tn\tcorner\tvariant\tdropped\tfrac\ttilted\tloose\tedge\theld_L\tbuilt_L\tmargin_before\t'
                    'first_default_L\tquenched_L\tmargin_after\tgave_back\tcertified_score\tsecs\tcut\n')
        for r in M:
            n, m, j = int(r['n']), int(r['donor']), R[r['id']]
            fr, sc = C.get(r['id'], (None, None))
            h.write('\t'.join([r.get(k) or '' for k in ('id', 'kind', 'donor', 'n', 'corner', 'variant', 'dropped', 'frac', 'tilted',
                                               'loose', 'edge', 'held_L', 'built_L', 'margin_before')] +
                              [repr(j['log'][0][1]) if j['log'] else 'None', repr(j['s_final']),
                               '%.4e' % (j['s_final'] - L[n]), '%.4e' % (float(r['built_L']) - j['s_final']),
                               repr(sc) if fr is not None else 'None', '%.0f' % j['secs'],
                               '1' if j.get('cut') else '0']) + '\n')
            if fr is None or not (sc < score[n] - 1e-10) or not (sc < float(T.get(n, {'new': 9})['new'])):
                continue
            if n in prior and not sc < float(prior[n]['new']):   # a live take dir holds this n lower now
                continue
            with open(os.path.join(a.take, '%d.csv' % n), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for q in fr:
                    w.writerow([q['n'], q['square_id'], q['x'], q['y'], q['angle']])
            what = {'b1': 'one border on', 'b2': 'two borders on', 'rev': 'a corner window of'}[r['kind']]
            if r.get('near'):                       # a near layout of another lane: name it and what it was built from
                v = int(r['variant'])
                keep = os.path.join(os.path.abspath(a.dir), r.get('donor_copy') or
                                    'donor-%d-%s.csv' % (m, r['id'].split('-')[3]))
                src = 'fq quench of %s on corner %d%s of %s; copy kept as %s (border_sweep.py)' % (
                    what[:-3], recipe_corner(r), ', gap variant %d' % v if v >= 4 else '', r['donor_source'], keep)
                lic = 'ours, on %s; that donor: %s' % (r['near'], r.get('donor_licence') or 'ours')
                import re
                q = re.search(r'(up|down)(\d+)from(\d+)', os.path.basename(r['near']))
                if q and int(q.group(3)) in origin:
                    M0 = int(q.group(3))
                    lic += ', built from the held n=%d; the held %d is %s: %s' % ((M0, M0) + origin[M0][1:])
            elif 'donor_take' in r and r['donor_take']:     # the donor was a take when starts built this corner
                src = 'fq quench of %s n=%d of %s, from %s (border_sweep.py)' % (what, m, r['donor_take'], r['donor_source'])
                lic = 'ours, on the n=%d of %s; that n: %s' % (m, r['donor_take'], r['donor_licence'])
            elif 'donor_take' not in r and m in prior:     # a manifest from before the donor columns: the take dirs now
                print('cert: %s has no donor columns; the source of n=%d is read from the take dirs now' % (r['id'], m))
                src = 'fq quench of %s n=%d from %s (border_sweep.py)' % (what, m, prior[m]['source'])
                lic = prior[m]['licence']
            else:
                src = 'fq quench of %s held n=%d (border_sweep.py)' % (what, m)
                lic = 'ours, on the held n=%d' % m + ('; the held %d comes from %s, %s' % ((m,) + origin[m][1:]) if m in origin else '')
            held = sub[n] if sub else float(prior[n]['held']) if n in prior else score[n]
            T[n] = {'n': n, 'held': repr(held), 'new': repr(sc), 'gain': '%.3e' % (held - sc), 'source': src, 'licence': lic}
            with open(tsv + '.tmp', 'w') as g:
                g.write('n\theld\tnew\tgain\tsource\tlicence\n')
                for k in sorted(T):
                    g.write('\t'.join(str(T[k][c]) for c in ('n', 'held', 'new', 'gain', 'source', 'licence')) + '\n')
            os.replace(tsv + '.tmp', tsv)           # a reader never sees half a table
            print('KEEP n=%d gain %.3e, %.3e below the base (%s)' % (n, held - sc, score[n] - sc, src), flush=True)
    print('cert: %d results read, %d below the held side and through floatsafe, take now holds %d n' % (
        len(M), len(cand), len(T)))


def best_takes(dirs, below=None):
    """n -> (take.tsv row, per-n file) of the smallest take of that n over the take dirs. below: n -> the
    submitted score; a take that is not under it by the take's bar is left out."""
    best = {}
    for d in dirs or []:
        for r in csv.DictReader(open(os.path.join(d, 'take.tsv')), delimiter='\t'):
            n = int(r['n'])
            if below is not None and not float(r['new']) < below[n] - 1e-10:
                continue
            if os.path.exists(os.path.join(d, '%d.csv' % n)) and (n not in best or float(r['new']) < float(best[n][0]['new'])):
                best[n] = (r, os.path.join(d, '%d.csv' % n))
    return best


def cmd_base(a):
    best = best_takes(a.takes, held_L(a.details)[1])
    at = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    rep = {n: list(csv.DictReader(open(p))) for n, (r, p) in best.items()}
    P = {}
    for r in csv.DictReader(open(a.held)):
        P.setdefault(int(r['n']), []).append(r)
    with open(a.out, 'w', newline='') as h:           # the layout engine_assemble.py writes
        w = csv.writer(h); w.writerow(['id', 'n', 'square_id', 'x', 'y', 'angle']); i = 0
        for n in range(1, 1001):
            assert len(rep.get(n, P[n])) == n
            for r in sorted(rep.get(n, P[n]), key=lambda r: int(r['square_id'])):
                w.writerow([i, n, r['square_id'], r['x'], r['y'], r['angle']]); i += 1
    with open(a.out_details, 'w', newline='') as h:     # take, source, licence: where a replaced n came from
        w = csv.writer(h); w.writerow(['n', 'L', 'score', 'take', 'source', 'licence'])
        for r in csv.DictReader(open(a.details)):
            n = int(r['n'])
            if n in best and float(best[n][0]['new']) < float(r['score']):
                t, p = best[n]
                w.writerow([n, repr((float(t['new']) + 1) * math.sqrt(n)), t['new'],
                            '%s at %s' % (os.path.basename(os.path.dirname(os.path.abspath(p))), at), t['source'], t['licence']])
            else:
                assert n not in best, n
                w.writerow([r['n'], r['L'], r['score']] + [r.get(k) or '' for k in ('take', 'source', 'licence')])
    print('base: %d n replaced: %s' % (len(best), ' '.join(str(n) for n in sorted(best))))


def cmd_report(a):
    f = lambda r, k: float(r[k])
    best = {}                                       # a start that ran more than once (kick seeds): its best run
    for r in csv.DictReader(open(os.path.join(a.take, 'work', 'sweep.tsv')), delimiter='\t'):
        if r['id'] not in best or f(r, 'quenched_L') < f(best[r['id']], 'quenched_L'):
            best[r['id']] = r
    R = list(best.values())
    grid = lambda r: abs(f(r, 'built_L') - round(f(r, 'built_L'))) < 1e-4      # a plain grid with holes, or nearly
    print('kind\tstarts\tdistinct n\tgave back > 1e-7\tmedian give-back of those\tlargest give-back\t'
          'ended within 3e-9 of the held side\tended below it\tcertified below the bar')
    for kind in ('b1', 'b2', 'rev'):
        for name, sel in (('grid start', grid), ('other', lambda r: not grid(r))):
            v = [r for r in R if r['kind'] == kind and sel(r)]
            g = sorted(f(r, 'gave_back') for r in v if f(r, 'gave_back') > 1e-7)
            print('%s, %s\t%d\t%d\t%d\t%s\t%s\t%d\t%d\t%d' % (
                kind, name, len(v), len({r['n'] for r in v}), len(g), '%.2e' % g[len(g) // 2] if g else '-',
                '%.2e' % g[-1] if g else '-', sum(abs(f(r, 'margin_after')) <= 3e-9 for r in v),
                sum(f(r, 'margin_after') < -3e-9 for r in v), sum(r['certified_score'] != 'None' and
                f(r, 'certified_score') < (f(r, 'held_L') / math.sqrt(int(r['n'])) - 1) - 1e-10 for r in v)))
    print()
    v = [r for r in R if r['kind'] != 'rev' and not grid(r)]
    print('border starts on a donor that is not a grid, by the tilted squares on the two walls that get the border:')
    for name, lo, hi in (('none', 0, 0), ('1 to 5', 1, 5), ('6 or more', 6, 10 ** 6)):
        w = [r for r in v if r['edge'] != '' and lo <= int(r['edge']) <= hi]
        g = sorted(f(r, 'gave_back') for r in w if f(r, 'gave_back') > 1e-7)
        print('%s\tstarts %d\tgave back %d\tlargest %s' % (name, len(w), len(g), '%.2e' % g[-1] if g else '-'))
    if a.board:
        B = {int(r['n']): float(r['L']) for r in json.load(open(a.board))}
        dist = lambda r: f(r, 'held_L') - B[int(r['n'])]
        print()
        print('border starts on a donor that is not a grid, edge count by the distance of the held target from the board:')
        print('edge\tdist\tstarts\tgave back > 1e-7\tgave back > 1e-3\tmedian give-back of those that moved\tlargest\t'
              'ended below held\tmedian margin before')
        for en, elo, ehi in (('1 to 5', 1, 5), ('6 to 14', 6, 14), ('15 to 29', 15, 29), ('30 or more', 30, 10 ** 6)):
            for dn, dlo, dhi in (('under 0.01', -1, 0.01), ('0.01 to 0.02', 0.01, 0.02), ('0.02 or more', 0.02, 9)):
                w = [r for r in v if r['edge'] != '' and elo <= int(r['edge']) <= ehi and dlo <= dist(r) < dhi]
                g = sorted(f(r, 'gave_back') for r in w if f(r, 'gave_back') > 1e-7)
                mb = sorted(f(r, 'margin_before') for r in w)
                print('%s\t%s\t%d\t%d\t%d\t%s\t%s\t%d\t%s' % (
                    en, dn, len(w), len(g), sum(x > 1e-3 for x in g), '%.2e' % g[len(g) // 2] if g else '-',
                    '%.2e' % g[-1] if g else '-', sum(f(r, 'margin_after') < -3e-9 for r in w),
                    '%.2e' % mb[len(mb) // 2] if mb else '-'))
    print()
    print('id\tdropped\tfrac\ttilted\tloose\tedge\tmargin_before\tmargin_after\tgave_back\tsecs')
    for r in sorted(R, key=lambda r: -f(r, 'gave_back')):
        if f(r, 'gave_back') > a.min or not grid(r) and r['kind'] != 'rev':
            print('\t'.join(r[k] for k in ('id', 'dropped', 'frac', 'tilted', 'loose', 'edge', 'margin_before',
                                           'margin_after', 'gave_back', 'secs')))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('enum'); p.add_argument('held'); p.add_argument('details'); p.add_argument('pairs')
    p.add_argument('--max', type=float, default=2e-3)
    p = sub.add_parser('starts'); p.add_argument('held'); p.add_argument('details'); p.add_argument('pairs'); p.add_argument('dir')
    p.add_argument('--max', type=float, default=2e-3); p.add_argument('--min-abs', type=float, default=TIE)
    p.add_argument('--kinds', default='b1,b2,rev'); p.add_argument('--per-n', type=int, default=0)
    p.add_argument('--variants', type=int, default=1); p.add_argument('--limit', type=int, default=10 ** 6)
    p.add_argument('--vfrom', type=int, default=0); p.add_argument('--min', type=float, default=-1e9)
    p.add_argument('--no-grid', action='store_true'); p.add_argument('--edge-min', type=int, default=0)
    p.add_argument('--gaps', default='')
    p = sub.add_parser('rank'); p.add_argument('held'); p.add_argument('details'); p.add_argument('pairs')
    p.add_argument('board'); p.add_argument('out'); p.add_argument('--max', type=float, default=3e-2)
    p.add_argument('--edge-min', type=int, default=0); p.add_argument('--dist-min', type=float, default=0.01)
    p.add_argument('--both-min', type=int, default=0); p.add_argument('--wall-min', type=int, default=2)
    p.add_argument('--kinds', default='b1'); p.add_argument('--per-n', type=int, default=0)
    p.add_argument('--moved')
    p = sub.add_parser('near'); p.add_argument('details'); p.add_argument('board'); p.add_argument('out')
    p.add_argument('takes', nargs='+'); p.add_argument('--done'); p.add_argument('--max', type=float, default=3e-2)
    p.add_argument('--kinds', default='b1,b2'); p.add_argument('--wall-min', type=int, default=2)
    p = sub.add_parser('gaps'); p.add_argument('dir'); p.add_argument('out'); p.add_argument('--min', type=float, default=1e-3)
    p = sub.add_parser('carry'); p.add_argument('details'); p.add_argument('out'); p.add_argument('src', nargs='+')
    p.add_argument('--tiers', default='7e-3,1.1e-2'); p.add_argument('--split', type=int, default=2)
    p = sub.add_parser('quench'); p.add_argument('dir'); p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--cap', type=float, default=600); p.add_argument('--passes', type=int, default=6)
    p.add_argument('--kick', type=float, default=1e-3); p.add_argument('--seeds', type=int, default=0)
    p.add_argument('--sfrom', type=int, default=0)
    p.add_argument('--fq', default=FQ); p.add_argument('--until', type=float, default=0)
    p = sub.add_parser('cert'); p.add_argument('held'); p.add_argument('details'); p.add_argument('dir'); p.add_argument('take')
    p.add_argument('--takes', nargs='*'); p.add_argument('--jobs', type=int, default=3)
    p.add_argument('--submitted'); p.add_argument('--sources', nargs='*')
    p = sub.add_parser('report'); p.add_argument('take'); p.add_argument('--min', type=float, default=1e-5)
    p.add_argument('--board')
    p = sub.add_parser('base'); p.add_argument('held'); p.add_argument('details'); p.add_argument('out')
    p.add_argument('out_details'); p.add_argument('takes', nargs='*')
    a = ap.parse_args()
    {'enum': cmd_enum, 'rank': cmd_rank, 'starts': cmd_starts, 'quench': cmd_quench, 'cert': cmd_cert, 'report': cmd_report,
     'base': cmd_base, 'near': cmd_near, 'gaps': cmd_gaps, 'carry': cmd_carry}[a.cmd](a)


if __name__ == '__main__':
    main()
