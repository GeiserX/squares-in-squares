"""r37: tools/invent/round36/heldshare.py against the held round 36 b row (the file bar37 names), not round 35 a."""
import sys, csv, numpy as np
sys.path.insert(0, 'tools/invent/round36')
import heldshare as _h
SUB = '$SCRATCH/bounties-squares/gather/round36-2026-11-18b.csv'
_c = {}
def held(n):
    if not _c:
        for r in csv.DictReader(open(SUB)): _c.setdefault(int(r['n']), []).append((float(r['x'].lstrip('s')), float(r['y'].lstrip('s'))))
    return np.array(_c[n])
_h.held = held
share = _h.share
if __name__ == '__main__':
    for p in sys.argv[1:]:
        n, b = share(p); print('%d share1e-3 %.3f share1e-2 %.3f %s' % (n, b[0], b[1], p))
