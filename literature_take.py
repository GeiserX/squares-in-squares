#!/usr/bin/env python3
"""Turn published packings from outside Kaggle into certified per-n files, the way angle_take.py does.

  literature_take.py HELD_DETAILS.csv OUT_DIR SPEC.tsv

SPEC.tsv (tab separated, header n, path, format, source, licence) names one published packing per row.
Formats read (each file is data: it is parsed, never executed):
  pose-yaml   jlevy/squares Witness/v2 decimal pose: witness.squares[].center [x, y], angle in degrees
  cert        de Winter certificate: first data line "n side", then "x y t" per square, t = tan(theta/2), rationals
  sqpk        Ostashev sqpk v1: lines "n N", "s S", then "x y degrees" per square
  txt         Casson layout: "Square k: x=.., y=.., deg=.."
  csv         one n in submission columns (x, y, angle in radians), as literature_scan.py cuts it out
Each packing goes through floatsafe (2.2e-11 clearance, the metric as written and after a pandas read).
It is kept only when its score is below the held score by more than 1e-10.
Writes OUT_DIR/<n>.csv (n, square_id, x, y, angle in radians) and OUT_DIR/take.tsv.
Run it with python -I.
"""
import csv, math, os, re, sys
from fractions import Fraction
from pathlib import Path

LANE = str(Path(__file__).resolve().parent)
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402
import mpmath  # noqa: E402

mpmath.mp.dps = 40


def rad(deg_text):
    return mpmath.nstr(mpmath.radians(mpmath.mpf(deg_text)), 30)


def dec(text):
    """A decimal or p/q text as a 30-digit decimal text."""
    if '/' in text:
        f = Fraction(text)
        return mpmath.nstr(mpmath.mpf(f.numerator) / mpmath.mpf(f.denominator), 30)
    return text


def read_pose_yaml(path):
    import yaml
    w = yaml.safe_load(open(path))['witness']
    if w['coordinates']['angle_unit'] != 'degrees' or w['representation'] != 'center-angle' or str(w['square_size']) != '1':
        raise ValueError('unexpected witness convention in ' + path)
    return int(w['n']), [(str(s['center'][0]), str(s['center'][1]), rad(str(s['angle']))) for s in w['squares']]


def read_cert(path):
    lines = [l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n = int(lines[0][0])
    out = []
    for x, y, t in lines[1:]:
        f = Fraction(t)
        th = 2 * mpmath.atan(mpmath.mpf(f.numerator) / mpmath.mpf(f.denominator))
        out.append((dec(x), dec(y), mpmath.nstr(th, 30)))
    return n, out


def read_sqpk(path):
    n, out = None, []
    for l in open(path):
        p = l.split()
        if not p or p[0].startswith('#') or p[0] == 's':
            continue
        if p[0] == 'n':
            n = int(p[1])
        elif len(p) == 3:
            out.append((p[0], p[1], rad(p[2])))
    return n, out


def read_txt(path):
    out = [(m.group(1), m.group(2), rad(m.group(3))) for m in
           re.finditer(r'x=(\S+?), y=(\S+?), deg=(\S+)', open(path).read())]
    return len(out), out


def read_csv(path):
    rows = list(csv.DictReader(open(path)))
    k = {c.lower(): c for c in rows[0]}
    return len(rows), [(r[k['x']].lstrip('s'), r[k['y']].lstrip('s'), r[k['angle']].lstrip('s')) for r in rows]


READ = {'pose-yaml': read_pose_yaml, 'cert': read_cert, 'sqpk': read_sqpk, 'txt': read_txt, 'csv': read_csv}


def main():
    held_csv, out, spec = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(held_csv))}
    kept, tot = 0, 0.0
    with open(os.path.join(out, 'take.tsv'), 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for s in csv.DictReader(open(spec), delimiter='\t'):
            n = int(s['n'])
            m, sq = READ[s['format']](s['path'])
            if m != n or len(sq) != n:
                print('drop', n, 'file holds', m, 'with', len(sq), 'squares'); continue
            rows = [{'n': str(n), 'square_id': str(i), 'x': x, 'y': y, 'angle': a} for i, (x, y, a) in enumerate(sq)]
            _, fr, score, e = floatsafe.work((n, rows))
            if fr is None or not (score < held[n] - 1e-10):
                print('drop', n, 'score', score, 'held', held[n], 'dilation', e, flush=True); continue
            with open(os.path.join(out, '%d.csv' % n), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr:
                    w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            L = (score + 1) * math.sqrt(n)
            print('keep', n, 'L %.12f' % L, 'score', repr(score), 'gain %.3e' % (held[n] - score), 'dilation', e, flush=True)
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, s['source'], s['licence']))
            kept += 1; tot += held[n] - score
    print('kept', kept, 'gain', repr(tot))


if __name__ == '__main__':
    main()
