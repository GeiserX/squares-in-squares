#!/usr/bin/env python3
"""T1 targets: our per-n sides against the per-puzzle board, as a work list.

  targets.py --board board.json --ours per_n.tsv --out DIR [--tag DATE] [--min-n 300]

board.json: list of {n, L, team, date} for n = 1..1000 (the per-puzzle board,
results/per-puzzle-lb-<date>.json). per_n.tsv: our L per n; any TSV with columns
n and L (score.py --out, gate.py details.csv as TSV/CSV both work).

Writes DIR/targets-<tag>.tsv, one row per n:
  n, ours_L, target_L, gap (score units), short (squares short at the target side:
  n minus the largest n' < n whose side of ours fits under target_L), family
  (fractional part of target_L at 1e-9), family_size, team, pslq (only for exact
  families with 2+ members: an integer relation of target_L over 1, sqrt2, sqrt3,
  sqrt5, sqrt7 with max coefficient 40, or empty), status (ok / missing target /
  missing ours).
and DIR/worklist-<tag>.jsonl: n >= --min-n where we trail, ordered by gap, with
each exact family's smallest member placed at the family's best position, then the
k = 1 band n (401, 442, ..., 962) not already listed.
Exits 2 on a board or table that does not have the expected columns or n.
"""
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path

K1_BAND = [401, 442, 485, 530, 577, 626, 677, 730, 785, 842, 901, 962]


def die(msg):
    print('targets.py: ' + msg, file=sys.stderr)
    sys.exit(2)


def read_board(path):
    try:
        rows = json.load(open(path))
    except Exception as e:
        die(f'board unreadable: {e}')
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
        die('board is not a list of records')
    need = {'n', 'L', 'team'}
    if not need <= set(rows[0]):
        die(f'board records lack {sorted(need - set(rows[0]))}')
    return {int(r['n']): r for r in rows}


def read_ours(path):
    with open(path, newline='') as h:
        head = h.readline()
        h.seek(0)
        rd = csv.DictReader(h, delimiter='\t' if '\t' in head else ',')
        if not {'n', 'L'} <= set(rd.fieldnames or []):
            die(f'{path} lacks columns n and L')
        out = {}
        for r in rd:
            try:
                L = float(r['L'])
            except ValueError:
                continue
            if L > 0:
                out[int(r['n'])] = L
    if not out:
        die(f'{path} has no usable L')
    return out


def pslq(Ltext):
    import mpmath
    mpmath.mp.dps = 50
    v = [mpmath.mpf(Ltext), 1, mpmath.sqrt(2), mpmath.sqrt(3), mpmath.sqrt(5), mpmath.sqrt(7)]
    rel = mpmath.pslq(v, maxcoeff=40, maxsteps=20000)
    return '' if rel is None else ' '.join(map(str, rel))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--board', required=True); ap.add_argument('--ours', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--tag', default='now')
    ap.add_argument('--min-n', type=int, default=300)
    a = ap.parse_args()
    board, ours = read_board(a.board), read_ours(a.ours)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    tgt = {n: float(r['L']) for n, r in board.items()}
    fam = defaultdict(list)
    for n, L in tgt.items():
        fam[f'{L % 1:.9f}'].append(n)
    rows = []
    for n in range(1, 1001):
        r = {'n': n, 'ours_L': ours.get(n), 'target_L': tgt.get(n), 'team': board.get(n, {}).get('team', '')}
        if n not in tgt:
            r.update(status='missing target', gap=None, short=None, family='', family_size=0, pslq='')
        elif n not in ours:
            r.update(status='missing ours', gap=None, short=None, family='', family_size=0, pslq='')
        else:
            g = (ours[n] - tgt[n]) / math.sqrt(n)
            fits = [m for m in range(1, n) if m in ours and ours[m] <= tgt[n] + 1e-12]
            key = f'{tgt[n] % 1:.9f}'
            r.update(status='ok', gap=max(g, 0.0), short=(n - max(fits)) if fits and g > 1e-12 else 0,
                     family=key, family_size=len(fam[key]),
                     pslq=pslq(board[n]['L']) if len(fam[key]) > 1 and g > 1e-12 else '')
        rows.append(r)

    cols = ['n', 'ours_L', 'target_L', 'gap', 'short', 'family', 'family_size', 'team', 'pslq', 'status']
    with open(out / f'targets-{a.tag}.tsv', 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=cols, delimiter='\t'); w.writeheader(); w.writerows(rows)

    trail = [r for r in rows if r['status'] == 'ok' and r['gap'] > 1e-12 and r['n'] >= a.min_n]
    trail.sort(key=lambda r: -r['gap'])
    seen, order = set(), []
    for r in trail:
        if r['n'] in seen:
            continue
        members = sorted(m['n'] for m in trail if m['family'] == r['family']) if r['family_size'] > 1 else [r['n']]
        for m in members:  # smallest member first, at the family's best position
            if m not in seen:
                seen.add(m); order.append(next(x for x in trail if x['n'] == m))
    for n in K1_BAND:
        r = rows[n - 1]
        if n not in seen and r['status'] == 'ok':
            seen.add(n); order.append({**r, 'why': 'k1 band'})
    with open(out / f'worklist-{a.tag}.jsonl', 'w') as h:
        for r in order:
            h.write(json.dumps(r) + '\n')

    ok = [r for r in rows if r['status'] == 'ok']
    tot = sum(r['gap'] for r in ok)
    short = defaultdict(lambda: [0, 0.0])
    for r in ok:
        if r['gap'] > 1e-12:
            short[r['short']][0] += 1; short[r['short']][1] += r['gap']
    exact = sum(r['gap'] for r in ok if r['family_size'] > 1)
    flags = [f"{r['n']} {r['status']}" for r in rows if r['status'] != 'ok']
    top = max(ok, key=lambda r: r['gap'])
    print(f'gap {tot:.4f}  top n={top["n"]} {top["gap"]:.5f}  exact-family share {exact:.4f}  worklist {len(order)}')
    print('squares short: ' + ', '.join(f'{k}: {v[0]} n / {v[1]:.4f}' for k, v in sorted(short.items())))
    if flags:
        print('flags: ' + ', '.join(flags))


if __name__ == '__main__':
    main()
