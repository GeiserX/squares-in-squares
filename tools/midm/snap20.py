"""snap20.py K [SECONDS]: snapshot K (50 or more) of the take files of the other lanes as kick starts, round 20.

It reads every take-*-r19 dir (frozen) and every take-*-r20 dir but this lane's. The start of an n is the lowest
certified file of those dirs, and only when it is more than 1e-10 below the round 18 file. Left out:
  - an n whose lowest file is this lane's own round 19 file (it had its kick and its legs)
  - a file whose bytes had a kick scan of 6 tries or more in round 19 (take-midm-r19/work/r30 to r42, with the scan
    tables in take-midm-r20/work/r19-boxE/run/s<K>), or that an earlier snapshot of this round holds
  - a file of the same lane within 1e-6 of score of the file an earlier snapshot of this round holds for that n
    (2e-9 until 23:38Z; a walk of the family lane posted 549 four times 3e-8 apart, and each took a scan)
  - a file not below this lane's own round 20 row of that n (round 19 item 4)
Writes work/r<K>/<n>.csv, work/r<K>.tsv (n, score, dir, source, licence, class) and work/q<K>-c<class>.q, lines in
ascending n. The classes, in the order the workers take them:
  1  a construction of round 19 or 20 at n under 640 (under 440 the first scans of round 19 found 9 of 20 times)
  2  a construction of round 20 at n of 640 and more
  3  a leg owed (MIDM_LEGS)
  4  every other file: a round 19 construction at n of 640 and more, and polish and harvest files
Seconds: SECONDS under n = 700, 1.5 times that to 799, 3 times that from 800 up (round 19 item 5: a scan of 225 s
holds 2 to 5 tries there, so the stop rule cannot act and a find has little room).
"""
import csv, filecmp, glob, math, os, shutil, sys
B = '$SCRATCH/bounties-squares/'; W = B + 'take-midm-r20/work/'; W19 = B + 'take-midm-r19/work/'
RUN19 = W + 'r19-boxE/run/'
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
K = int(sys.argv[1]); secs = int(sys.argv[2]) if len(sys.argv) > 2 else 150
QUENCH = ('polish', 'harvest')
RK = 'r%d' % K; os.makedirs(W + RK, exist_ok=True)
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(B + 'gate/cand-round18-1112a/details.csv'))}
legs = {int(x) for x in os.environ.get('MIDM_LEGS', '').split(',') if x}
best = {}
for d in sorted(glob.glob(B + 'take-*-r19') + glob.glob(B + 'take-*-r20')):
    b = os.path.basename(d)
    if b in ('take-midm-r20',) or b.startswith('take-assemble') or not os.path.exists(d + '/take.tsv'):
        continue
    for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
        try:
            n = int(r['n']); f = '%s/%d.csv' % (d, n)
            P = mlp.load(f, {n})[n]
            if len(P) != n:
                continue
            sc = min(float(r['new']), mlp.side(P) / math.sqrt(n) - 1)
        except Exception as e:
            print('skip', b, r.get('n'), e); continue
        if n not in best or sc < best[n][0]:
            best[n] = (sc, b, r.get('source', ''), r.get('licence', ''), f)


def kicked19(n, f):
    for j in range(30, 43):
        g = W19 + 'r%d/%d.csv' % (j, n)
        if os.path.exists(g) and filecmp.cmp(f, g, shallow=False):
            for t in glob.glob(RUN19 + 's%d/scan-%d-*.tsv' % (j, n)):
                if sum(1 for l in open(t) if l[:1].isdigit()) >= 6:
                    return True
    return False


lines = ['n\tscore\tdir\tsource\tlicence\tclass']; q = []; out = {'held': 0, 'own': 0, 'own20': 0, 'kicked19': 0, 'earlier': 0, 'requenched': 0}
own20 = {}     # round 19 item 4: a start above our own round 20 row of that n is a waste (263 took 613 s for nothing)
if os.path.exists(B + 'take-midm-r20/take.tsv'):
    own20 = {int(r['n']): float(r['new']) for r in csv.DictReader(open(B + 'take-midm-r20/take.tsv'), delimiter='\t')}
prev = {}
for j in range(50, K):
    if os.path.exists(W + 'r%d.tsv' % j):
        for r in csv.DictReader(open(W + 'r%d.tsv' % j), delimiter='\t'):
            prev[int(r['n'])] = (float(r['score']), r['dir'])
for n in sorted(best):
    sc, d, so, lic, f = best[n]
    if not sc < held[n] - 1e-10:
        out['held'] += 1; continue
    if n in own20 and not sc < own20[n] - 1e-10:
        out['own20'] += 1; continue
    lane = d[5:-4]
    if lane == 'midm':
        if n not in legs:
            out['own'] += 1; continue
        cl = 3
    elif lane in QUENCH:
        cl = 4
    elif n < 640:
        cl = 1
    elif d.endswith('-r20'):
        cl = 2
    else:
        cl = 4
    if d.endswith('-r19') and kicked19(n, f):
        out['kicked19'] += 1; continue
    if any(os.path.exists(W + 'r%d/%d.csv' % (j, n)) and filecmp.cmp(f, W + 'r%d/%d.csv' % (j, n), shallow=False) for j in range(50, K)):
        out['earlier'] += 1; continue
    if n in prev and prev[n][1] == d and abs(prev[n][0] - sc) < 1e-6:     # 1e-6 from 23:38Z: family re-posts 549 every few minutes 3e-8 lower
        out['requenched'] += 1; continue
    shutil.copyfile(f, W + RK + '/%d.csv' % n)
    P = mlp.load(W + RK + '/%d.csv' % n, {n})[n]; sc = min(sc, mlp.side(P) / math.sqrt(n) - 1)
    lines.append('%d\t%r\t%s\t%s\t%s\t%d' % (n, float(sc), d, so.replace('\t', ' '), lic.replace('\t', ' '), cl))
    s = secs if n < 700 else (int(secs * 1.5) if n < 800 else secs * 3)
    q.append((cl, n, 'scan %d %s/%d.csv %d %d kick,lkick 0' % (n, RK, n, s, K)))
open(W + RK + '.tsv.tmp', 'w').write('\n'.join(lines) + '\n'); os.rename(W + RK + '.tsv.tmp', W + RK + '.tsv')
for cl in (1, 2, 3, 4):
    L = [l for c, n, l in q if c == cl]
    open(W + 'q%d-c%d.q' % (K, cl), 'w').write('\n'.join(L) + '\n' if L else '')
    print('class', cl, len(L), 'starts:', ' '.join('%d(%s)' % (n, best[n][1][5:]) for c, n, l in q if c == cl))
print(len(best), 'n with a take file;', out)
