#!/usr/bin/env python3
"""Polish starts from the near files of the builders: layouts that certify a little above the held score.

  near_starts.py HELD_DETAILS.csv STARTS_DIR SEEN_NEAR.tsv SEEN.tsv TAKE_DIR [TAKE_DIR ...] [--max GAP] [--tag K]

A builder writes a layout that ends just above the held side under a near/ folder, at any depth of its take dir.
The fq quench can take such a file under the held score. For each csv under TAKE_DIR/**/near/ that is new since
the last call (path, size and mtime, kept in SEEN_NEAR.tsv), this scores it with floatsafe at 2.2e-11. A file
counts when it certifies and its score is at most GAP (default 2e-5) above the held score. Per n the lowest
counting file of this call (the lowest bounding side that certifies) gets its own start dir STARTS_DIR/<n>-near-K (the csv and a take.tsv), unless SEEN.tsv
(the starts polish_follow.sh already handed out from the take dirs) holds a lower score for that n.
It prints one line per start, "start N DIR GAP", in the order of GAP, and a last line with the count.
A file younger than 10 s is left for the next call: it may still be written.
"""
import argparse, csv, glob, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import floatsafe  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('det'); ap.add_argument('starts'); ap.add_argument('seen_near'); ap.add_argument('seen')
ap.add_argument('dirs', nargs='+'); ap.add_argument('--max', type=float, default=2e-5); ap.add_argument('--tag', default='0')
a = ap.parse_args()
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.det))}
seen = {}
if os.path.exists(a.seen):
    seen = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.seen), delimiter='\t')}
done = set()
if os.path.exists(a.seen_near):
    done = set(l.rstrip('\n') for l in open(a.seen_near))
new_keys, cand, best, now = [], {}, {}, time.time()
for d in a.dirs:
    for p in sorted(glob.glob(d.rstrip('/') + '/**/near/*.csv', recursive=True)):
        try:
            st = os.stat(p)
        except OSError:
            continue
        key = '%s\t%d\t%d' % (p, st.st_size, int(st.st_mtime))
        if key in done or now - st.st_mtime < 10:
            continue
        new_keys.append(key)
        try:
            rows = [{k: q[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for q in csv.DictReader(open(p))]
            n = int(rows[0]['n'])
        except (OSError, KeyError, ValueError, IndexError):
            print('unreadable', p); continue
        if len(rows) != n or n not in held:
            print('drop', n, 'rows', len(rows), p); continue
        # the bounding side as float64 first: the metric is slow, and most near files are too far above held
        h = [0.5 * (abs(math.cos(float(r['angle']))) + abs(math.sin(float(r['angle'])))) for r in rows]
        xs = [float(r['x']) for r in rows]; ys = [float(r['y']) for r in rows]
        side = max(max(x + e for x, e in zip(xs, h)) - min(x - e for x, e in zip(xs, h)),
                   max(y + e for y, e in zip(ys, h)) - min(y - e for y, e in zip(ys, h)))
        raw = side / math.sqrt(n) - 1
        if raw - held[n] > a.max + 1e-9 or raw >= seen.get(n, 9.0):
            continue
        cand.setdefault(n, []).append((raw, p, rows, os.path.relpath(p, os.path.dirname(os.path.abspath(d.rstrip('/'))))))
for n, cs in cand.items():                    # per n only the lowest file that certifies: the metric is slow
    for raw, p, rows, rel in sorted(cs, key=lambda c: c[0]):
        _, fr, score, e = floatsafe.work((n, rows))
        if fr is None:
            print('not certified', n, p); continue
        if score - held[n] <= a.max and score < seen.get(n, 9.0) - 1e-10:
            best[n] = (score, rel, fr)
        break
os.makedirs(a.starts, exist_ok=True)
out = []
for n, (score, rel, fr) in best.items():
    s = '%s/%d-near-%s' % (a.starts, n, a.tag)
    os.makedirs(s, exist_ok=True)
    with open('%s/%d.csv' % (s, n), 'w', newline='') as h:     # the certified rows, as floatsafe wrote them
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in sorted(fr, key=lambda r: int(r['square_id'])):
            w.writerow([n, r['square_id'], r['x'], r['y'], r['angle']])
    with open(s + '/take.tsv', 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        h.write('%d\t%r\t%r\t%.3e\tnear file %s\town (builder near file)\n' % (n, held[n], score, held[n] - score, rel))
    out.append((score - held[n], n, s))
with open(a.seen_near, 'a') as h:
    for k in new_keys:
        h.write(k + '\n')
for gap, n, s in sorted(out):
    print('start %d %s %.3e' % (n, s, gap))
print('near: %d new files, %d starts: %s' % (len(new_keys), len(out), ' '.join(str(n) for _, n, _ in sorted(out))))
