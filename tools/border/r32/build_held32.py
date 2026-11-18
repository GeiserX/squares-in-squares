"""r31: held rows of the round 31 b file (bar31) that no kick or claim line of handoff-r29..r31 names by n.
Writes held32/<n>.csv (the submitted bytes of that n), held32/<n>.csv.json (a short record that points at the
results table row), and held32/order.json (n -> board score gap, largest first) plus held32/info.json."""
import csv, json, math, re, hashlib, sys
from pathlib import Path
csv.field_size_limit(1 << 30)
S = Path('$SCRATCH/bounties-squares'); W = S / 'take-border-r32/work'; H = W / 'held32'
R = Path('results')
SUB = S / 'gather/round31-2026-11-16b.csv'
subsha = hashlib.sha256(SUB.read_bytes()).hexdigest()
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round32-briefs/bar32.tsv'), delimiter='\t')}
rows = {}
for r in csv.DictReader(open(SUB)):
    rows.setdefault(int(r['n']), []).append(r)
tables = sorted(R.glob('round*-best-*.tsv'), key=lambda p: int(re.match(r'round(\d+)', p.name)[1]))
last = {}
for t in tables:
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: last[int(r['n'])] = (t.name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError): pass
named = {}
for h, skip_own in (('handoff-r30.log', False), ('handoff-r32.log', False), ('handoff-r32.log', True)):
    p = S / h
    if not p.exists(): continue
    for line in open(p, errors='replace'):
        if skip_own and ' border -> ' in line: continue
        if not re.search(r'kick|claim', line, re.I): continue
        for m in re.finditer(r'\bn\s*=\s*(\d+)', line): named.setdefault(int(m[1]), h)
gap = {}
for r in csv.DictReader(open(S / 'main-r17/gap-by-n.tsv'), delimiter='\t'):
    n = int(r['n']); side = (bar[n] + 1) * math.sqrt(n); gap[n] = (side - float(r['board_L'])) / math.sqrt(n)
fr = {}
for n, b in bar.items():
    s = (b + 1) * math.sqrt(n); fr.setdefault(round(s - math.floor(s), 8), []).append(n)
info = {}
for n in sorted(rows):
    tab = last.get(n); text = (tab[1] + ' ' + tab[2]) if tab else ''
    bad = bool(re.search(r'prvsiyan/squares-verified-best-of-1105|CC BY-SA', text)) or (n in (639, 691, 745, 858, 918) and 'penguin069' in text) or n in (639, 691, 745, 858, 918, 980)
    s = (bar[n] + 1) * math.sqrt(n)
    rigid = len(fr[round(s - math.floor(s), 8)]) >= 3   # r31: a fraction shared by 3 or more n marks a closed form; a pair is a border step (539 = 494 + strip)
    plain_pub = bool(tab) and bool(re.match(r'\W*harvest lane', tab[1])) and not re.search(r'kick|fq quench of|island|soft|LP', tab[1][:400], re.I)
    seed = bool(re.search(r'Samanyu', text))
    info[n] = dict(table=tab[0] if tab else None, named=named.get(n), gap=gap.get(n), rigid=rigid, plain_public=plain_pub, seed=seed, bad=bad)
    out = H / f'{n}.csv'
    with open(out, 'w') as f:
        w = csv.writer(f); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in rows[n]: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    src = (f'held n = {n} of round 31 b (the submitted packing gather/round31-2026-11-16b.csv, sha256 {subsha}, gate '
           f'gate/cand-round31-1116b, bar32 source "held round31-2026-11-16b"; a row of a file we submitted is our own layout, '
           f'round 32 override 2); its source and licence: the row of n = {n} in results/{tab[0]}' if tab else
           f'held n = {n} of round 31 b (gather/round31-2026-11-16b.csv, sha256 {subsha}); no results/round*-best table holds n = {n}: its row is older than round 7, see the held-file chain')
    lic = (f'own layout (held row); upstream as results/{tab[0]} records' if tab else 'own layout (held row)')
    Path(str(out) + '.json').write_text(json.dumps(dict(source=src, licence=lic, n=n, sha256=hashlib.sha256(out.read_bytes()).hexdigest(), held_file=str(SUB), held_sha256=subsha)))
order = {n: v['gap'] for n, v in info.items() if not v['named'] and not v['bad'] and v['gap'] is not None and v['gap'] >= 1e-7 and not v['rigid']}
order = dict(sorted(order.items(), key=lambda kv: (info[kv[0]]['plain_public'], -kv[1])))
# r32: prior 900 s kicks of the same row. A row that round 31 b did not change kept the round 30 c bytes, so every r31
# kick or claim line that names its n kicked these bytes (other lanes pin their own copies, so a sha256 match misses them).
bar31 = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round31-briefs/bar31.tsv'), delimiter='\t')}
full31, probe31 = {}, {}
for line in open(S / 'handoff-r31.log', errors='replace'):
    if not re.search(r'kick|claim', line, re.I) or not re.search(r'\b900\s*s|900s', line): continue
    probed = bool(re.search(r'probe[^0-9]{0,4}(?:60|90|120)|(?:60|90|120)\s*s probe', line, re.I))
    for m in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)):
        (probe31 if probed else full31)[m] = (probe31 if probed else full31).get(m, 0) + 1
for n, v in info.items():
    v['changed31'] = bar.get(n, 0) < bar31.get(n, 0) - 1e-15
    v['full31'] = 0 if v['changed31'] else full31.get(n, 0)
    v['probe31'] = 0 if v['changed31'] else probe31.get(n, 0)
(H / 'order.json').write_text(json.dumps(order)); (H / 'info.json').write_text(json.dumps(info))
print('changed in round 31 b', sum(v['changed31'] for v in info.values()), 'unprobed 900 s r31 kick lines', sum(full31.values()), 'probed', sum(probe31.values()))
print('held rows', len(rows), 'open (unnamed, gap>=1e-7, not rigid, not excluded)', len(order))
print('named in r30..r32 kick/claim lines', len(named), 'rigid', sum(v['rigid'] for v in info.values()))
print('open with n>=300', sum(1 for n in order if n >= 300), 'plain public among open', sum(info[n]['plain_public'] for n in order), 'seed among open', sum(info[n]['seed'] for n in order))
print(list(order.items())[:40])
