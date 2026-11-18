"""Write the x-mirror of a packing csv (x -> -x shifted to the same box, angle -> -angle).
An exact symmetry: the same squares, the same bounding side, the same clearances. A seeded kick then takes another path."""
import csv, sys
src, dst = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src)))
xs = [float(str(r['x']).lstrip('s')) for r in rows]
c = min(xs) + max(xs)
with open(dst, 'w', newline='') as h:
    w = csv.writer(h)
    w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
    for r, x in zip(rows, xs):
        w.writerow([r['n'], r['square_id'], repr(c - x), str(r['y']).lstrip('s'), repr(-float(str(r['angle']).lstrip('s')))])
