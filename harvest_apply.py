#!/usr/bin/env python3
"""Copy merged per-n winners into a running driver's state, where they are better.

  python3 harvest_apply.py MERGED_DIR STATE_DIR [--mod K,R]

MERGED_DIR is harvest_merge.py's --out (best.tsv + best/<n>.csv). For each n
(in the K,R residue class, if given) whose merged score beats STATE/best/<n>.score,
the csv and score are replaced atomically, csv first; drive.py reads both
fresh on every job, so a running driver picks them up without a restart. Every
replacement is appended to STATE/imports.tsv.
"""
import argparse, csv, math, os, pathlib, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('merged', type=pathlib.Path)
    ap.add_argument('state', type=pathlib.Path)
    ap.add_argument('--mod')
    a = ap.parse_args()
    mod = tuple(int(x) for x in a.mod.split(',')) if a.mod else None
    best = a.state / 'best'
    n_done, gain = 0, 0.0
    for r in csv.DictReader(open(a.merged / 'best.tsv'), delimiter='\t'):
        n, s = int(r['n']), float(r['score'])
        if mod and n % mod[0] != mod[1]:
            continue
        sp = best / f'{n}.score'
        old = float(sp.read_text()) if sp.exists() else math.inf
        if s < old - 1e-13:
            tmp = best / f'{n}.csv.import'
            tmp.write_bytes((a.merged / 'best' / f'{n}.csv').read_bytes())
            os.replace(tmp, best / f'{n}.csv')
            tmp = best / f'{n}.score.import'
            tmp.write_text(repr(s) + '\n')
            os.replace(tmp, sp)
            with open(a.state / 'imports.tsv', 'a') as h:
                h.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\t{n}\t{old!r}\t{s!r}\t{r['source']}\n")
            n_done += 1
            gain += (old - s) if math.isfinite(old) else 0
    print(f'{a.state}: imported {n_done} puzzles, gain {gain:.10f}')


if __name__ == '__main__':
    main()
