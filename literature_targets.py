#!/usr/bin/env python3
"""Add the outside record and the structural bound to the targets table.

  literature_targets.py TARGETS.tsv EXT_DIR TAKE_DIR OUT.tsv

TARGETS.tsv is what tools/targets.py wrote (our sides against the per-puzzle board). EXT_DIR holds the
outside sources as data, never executed:
  jl/                       every ledger.json, claims.json and beyond-horizon file of jlevy/squares
                            (git archive of those paths), the register's intake of all reported sides
  kb/packing/witnesses/known-best/n-NNN.yaml   the register's witness per n <= 324
  JoostdeWinter_square-packing, dostashev_square-packing, griffcass_square-packing   clones
TAKE_DIR/take.tsv holds this round's certified wins.
Adds: outside_L (smallest side published outside Kaggle), outside_src, outside_minus_ours (negative: the
outside record beats us), struct_L (our sides closed under L(n) <= L(n+1) and L(n + 2 floor(L) + 1) <= L + 1),
new_L (this round). Run it with python -I.
"""
import csv, glob, json, math, os, re, sys
from fractions import Fraction


def num(v):
    try:
        return float(Fraction(v)) if isinstance(v, str) and '/' in v else float(v)
    except Exception:
        return None


def main():
    targets, ext, take, out = sys.argv[1:5]
    T = list(csv.DictReader(open(targets), delimiter='\t'))
    ours = {int(r['n']): float(r['ours_L']) for r in T}
    best = {}

    def put(n, v, src):
        if v and n in ours and v * v >= n - 1e-9 and (n not in best or v < best[n][0]):
            best[n] = (v, src)

    def walk(o, src, ctx):
        if isinstance(o, dict):
            n = o.get('n', ctx)
            if isinstance(n, int):
                for k in ('side', 'ceiling', 'exact_side', 'offered_side'):
                    if k in o:
                        put(n, num(o[k]), src)
            for v in o.values():
                walk(v, src, n if isinstance(n, int) else ctx)
        elif isinstance(o, list):
            for v in o:
                walk(v, src, ctx)

    for f in glob.glob(os.path.join(ext, 'jl', '**', '*.json'), recursive=True):
        src = 'jlevy/squares ' + next((p for p in f.split(os.sep) if re.search(r'20\d\d', p)), os.path.basename(f))
        walk(json.load(open(f)), src, None)
    for f in glob.glob(os.path.join(ext, 'kb', 'packing', 'witnesses', 'known-best', 'n-*.yaml')):
        head = open(f).read(6000)
        n = re.search(r'^\s+n: (\d+)', head, re.M); s = re.search(r"^\s+side: '?([^'\n]+)'?", head, re.M)
        if n and s:
            put(int(n.group(1)), num(s.group(1).strip()), 'jlevy/squares known-best witness')
    for f in glob.glob(os.path.join(ext, 'JoostdeWinter_square-packing', 'above324*', 'n*.cert')):
        for l in open(f):
            if not l.startswith('#'):
                n, s = l.split()[:2]; put(int(n), num(s), 'de Winter ' + f.split(os.sep)[-2]); break
    for f in glob.glob(os.path.join(ext, 'dostashev_square-packing', 'records', '*.sqpk')):
        t = open(f).read()
        put(int(re.search(r'^n (\d+)', t, re.M).group(1)), num(re.search(r'^s (\S+)', t, re.M).group(1)), 'Ostashev records')
    g = os.path.join(ext, 'griffcass_square-packing', 'results', 'summary.csv')
    if os.path.exists(g):
        for r in csv.DictReader(open(g)):
            put(int(r['n']), num(r['our_side']), 'Casson results')

    new = {}
    for r in csv.DictReader(open(os.path.join(take, 'take.tsv')), delimiter='\t'):
        new[int(r['n'])] = (float(r['new']) + 1) * math.sqrt(int(r['n']))
    d = dict(ours)
    ch = True
    while ch:
        ch = False
        for n in range(1, 1001):
            m = n + 2 * math.floor(d[n]) + 1
            if m <= 1000 and d[m] > d[n] + 1 + 1e-9 * d[m]:
                d[m] = d[n] + 1; ch = True
        for n in range(999, 0, -1):
            if d[n] > d[n + 1] + 1e-12:
                d[n] = d[n + 1]; ch = True

    cols = list(T[0].keys()) + ['outside_L', 'outside_src', 'outside_minus_ours', 'struct_L', 'new_L']
    beat = 0
    with open(out, 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=cols, delimiter='\t'); w.writeheader()
        for r in T:
            n = int(r['n'])
            o = best.get(n)
            r['outside_L'] = repr(o[0]) if o else ''
            r['outside_src'] = o[1] if o else ''
            r['outside_minus_ours'] = '%.3e' % (o[0] - ours[n]) if o else ''
            r['struct_L'] = repr(d[n]) if d[n] < ours[n] else ''
            r['new_L'] = repr(new[n]) if n in new else ''
            beat += bool(o and (ours[n] - o[0]) / math.sqrt(n) > 1e-10)
            w.writerow(r)
    print('n with an outside side:', len(best), ' outside beats ours by more than 1e-10 of score:', beat,
          ' struct wins:', sum(1 for n in d if d[n] < ours[n]), ' new this round:', len(new))


if __name__ == '__main__':
    main()
