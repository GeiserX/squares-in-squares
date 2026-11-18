#!/usr/bin/env python3
"""rebuild_reopen27.py: pin, certify and walk the layouts that round 27 re-opens (the Samanyu-dev rule is lifted).

  rebuild_reopen27.py LIST.tsv OUTDIR
LIST.tsv lines: n <tab> path. For each line: a byte snapshot OUTDIR/pins/<n>-<sha16>.csv (and its sidecars),
floatsafe at 2.2e-11 against bar27 (round27-briefs/bar27.tsv, below by more than 1e-10) into
OUTDIR/cert/<n>-<sha16>.csv, the round 27 walk (rebuild_walk27.check) and a record OUTDIR/records/<n>-<sha16>.json
with the start path, its full sha256, the source text of its lane (take.tsv row, sidecar json), the cert score
and the walk. Prints one JSON line per start. Our own code; it imports floatsafe and rebuild_walk27."""
import csv, hashlib, json, os, shutil, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402
import rebuild_walk27 as w27  # noqa: E402

S = '$SCRATCH/bounties-squares/'
csv.field_size_limit(1 << 28)
BAR = {int(r['n']): (float(r['bar']), r['source']) for r in csv.DictReader(open(S + 'round27-briefs/bar27.tsv'), delimiter='\t')}


def lane_text(p, n):
    out = []
    d = os.path.dirname(p)
    if os.path.basename(p) == '%d.csv' % n and os.path.isfile(d + '/take.tsv'):
        for r in csv.DictReader(open(d + '/take.tsv', errors='replace'), delimiter='\t'):
            if r.get('n') == str(n):
                out.append('take.tsv row: ' + (r.get('source') or '') + ' || ' + (r.get('licence') or ''))
    for s in (p + '.json', p[:-4] + '.json', p + '.origin.json', p + '.source.json', p + '.provenance.json'):
        if os.path.isfile(s) and os.path.getsize(s) < 2_000_000:
            out.append(os.path.basename(s) + ': ' + open(s, errors='replace').read()[:6000])
    return out


def main():
    out = sys.argv[2]
    for sub in ('pins', 'cert', 'records'):
        os.makedirs(out + '/' + sub, exist_ok=True)
    for line in open(sys.argv[1]):
        if not line.strip() or line.startswith('n\t'):
            continue
        n, p = line.split('\t')[:2]
        n, p = int(n), p.strip()
        sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        tag = '%d-%s' % (n, sha[:16])
        pin = out + '/pins/' + tag + '.csv'
        if not os.path.isfile(pin):
            shutil.copy2(p, pin)
        rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(pin)) if int(r['n']) == n]
        rec = {'n': n, 'start': p, 'sha256': sha, 'pin': pin, 'bar27': BAR[n][0], 'bar_source': BAR[n][1]}
        _, fr, score, e = floatsafe.work((n, rows)) if len(rows) == n else (None, None, None, 'rows %d' % len(rows))
        rec['cert_score'] = score
        if fr is not None and score < BAR[n][0] - 1e-10:
            cp = out + '/cert/' + tag + '.csv'
            with open(cp, 'w', newline='') as g:
                wr = csv.writer(g); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr:
                    wr.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            rec['cert'] = cp
            rec['gain'] = BAR[n][0] - score
        rec['lane_text'] = lane_text(p, n)
        rec['walk27'] = w27.check(p)
        json.dump(rec, open(out + '/records/' + tag + '.json', 'w'), indent=1)
        print(json.dumps({k: rec[k] for k in ('n', 'start', 'sha256', 'cert_score', 'bar27')} | {
            'gain': rec.get('gain'), 'clean': rec['walk27'].get('clean'), 'hits': rec['walk27'].get('hits', [])[:4],
            'gone': rec['walk27'].get('gone', [])[:4], 'share': rec['walk27'].get('prvsiyan_share')}), flush=True)


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
