#!/usr/bin/env python3
"""The fq quench of a band row, in place of the sequential LP of k123_band3.py build (avenues/k123.md, section 10).

k123_band3.py build opens the box to clear the tolerance of the refill, and the chains turn back while the
box is open. This tool gives the tolerant layout straight to fq with a small loosen, so the chains keep
their turn while the uprights find their places.

  k123_band3q.py DETAILS OUTDIR FQ ROW.json [ROW.json ...] [--loosen 1.001,1.003,1.01]

A row is one json line of k123_band3.py scan. One line per try goes to stdout. A side below the held one by
1e-9 gets the deep polish of midm_scan.py and is written to OUTDIR/raw/<n>-<tag>.csv (raw rows; certify
with methods_take.py on boxA).
Control: the row of m 26, 32 of 33 chains, turn 10.10 must come back to the held side of 680.
Our own code. It imports k123_band3 (layout), midm_scan (quench) and family_step (fold). fq is Evan
Daniel's MIT quench binary, used by path.
"""
import argparse, csv, json, math, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import family_step as fs  # noqa: E402
import k123_band3 as k3  # noqa: E402
import midm_scan as ms  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("details"); ap.add_argument("out"); ap.add_argument("fq"); ap.add_argument("rows", nargs="+")
    ap.add_argument("--loosen", default="1.001,1.003,1.01")
    a = ap.parse_args()
    held = {int(r["n"]): float(r["score"]) for r in csv.DictReader(open(a.details))}
    os.makedirs(a.out, exist_ok=True); tmp = a.out + "/tmp"; os.makedirs(tmp, exist_ok=True)
    for line in a.rows:
        r = json.loads(open(line).read() if os.path.exists(line) else line)
        n = r["m"] * r["m"] + r["k"]
        L, T, F = k3.layout(r)
        if len(F) < n:
            print("row holds %d, not %d" % (len(F), n), flush=True); continue
        if len(F) > n:                                   # drop the uprights nearest a far corner
            up = np.nonzero(np.abs(fs.fold(F[:, 2])) < 1e-9)[0]
            d = np.abs(F[up, 1] - F[up, 0])
            gone = set(up[np.argsort(-d)][:len(F) - n].tolist())
            F = F[[i for i in range(len(F)) if i not in gone]]
        Ln = (held[n] + 1) * math.sqrt(n); best = Ln
        for lo in a.loosen.split(","):
            tag = "w%d-ab%d%d-n%d-i%d-%s-phi%.3f-tau%.2f-lo%s" % (r["w"], r["a"], r["b"], r["n"], r["i"], r["pick"], r["phi"], r["tau"], lo)
            s, X = ms.to_fq(F); t0 = time.time()
            s2, X2 = ms.quench(a.fq, tmp, s, X, ["--loosen", lo])
            if s2 is None or not math.isfinite(s2):
                print("n %d %s: built %.9f -> nan  %.0f s" % (n, tag, L, time.time() - t0), flush=True); continue
            if s2 < best - 1e-9:
                s3, X3 = ms.quench(a.fq, tmp, s2, X2, ms.POLISH)
                if s3 is not None and s3 < s2:
                    s2, X2 = s3, X3
                best = s2; ms.write_raw(a.out, n, ms.from_fq(X2), tag)
            print("n %d %s: built %.9f -> %.9f (held %.9f, %+.3e) %s  %.0f s" % (
                n, tag, L, s2, Ln, s2 - Ln, "BELOW" if s2 < Ln - 1e-9 else "above", time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
