"""Solve one immutable table job in the spare remote slot."""
import os
from pathlib import Path
import pickle
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules as M

if __name__ == '__main__':
    src, out = map(Path, sys.argv[1:3])
    q = pickle.load(src.open('rb'))
    from modules_policy24 import piece
    if piece(q)['status'] != 'none':
        print(q['id'], 'deferred source group', flush=True)
        sys.exit(0)
    t = M.tabulate(q)
    valid = t.get('tab') is not None if q['kind'] == 'corner' else t.get('knots') is not None
    if valid:
        with out.with_suffix('.tmp').open('wb') as h:
            pickle.dump([(q, t)], h)
        os.replace(out.with_suffix('.tmp'), out)
    print(q['id'], 'table valid', valid, flush=True)
