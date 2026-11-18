#!/usr/bin/env python3
"""rebuild_take.py: certify and publish the rows of the rebuild lane.

  rebuild_take.py cert N RAW.csv OUT.csv BAR_SCORE
      floatsafe.work (2.2e-11 clearance, the metric as written and after a pandas read); writes OUT.csv and
      prints 'ok N score side' when the score is below BAR_SCORE by more than 1e-10, else 'drop ...'.
  rebuild_take.py publish TAKEDIR ROWS.json
      ROWS.json: {n: {cert, held, source, licence}}. Each row stays only while it is lower than the same n in
      every other live take-*-r<SQ_ROUND>/take.tsv by more than 1e-10 (SQ_ROUND in the environment, default 26). Writes TAKEDIR/<n>.csv first, then take.tsv by
      rename. Prints the rows kept and the gain against the base bar and beyond the other live takes.
Our own code. It imports floatsafe and does not change it."""
import csv, glob, json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floatsafe  # noqa: E402

S = '$SCRATCH/bounties-squares'
csv.field_size_limit(1 << 28)


def cert(n, raw, out, bar):
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(raw)) if int(r['n']) == n]
    if len(rows) != n:
        print('drop', n, 'rows', len(rows)); return None
    _, fr, score, e = floatsafe.work((n, rows))
    if fr is None or not score < bar - 1e-10:
        print('drop', n, score, bar, e); return None
    with open(out, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    print('ok', n, repr(score), '%.12f' % ((score + 1) * math.sqrt(n)), e)
    return score


def live(me):
    best = {}
    for t in glob.glob(S + '/take-*-r%s/take.tsv' % os.environ.get('SQ_ROUND', '26')):
        if os.path.dirname(t) == os.path.abspath(me):
            continue
        try:
            for r in csv.DictReader(open(t), delimiter='\t'):
                n, s = int(r['n']), float(r['new'])
                if s < best.get(n, (math.inf,))[0]:
                    best[n] = (s, t)
        except Exception as e:
            print('unreadable', t, e)
    return best


def publish(tdir, rows_json):
    R = {int(k): v for k, v in json.load(open(rows_json)).items()}
    other = live(tdir)
    keep = {}
    g1 = g2 = 0.0
    for n in sorted(R):
        r = R[n]
        s = cert(n, r['cert'], os.path.join(tdir, '.%d.csv.tmp' % n), r['held'])
        if s is None:
            continue
        o = other.get(n, (math.inf, ''))
        if not s < o[0] - 1e-10:
            print('beaten', n, s, o); os.remove(os.path.join(tdir, '.%d.csv.tmp' % n)); continue
        os.replace(os.path.join(tdir, '.%d.csv.tmp' % n), os.path.join(tdir, '%d.csv' % n))
        keep[n] = (s, r)
        g1 += r['held'] - s; g2 += min(r['held'], o[0]) - s
    tmp = os.path.join(tdir, '.take.tsv.tmp')
    with open(tmp, 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for n in sorted(keep):
            s, r = keep[n]
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, r['held'], s, r['held'] - s, r['source'], r['licence']))
    os.replace(tmp, os.path.join(tdir, 'take.tsv'))
    print('kept', sorted(keep), 'gain', repr(g1), 'beyond live', repr(g2))


if __name__ == '__main__':
    if sys.argv[1] == 'cert':
        cert(int(sys.argv[2]), sys.argv[3], sys.argv[4], float(sys.argv[5]))
    else:
        publish(sys.argv[2], sys.argv[3])
