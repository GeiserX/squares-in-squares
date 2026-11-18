#!/usr/bin/env python3
"""midm round 31: rows of a changed public file that sit just above our bar, as kick starts.

The harvest lane posts the rows of a changed public file that certify below our bar. The rows a little above it are
fresh geometry too, and a kick may take them below (midm round 21: 12 of 119 public layouts within 1e-4 of score above
the held one gave a certified gain after a kick). This tool writes one start per n for the rows of one public
submission file whose score is 1e-6 to 1e-4 above bar31, after three checks:
  - n is not one of 639 691 745 858 918 (override 3, the penguin069 union);
  - the harvest round 31 share audit (tools/harvest31/policy.py audit: every harvested prvsiyan 1105 version that is
    not our own seed, bounding-box and ICP alignment, eight symmetries) gives a share under 0.4 at 1e-3 and at 1e-2;
  - the row differs from our held row of n (share against the held row at 1e-3 under 0.9), so it is not our own
    layout polished less.
Each start is work/pubnear/<n>-<tag>-<sha12>.csv with a .json record (source, licence, audit evidence, the sha256 of the
public file) and one "pub <path> <priority>" line for work/extra-starts.txt on stdout.
Usage: pubnear31.py PUBLIC_CSV TAG "SOURCE TEXT" "LICENCE" [lo hi]
"""
import csv, hashlib, json, math, sys
from pathlib import Path

L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L / 'tools/harvest31'))
import policy  # noqa: E402  (harvest round 31 share audit, imported, not edited)
import numpy as np  # noqa: E402

B = Path('$SCRATCH/bounties-squares')
W = B / 'take-midm-r31/work'
BAR = B / 'round31-briefs/bar31.tsv'
HELD = B / 'gather/round30-2026-11-15c.csv'
OUT_N = {639, 691, 745, 858, 918}


def rows_by_n(path, want=None):
    out = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            n = int(r['n'])
            if want is None or n in want:
                out.setdefault(n, []).append(r)
    return out


def side(rows):
    lo = [math.inf] * 2; hi = [-math.inf] * 2
    for r in rows:
        a = float(r['angle']); x = float(r['x']); y = float(r['y'])
        h = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        lo[0] = min(lo[0], x - h); hi[0] = max(hi[0], x + h); lo[1] = min(lo[1], y - h); hi[1] = max(hi[1], y + h)
    return max(hi[0] - lo[0], hi[1] - lo[1])


def centres(rows):
    a = np.array([[float(r['x']), float(r['y'])] for r in rows])
    return a - (a.min(0) + a.max(0)) / 2


def main():
    src, tag, stext, lic = sys.argv[1:5]
    lo, hi = (float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (1e-6, 1e-4)
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BAR), delimiter='\t')}
    fsha = hashlib.sha256(Path(src).read_bytes()).hexdigest()
    pub = rows_by_n(src)
    cand = {}
    for n, rows in pub.items():
        if len(rows) != n or n in OUT_N:
            continue
        m = side(rows) / math.sqrt(n) - 1 - bar[n]
        if lo < m <= hi:
            cand[n] = m
    held = rows_by_n(HELD, set(cand))
    od = W / 'pubnear'; od.mkdir(parents=True, exist_ok=True)
    kept = 0
    for n in sorted(cand, key=lambda k: cand[k]):
        rows = pub[n]
        ok, ev = policy.audit([dict(r, n=str(n)) for r in rows])
        mx = max([max(e['share1e3'], e['share1e2']) for e in ev] or [0.0])
        hs = policy.share(centres(rows), centres(held[n]))
        why = 'margin %+.3g, 1105 share max %.3f, share with our held row %.3f/%.3f at 1e-3/1e-2' % (cand[n], mx, hs[1], hs[2])
        if not ok:
            print('# skip n=%d: %s (1105 share)' % (n, why)); continue
        if hs[1] >= 0.9:
            print('# skip n=%d: %s (our own layout, polished less)' % (n, why)); continue
        body = 'n,square_id,x,y,angle\n' + ''.join('%d,%d,%s,%s,%s\n' % (n, i, r['x'], r['y'], r['angle']) for i, r in enumerate(rows))
        h = hashlib.sha256(body.encode()).hexdigest()
        p = od / ('%d-%s-%s.csv' % (n, tag, h[:12]))
        p.write_text(body)
        rec = dict(n=n, kind='public-near', public_first=True,
                   source='public %s, row n = %d as published (public file sha256 %s), %.3g of score above bar31; '
                          'no fq, no change' % (stext, n, fsha, cand[n]),
                   licence=lic, evidence=ev, held_share=dict(share1e3=hs[1], share1e2=hs[2]), path=str(p), sha256=h,
                   public_file=src, public_file_sha256=fsha)
        Path(str(p) + '.json').write_text(json.dumps(rec, indent=1))
        kept += 1
        print('pub %s %.5f %s' % (p, 0.15 + min(cand[n], 1e-4) * 400, why))
    print('# %d of %d candidates kept' % (kept, len(cand)))


if __name__ == '__main__':
    main()
