#!/usr/bin/env python3
"""Order a worker queue: certified quenches, complete priority designs, then near files."""
import os
import sys


_BARS = {}


def margin(n, tag, root):
    """score of starts/N-TAG.csv over the bar of n in bars.txt (n score per line), or None"""
    if not _BARS:
        try:
            for line in open(os.path.join(root, 'bars.txt')):
                k, v = line.split()[:2]
                _BARS[int(k)] = float(v)
        except (OSError, ValueError):
            _BARS[-1] = 0.0
    if int(n) not in _BARS:
        return None
    try:
        import math, csv
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from methods_lp import half
        import numpy as np
        rows = list(csv.DictReader(open(os.path.join(root, 'starts', n + '-' + tag + '.csv'))))
        X = np.array([[float(r['x']), float(r['y']), float(r['angle'])] for r in rows])
        h = half(X[:, 2])
        side = max(float((X[:, 0] + h).max() - (X[:, 0] - h).min()), float((X[:, 1] + h).max() - (X[:, 1] - h).min()))
        return side / math.sqrt(int(n)) - 1 - _BARS[int(n)]
    except Exception:
        return None


def rank(line, root):
    fields = line.split()
    if len(fields) < 2:
        return (9, 0)
    n, tag = fields[:2]
    mode = fields[2] if len(fields) > 2 else 'pass'
    if mode == 'certified':
        priority = 0
    elif mode == 'kick':
        priority = 0.4          # round 30: kick legs from an unclaimed forensics file 2e-5 to 1.2e-4 over the bar (boxD only)
    elif mode == 'deep':
        priority = 5.0          # round 33: shared deep-kick queue (main session 21:46Z), behind fresh files, follows and islands
    elif mode == 'lk' and tag.startswith('u'):
        priority = 2.0          # round 33: 150 s lkick legs of another lane's fresh certified row nobody claimed for 10 minutes
                                # (round 32: backlog's lkick follows of fresh rows gave 17 of its 31 certified steps)
    elif mode == 'lk':
        priority = 5.5          # round 32: held-row lkicks fill idle slots behind fresh forensics rect islands (3.0 to 4.5)
    elif mode == 'lpq':
        priority = 0.3          # round 29: LP and polish fq of a legal file just above the bar (minutes, border r28 path)
    elif tag.startswith(('k12', 'xk12', 'fk12')):
        priority = 4.6          # round 29 (09:05Z): every k123 start dry (10 short, 5 islands on near and fresh take files),
                                # while forensics islands found on 10 of 42 and midm take islands on 1 of 3; they wait
    elif tag.startswith('z'):
        priority = 0.7          # round 27: rows reopened by the lift of the Samanyu-dev rule, untouched for three rounds
    elif mode == 'island' and tag.startswith('f'):
        priority = 2.5          # round 27: a fresh midm, twoshort or k123 file gets its island ahead of the probes
    elif mode == 'again':
        priority = 1.5          # round 28: the next leg of an island that found (593: legs 2 and 3 found again)
    elif mode == 'island' and tag.startswith('x'):
        priority = 3.5          # round 28: a loose near file within 1e-3 of the bar gets its island before the probes
        m = margin(n, tag, root)
        if m is not None:
            # round 28 (02:20Z): soft plus fq gained about 2.3e-4 of score on the loose forensics files (421 crossed from
            # 2.1e-4, 593 reached 4.4e-5 from 2.7e-4), so the files closest above 1.5e-4 go first and tight ones last
            priority = 3.0 + min(m, 1e-3) * 1000 if m > 1.5e-4 else 4.5
    elif mode == 'island' and tag.startswith('p'):
        # round 31: the pool of round 30 forensics rect files that round 30 soft never started waits behind fresh round 31
        # rect files of the same margin (lesson 6d: fresh geometry pays)
        priority = 4.0
        m = margin(n, tag, root)
        if m is not None:
            priority = 3.6 + min(m, 1e-3) * 1000 if m > 1.5e-4 else 4.6
    elif tag.startswith(('k12', 'xk12')):
        priority = 4.6          # round 29 (08:10Z): k123 short starts 0 finds in 7 (and k123 islands 0 in 3), while forensics
                                # islands found on 7 of 26 and crossed once (747); they wait behind the near-file islands
    elif tag.startswith(('rea', 'xrea')):
        priority = 2
    elif tag.startswith('b'):
        priority = 5            # round 25: base rows of frozen takes wait behind fresh probes
    elif mode == 'island':
        priority = 6            # round 26: an idle-slot island goes after every handoff start
    elif mode == 'probe':
        priority = 4
    else:
        priority = 3
    path = os.path.join(root, 'starts', n + '-' + tag + '.csv')
    if n == '847' and mode != 'certified':
        priority = 0.5
    return priority, -os.path.getmtime(path) if os.path.exists(path) else 0


def main():
    path = os.path.abspath(sys.argv[1])
    root = os.path.dirname(path)
    lines = [line for line in open(path) if line.strip()]
    lines.sort(key=lambda line: rank(line, root))
    with open(path + '.ordered', 'w') as f:
        f.writelines(lines)
    os.replace(path + '.ordered', path)


if __name__ == '__main__':
    main()
