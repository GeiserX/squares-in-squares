#!/usr/bin/env python3
"""Second check of a take dir, per n, with the gate's own parts (no full gate run):
pandas default read of each per-n file, the unchanged metric, and the gate's independent float64
separating-axis check at 2e-11. Prints one line per n and exits 1 if any n fails or does not beat held.

  literature_check.py HELD_DETAILS.csv TAKE_DIR        (run with python -I)
"""
import csv, glob, importlib.util, io, math, os, sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE))
import pandas as pd  # noqa: E402
import kaggle_metric as km  # noqa: E402

spec = importlib.util.spec_from_file_location('gate', LANE / 'tools' / 'gate.py')
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)


def main():
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(sys.argv[1]))}
    bad, tot = 0, 0.0
    for f in sorted(glob.glob(os.path.join(sys.argv[2], '[0-9]*.csv')), key=lambda p: int(Path(p).stem)):
        df = pd.read_csv(f)   # Kaggle's view
        n = int(df['n'].iloc[0])
        rows = [{k: str(v) for k, v in r.items()} for r in df.to_dict('records')]
        _, s, _, why = km.evaluate_single_puzzle(n, rows)
        gap = gate.sat_min_gap(df[['x', 'y', 'angle']].to_numpy(dtype=float))
        ok = why == 'ok' and len(df) == n and gap >= 2e-11 and s < held[n] - 1e-10
        bad += not ok; tot += held[n] - s if ok else 0.0
        print(n, 'OK ' if ok else 'BAD', 'rows', len(df), 'metric', why, 'score', repr(s), 'held', repr(held[n]),
              'gain %.3e' % (held[n] - s), 'min gap %.2e' % gap, flush=True)
    print('checked; bad', bad, 'gain', repr(tot))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
