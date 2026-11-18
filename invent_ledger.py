#!/usr/bin/env python3
"""Coverage ledger of the soft chain: which held layouts never had a pass.

Reads the round tables (results/round*-best-*.tsv: the newest step of each held n), the gate details of each
round (how far that step moved its n) and the soft lane's plans of rounds 11 to 16 (take-soft-r*/work/plan.json:
which packings had a start). A layout had a pass when a soft start has the held score to 2e-9.

Usage: invent_ledger.py OUT.tsv
Output columns: n, round, kind, moved, board_gap, soft_starts_on_held, soft_starts_any, source, licence.
Our own code. Reads tables only.
"""
import csv, glob, json, os, re, sys
S = '$SCRATCH/bounties-squares'
LANE = '.'
def kind_of(src):
    if src.startswith('own soft-box'): return 'soft'
    if src.startswith('family_step'): return 'family'
    if src.startswith('family_readers'): return 'readers'
    if src.startswith('modules.py'): return 'modules'
    if src.startswith('fq quench of one border') or 'border_sweep' in src: return 'border'
    if src.startswith('zone_') or 'zone_corner' in src or 'zone_search' in src or 'zone_lowf' in src: return 'corners'
    if src.startswith('fq quench'): return 'polish'
    if src.startswith('inflate.py'): return 'inflate'
    return 'harvest'
gates = {9: 'cand-round9-1111a', 10: 'cand-round10-1111a', 11: 'cand-round11-1111b', 12: 'cand-round12-1112a', 13: 'cand-round13-1112a',
         14: 'cand-round14-1112a', 15: 'cand-round15-1112a'}
det = {}
for r, d in gates.items():
    p = '%s/gate/%s/details.csv' % (S, d)
    if os.path.exists(p):
        det[r] = {int(x['n']): float(x['score']) for x in csv.DictReader(open(p))}
held = det[15]
newest = {}
for p in sorted(glob.glob(LANE + '/results/round*-best-*.tsv'), key=lambda p: int(re.search(r'round(\d+)-', p).group(1))):
    r = int(re.search(r'round(\d+)-', p).group(1))
    for x in csv.DictReader(open(p), delimiter='\t'):
        if x.get('source'):
            newest[int(x['n'])] = (r, x['source'], x.get('licence') or '')
# soft starts of every round: n -> list of (round, start score, kind)
soft = {}
for p in sorted(glob.glob(S + '/take-soft-r*/work/plan.json')):
    r = int(re.search(r'soft-r(\d+)', p).group(1))
    for j in json.load(open(p))['jobs']:
        if j.get('skipped'): continue
        soft.setdefault(j['n'], []).append((r, j['start'], j.get('kind')))
gap = {}
for l in open(S + '/main-r17/gap-by-n.tsv'):
    a = l.split('\t')
    if a[0] != 'n': gap[int(a[0])] = float(a[6])
rows = []
for n in range(300, 1001):
    if n not in newest: continue
    r, src, lic = newest[n]
    k = kind_of(src)
    moved = det[r - 1][n] - det[r][n] if (r in det and r - 1 in det) else float('nan')
    had = [s for s in soft.get(n, []) if abs(s[1] - held[n]) < 2e-9]
    rows.append((n, r, k, moved, gap.get(n, 0.0), len(had), len(soft.get(n, [])), src[:90], lic))
with open(sys.argv[1], 'w') as h:
    h.write('n\tround\tkind\tmoved\tboard_gap\tsoft_starts_on_held\tsoft_starts_any\tsource\tlicence\n')
    for x in rows:
        h.write('%d\t%d\t%s\t%.3e\t%.3e\t%d\t%d\t%s\t%s\n' % x)
import collections
c = collections.Counter(); u = collections.Counter()
for x in rows:
    c[x[2]] += 1
    if x[5] == 0: u[x[2]] += 1
print('held n of 300 and more with a named newest step:', len(rows))
for k in c: print('  %-8s held %3d   no soft start on the held packing %3d' % (k, c[k], u[k]))
