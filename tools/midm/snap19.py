"""snap19.py K [SECONDS]: snapshot K (30 or more) of the take files of the other lanes as kick starts, round 19.

It reads every take-*-r17 dir (frozen) and every take-*-r19 dir but this lane's. The start of an n is the lowest
certified file of those dirs, and only when it is more than 1e-10 below the held score. Left out:
  - a file whose bytes had a kick scan of 6 tries or more in round 17 (work/r17 to r22 of take-midm-r17, with a
    scan table in boxE-final/run/s<K>), or that an earlier snapshot of this round holds
  - a file of the same lane within 2e-9 of score of the file an earlier snapshot of this round holds for that n
  - an n whose lowest file is this lane's own round 17 file (it had its kick and its leg); MIDM_LEGS=875,... adds
    one leg from such a file
Writes work/r<K>/<n>.csv, work/r<K>.tsv (n, score, dir, source, licence, class) and work/q<K>.q. The classes, in
the order the queue runs them:
  1  a construction of round 19 (a take-*-r19 dir that is not polish or harvest)
  2  a construction that entered a frozen round 17 dir after the last snapshot of round 17 (19:16 UTC)
  3  a leg owed (MIDM_LEGS)
  4  every other file: polish and harvest files, and the files of the snapshots 19 to 22 that never ran
"""
import csv, filecmp, glob, math, os, shutil, sys
B = '$SCRATCH/bounties-squares/'; W = B + 'take-midm-r19/work/'; W17 = B + 'take-midm-r17/work/'
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
K = int(sys.argv[1]); secs = int(sys.argv[2]) if len(sys.argv) > 2 else 150
T1916 = 1794510960.0        # 2026-11-12 19:16 UTC, snapshot 22 of round 17
QUENCH = ('polish', 'harvest')
RK = 'r%d' % K; os.makedirs(W + RK, exist_ok=True)
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(B + 'gate/cand-round17-1112a/details.csv'))}
legs = {int(x) for x in os.environ.get('MIDM_LEGS', '').split(',') if x}
best = {}
for d in sorted(glob.glob(B + 'take-*-r17') + glob.glob(B + 'take-*-r19')):
    b = os.path.basename(d)
    if b in ('take-midm-r19', 'take-assemble-r17') or not os.path.exists(d + '/take.tsv'):
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


def kicked17(n, f):
    for j in range(17, 23):
        g = W17 + 'r%d/%d.csv' % (j, n)
        if os.path.exists(g) and filecmp.cmp(f, g, shallow=False):
            for t in glob.glob(W17 + 'boxE-final/run/s%d/scan-%d-*.tsv' % (j, n)):
                if sum(1 for l in open(t) if l[:1].isdigit()) >= 6:
                    return True
    return False


lines = ['n\tscore\tdir\tsource\tlicence\tclass']; q = []; out = {'held': 0, 'own': 0, 'kicked17': 0, 'earlier': 0, 'requenched': 0}
prev = {}       # n -> (score, dir) of the newest earlier snapshot of this round that holds n
for j in range(30, K):
    if os.path.exists(W + 'r%d.tsv' % j):
        for r in csv.DictReader(open(W + 'r%d.tsv' % j), delimiter='\t'):
            prev[int(r['n'])] = (float(r['score']), r['dir'])
for n in sorted(best):
    sc, d, so, lic, f = best[n]
    if not sc < held[n] - 1e-10:
        out['held'] += 1; continue
    lane = d[5:-4]
    if lane == 'midm':
        if n not in legs:
            out['own'] += 1; continue
        cl = 3
    elif d.endswith('-r19'):
        cl = 4 if lane in QUENCH else 1
    else:
        if kicked17(n, f):
            out['kicked17'] += 1; continue
        cl = 2 if (os.path.getmtime(f) > T1916 and lane not in QUENCH) else 4
    if any(os.path.exists(W + 'r%d/%d.csv' % (j, n)) and filecmp.cmp(f, W + 'r%d/%d.csv' % (j, n), shallow=False) for j in range(30, K)):
        out['earlier'] += 1; continue
    if n in prev and prev[n][1] == d and abs(prev[n][0] - sc) < 2e-9:
        out['requenched'] += 1; continue        # the lane wrote the same layout again after one more quench: the queued line stands
    shutil.copyfile(f, W + RK + '/%d.csv' % n)
    P = mlp.load(W + RK + '/%d.csv' % n, {n})[n]; sc = min(sc, mlp.side(P) / math.sqrt(n) - 1)
    lines.append('%d\t%r\t%s\t%s\t%s\t%d' % (n, float(sc), d, so.replace('\t', ' '), lic.replace('\t', ' '), cl))
    q.append((cl, n, 'scan %d %s/%d.csv %d %d kick,lkick 0' % (n, RK, n, secs if n < 700 else int(secs * 1.5), K)))
open(W + RK + '.tsv.tmp', 'w').write('\n'.join(lines) + '\n'); os.rename(W + RK + '.tsv.tmp', W + RK + '.tsv')
for cl in (1, 2, 3, 4):
    L = [l for c, n, l in q if c == cl]
    open(W + 'q%d-c%d.q' % (K, cl), 'w').write('\n'.join(L) + '\n' if L else '')
    print('class', cl, len(L), 'starts:', ' '.join('%d(%s)' % (n, best[n][1][5:]) for c, n, l in q if c == cl))
print(len(best), 'n with a take file;', out)
