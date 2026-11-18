"""forensics_fqpol.py FQ IN_DIR OUT_DIR WORKER NWORKERS [DEADLINE_EPOCH] [FLAGS]: one fq polish quench (the POLISH flags of midm_scan.py,
or with FLAGS = d the fq default: loosen 1.02, ALM, polish) of every per-n csv in IN_DIR whose index modulo NWORKERS
is WORKER; writes OUT_DIR/<name>.csv when fq returns a layout."""
import sys, os, csv, glob, tempfile, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midm_scan as ms, forensics_compose as fc
fq, ind, out, wk, nw = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
dl = float(sys.argv[6]) if len(sys.argv) > 6 else 1e18
flags = () if len(sys.argv) > 7 and sys.argv[7] == 'd' else ms.POLISH
os.makedirs(out, exist_ok=True)
for i, p in enumerate(sorted(glob.glob(ind + '/*.csv'))):
    if i % nw != wk:
        continue
    if time.time() > dl:
        print('deadline'); break
    name = os.path.basename(p)[:-4]; n = int(name.split('-')[0])
    if os.path.exists('%s/%s.csv' % (out, name)):
        continue
    sq = [(float(r['x'].lstrip('s')), float(r['y'].lstrip('s')), float(r['angle'].lstrip('s'))) for r in csv.DictReader(open(p))]
    s, Q = fc.frame(sq)
    X = np.column_stack([Q[:, 0], Q[:, 1], np.degrees(Q[:, 2])])
    t = time.time(); s2, Y = ms.quench(fq, tempfile.gettempdir(), s, X, flags, timeout=600)
    if Y is None:
        print(name, 'no layout', flush=True); continue
    fc.write_csv('%s/%s.csv' % (out, name), n, ms.from_fq(Y))
    print(name, 'side in %.12f out %.12f  %.0f s' % (s, s2, time.time() - t), flush=True)
