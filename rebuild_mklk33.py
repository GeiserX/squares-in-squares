"""mklk33.py: the round 33 rebuild share of override 6b/8. Held round 32 a rows of n 700 to 1000 whose bytes no lkick claim of
handoff-r29..r33 names (any lane), not a 45-degree lattice row (known list, or every tilted square at 45 degrees), side not
p/q (q<=40) nor a+b*sqrt(2)/2, side fraction not shared with another n. List 1: held side above the 2026-11-09 board side
(largest board gap first); list 2: at or below it (largest n first). Writes work/lkorder.txt and work/lkskip.tsv."""
import csv, hashlib, math, re, collections
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r33/work/'
LATTICE = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(W + 'bar33.tsv'), delimiter='\t')}
side = {n: (b + 1) * math.sqrt(n) for n, b in bar.items()}
board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(S + 'main-r17/gap-by-n.tsv'), delimiter='\t')}
frac = collections.Counter(round(s % 1, 9) for n, s in side.items() if n > 1)
lk = []
for k in (29, 30, 31, 32, 33):
    for l in open(S + 'handoff-r%d.log' % k, errors='replace'):
        if 'invent_rest' in l or ('lkick' in l and 'midm' not in l):
            lk.append([h.lower() for h in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{12,64})(?![0-9a-fA-F])', l)])
def closed(s):
    for q in range(1, 41):
        if abs(s * q - round(s * q)) < 1e-8 * q:
            return 'p/q q=%d' % q
    for b in range(0, 100):
        a = s - b * math.sqrt(2) / 2
        if abs(a - round(a)) < 1e-8:
            return 'a+b*sqrt2/2 b=%d' % b
    return ''
def lattice45(n):
    if n in LATTICE:
        return 'known lattice n'
    tilt = []
    for r in csv.DictReader(open(W + 'held33/%d.csv' % n)):
        a = float(str(r['angle']).lstrip('s')) % 90
        if min(a, 90 - a) > 1e-6:
            tilt.append(a)
    if tilt and all(abs(a - 45) < 1e-6 for a in tilt):
        return 'every tilted square at 45 degrees'
    return ''
l1, l2, skip = [], [], []
for n in range(700, 1001):
    sha = hashlib.sha256(open(W + 'held33/%d.csv' % n, 'rb').read()).hexdigest()
    why = lattice45(n) or closed(side[n]) or ('shared side fraction' if frac[round(side[n] % 1, 9)] > 1 else '')
    if not why and any(any(sha.startswith(h) for h in hx) for hx in lk):
        why = 'lkicked before (claim names the bytes)'
    if why:
        skip.append((n, why)); continue
    g = side[n] - board.get(n, side[n])
    (l1 if g > 1e-9 else l2).append((n, g))
l1.sort(key=lambda x: -x[1]); l2.sort(key=lambda x: -x[0])
with open(W + 'lkorder.txt', 'w') as f:
    for n, g in l1:
        f.write('%d\tlist 1: held side %.3e above the 2026-11-09 board side, first lkick of this geometry\n' % (n, g))
    for n, g in l2:
        f.write('%d\tlist 2: held side at or below the board side (gap %.3e), first lkick of this geometry\n' % (n, g))
with open(W + 'lkskip.tsv', 'w') as f:
    for n, w in skip:
        f.write('%d\t%s\n' % (n, w))
print('list1', len(l1), 'list2', len(l2), 'skip', len(skip), collections.Counter(w.split(' ')[0] for _, w in skip))
