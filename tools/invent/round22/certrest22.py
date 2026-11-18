# Certify round 22 runs after their certified-input fq quench on boxE.
# Usage: certrest22.py TAKEDIR RAWDIR|SOURCE|LICENCE [...]
# Require floatsafe at 2.2e-11, a score margin greater than 1e-10 against round 20,
# every frozen round 21 take, and every other live round 22 take.
# Write CSVs first and replace take.tsv by rename. Cache only unchanged files.
import csv, glob, json, os, sys
R = '.'; sys.path.insert(0, R)
import floatsafe
S = '$SCRATCH/bounties-squares'
T, specs = sys.argv[1], sys.argv[2:]
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(S + '/gate/cand-round20-1113a/details.csv'))}
bar = dict(held); who = {}
for p in sorted(glob.glob(S + '/take-*-r21/take.tsv') + glob.glob(S + '/take-*-r22/take.tsv')):
    if '/take-invent-r22/' in p: continue
    try:
        for r in csv.DictReader(open(p), delimiter='\t'):
            if r['n'].isdigit() and float(r['new']) < bar[int(r['n'])]: bar[int(r['n'])] = float(r['new']); who[int(r['n'])] = p.split('/')[-2]
    except Exception as ex: print('skip', p, ex)
best = {}
def offer(n, score, rows, src, lic, p):
    if not (score < held[n] - 1e-10): return
    if not (score < bar[n] - 1e-10): print('drop', n, score, 'not below', who.get(n), bar[n], '%.3e' % (score - bar[n]), p); return
    if n not in best or score < best[n][0]: best[n] = (score, rows, src, lic, p)
CF = os.path.dirname(os.path.abspath(__file__)) + '/fs-cache.json'   # path -> [mtime, floatsafe score or None]
try: cache = json.load(open(CF))
except Exception: cache = {}
if os.path.exists(T + '/take.tsv'):
    for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t'):
        n = int(r['n']); p = '%s/%d.csv' % (T, n)
        rows = [{k: x[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for x in csv.DictReader(open(p))]
        mt = os.path.getmtime(p); c = cache.get(p)
        if c and c[0] == mt and c[1] is not None:
            fr, score = rows, c[1]
        else:
            _, fr, score, e = floatsafe.work((n, rows))
            cache[p] = [mt, score if fr is not None else None]
        if fr is not None: offer(n, score, fr, r['source'], r['licence'], p)
for spec in specs:
    raw, src, lic = spec.split('|')
    only = None                                               # RAWDIR#N: only the files of that n (fq-once dirs)
    if '#' in raw: raw, only = raw.split('#')[0], int(raw.split('#')[1])
    last = {}                                                 # n-slSEED-TRY.csv: a later try of one run is lower
    for p in glob.glob(raw + '/*.csv'):
        b = os.path.basename(p)[:-4].split('-')
        key = tuple(b[:2]) if len(b) == 3 and b[2].isdigit() else tuple(b)
        t = int(b[2]) if len(b) == 3 and b[2].isdigit() else 0
        if key not in last or t > last[key][0]: last[key] = (t, p)
    for p in sorted(v[1] for v in last.values()):
        n = int(os.path.basename(p)[:-4].split('-')[0])
        if only is not None and n != only: continue
        mt = os.path.getmtime(p); c = cache.get(p)
        if c and c[0] == mt:                                  # a file seen before: skip floatsafe when it cannot count
            if c[1] is None: print('drop unsafe (cached)', p); continue
            if n in best and c[1] >= best[n][0]: print('skip unchanged lower row held', n, p); continue
            if not (c[1] < held[n] - 1e-10 and c[1] < bar[n] - 1e-10): offer(n, c[1], None, src, lic, p); continue
        rows = [{k: x[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for x in csv.DictReader(open(p))]
        if len(rows) != n: print('drop rows', p); continue
        _, fr, score, e = floatsafe.work((n, rows))
        cache[p] = [mt, score if fr is not None else None]
        if fr is None: print('drop unsafe', p, e); continue
        offer(n, score, fr, src, lic, p)
with open(CF + '.tmp', 'w') as h: json.dump(cache, h)
os.replace(CF + '.tmp', CF)
lines = ['n\theld\tnew\tgain\tsource\tlicence\n']; tot = net = 0.0
for n in sorted(best):
    score, fr, src, lic, p = best[n]
    if os.path.abspath(p) != os.path.abspath('%s/%d.csv' % (T, n)):
        with open('%s/%d.csv.tmp' % (T, n), 'w', newline='') as g:
            w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace('%s/%d.csv.tmp' % (T, n), '%s/%d.csv' % (T, n))
    tot += held[n] - score; net += bar[n] - score
    lines.append('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, src, lic))
    print('keep', n, held[n], score, '%.3e' % (held[n] - score), 'over the bar %.3e' % (bar[n] - score), who.get(n, 'round 20 file'), p)
for p in glob.glob(T + '/*.csv'):
    if int(os.path.basename(p)[:-4]) not in best: os.remove(p)
with open(T + '/take.tsv.tmp', 'w') as h: h.writelines(lines)
os.replace(T + '/take.tsv.tmp', T + '/take.tsv')
print('kept', len(best), 'gain', repr(tot), 'over the bar', repr(net))
