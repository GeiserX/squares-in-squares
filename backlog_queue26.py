#!/usr/bin/env python3
"""backlog_queue26: the round 26 queue of the backlog lane (avenues/backlog.md, Round 26).

Two queues, interleaved one for one, the best measured first:
  held   invent_rest.py lkick (300 s, no fq inside) from the held round 25 b layout of each n that rounds 24 and 25
         moved. In round 25 this kick from a start at the bar certified 3 of 6 n (550 1.05e-5, 978 4.4e-6, 791 1e-9).
         Ranked by the size of the move: a larger move is a fresher construction. 873 is left out (midm r25 kicked it
         about 20 times). An n where a live take-*-r26 is already below the bar is left to the follow items.
  midm   midm_scan.py kick,lkick (the midm r25 worker25.py settings) from the unstarted raw designs of the frozen
         take-midm-r25/work/pending-final.json whose side is within 3e-5 of score of the bar, at most 3 distinct starts
         per n, nearest first.
The start of a held item is the layout of n in gather/round25-2026-11-14b.csv, written to work/starts/.
The ancestry walk runs at certification (backlog_ctl.deep_check), on the full source cell of the result.

  backlog_queue26.py OUT.json
"""
import csv, json, math, os, sys
from collections import defaultdict

S = '$SCRATCH/bounties-squares'
LANE = os.path.dirname(os.path.abspath(__file__))
csv.field_size_limit(1 << 30)
W = S + '/take-backlog-r26/work'
HELD = S + '/gather/round25-2026-11-14b.csv'
TABLE = LANE + '/results/round25-best-2026-11-14.tsv'


def details(p):
    return {int(r['n']): float(r['score']) for r in csv.DictReader(open(p))}


def main():
    out = sys.argv[1]
    bar = details(S + '/gate/cand-round25-1114b/details.csv')
    old = details(S + '/gate/cand-round23-1113b/details.csv')
    table = {int(r['n']): r for r in csv.DictReader(open(TABLE), delimiter='\t')}
    moved = sorted((n for n in bar if bar[n] < old[n] - 1e-12 and n != 873), key=lambda n: -(old[n] - bar[n]))
    rows = defaultdict(list)
    for r in csv.DictReader(open(HELD)):
        n = int(r['n'])
        if n in moved:
            rows[n].append(r)
    held = []
    for n in moved:
        p = '%s/starts/%d-r25b.csv' % (W, n)
        with open(p, 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for i, r in enumerate(rows[n]):
                w.writerow([n, r['square_id'], r['x'], r['y'], r['angle']])
        t = table.get(n, {})
        held.append(dict(owner='invent', id='invent:r25b-held-%d' % n, n=n, start=p, start_score=bar[n], gap=0.0,
                         pred=old[n] - bar[n], seconds=300, seed=7, fq=False, queue=HELD,
                         tool='invent_rest.py lkick (300 s, seed 7, no fq inside)',
                         source_text=('invent_rest.py lkick from the held layout of n=%d in gather/round25-2026-11-14b.csv '
                                      '(results/round25-best-2026-11-14.tsv row: %s; take %s)' % (n, t.get('source', 'see results/round23-best-2026-11-13.tsv'), t.get('take', ''))),
                         licence_text=t.get('licence', 'see results/round25-best-2026-11-14.tsv')))
    gaps = json.load(open(W + '/midm-pending-gaps.json'))
    byn = defaultdict(list)
    for e in sorted(gaps, key=lambda e: e['gap']):
        if e['gap'] < 3e-5 and e['n'] != 873:
            if all(abs(e['gap'] - f['gap']) > 1e-8 for f in byn[e['n']]) and len(byn[e['n']]) < 3:
                byn[e['n']].append(e)
    mid = []
    for e in sorted((e for l in byn.values() for e in l), key=lambda e: e['gap']):
        tr = list(csv.DictReader(open(e['source_table']), delimiter='\t'))[0]
        mid.append(dict(owner='midm', id='midm:r25pend-k%d' % e['k'], n=e['n'], start=e['input_local'], start_score=e['start_score'],
                        gap=e['gap'], pred=0.0, seconds=int(e['seconds']), seed=int(e['seed']), sigma=e['sigma'],
                        queue=S + '/take-midm-r25/work/pending-final.json', tool='midm_scan.py kick,lkick',
                        record_source='take-midm-r25/work/%s row: %s' % (os.path.basename(e['source_table']), tr['source']),
                        record_licence=tr['licence']))
    items = []
    for i in range(max(len(held), len(mid))):
        items += held[i:i + 1] + mid[i:i + 1]
    json.dump(dict(items=items), open(out + '.tmp', 'w'), indent=0)
    os.replace(out + '.tmp', out)
    print('held', len(held), 'midm', len(mid))
    for it in items[:16]:
        print(it['id'], it['n'], '%.3e' % it['gap'], '%.3e' % it['pred'])


if __name__ == '__main__':
    main()
