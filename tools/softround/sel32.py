#!/usr/bin/env python3
"""sel32.py OUT.json: round 32. The pool of held round 31 b rows for the 150 s lkick fill of follow.lk_fill, in the
twoshort round 31 rule (tools/twoshort/r31/sel31b.py, read and not imported, so the round 32 files are named here):
drop rows a kick or claim line of handoff-r29 to r32 names as held or by a file of the held geometry, rows changed in rounds 29 to 31 (their lanes kicked them),
rows whose side is a closed form a + b*sqrt(2) in quarter steps, rows whose last source is a plain public file, and rows
whose source names the prvsiyan 1105 file. Rank the rest by board score gap. Twoshort's 18 unrun round 31 jobs (its round
31 next item 1: twoshort runs them) and rows whose side fraction is a p/q with q up to 40 (twoshort round 31 next item 4:
about 20 probes of them found nothing) go last. Writes OUT.json (the ordered n list) and OUT.detail.json."""
import csv, glob, json, math, re, sys
from fractions import Fraction
from pathlib import Path
csv.field_size_limit(16000000)
B = Path('$SCRATCH/bounties-squares'); R = Path('results')
L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(B / 'gate/cand-round31-1116b/details.csv'))}
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(B / 'round32-briefs/bar32.tsv'), delimiter='\t')}
gap = {int(r['n']): r for r in csv.DictReader(open(B / 'main-r17/gap-by-n.tsv'), delimiter='\t')}
TWOSHORT_R31_UNRUN = {751, 753, 801, 803, 816, 847, 849, 850, 853, 861, 866, 915, 921, 929, 936, 981, 989, 992}
# A kick or claim line names n by n=N or a held*/N.csv path. It kicked the held row when it says held, or when one of the
# csv files it names has the geometry of the held row (follow.geometry_id: translation, symmetry, order and rounding
# ignored). Round 31 twoshort tier 2 measured that most lines of an n name only its near or rect files, other layouts.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from follow import geometry_id
import ctl
named = {}
for lg in ('handoff-r29.log', 'handoff-r30.log', 'handoff-r31.log', 'handoff-r32.log'):
    for line in open(B / lg, errors='replace'):
        if re.search(r'kick|claim', line, re.I):
            ns = {int(m) for m in re.findall(r'\bn ?= ?(\d{1,4})\b', line)} | {int(m) for m in re.findall(r'held\w*/(\d{1,4})\.csv', line)}
            for n in ns:
                named.setdefault(n, []).append((lg, line))
held_rows = {}
for r in csv.DictReader(open(B / 'gather/round31-2026-11-16b.csv', newline='')):
    held_rows.setdefault(int(r['n']), []).append({k: r[k] for k in ctl.KEYS})
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
    if n < 30 or n not in held_rows:
        continue
    hg = geometry_id(held_rows[n])
    for lg, line in lines:
        if re.search(r'held', line, re.I):
            kicked[n] = lg + ' held'; break
        paths = re.findall(r'$DATA/[^\s,;<>()]+\.csv', line) + [str(B / q) for q in re.findall(r'(?<![/\w])(take-[^\s,;<>()]+\.csv)', line)]
        if any(geo_of(q, n) == hg for q in paths if Path(q).is_file()):
            kicked[n] = lg + ' same geometry'; break
changed = set()
for k in (29, 30, 31):
    for f in glob.glob(str(R / ('round%d-best-*.tsv' % k))):
        for r in csv.DictReader(open(f), delimiter='\t'):
            changed.add(int(r['n']))
src = {}
for f in sorted(glob.glob(str(R / 'round*-best-*.tsv')), key=lambda f: int(re.search(r'round(\d+)-best', f)[1])):
    for r in csv.DictReader(open(f), delimiter='\t'):
        try:
            src[int(r['n'])] = (Path(f).name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError):
            pass
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


out = []
for n in range(30, 1001):
    why = []
    if n in kicked: why.append('kick or claim line ' + kicked[n])
    if n in changed: why.append('changed r29-31')
    c = closed(L[n])
    if c < 2e-9: why.append('closed form %.1e' % c)
    s = src.get(n, ('', '', '')); st = s[1]
    if 'squares-verified-best-of-1105' in st and 'own Samanyu' not in st: why.append('names prvsiyan 1105')
    if st.startswith('harvest') and 'kick' not in st: why.append('plain public source')
    g = gap.get(n); sg = 0.0
    if g:
        sg = bar[n] - (float(g['board_L']) / math.sqrt(n) - 1)
    last = n in TWOSHORT_R31_UNRUN or pq(L[n])
    out.append(dict(n=n, L=L[n], bar=bar[n], gap=sg, closed=c, pq=pq(L[n]), last=last, src_table=s[0], why=why))
ok = [o for o in out if not o['why']]
ok.sort(key=lambda o: (o['last'], -o['gap']))
json.dump([o['n'] for o in ok], open(sys.argv[1], 'w'))
json.dump(dict(ok=ok, all=out), open(sys.argv[1].replace('.json', '.detail.json'), 'w'), indent=1)
print('rows', len(out), 'ok', len(ok), 'kicked', len(kicked), 'changed', len(changed),
      'closed', sum(1 for o in out if o['closed'] < 2e-9), 'last', sum(1 for o in ok if o['last']))
for o in ok[:30]:
    print(o['n'], '%.9f' % o['L'], 'gap %.3e' % o['gap'], 'pq' if o['pq'] else '', 'last' if o['last'] else '', o['src_table'])
