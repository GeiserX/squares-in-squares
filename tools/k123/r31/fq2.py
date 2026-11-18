"""fq2.py IN.csv N OUTDIR FQ BAR: the fq loop of midm_fqonce.py (default flags, then the deep flags, up to three
rounds) on one file. It writes OUTDIR/raw/<N>-fq2.csv when the side ends below BAR by 1e-9. One line on stdout.
Why: in round 20 one such loop took the 910 of a join 3.8e-3 lower after the single tight quench of k123_turn.py."""
import os, sys, pathlib
sys.path.insert(0, os.path.expanduser('$SCRATCH/squares-k123/lane'))
import methods_lp as mlp  # noqa: E402
from midm_scan import to_fq, from_fq, quench, POLISH, write_raw  # noqa: E402
p, n, out, fq, bar = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5])
tmp = out + '/tmp2'; os.makedirs(tmp, exist_ok=True)
P = mlp.load(p, {n})[n]; s, X = to_fq(P); s0 = s
if abs(s-bar)<1e-5:
    print("fq2 skip near tie %.12f bar %.12f" % (s,bar),flush=True)
    sys.exit(0)
base = 1.0
key = os.path.basename(out)
try:
    for line in open(os.path.expanduser('$SCRATCH/squares-k123/queue.tsv')):
        w = line.rstrip('\n').split('\t')
        if len(w)>7 and '%s-%s-%s' % (w[7],w[0],w[1]) == key:
            base = float(w[5]); break
except OSError:
    pass
hotp=pathlib.Path(os.path.expanduser('$SCRATCH/squares-k123/priority-pools.txt'))
hot=hotp.read_text().split() if hotp.exists() else []
deep = base >= 0 or any(key.startswith(v+'-') for v in hot)
flags = ((), POLISH) if deep else ((),)
for rnd in range(3 if deep else 1):
    imp = False
    for fl in flags:
        s2, X2 = quench(fq, tmp, s, X, fl)
        if s2 is not None and s2 < s - 3e-9:
            s, X, imp = s2, X2, True
    if not imp:
        break
if s < bar - 1e-9:
    write_raw(out, n, from_fq(X), 'fq2')
print('fq2 %.12f -> %.12f bar %.12f %+.3e' % (s0, s, bar, s - bar), flush=True)
