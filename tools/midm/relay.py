#!/usr/bin/env python3
"""relay.py N [N ...]: kick legs from the best raw result of each n, until a leg finds nothing (at most LEGS legs).

A leg is midm_scan.py (kick, lkick) for SECONDS from the lowest file of run/*/raw/<n>-*.csv; its own finds go to
run/relay/raw. Runs on boxE from the midm dir; ./deadline ends it."""
import glob, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp

BASE = os.path.expanduser('$SCRATCH/squares-base'); SECONDS = int(os.environ.get('RELAY_SECONDS', '120')); LEGS = int(os.environ.get('RELAY_LEGS', '6'))


def best(n):
    fs = [f for f in glob.glob('run/s[2-9]*/raw/%d-*.csv' % n) + glob.glob('run/relay/raw/%d-*.csv' % n)]
    return min(((mlp.side(mlp.load(f, {n})[n]), f) for f in fs), default=(None, None))


for n in [int(v) for v in sys.argv[1:]]:
    for leg in range(LEGS):
        if float(open('deadline').read()) - time.time() < SECONDS + 30 or os.path.exists('STOP'):
            sys.exit(0)
        s0, f = best(n)
        if f is None:
            break
        subprocess.run([BASE + '/venv/bin/python', 'midm_scan.py', '--n', str(n), '--sub', f, '--out', 'run/relay', '--fq', BASE + '/fq',
                        '--seconds', str(SECONDS), '--seed', str(100 + leg + int(time.time()) % 1000 * 10), '--modes', 'kick,lkick', '--deadline', 'deadline'])
        s1, _ = best(n)
        print('relay n=%d leg %d: %.12f -> %.12f' % (n, leg, s0, s1), flush=True)
        if not s1 < s0 - 1e-9:
            break
