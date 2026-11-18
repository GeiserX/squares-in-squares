#!/usr/bin/env python3
"""midm round 31: stop a scan of a start above the bar when it has not crossed the bar after 300 s.

Measured first: the pub-near scans that paid crossed early and the ones that did not cross never did. 812 crossed bar31 at
34 s (and went on to 8.2e-5 of gain by 1177 s); 503 and 871 made most of their gain by 134 s and 214 s and ended 9.8e-6 and
2.9e-5 above the bar after 993 s and 1352 s. A find above the bar keeps a scan past the 120 s probe, so such a scan held
its slot for 900 s or more and then wrote legs that are 120 s probes of a row above the bar.

Every 20 s this loop reads the worker log of each box, takes the running scans of kinds whose start is above the bar
(pub-near, rect, fresh-near, fresh-near-far, drop1), and writes the box's cancel marker for a scan that has run 300 s or
more with its lowest find still not 1e-10 of score below bar31 (or with no find). A cancelled scan certifies its lowest
find as before, but writes no legs. One STATE line per cancel. It stops at the search deadline.
Usage: crossstop31.py  (runs until 23:50Z; pid in work/crossstop.pid)
"""
import calendar, csv, json, math, os, re, subprocess, time
from pathlib import Path

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r31'; W = T / 'work'
BAR = B / 'round31-briefs/bar31.tsv'
BOXES = {'boxE': 'boxE', 'boxD': 'boxD'}
DIR = 'scratch/squares-midm'
KINDS = {'pub-near', 'rect', 'fresh-near', 'fresh-near-far', 'drop1'}
AFTER = 300.0
SEARCH_END = 1794786600
SSH = ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes']


def state(msg):
    with open(T / 'STATE.txt', 'a') as h:
        h.write('%s boxA %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), msg))


def sh(host, cmd):
    try:
        return subprocess.run(SSH + [host, cmd], capture_output=True, text=True, timeout=60).stdout
    except subprocess.TimeoutExpired:
        return ''


def running(log):
    """(stem, job, start epoch) of each START line with no END line after it, per slot."""
    cur = {}
    for line in log.splitlines():
        m = re.match(r'(\S+) START slot=(\d+) (\{.*\})$', line)
        if m:
            t = calendar.timegm(time.strptime(m[1], '%Y-%m-%dT%H:%M:%SZ'))
            cur[m[2]] = (json.loads(m[3]), t)
            continue
        m = re.match(r'\S+ (END|STOP|BEGIN) slot=(\d+)', line)
        if m:
            cur.pop(m[2], None)
    out = []
    for slot, (j, t) in cur.items():
        leg = j.get('leg', 0)
        stem = '%d-%d' % (j['k'], j['n']) if not leg else '%d-%d-L%d' % (j['k'], j['n'], leg + 50 if j.get('sib') else leg)
        out.append((stem, j, t))
    return out


def main():
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BAR), delimiter='\t')}
    (W / 'crossstop.pid').write_text(str(os.getpid()))
    done = set()
    while time.time() < SEARCH_END and not (W / 'STOP').exists():
        for name, host in BOXES.items():
            for stem, j, t0 in running(sh(host, 'tail -400 ~/%s/logs/worker.log' % DIR)):
                if stem in done or j.get('kind') not in KINDS or time.time() - t0 < AFTER:
                    continue
                n = j['n']; lim = (bar[n] - 1e-10 + 1) * math.sqrt(n)
                f = sh(host, 'grep -h "^# FIND" ~/%s/run/s%d/scan-%d-%d.tsv | tail -1' % (DIR, j['k'], n, j['seed']))
                m = re.search(r' side ([0-9.]+)', f)
                best = float(m[1]) if m else None
                if best is not None and best < lim:
                    done.add(stem); continue          # crossed: let it run
                sh(host, 'touch ~/%s/cancel/%s' % (DIR, stem))
                done.add(stem)
                state('CROSS-STOP %s k=%d n=%d kind=%s leg=%d after %.0f s: lowest find %s, bar31 side %.12f (crossstop31.py)' % (
                    name, j['k'], n, j['kind'], j.get('leg', 0), time.time() - t0,
                    '%.12f' % best if best is not None else 'none', lim))
        time.sleep(20)


if __name__ == '__main__':
    main()
