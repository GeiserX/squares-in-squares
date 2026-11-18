# Credit required: reuse of this file, its layouts or its ideas must credit Sergio Fernández Rubio (GeiserX, https://github.com/GeiserX/squares-in-squares). See NOTICE and AI_NOTICE.md.
"""Score a submission the way Kaggle does: pandas default read, to_csv, then the metric.

Usage: pdscore.py <submission.csv> <jobs>. Prints the total and every n that fails.
"""
import sys, math
from multiprocessing import Pool
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd, kaggle_metric as km
def work(a):
    n, rows = a
    try: return km.evaluate_single_puzzle(n, rows)
    except Exception as e: return (n, km.infeasible_score(n), None, f'err {e}')
if __name__ == '__main__':
    df = pd.read_csv(sys.argv[1])  # default dtypes, as a plain Kaggle loader would
    df = df.drop(columns=['id'])
    pz = km._parse_submission_csv(df.to_csv(index=False))
    with Pool(int(sys.argv[2])) as p:
        res = list(p.imap_unordered(work, sorted(pz.items()), chunksize=1))
    tot = math.fsum(r[1] for r in res) + sum(km.infeasible_score(n) for n in range(1,1001) if n not in pz)
    bad = sorted((r[0], r[3]) for r in res if r[3] != 'ok')
    print('total', f'{tot:.10f}', 'not-ok', len(bad))
    for b in bad: print(*b, sep='\t')
