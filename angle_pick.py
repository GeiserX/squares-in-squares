"""per n: side of the base, the pol1 file and the pol2 file; copy the smallest that beats the base into OUT/"""
import sys, os, csv, shutil, math
sys.path.insert(0,'.')
from engine_lib import load, normalize
base, out, dirs = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
P = load(base); tot = 0.0
ns = sorted({int(f[:-4]) for d in dirs for f in os.listdir(d) if f[:-4].isdigit() and f.endswith('.csv')})
for n in ns:
    sb = normalize(P[n])[0]; best = (sb, None)
    for d in dirs:
        f = '%s/%d.csv' % (d, n)
        if os.path.exists(f):
            s = normalize([(float(r['x']),float(r['y']),float(r['angle'])) for r in csv.DictReader(open(f))])[0]
            if s < best[0] - 1e-11: best = (s, f)
    print(n, '%.10f' % sb, '%.10f' % best[0], best[1] or 'BASE-KEPT', '%.2e' % ((sb - best[0]) / math.sqrt(n)))
    if best[1]: shutil.copy(best[1], '%s/%d.csv' % (out, n)); tot += (sb - best[0]) / math.sqrt(n)
print('total gain over base %.4e, files %d' % (tot, len(os.listdir(out))))
