"""near20.py: kick starts from the near folders of the take dirs, round 20 (on boxA).

No snapshot reads a near/ folder: a layout another lane built and did not certify never gets a kick. This tool
scores those files against the bar of their n and queues the chosen ones for the kick workers.

  near20.py list [NMAX]        every near/*.csv of take-*-r19 and take-*-r20 under NMAX, with its score, the bar
                               (the lowest of the round 18 file and every take.tsv of r19 and r20) and the gap
  near20.py queue PICKS [BASE] PICKS holds lines "<path under the scratch dir>\t<note>". One file per n per snapshot:
                               K = BASE (49) for the first file of an n, BASE - 1 for the second, and so on, so that
                               the start table r<K>.tsv of midm_take.py holds one row per n. Writes work/r<K>/<n>.csv,
                               work/r<K>.tsv and work/q<K>-c4.q. Class 4 files with K under 50 sort before the class 4
                               backlog of snapshot 50, so the workers take them first.
  near20.py stats RUNDIR       one line per kick scan of a near start (run dirs s40 to s49): the gap of the start and
                               of the best find to the bar of the other lanes (our own round 20 rows left out)
"""
import csv, glob, math, os, re, shutil, sys
import numpy as np
S = '$SCRATCH/bounties-squares/'; W = S + 'take-midm-r20/work/'
RES = 'results/'
LIC = ('ours (a construction of the %s lane that it did not certify, see its near folder); the held packings it '
       'starts from: seed merged0, see README (Couzo MIT; Samanyu-dev, no licence)')


def side(p):
    a = np.loadtxt(p, delimiter=',', skiprows=1, usecols=(2, 3, 4)); x, y, t = a[:, 0], a[:, 1], a[:, 2]
    c, s = np.cos(t), np.sin(t); xs = []; ys = []
    for dx, dy in ((.5, .5), (.5, -.5), (-.5, .5), (-.5, -.5)):
        xs.append(x + dx * c - dy * s); ys.append(y + dx * s + dy * c)
    xs = np.concatenate(xs); ys = np.concatenate(ys)
    return float(max(xs.max() - xs.min(), ys.max() - ys.min())), len(a)


def bars(own=True):
    low = {int(r['n']): (float(r['score']), 'r18') for r in csv.DictReader(open(S + 'gate/cand-round18-1112a/details.csv'))}
    for d in glob.glob(S + 'take-*-r19') + glob.glob(S + 'take-*-r20'):
        if (own or not d.endswith('take-midm-r20')) and os.path.exists(d + '/take.tsv'):
            for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
                try:
                    n = int(r['n']); v = float(r['new'])
                except (KeyError, TypeError, ValueError):
                    continue
                if v < low[n][0]:
                    low[n] = (v, os.path.basename(d)[5:])
    return low


def held_src():
    src = {}
    for t in ('round18-best-2026-11-12', 'round17-best-2026-11-12'):
        if os.path.exists(RES + t + '.tsv'):
            for r in csv.DictReader(open(RES + t + '.tsv'), delimiter='\t'):
                src.setdefault(int(r['n']), (r.get('source', ''), r.get('licence', ''), t))
    return src


if sys.argv[1] == 'list':
    nmax = int(sys.argv[2]) if len(sys.argv) > 2 else 1001; low = bars(); rows = []
    for p in sorted(glob.glob(S + 'take-*-r19/near/*.csv') + glob.glob(S + 'take-*-r20/near/*.csv')):
        try:
            L, n = side(p)
        except Exception:
            continue
        if n < nmax:
            sc = L / math.sqrt(n) - 1; rows.append((n, sc - low[n][0], sc, low[n][0], low[n][1], p.replace(S, '')))
    for r in sorted(rows):
        print('%d\tgap %.3e\tscore %.10f\tbar %.10f %s\t%s' % r)
elif sys.argv[1] == 'queue':
    picks = [l.split('\t') for l in open(sys.argv[2]).read().split('\n') if l.strip() and not l.startswith('#')]
    base = int(sys.argv[3]) if len(sys.argv) > 3 else 49; per = {}; src = held_src()
    for p, note in picks:
        L, n = side(S + p); sc = L / math.sqrt(n) - 1
        k = base - per.get(n, 0); per[n] = per.get(n, 0) + 1
        lane_dir = p.split('/')[0]; lane = lane_dir[5:].rsplit('-r', 1)[0]
        m = re.search(r'-win(\d+)-', p)
        if m:       # a corner window of the forensics lane: the licence of the held packing it was cut from
            f = int(m.group(1)); s = src.get(f, ('seed merged0, see README', 'see README', ''))
            lic = 'ours, a corner window of the held packing of n = %d; that n: %s (%s, results/%s.tsv)' % (f, s[1], s[0][:160], s[2])
        else:
            lic = LIC % lane
        os.makedirs(W + 'r%d' % k, exist_ok=True); shutil.copy(S + p, W + 'r%d/%d.csv' % (k, n))
        t = W + 'r%d.tsv' % k; new = not os.path.exists(t)
        with open(t, 'a') as g:
            if new:
                g.write('n\tscore\tdir\tsource\tlicence\tclass\n')
            g.write('%d\t%r\t%s\tthe near miss %s of that lane, not certified there: %s\t%s\t4\n' % (n, sc, lane_dir, p.split('/', 1)[1], note, lic))
        secs = 150 if n < 700 else (225 if n < 800 else 450)
        open(W + 'q%d-c4.q' % k, 'a').write('scan %d r%d/%d.csv %d %d kick,lkick 0\n' % (n, k, n, secs, k))
        print(k, n, '%.10f' % sc, p)
elif sys.argv[1] == 'stats':
    low = bars(own=False); tot = [0, 0, 0.0, 0.0]
    for t in sorted(glob.glob(sys.argv[2] + '/s4[0-9]/scan-*.tsv')):
        end = [l for l in open(t) if l.startswith('# END')]
        if not end:
            continue
        m = re.search(r'n=(\d+) tries (\d+) finds (\d+) best ([0-9.]+) held ([0-9.]+) seconds (\d+)', end[0])
        n, tries, finds, best, start, secs = int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)), float(m.group(5)), int(m.group(6))
        b = low[n][0]; g0 = start / math.sqrt(n) - 1 - b; g1 = best / math.sqrt(n) - 1 - b
        tot[0] += 1; tot[1] += secs; tot[2] += -g1 if g1 < -1e-10 else 0.0; tot[3] += (start - best) / math.sqrt(n)
        print('%s\tn %d\ttries %d\tfinds %d\ts %d\tstart gap %.3e\tbest gap %.3e\t%s' % (
            os.path.basename(os.path.dirname(t)) + '/' + os.path.basename(t), n, tries, finds, secs, g0, g1, 'BELOW' if g1 < -1e-10 else ''))
    print('scans %d, seconds %d, kick gain on the starts %.3e, below the bar of the other lanes by %.3e' % tuple(tot[:2] + [tot[3], tot[2]]))
