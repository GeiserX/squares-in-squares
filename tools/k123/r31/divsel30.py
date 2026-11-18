"""sel21.py OUT.txt K LOG [LOG ...]: quench list from k123_join.py scan logs (sel20.py of round 20 without its
round 19 skip list). Keeps counts at the start's m whose bar is above the board, scores each start by
base = room + d - max(r, 0), keeps the K best starts of each count with base >= -0.03 (one per base to 1e-4),
and orders by rank in the count, then by the board gap in score. Lines: n tag dir d bar base gap."""
import csv, math, re, sys, os
out, K, logs = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
B = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open('board.tsv'), delimiter='\t')}
ALLOW={int(n) for n in os.environ.get('K123_ALLOW_BOARD_COUNTS','').split(',') if n}
rows = {}
for lg in logs:
    d = 'scan' + re.search(r'scan(\w+)\.log', lg).group(1)
    for l in open(lg):
        q = re.match(r'(\d+)(r?) \+ (\d+)(r?): n (\d+) m (\d+) k (-?\d+)  start ([\d.]+) \(d ([\d.]+), gap (\S+), r (\S+), perp (\S+)\)  bar ([\d.]+)  room (\S+)  (\S+) WRITTEN', l)
        if not q:
            continue
        nx, rx, ny, ry, n2, m2, k, start, dd, gap, r, perp, bar, room, tag = q.groups()
        n2, m2, bar = int(n2), int(m2), float(bar)
        if int(bar) != m2 or (bar - B.get(n2, 9e9) < 1e-6 and n2 not in ALLOW):
            continue
        if nx + rx == ny + ry and tag.endswith('-s0'):
            continue
        base = float(room) + float(dd) - max(float(r), 0.0)
        if base < -0.03:
            continue
        rows.setdefault(n2, []).append((-base, tag, d, dd, bar))
lines = []
for n2, v in rows.items():
    v.sort(); seen = set(); keep = []
    for b, tag, d, dd, bar in v:
        m=re.search(r'-j(\d+)-',tag);key = (round(b, 4),int(m[1])//6)
        if key in seen:
            continue
        seen.add(key); keep.append((b, tag, d, dd, bar))
        if len(keep) >= K:
            break
    gap = max(0.0, (keep[0][4] - B.get(n2, 0)) / math.sqrt(n2))
    for i, (b, tag, d, dd, bar) in enumerate(keep):
        lines.append((i, -gap, b, n2, tag, d, dd, bar))
lines.sort()
with open(out, 'w') as h:
    for i, g, b, n2, tag, d, dd, bar in lines:
        h.write('%d\t%s\t%s\t%s\t%.6f\t%+.6f\t%+.3e\n' % (n2, tag, d, dd, bar, -b, -g))
print(len(lines), 'starts,', len(rows), 'counts')
