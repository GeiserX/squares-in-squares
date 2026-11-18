"""Border r29: grow1 jobs at the integer band edge (one-shot queue, boxA, light python).
At each m the first n of the band where we hold the plain grid (side exactly m) is n_low = m*m - k_max. The board of
2026-11-09 holds a tilted packing below m at four such n_low (605, 762, 877, 937, and 1000), and backlog r29 put 90
(m = 10, the plain grid before) at 9.99404 from a public layout. Our layout of n_low - 1 sits 0.003 to 0.024 below m.
Test: midm_scan.py --modes grow1 puts one square into the widest hole of our n_low - 1 layout and quenches it with fq
(flag sets d, t, k, K); any end below m - 1e-9 is a find. Donors must have a clean recorded source: rows of the held
file only when a results/round*-best table names their source (a row from 'seed merged0' stays out), or a live take.
The jobs go into kq/ (kfeed29.py collects and certifies the finds)."""
import csv, glob, hashlib, json, math, re, subprocess, sys, time
from pathlib import Path
csv.field_size_limit(1 << 28)
W = Path(__file__).parent; S = W.parent.parent; T = W.parent; D = W / 'kq'
R = Path('results')
HELD = S / 'gather/round27-2026-11-15b.csv'
REMOTE = 'boxC:scratch/squares-border-r29/'
fs = sorted(glob.glob(str(R / 'round*-best-*.tsv')), key=lambda f: (int(re.search(r'round(\d+)', f)[1]), f), reverse=True)
def canon(n):
    for f in fs:
        for r in csv.DictReader(open(f), delimiter='\t'):
            if r.get('n') == str(n): return Path(f).name, r
    return None, None
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
# (target, donor source): 'held' = the held row of n-1, or a take csv path
PLAN = [(937, 'held', 1500), (91, str(S / 'take-backlog-r29/90.csv'), 600), (762, 'held', 1500), (133, 'held', 600), (605, 'held', 1500),
        (345, 'held', 600), (158, 'held', 600), (1000, 'held', 1500)]
if len(sys.argv) > 1: PLAN = [p for p in PLAN if str(p[0]) in sys.argv[1:]]
need = {t for t, _, _ in PLAN} | {t - 1 for t, _, _ in PLAN}
rows = {}
for r in csv.DictReader(open(HELD)):
    n = int(r['id'].split('_')[0]) if 'id' in r and '_' in r['id'] else int(r.get('n', 0))
    if n in need: rows.setdefault(n, []).append(r)
def write(path, n, rr):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, r in enumerate(rr):
            a = r['angle'] if 'angle' in r else r['deg']
            w.writerow([n, i, r['x'].lstrip('s'), r['y'].lstrip('s'), a.lstrip('s')])
index = json.load(open(D / 'index.json')) if (D / 'index.json').exists() else {}
for tgt, dsrc, sec in PLAN:
    d = tgt - 1
    if dsrc == 'held':
        f, cr = canon(d)
        if not cr: log(f'BOUNDARY {tgt}: the held row of {d} has no results/round*-best source (seed merged0); skipped'); continue
        drows = rows[d]; src_text = f'the held row n={d} of gather/round27-2026-11-15b.csv; results/{f} n={d}: {cr["source"]}'; lic = cr.get('licence', '')
    else:
        drows = list(csv.DictReader(open(dsrc)))
        trow = next((r for r in csv.DictReader(open(Path(dsrc).parent / 'take.tsv'), delimiter='\t') if r['n'] == str(d)), None)
        src_text = f'{dsrc}, from {Path(dsrc).parent}/take.tsv: {trow["source"] if trow else ""}'; lic = trow.get('licence', '') if trow else ''
    tmpd = W / 'staged' / f'bnd-{tgt}-donor.csv'; write(tmpd, d, drows)
    tmps = W / 'staged' / f'bnd-{tgt}-sub.csv'; write(tmps, tgt, rows[tgt])
    db = tmpd.read_bytes(); sb = tmps.read_bytes()
    ident = 'b' + hashlib.sha256(db + sb).hexdigest()[:11]
    if ident in index: continue
    (D / 'nin' / f'{ident}_{tgt}.csv').write_bytes(sb); (D / 'nin' / f'{ident}_{tgt}.donors.csv').write_bytes(db)
    seed = int(hashlib.sha256(db).hexdigest()[:6], 16) % 1000
    (D / 'jobs' / f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{tgt}.csv', donors=f'nin/{ident}_{tgt}.donors.csv', out=f'nout/{ident}_{tgt}', n=tgt, seconds=sec, seed=seed, modes='grow1', priority=-50 if tgt > 500 else -40)))
    index[ident] = dict(path=str(HELD) if dsrc == 'held' else dsrc, n=tgt, sha256=hashlib.sha256(sb).hexdigest(), side=float(math.ceil(math.sqrt(tgt))), gap=0.0, seed=seed,
                        boundary=dict(donor_n=d, source_text=src_text, licence=lic, donor_sha256=hashlib.sha256(db).hexdigest(), seconds=sec), t=time.time())
    tmp = D / 'index.tmp'; tmp.write_text(json.dumps(index)); tmp.replace(D / 'index.json')
    with open(S / 'handoff-r29.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan grow1 (seed {seed}) of n={tgt} at the integer band edge: our n={d} layout plus one square in its widest hole, then fq; donor sha256 {hashlib.sha256(db).hexdigest()[:16]} ({src_text[:160]})\n')
    log(f'BOUNDARY queue {tgt}: grow1 from the n={d} layout ({src_text[:200]}), donor sha256 {hashlib.sha256(db).hexdigest()[:16]}, {sec} s, seed {seed}; boxC kq job {ident}; find = any end below side {math.ceil(math.sqrt(tgt))} - 1e-9')
subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
