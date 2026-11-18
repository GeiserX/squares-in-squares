#!/usr/bin/env python3
"""rebuild_run.py ROOT FQ PY: one worker of the rebuild lane on a box (one process, children run in turn).

ROOT holds lane/ (the lane code), deadline (unix time), queue.tsv (lines: key <tab> n <tab> bar side <tab>
start file relative to ROOT [<tab> quench]) and gets out/<key>/. A fifth column 'quench' runs one default fq
quench of the start file only (the quench of a certified file before publication) and writes out/<key>/q.csv.
A fifth column 'kick:SECONDS' runs midm_scan.py --modes lkick,kick on the start for SECONDS and writes the lowest
legal result as out/<key>/best.csv; 'kick:SECONDS:PROBE' stops the scan at PROBE seconds when no find has gained more
than PROBE_MIN (1e-8) of side yet (round 31 probe); 'scan:SECONDS:MODES:DONOR' runs midm_scan.py with those modes
and --donors ROOT/DONOR (drop1 or grow1 from a fresh layout of n+1 or n-1). The worker takes the queue in file order, re-reading it after
every job so new lines placed first run next, and claims each key with mkdir claims/<key>. Per start: k123_turn.py
--turns=0 --modes self --loosen 1.001 --keep (the single tight fq quench of the k123 lane), then the fq loop of
fq2.py (default flags, then the deep POLISH flags, up to three rounds, kept while the side falls by 3e-9). Writes
out/<key>/best.csv (lowest side reached, raw rows) and out/<key>/done.json. With REBUILD_TRIAGE=D in the environment a start whose turned side is more than D above the bar skips the fq loop
(round 26: the fq loop moved round 25 ends by 3e-4 of side at most). Every child dies at the deadline.
Our own code; it runs k123_turn.py and imports midm_scan and methods_lp unchanged."""
import json, math, os, pathlib, signal, subprocess, sys, time

R = pathlib.Path(sys.argv[1]); FQ = sys.argv[2]; PY = sys.argv[3]
# REBUILD_TRIAGE: skip the fq loop when the turned start is more than this above the bar (default: never skip)
TRIAGE = float(os.environ.get('REBUILD_TRIAGE', 'inf'))
sys.path.insert(0, str(R / 'lane'))
os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
import methods_lp as mlp  # noqa: E402
import family_step as fs  # noqa: E402
from midm_scan import to_fq, from_fq, quench, POLISH  # noqa: E402


def left():
    return float((R / 'deadline').read_text()) - time.time()


def probe_gain(d):
    """the largest side gain of a '# FIND' line in d/scan-*.tsv (midm_scan writes 'side S (held H'), 0 when none"""
    import re
    g = 0.0
    for f in pathlib.Path(d).glob('scan-*.tsv'):
        for m in re.finditer(r'^# FIND .* side ([0-9.]+) \(held ([0-9.]+)', f.read_text(errors='replace'), re.M):
            g = max(g, float(m.group(2)) - float(m.group(1)))
    return g


def run(args, log, cap, probe=None):
    """probe=(SECONDS, DIR): stop the child at SECONDS when no '# FIND' line of DIR/scan-*.tsv gained more than
    PROBE_MIN (1e-8) of side below the start, and return -3 (round 31: quench r30 measured 10 of 89 kicks improving on
    any try, every one that paid improving early; the first try of a held row is often an fq polish of 1e-9 to 3e-9)"""
    t = min(left(), cap)
    if t <= 0:
        return -1
    with open(log, 'a') as h:
        p = subprocess.Popen(args, stdout=h, stderr=h, start_new_session=True)
        if probe is not None and probe[0] < t:
            try:
                return p.wait(timeout=probe[0])
            except subprocess.TimeoutExpired:
                if probe_gain(probe[1]) <= float(os.environ.get('PROBE_MIN', '1e-8')):
                    os.killpg(p.pid, signal.SIGKILL); p.wait(); return -3
            t = max(1.0, min(left(), cap) - probe[0])
        try:
            return p.wait(timeout=t)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL); p.wait(); return -2


(R / 'claims').mkdir(exist_ok=True); (R / 'out').mkdir(exist_ok=True)
while left() > 0:
    lines = [l.split('\t') for l in (R / 'queue.tsv').read_text().splitlines() if l.count('\t') >= 3]
    job = None
    for w in lines:
        try:
            (R / 'claims' / w[0]).mkdir(); job = w; break
        except FileExistsError:
            continue
    if job is None:
        time.sleep(10); continue
    key, n, bar, src = job[0], int(job[1]), float(job[2]), R / job[3]
    d = R / 'out' / key; d.mkdir(exist_ok=True)
    rec = dict(key=key, n=n, bar=bar, start=str(src), t0=time.strftime('%H:%M:%SZ', time.gmtime()))
    try:
        P0 = mlp.load(str(src), {n})[n]; rec['start_side'] = float(mlp.side(P0))
        if len(job) > 4 and job[4].strip() == 'quench':
            s, X = to_fq(P0); tmp = str(d / 'tmpq'); os.makedirs(tmp, exist_ok=True)
            # round 33 (lesson 6e): the full fq loop of midm_fqonce.py (default flags, then POLISH, up to three rounds),
            # not one default quench: border's polish-only fq left 1.68e-6 of score on its 864 find in round 32
            s0 = s; rec['quench_ok'] = False; rec['fq_steps'] = []
            for rnd in range(3):
                imp = False
                for fl in ((), POLISH):
                    if left() <= 5:
                        break
                    s2, X2 = quench(FQ, tmp, s, X, fl, timeout=min(300, max(1, left())))
                    rec['fq_steps'].append(None if s2 is None else float(s2))
                    if s2 is not None:
                        rec['quench_ok'] = True
                        if s2 < s - 1e-11:
                            s, X, imp = s2, X2, True
                if not imp:
                    break
            if s < s0:
                fs.write_rows(str(d / 'q.csv'), n, from_fq(X)); rec['side'] = float(s); rec['room'] = bar - float(s)
            raise StopIteration
        if len(job) > 4 and job[4].strip().startswith('lk:'):   # round 32: lk:SECONDS runs invent_rest.py --modes lkick
            # (no fq inside; the collector certifies the best raw file and queues one fq quench of the certified file).
            # twoshort r31: a 150 s lkick moved 12 of 121 held rows, a 900 s midm probe 2 of 70
            sec = float(job[4].strip().split(':')[1])
            # round 33: lk:SECONDS:w runs the walker (--walk 3e-6) over --modes seg,lkick, for a layout whose plain lkicks
            # stalled (our 740 drop1 chain: the first lkick moved 1.5e-5 of side, the next 9 seeds nothing)
            lkx = ['--modes', 'seg,lkick', '--walk', '3e-6'] if job[4].strip().split(':')[2:3] == ['w'] else ['--modes', 'lkick']
            rec['lk_code'] = run([PY, '-I', str(R / 'lane/invent_rest.py'), str(n), str(src), str(d), '--seconds', str(sec),
                                  '--seed', str(abs(hash(key)) % 10000)] + lkx + ['--bar', str(bar),
                                  '--deadline', str(R / 'deadline')], d / 'lk.log', sec + 120)
            best = None
            for c in sorted(d.glob('raw/*.csv')):
                try:
                    P = mlp.load(str(c), {n})[n]
                except Exception:
                    continue
                if len(P) == n and mlp.min_gap(P) > -1e-9 and (best is None or mlp.side(P) < best[0]):
                    best = (float(mlp.side(P)), P)
            if best is not None:
                fs.write_rows(str(d / 'best.csv'), n, best[1]); rec['side'] = best[0]; rec['room'] = bar - best[0]
            raise StopIteration
        if len(job) > 4 and job[4].strip().startswith(('kick:', 'scan:')):
            kf = job[4].strip().split(':')
            sec = float(kf[1])
            if kf[0] == 'scan':   # round 31: scan:SECONDS:MODES:DONOR (drop1/grow1 from a fresh layout of n+1 or n-1 in DONOR)
                probe, modes, extra = 0.0, kf[2], (['--donors', str(R / kf[3])] if len(kf) > 3 and kf[3] else [])
            else:
                probe, modes, extra = (float(kf[2]) if len(kf) > 2 else 0.0), 'lkick,kick', []
            rec['kick_code'] = run([PY, '-I', str(R / 'lane/midm_scan.py'), '--n', str(n), '--sub', str(src), '--out', str(d),
                                    '--fq', FQ, '--seconds', str(sec), '--modes', modes, '--deadline', str(R / 'deadline'),
                                    '--seed', str(abs(hash(key)) % 1000)] + extra, d / 'kick.log', sec + 120,
                                   probe=(probe, d) if probe > 0 else None)
            if probe > 0:
                rec['probe'] = probe; rec['probe_stop'] = rec['kick_code'] == -3
            best = None
            for c in sorted(d.glob('raw/*.csv')):
                try:
                    P = mlp.load(str(c), {n})[n]
                except Exception:
                    continue
                if len(P) == n and mlp.min_gap(P) > -1e-9 and (best is None or mlp.side(P) < best[0]):
                    best = (float(mlp.side(P)), P)
            if best is not None:
                fs.write_rows(str(d / 'best.csv'), n, best[1]); rec['side'] = best[0]; rec['room'] = bar - best[0]
            raise StopIteration
        rec['turn_code'] = run([PY, '-I', str(R / 'lane/k123_turn.py'), str(src), str(n), str(d), FQ, '--turns=0',
                                '--modes', 'self', '--loosen', '1.001', '--bar', str(bar), '--keep'], d / 'turn.log', 300)
        cands = sorted(d.glob('turn/*.csv')) + sorted(d.glob('raw/*.csv'))
        best = None
        for c in cands:
            try:
                P = mlp.load(str(c), {n})[n]
            except Exception:
                continue
            if len(P) == n and mlp.min_gap(P) > -1e-9:
                s = float(mlp.side(P))
                if best is None or s < best[0]:
                    best = (s, P)
        if best is not None and best[0] - bar > TRIAGE:
            rec['turn_side'] = best[0]; rec['triage'] = 'skip fq loop: turn side %.3e above the bar' % (best[0] - bar)
            fs.write_rows(str(d / 'best.csv'), n, best[1]); rec['side'] = best[0]; rec['room'] = bar - best[0]
            best = None
        if best is not None:
            rec['turn_side'] = best[0]
            s, X = to_fq(best[1]); tmp = str(d / 'tmp2'); os.makedirs(tmp, exist_ok=True)
            for rnd in range(3):
                imp = False
                for fl in ((), POLISH):
                    if left() <= 5:
                        break
                    s2, X2 = quench(FQ, tmp, s, X, fl, timeout=min(240, max(1, left())))
                    if s2 is not None and s2 < s - 3e-9:
                        s, X, imp = s2, X2, True
                if not imp:
                    break
            P = from_fq(X)
            if s < best[0]:
                best = (s, P)
            fs.write_rows(str(d / 'best.csv'), n, best[1])
            rec['side'] = best[0]; rec['room'] = bar - best[0]
    except StopIteration:
        pass
    except Exception as e:
        rec['error'] = type(e).__name__ + ': ' + str(e)
    rec['t1'] = time.strftime('%H:%M:%SZ', time.gmtime())
    (d / 'done.json').write_text(json.dumps(rec))
    with open(R / 'done.jsonl', 'a') as h:
        h.write(json.dumps(rec) + '\n')
