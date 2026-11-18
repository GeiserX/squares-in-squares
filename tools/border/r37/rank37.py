"""r36: rank k123 near donors by board room (brief 6c): room = (bar37 - board, of score) - (donor - bar37).
Seeds already claimed per sha (handoff-r35 and r36, any lane) are counted; donors with two or more seeds are dropped."""
import csv, glob, math, re, sys, json, hashlib
from pathlib import Path
S = Path('$SCRATCH/bounties-squares')
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S/'round37-briefs/bar37.tsv'), delimiter='\t')}
board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(S/'main-r17/gap-by-n.tsv'), delimiter='\t')}
OUT = {639, 691, 745, 858, 918}
def side(p):
    xs0 = ys0 = 1e18; xs1 = ys1 = -1e18
    for r in csv.DictReader(open(p)):
        x, y, a = (float(str(r[k]).lstrip('s')) for k in ('x', 'y', 'angle'))
        h = (abs(math.cos(a)) + abs(math.sin(a))) / 2
        xs0 = min(xs0, x-h); xs1 = max(xs1, x+h); ys0 = min(ys0, y-h); ys1 = max(ys1, y+h)
    return max(xs1-xs0, ys1-ys0)
claims = {}
for h in ('handoff-r34.log', 'handoff-r35.log', 'handoff-r36.log', 'handoff-r37.log'):
    for line in open(S/h, errors='replace'):
        if 'claim' not in line.lower(): continue
        for sh in set(re.findall(r'\b([0-9a-f]{16})', line)):
            sd = re.findall(r'seeds?\s*=?\s*\[?([\d, ]+)', line)
            claims.setdefault(sh, set()).add((line.split()[1], line[:20]))
live = {}
for t in glob.glob(str(S/'take-*-r37/take.tsv')):
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: n = int(r['n']); live[n] = min(live.get(n, 9), float(r['new']))
        except Exception: pass
rows = []
EXTRA = [l.strip() for l in open(S/'take-border-r37/work/rank/extra.txt')] if (S/'take-border-r37/work/rank/extra.txt').exists() else []   # r37: rewalked donors (brief 6h)
for p in sorted(glob.glob(str(S/'take-*-r3[4-7]/near/*.csv'))) + EXTRA:
    m = re.match(r'(\d+)[-_.]', Path(p).name)
    if not m: continue
    n = int(m[1])
    if n in OUT or n not in board: continue
    sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    try: s = side(p)
    except Exception as e: continue
    sc = s/math.sqrt(n) - 1
    above = sc - bar[n]
    bgap = bar[n] - (board[n]/math.sqrt(n) - 1)
    room = bgap - above
    nclaim = len(claims.get(sha[:16], ()))
    rows.append((room, n, above, bgap, nclaim, sha[:16], p, live.get(n)))
rows.sort(reverse=True)
seen = set()
with open(S/'take-border-r37/work/rank/donors.tsv', 'w') as f:
    f.write('room\tn\tabove\tboardgap\tclaims\tsha16\tpath\tlive\n')
    for r in rows:
        if r[6].split('/near/')[1] in seen: continue
        seen.add(r[6].split('/near/')[1])
        f.write('\t'.join(map(str, (f'{r[0]:.3e}', r[1], f'{r[2]:.3e}', f'{r[3]:.3e}', r[4], r[5], r[6], r[7]))) + '\n')
