#!/usr/bin/env python3
"""backlog_reopen27: the round 27 re-open queue of the backlog lane (avenues/backlog.md, Round 27).

Round 27 lifts the Samanyu-dev rule, so per-n files of the frozen take dirs (top level and near/) that lanes
refused, withdrew or parked for that ancestry can enter again. work/prescan.out lists every such file whose side
as it stands is below the round 27 bar (scripts/prescan.py). This driver gates them, the counts with the largest
side gain first, with backlog_gate27.check (share test and the assembler walk with the seed hits lifted; floatsafe
is left to the box worker) and appends one JSON line per file to work/reopen-gate.jsonl. The first clean file of a
count ends that count; at most MAXTRY files per count. backlog_ctl.py queues the clean ones.

  backlog_reopen27.py PRESCAN OUT [MAXTRY]
"""
import csv, hashlib, json, os, sys, time

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.dont_write_bytecode = True
import backlog_gate27 as G  # noqa: E402
S = '$SCRATCH/bounties-squares'
R = os.environ.get('BACKLOG_ROUND', '27')           # round 28: bar28 and the r28 stop file
OUT_N = {639, 691, 745, 858, 918, 980, 801}          # rules a-c: every frozen file of these counts stays out
if int(R) >= 29:
    OUT_N.discard(801)                               # round 29 rule 3: the 801 row and its descendants are ours


def main():
    pre, out = sys.argv[1], sys.argv[2]; maxtry = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + '/round%s-briefs/bar%s.tsv' % (R, R)), delimiter='\t')}
    by = {}
    for line in open(pre):
        n, sc, gap, f = line.rstrip('\n').split('\t')
        by.setdefault(int(n), []).append((float(sc), f))
    done = set()
    if os.path.exists(out):
        for line in open(out):
            try:
                done.add(json.loads(line)['path'])
            except Exception:
                pass
    order = sorted(by, key=lambda n: min(s for s, _ in by[n]) - bar[n])
    stop = S + '/take-backlog-r%s/work/STOPREOPEN' % R
    for n in order:
        if n in OUT_N:
            continue
        seen_sha = set(); tried = 0
        for sc, f in sorted(by[n]):
            if os.path.exists(stop):
                return
            p = S + '/' + f if not f.startswith('/') else f
            if p in done:
                tried += 1
                continue
            try:
                h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            except OSError:
                continue
            if h in seen_sha:
                continue
            seen_sha.add(h)
            t0 = time.time()
            try:
                r = G.check(p, n=n, cert=False)
            except Exception as ex:
                r = dict(path=p, n=n, ok=False, hits=['error %s' % ex], score=sc)
            r.update(sha256=h, bar=bar[n], quick=sc, secs=round(time.time() - t0, 1), utc=time.strftime('%H:%M:%SZ', time.gmtime()))
            with open(out, 'a') as o:
                o.write(json.dumps(r) + '\n')
            tried += 1
            if r['ok'] or tried >= maxtry:
                break


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
