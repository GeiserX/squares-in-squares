#!/usr/bin/env python3
"""sel33.py OUT.json: round 33. The pool of held round 32 a rows for the 150 s lkick fill of follow.lk_fill.

Round 33 lesson 6b: first lkicks of held rows are split by n (twoshort 1 to 399, soft 400 to 699, rebuild 700 to 1000),
each only on rows whose current geometry no lane has lkicked, rows above the 2026-11-09 board side first, no second seeds.
Changes against sel32.py:
  1. n 400 to 699 only;
  2. the current geometry decides. A kick or claim line of handoff-r29 to r33 drops a row when one csv it names has the
     geometry of the held round 32 a row (follow.geometry_id), or when it says held and was written after the row last
     changed (a held line of an older round names an older geometry). sel32's "changed r29-31" drop is gone: a changed
     row whose new geometry no line names is a first lkick (twoshort r32 next item 2);
  3. dropped as dead ends measured in round 32: 45-degree lattice rows (lesson 6c), rows whose side fraction is a p/q with
     q up to 40 or is shared with another n (twoshort r32: 0 of 21), closed-form sides, rows naming the prvsiyan 1105
     file, plain public rows (quench and rebuild own those);
  4. order: above the board side first (rebuild r32: 4 of 61 above, 0 of 19 at or below), then rows whose last source
     text names no kick, then by board score gap. Rows at or below the board side go last.
Writes OUT.json (the ordered n list) and OUT.detail.json."""
import csv, glob, json, math, re, sys
from fractions import Fraction
from pathlib import Path
csv.field_size_limit(16000000)
B = Path('$SCRATCH/bounties-squares'); R = Path('results')
L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(B / 'gate/cand-round32-1116a/details.csv'))}
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(B / 'round33-briefs/bar33.tsv'), delimiter='\t')}
gap = {int(r['n']): r for r in csv.DictReader(open(B / 'main-r17/gap-by-n.tsv'), delimiter='\t')}
LO, HI = 400, 699
# round 33, 19:0xZ (main session: keep the boxes busy with this queue): SEL_SINCE=31 counts only kick or claim lines of
# rounds 31 to 33, so a row whose last kick line is of round 29 or 30 comes back for one 150 s lkick (round 32 sel32 used
# the same sliding window: its rows had no line in rounds 29 to 32, and its first pass gave 465)
import os
SINCE = int(os.environ.get('SEL_SINCE', '29'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from follow import geometry_id
import ctl
# the round in which each n last changed (results/roundK-best tables)
last_change = {}
for f in glob.glob(str(R / 'round*-best-*.tsv')):
    k = int(re.search(r'round(\d+)-best', f)[1])
    for r in csv.DictReader(open(f), delimiter='\t'):
        try:
            n = int(r['n'])
        except (ValueError, KeyError):
            continue
        last_change[n] = max(last_change.get(n, 0), k)
src = {}
for f in sorted(glob.glob(str(R / 'round*-best-*.tsv')), key=lambda f: int(re.search(r'round(\d+)-best', f)[1])):
    for r in csv.DictReader(open(f), delimiter='\t'):
        try:
            src[int(r['n'])] = (Path(f).name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError):
            pass
named = {}
for k in range(SINCE, 34):
    lg = B / ('handoff-r%d.log' % k)
    if not lg.exists():
        continue
    for line in open(lg, errors='replace'):
        if re.search(r'kick|claim', line, re.I):
            ns = {int(m) for m in re.findall(r'\bn ?= ?(\d{1,4})\b', line)} | {int(m) for m in re.findall(r'held\w*/(\d{1,4})\.csv', line)}
            for n in ns:
                if LO <= n <= HI:
                    named.setdefault(n, []).append((k, line))
held_rows = {}
for r in csv.DictReader(open(B / 'gather/round32-2026-11-16a.csv', newline='')):
    n = int(r['n'])
    if LO <= n <= HI:
        held_rows.setdefault(n, []).append({k: r[k] for k in ctl.KEYS})
_geo = {}


def geo_of(path, n):
    if path not in _geo:
        try:
            rows = [r for r in ctl.rows_of(path) if int(r['n']) == n]
            _geo[path] = geometry_id(rows) if len(rows) == n else None
        except Exception:
            _geo[path] = None
    return _geo[path]


kicked = {}
for n, lines in named.items():
    if n not in held_rows:
        continue
    hg = geometry_id(held_rows[n])
    for k, line in lines:
        if re.search(r'held', line, re.I) and k > last_change.get(n, 0):
            kicked[n] = 'handoff-r%d held' % k; break
        paths = re.findall(r'$DATA/[^\s,;<>()]+\.csv', line) + [str(B / q) for q in re.findall(r'(?<![/\w])(take-[^\s,;<>()]+\.csv)', line)]
        if any(geo_of(q, n) == hg for q in paths if Path(q).is_file()):
            kicked[n] = 'handoff-r%d same geometry' % k; break
S2 = math.sqrt(2)


def closed(x):
    best = 9
    for b4 in range(0, 161):
        a = x - b4 / 4 * S2; best = min(best, abs(a * 8 - round(a * 8)) / 8)
    return best


def pq(x):
    f = x - math.floor(x)
    fr = Fraction(f).limit_denominator(40)
    return abs(f - fr.numerator / fr.denominator) < 1e-9


def lattice(rows):
    """every tilted square at 45 degrees (lesson 6c)"""
    tilted = 0
    for r in rows:
        d = math.degrees(float(str(r['angle']).lstrip('s'))) % 90.0
        if min(d, 90 - d) < 1e-6:
            continue
        if abs(d - 45) > 1e-6:
            return False
        tilted += 1
    return tilted > 0


fracs = {}
for n, x in L.items():
    fracs.setdefault(round(x - math.floor(x), 9), []).append(n)
out = []
for n in range(LO, HI + 1):
    why = []
    if n in kicked: why.append('kick or claim line ' + kicked[n])
    c = closed(L[n])
    if c < 2e-9: why.append('closed form %.1e' % c)
    if pq(L[n]): why.append('p/q side fraction')
    sh = [m for m in fracs.get(round(L[n] - math.floor(L[n]), 9), []) if m != n]
    if sh: why.append('side fraction shared with %s' % sh[:4])
    if lattice(held_rows[n]): why.append('45-degree lattice')
    s = src.get(n, ('', '', '')); st = s[1]
    if 'squares-verified-best-of-1105' in st and 'own Samanyu' not in st: why.append('names prvsiyan 1105')
    if st.startswith('harvest') and 'kick' not in st: why.append('plain public source')
    g = gap.get(n); sg = 0.0; above = False
    if g:
        sg = bar[n] - (float(g['board_L']) / math.sqrt(n) - 1)
        above = L[n] > float(g['board_L']) + 1e-9
    kickish = bool(re.search(r'kick', st, re.I)) and last_change.get(n, 0) >= 29
    out.append(dict(n=n, L=L[n], bar=bar[n], gap=sg, above=above, kickish=kickish, last_change=last_change.get(n, 0),
                    src_table=s[0], why=why))
ok = [o for o in out if not o['why']]
ok.sort(key=lambda o: (not o['above'], o['kickish'], -o['gap']))
json.dump([o['n'] for o in ok], open(sys.argv[1], 'w'))
json.dump(dict(ok=ok, all=out), open(sys.argv[1].replace('.json', '.detail.json'), 'w'), indent=1)
print('rows', len(out), 'ok', len(ok), 'above', sum(o['above'] for o in ok), 'kicked', len(kicked),
      'dropped', {w.split(' ')[0]: sum(1 for o in out if any(x.startswith(w.split(' ')[0]) for x in o['why'])) for w in ('kick', 'closed', 'p/q', 'side', '45-degree', 'names', 'plain')})
for o in ok[:40]:
    print(o['n'], '%.9f' % o['L'], 'gap %.3e' % o['gap'], 'above' if o['above'] else 'atboard', 'kickish' if o['kickish'] else '', o['last_change'])
