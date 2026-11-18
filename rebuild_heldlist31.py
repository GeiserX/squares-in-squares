"""heldlist31.py: extract every bar31 row (gather/round30-2026-11-15c.csv) to work/held31/<n>.csv and rank the held
rows for a first 900 s kick (probe 120 s). Per n: the bar31 score, the board side gap (main-r17/gap-by-n.tsv board_L),
the latest round table that lists n (its source cell), how many kick or claim lines of handoff-r28..r31 name the n,
and whether the side fraction repeats in another n (a rigid construction). Writes work/heldlist31.tsv."""
import csv, glob, math, os, re, collections
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
csv.field_size_limit(1 << 28)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(W + 'bar31.tsv'), delimiter='\t')}
bar30 = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r30/work/bar30b.tsv'), delimiter='\t')}
rows = collections.defaultdict(list)
for r in csv.DictReader(open(S + 'gather/round30-2026-11-15c.csv')):
    rows[int(r['n'])].append(r)
for n, rr in rows.items():
    p = W + 'held31/%d.csv' % n
    if not os.path.isfile(p):
        with open(p, 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in rr:
                w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
board = {}
for r in csv.DictReader(open(S + 'main-r17/gap-by-n.tsv'), delimiter='\t'):
    board[int(r['n'])] = float(r['board_L'])
src = {}
R = 'results/'
tabs = sorted(glob.glob(R + 'round*-best-*.tsv'), key=lambda f: int(re.search(r'round(\d+)-', f).group(1)))
tabs.append(S + 'take-assemble-r30/round30-best-2026-11-15.tsv')
for f in tabs:
    rd = int(re.search(r'round(\d+)-', f).group(1))
    try:
        for r in csv.DictReader(open(f), delimiter='\t'):
            try:
                src[int(r['n'])] = (rd, ' '.join((r.get('source') or '').split())[:300], (r.get('licence') or '')[:120])
            except Exception:
                pass
    except Exception:
        pass
kicks = collections.Counter()
KRX = re.compile(r'kick|claim', re.I)
for h in ('handoff-r28.log', 'handoff-r29.log', 'handoff-r30.log', 'handoff-r31.log'):
    if not os.path.isfile(S + h):
        continue
    for l in open(S + h, errors='replace'):
        if not KRX.search(l):
            continue
        for m in set(re.findall(r'\bn ?= ?(\d+)\b', l)) | set(re.findall(r'/(\d+)(?:\.csv|-)', l)):
            kicks[(h[8:11], int(m))] += 1
frac = collections.Counter('%.8f' % ((1 + bar[n]) * math.sqrt(n) % 1) for n in bar)
with open(W + 'heldlist31.tsv', 'w') as g:
    g.write('n\tbar31\tside\tboard_gap_side\tnew_in_r30\tkicks_r28\tkicks_r29\tkicks_r30\tkicks_r31\tfrac_repeat\tround\tsource\tlicence\n')
    for n in sorted(bar):
        side = (1 + bar[n]) * math.sqrt(n)
        g.write('%d\t%r\t%.10f\t%.3e\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\n' % (
            n, bar[n], side, side - board.get(n, side), int(bar[n] < bar30.get(n, 9) - 1e-12),
            kicks[('r28', n)], kicks[('r29', n)], kicks[('r30', n)], kicks[('r31', n)],
            frac['%.8f' % (side % 1)] - 1, src.get(n, ('', '', ''))[0], src.get(n, ('', '', ''))[1], src.get(n, ('', '', ''))[2]))
print('ok', len(bar))
