"""scancert30.py SCAN.tsv [K]: certify (finesafe, rt30.cert) the K lowest files per n of a scanwork30 output that are below bar30,
skipping n in EXCL; prints n, score, gain, path; certs in work/scancert/<n>-<sha12>.csv; results cached in work/scancert.json."""
import csv, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rt31 as rt
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
K = int(sys.argv[2]) if len(sys.argv) > 2 else 3
EXCL = {639, 691, 745, 858, 918}
C = W + 'scancert.json'
cache = json.load(open(C)) if os.path.isfile(C) else {}
by = {}
for l in open(sys.argv[1]):
    if l.startswith(('#', 'DONE')):
        continue
    n, side, g, p = l.rstrip('\n').split('\t')
    by.setdefault(int(n), []).append((float(g), p))
for n in sorted(by, key=lambda n: -max(g for g, _ in by[n])):
    if n in EXCL:
        continue
    for g, p in sorted(by[n], reverse=True)[:K]:
        try:
            sha = hashlib.sha256(open(S + p, 'rb').read()).hexdigest()
        except OSError:
            continue
        if sha not in cache:
            out = W + 'scancert/%d-%s.csv' % (n, sha[:12])
            s = rt.cert(n, S + p, out, bar[n])
            cache[sha] = {'n': n, 'path': p, 'score': s, 'cert': out if s is not None else None}
            json.dump(cache, open(C, 'w'), indent=1)
        v = cache[sha]
        print('%d\t%s\t%s\t%s' % (n, v['score'], ('%.3e' % (bar[n] - v['score'])) if v['score'] is not None else '-', p), flush=True)
