#!/usr/bin/env python3
"""mkqueue.py GAP.tsv OUTDIR: the four queues of the midm slice run (n = 257 to 440), for worker.sh.

q1  the engine controls (sqpack and FTMC on the files held before the public finds), then kick scans
q2  the seeded island (midm_soft.py) on the 20 n with the largest gap, then the plain soft-box island with
    its own drop1 start on the first 6 of them, then the plain island on the trailing n below 300
q3, q4  the kick scans (midm_scan.py, modes kick and lkick): the n that moved in the last two days first (60 s),
    then every trailing n by gap (40 s), then the rest of the slice (20 s)
"""
import csv, sys

HELD = 'round15-2026-11-12a-slice.csv'; R12 = 'round12-2026-11-12a-slice.csv'; R14 = 'round14-2026-11-12a-slice.csv'
MOVED = [370, 374, 403, 410, 411, 412, 418, 335, 269, 378, 419, 421, 415, 341, 268]


def main():
    gap, out = sys.argv[1], sys.argv[2]
    rows = [r for r in csv.DictReader(open(gap), delimiter='\t') if 257 <= int(r['n']) <= 440]
    trail = [int(r['n']) for r in sorted(rows, key=lambda r: -float(r['score_gap'])) if float(r['score_gap']) > 1e-9]
    rest = [int(r['n']) for r in rows if int(r['n']) not in trail]
    q = {1: [], 2: [], 3: [], 4: []}
    for n, sub, ref in ((410, R12, '20.764282966598266'), (370, R14, '19.756747264362865')):
        for mode in ('local', 'drop', 'grow'):
            q[1].append('sq %d %s 100 1 %s %s' % (n, sub, mode, ref))
        q[1].append('ftmc %d %s 150 1 - %s' % (n, sub, ref))
    for n in trail[:20]:
        q[2].append('seed %d %s 75 1 drop1,drop2,grow1 2e-4' % (n, HELD))
    for n in trail[:6]:
        q[2].append('soft %d %s 120 1 drop1 2e-4' % (n, HELD))
    for n in [t for t in trail if t < 300]:
        q[2].append('soft %d %s 120 1 best 2e-4' % (n, HELD))
    kick = [(n, 60) for n in MOVED] + [(n, 40) for n in trail if n not in MOVED] + [(n, 20) for n in rest if n not in MOVED]
    for i, (n, s) in enumerate(kick):
        q[3 + i % 2].append('scan %d %s %d 1 kick,lkick 0' % (n, HELD, s))
    for k, lines in q.items():
        open('%s/q%d.q' % (out, k), 'w').write('\n'.join(lines) + '\n')
        print('q%d' % k, len(lines), 'lines', sum(int(l.split()[3]) for l in lines), 's')


if __name__ == '__main__':
    main()
