"""Write results/modules-r26-2026-11-14.tsv: the take rows, every build of the round, then every kick with its start and best.

Scores are bounding scores (side/sqrt(n) - 1) of the raw files; the take rows carry the certified scores of take.tsv.
base_score is the round 25 b gate (gate/cand-round25-1114b/details.csv); minus_base is best (or built) score minus base.
Usage: table26.py OUT.tsv [since_epoch]"""
import csv, glob, json, math, os, re, sys
from pathlib import Path
import numpy as np
csv.field_size_limit(2**30)
R = Path('$SCRATCH/bounties-squares'); T = R / 'take-modules-r26'; W = T / 'work'
bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(R / 'gate/cand-round25-1114b/details.csv'))}
SINCE = float(sys.argv[2]) if len(sys.argv) > 2 else 1794662040.0  # 2026-11-14T13:14:00Z, the round 26 workers' start


def score(p):
    rows = list(csv.DictReader(open(p)))
    P = np.array([(float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s')), float(str(r['angle']).lstrip('s'))) for r in rows])
    h = (np.abs(np.cos(P[:, 2])) + np.abs(np.sin(P[:, 2]))) / 2
    L = max((P[:, 0] + h).max() - (P[:, 0] - h).min(), (P[:, 1] + h).max() - (P[:, 1] - h).min())
    return len(P), float(L / math.sqrt(len(P)) - 1)


def sc(n, side):
    return side / math.sqrt(n) - 1 if side is not None else None


out = open(sys.argv[1], 'w', newline='')
w = csv.writer(out, delimiter='\t', lineterminator='\n')
w.writerow(['kind', 'n', 'name', 'box', 'detail', 'base_score', 'start_score', 'best_score', 'minus_base', 'finds', 'note'])
for r in csv.DictReader((T / 'take.tsv').open(), delimiter='\t'):
    w.writerow(['take', r['n'], f'take-modules-r26/{r["n"]}.csv', 'boxD quench', 'certified', r['held'], '', r['new'],
                '%.6e' % (float(r['new']) - float(r['held'])), '', 'source and licence in take.tsv'])
builds = []
for p in sorted(W.glob('boxD-raw/*.json')) + sorted(W.glob('boxD-raw/*.nostart')):
    if p.stat().st_mtime < SINCE or 'rekick' in p.name or 'r26kick' in p.name:
        continue
    try:
        j = json.loads(p.read_text())
    except ValueError:
        continue
    n = int(j['n'])
    ids = j.get('ids') or [q['id'] for q in j.get('modules', [])]
    built = j.get('built')
    s = sc(n, built)
    builds.append(['build', n, p.stem, 'boxD', ' '.join(ids) + ' stacks ' + ','.join(map(str, j.get('stacks', []))),
                   repr(bar[n]), repr(sc(n, j['predicted'])) if j.get('predicted') else '', repr(s) if s is not None else '',
                   '%.6e' % (s - bar[n]) if s is not None else '', '', j.get('why', 'built, slp squeeze')])
w.writerows(sorted(builds, key=lambda r: (r[1], r[2])))
for box, root in [('boxD', W / 'kickfetch'), ('boxB', W / 'mmkicks')]:
    for d in sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []:
        src = W / 'inject' / (d.name + '.csv')
        if not src.exists():
            src = W / 'boxD-raw' / (d.name + '.csv')
        if not src.exists() or src.stat().st_mtime < SINCE - 86400:
            continue
        n = int(d.name.split('-')[0])
        s0 = score(src)[1]
        finds = sorted((d / 'raw').glob('*.csv'))
        best = min((score(p)[1] for p in finds), default=float('nan'))
        w.writerow(['kick', n, d.name, box, 'midm_scan lkick,kick sigma 0.02, 450 s, seed 26', repr(bar[n]), repr(s0),
                    repr(best) if finds else '', '%.6e' % (best - bar[n]) if finds else '', len(finds), ''])
# boxD kicks: the box worker records each one in STATE.txt ("kick: finish fresh kick NAME, returncode R, finds K")
# and the local loop copies its finds to kickraw/<n>-NAME-<n>-(l)kick-26-<i>.csv; kickfetch/ was never used in round 26.
seen = set()
for line in (T / 'STATE.txt').read_text().splitlines():
    m = re.match(r'(\S+) kick: finish fresh kick (\S+), returncode (\d+), finds (\d+)', line)
    if not m or m.group(2) in seen:
        continue
    name = m.group(2)
    seen.add(name)
    n = int(name.split('-')[0])
    src = W / 'boxD-raw' / (name + '.csv')
    if not src.exists():
        src = W / 'inject' / (name + '.csv')
    s0 = score(src)[1] if src.exists() else float('nan')
    finds = sorted(W.glob(f'kickraw/{n}-{name}-{n}-*kick-26-*.csv'))
    best = min((score(p)[1] for p in finds), default=float('nan'))
    w.writerow(['kick', n, name, 'boxD', 'midm_scan lkick,kick sigma 0.02, 450 s, seed 26', repr(bar[n]), repr(s0),
                repr(best) if finds else '', '%.6e' % (best - bar[n]) if finds else '', len(finds),
                f'returncode {m.group(3)}, worker finds {m.group(4)}'])
out.close()
print('written', sys.argv[1])
