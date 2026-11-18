#!/usr/bin/env python3
"""lkleg.py N TAG: round 32. Twoshort-style lkick legs of 150 s (the invent lane's invent_rest.py, mode lkick, no fq
inside) from the smallest packing under run/N-TAG (starts/N-TAG.csv first). Their finds land in run/N-TAG/raw as
N-slSEED-K.csv, as invent_rest writes them, and collect certifies them like every other raw file.

Leg rule (twoshort round 31 next items 1 and 2): a leg that moves the side more than MOVE (1e-8) gets the next leg from
its best with a new seed, up to LEGS (8) legs; when a leg is dry after the chain gained 1e-5 of score or more, up to two
more seeds run from the same best. Exit 0 when the chain moved the side (chain.sh then runs fqjob.py on the best),
3 when nothing moved.

Why: round 31 twoshort measured a 150 s invent_rest lkick of a held row no lane kicked in rounds 29 to 31 moving 12 of
121 rows, against 2 of 70 for a 900 s midm probe; the round 32 soft brief runs these on held rows nobody claimed."""
import math, os, re, signal, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from bestof import best

SEC = int(os.environ.get('LKSEC', '150'))
LEGS = int(os.environ.get('LKLEGS', '8'))
MOVE = 1e-8            # side
BIG = 1e-5             # score gained by the chain: a dry leg after this gets up to EXTRA more seeds
EXTRA = 2
SEED0 = int(os.environ.get('LKSEED', '3301'))


def bar_side(n):
    try:
        for line in open(HERE + '/bars.txt'):
            k, v = line.split()[:2]
            if int(k) == n:
                return (1 + float(v)) * math.sqrt(n)
    except (OSError, ValueError):
        pass
    return 0.0


def run_leg(n, tag, out, seed, sec):
    L, p = best(n, tag)
    print('LKLEG n=%d tag=%s seed %d seconds %d from %s side %.12f %s' % (n, tag, seed, sec, p, L,
          time.strftime('%H:%M:%S', time.gmtime())), flush=True)
    cmd = [HERE + '/py', HERE + '/invent_rest.py', str(n), p, out, '--seconds', str(sec), '--seed', str(seed),
           '--modes', 'lkick', '--bar', repr(bar_side(n)), '--deadline', HERE + '/deadline']
    proc = subprocess.Popen(cmd, start_new_session=True, stdout=open(out + '/lk-%d.log' % seed, 'a'), stderr=subprocess.STDOUT)
    try:
        proc.wait(timeout=sec + 180)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL); proc.wait()
        print('LKLEG n=%d tag=%s seed %d timeout' % (n, tag, seed), flush=True)
    L2, p2 = best(n, tag)
    tries = 0
    try:
        tries = sum(1 for l in open('%s/slide-%d-%d.tsv' % (out, n, seed)) if l.strip() and not l.startswith('#'))
    except OSError:
        pass
    print('LKEND n=%d tag=%s seed %d side %.12f -> %.12f moved %.3e tries %d best %s %s' % (
        n, tag, seed, L, L2, L - L2, tries, p2, time.strftime('%H:%M:%S', time.gmtime())), flush=True)
    return L, L2


def main():
    n, tag = int(sys.argv[1]), sys.argv[2]
    out = '%s/run/%d-%s' % (HERE, n, tag); os.makedirs(out + '/raw', exist_ok=True)
    L0, _ = best(n, tag)
    seed = SEED0; legs = 0; extra = 0; moved = False
    # round 32 (14:2xZ): a second lk job of an n (tag hhel1, hhel2, ...) starts at a new seed (3401, 3501, ...); with the
    # same seed it would replay the first job's tries from the same held row
    k = re.match(r'^hhel(\d+)$', tag)
    if k and 'LKSEED' not in os.environ:
        seed = SEED0 + 100 * int(k[1])
    while legs < LEGS:
        if os.path.exists(out + '/STOP'):
            print('LKSTOP n=%d tag=%s STOP file' % (n, tag), flush=True); break
        left = float(open(HERE + '/deadline').read().split()[0]) - time.time()
        sec = int(min(SEC, left - 75))
        if sec < 60:
            print('LKSKIP n=%d tag=%s deadline (%d s left)' % (n, tag, left), flush=True); break
        a, b = run_leg(n, tag, out, seed, sec)
        legs += 1; seed += 1
        if a - b > MOVE:
            moved = True
            continue
        if (L0 - b) / math.sqrt(n) >= BIG and extra < EXTRA:
            extra += 1
            continue
        break
    L1, _ = best(n, tag)
    print('LKCHAIN n=%d tag=%s legs %d side %.12f -> %.12f gain of score %.3e' % (n, tag, legs, L0, L1, (L0 - L1) / math.sqrt(n)),
          flush=True)
    sys.exit(0 if moved else 3)


if __name__ == '__main__':
    main()
