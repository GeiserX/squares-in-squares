#!/usr/bin/env python3
"""kickleg.py N TAG: round 30. After the island and its fq quench, one 900 s kick scan (the midm lane's midm_scan.py,
modes kick and lkick, sigma 0.04, --stop6) from the smallest packing under run/N-TAG, when that packing is at most KMAX of
score above the all-lane bar of n in bars.txt (or below it). Its finds land in run/N-TAG/raw as midm_scan writes them,
and collect certifies them like every other raw file. Exit 0 when the scan ran, 3 when it was skipped.

Why: round 29 islands found on 17 of 97 forensics files and reached the held floor four times, but crossed once (747),
and the midm lane's 900 s kick of a forensics file that had moved into our 747 basin went 2.5e-7 of side lower than our
fq polish. Our near files above the bar get no kick from the other lanes (rebuild kicks near files only below the bar)."""
import math, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import methods_lp as mlp
from bestof import best

KMAX = 2.5e-4          # score above the bar: round 28 measured soft plus fq gaining about 2.3e-4 on loose forensics files
KSEC = int(os.environ.get("KICKSEC", "900"))
LEGS = 3
LEGS_NEAR = 8
NEAR = 2e-5          # score over the bar
CHAIN = 1e-6          # side
CLOSE = 2e-6          # score over the bar: a chain this close goes on while a leg removes more than TINY of side
PROBE, PROBE_TRIES, PROBE_MAX = 120, 4, 300   # round 31 lesson c (quench r30: every kick that paid improved early)
TINY = 1e-9           # side (round 30, 17:15Z: 689 leg 1 took 5.6e-8 to 1.9e-8 over, 9.6e-7 of side, under CHAIN)


def bar_of(n):
    try:
        for line in open(HERE + '/bars.txt'):
            k, v = line.split()[:2]
            if int(k) == n:
                return float(v)
    except (OSError, ValueError):
        pass
    return None


def leg(n, tag, out):
    """one kick scan from the smallest packing under run/N-TAG; returns (side before, side after) or None when skipped"""
    L, p = best(n, tag)
    bar = bar_of(n)
    score = L / math.sqrt(n) - 1
    if bar is None or score - bar > KMAX:
        print('KICKSKIP n=%d tag=%s score %.12f bar %s margin %s' % (n, tag, score, bar, None if bar is None else '%.3e' % (score - bar)), flush=True)
        return None
    dl = float(open(HERE + '/fqdeadline').read())
    sec = int(min(KSEC, dl - time.time() - 120))
    if sec < 60:
        print('KICKSKIP n=%d tag=%s deadline (%d s left)' % (n, tag, sec), flush=True)
        return None
    # round 31: seeds from 500 (round 30 legs used 300 up, and the r30 next list asks for new seeds on the close misses)
    seed = 500 + len([f for f in os.listdir(out) if f.startswith('scan-%d-' % n)]) if os.path.isdir(out) else 500
    print('KICK n=%d tag=%s from %s side %.12f score %.12f bar %.12f margin %.3e seconds %d seed %d %s' % (
        n, tag, p, L, score, bar, score - bar, sec, seed, time.strftime('%H:%M:%S', time.gmtime())), flush=True)
    cmd = [HERE + '/py', HERE + '/midm_scan.py', '--n', str(n), '--sub', p, '--out', out, '--fq', HERE + '/fq',
           '--seconds', str(sec), '--seed', str(seed), '--modes', 'kick,lkick', '--ref', '0', '--deadline', HERE + '/fqdeadline',
           '--kicks', '0.04', '--stop6']
    # Round 31 lesson c: probe the kick and stop it when no try improves. --stop6 alone missed it: on 689 the lkick tries
    # came back 4.6e-8 of side above the start, not within 5e-9, so the scan ran its 900 s with no find. Here the scan
    # stops at the first check after PROBE s with at least PROBE_TRIES tries and none below the start side, or after
    # PROBE_MAX s with none below it.
    import signal
    tsv = '%s/scan-%d-%d.tsv' % (out, n, seed)
    proc = subprocess.Popen(cmd, start_new_session=True)
    t0 = time.time(); probed = False
    while proc.poll() is None:
        time.sleep(5)
        el = time.time() - t0
        if el > sec + 120:
            os.killpg(proc.pid, signal.SIGTERM); print('KICK n=%d tag=%s timeout' % (n, tag), flush=True); break
        if probed or el < PROBE or os.environ.get('KICKNOPROBE') == '1':   # round 33: deep mode runs unprobed
            continue
        try:
            sides = [float(l.split('\t')[4]) for l in open(tsv) if not l.startswith('#') and len(l.split('\t')) > 4]
        except (OSError, ValueError):
            sides = []
        if any(x < L - 1e-9 for x in sides):          # midm_scan writes a find only 1e-9 of side below its best
            probed = True
            print('KICKPROBE n=%d tag=%s improved after %.0f s (%d tries), running on' % (n, tag, el, len(sides)), flush=True)
        elif len(sides) >= PROBE_TRIES or el >= PROBE_MAX:
            os.killpg(proc.pid, signal.SIGTERM)
            print('KICKPROBE n=%d tag=%s stop: no try below the start in %.0f s (%d tries)' % (n, tag, el, len(sides)), flush=True)
            break
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
    L2, p2 = best(n, tag)
    print('KICKEND n=%d tag=%s side %.12f -> %.12f gain of score %.3e best %s %s' % (
        n, tag, L, L2, (L - L2) / math.sqrt(n), p2, time.strftime('%H:%M:%S', time.gmtime())), flush=True)
    return L, L2


def main():
    # Round 30 (13:20Z): chain legs while a leg removes more than CHAIN of side, up to LEGS (twoshort r29: 752 came on
    # its second 900 s leg; our 865 leg 1 removed 8.7e-4 of side and the island again leg after it was dry).
    n, tag = int(sys.argv[1]), sys.argv[2]
    out = '%s/run/%d-%s' % (HERE, n, tag)
    ran = False
    k = 0
    while True:
        r = leg(n, tag, out)
        if r is None:
            break
        ran = True; k += 1
        bar0 = bar_of(n)
        close = bar0 is not None and r[1] / math.sqrt(n) - 1 - bar0 < CLOSE
        if os.path.exists(out + '/STOP') or r[0] - r[1] <= (TINY if close else CHAIN):
            break
        # round 30 (15:40Z): a chain within NEAR of the bar may run up to LEGS_NEAR legs (910: legs 1 to 3 gained 1.49e-5,
        # 5.3e-6 and more, ending 4.8e-7 over the bar after leg 2)
        bar = bar_of(n)
        near = bar is not None and r[1] / math.sqrt(n) - 1 - bar < NEAR
        if k >= (LEGS_NEAR if near else LEGS):
            break
    sys.exit(0 if ran else 3)


if __name__ == '__main__':
    main()
