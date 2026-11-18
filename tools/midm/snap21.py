"""snap21.py K [SECONDS]: snapshot K (21 to 99) of the take files of the other lanes as kick starts, round 21.

It reads every take-*-r20 dir (frozen) and every take-*-r21 dir but this lane's. The start of an n is the lowest
certified file of those dirs, and only when it is more than 1e-10 below the round 19 file. Left out:
  - an n whose lowest file is this lane's own round 20 file (it had its kick and its legs; owed legs go by hand)
  - a file whose bytes had a kick scan of 6 tries or more in round 20 (take-midm-r20/work/r43 to r99, with the scan
    tables in take-midm-r20/work/r20-boxE/run/s<K>), or that an earlier snapshot of this round holds
  - a file of the same lane within 1e-6 of score of the file an earlier snapshot of round 20 or 21 holds for that n
  - a file not below this lane's own round 21 row of that n, or within 1e-8 of our round 20 or 21 row (our file again)
  - a polish or harvest file within 1e-6 of score of a file an earlier snapshot holds for that n
Writes work/r<K>/<n>.csv, work/r<K>.tsv (n, score, dir, source, licence, class) and work/q<K>-c<class>.q, lines in
ascending n. The classes, in the order the workers take them:
  1  a construction at n under 640 (round 20: 5 of 18 first scans found there)
  2  a construction of round 21 at n of 640 and more
  3  a construction of round 20 at n of 640 and more that never had a kick scan (the frozen backlog)
  4  a polish or harvest file of an n that had a kick scan of 6 tries or more in round 20. A quench of a layout that
     never had a kick takes the class of a construction (the harvest lane quenches the new layouts of other lanes:
     869, 811, 969, 980 and 982 of round 20 were never kicked)
Seconds: SECONDS under n = 700, 1.5 times that to 799, 3 times that from 800 up.
"""
import csv, filecmp, glob, math, os, shutil, sys
B = '$SCRATCH/bounties-squares/'; W = os.environ.get('MIDM_W', B + 'take-midm-r21/work/'); W20 = B + 'take-midm-r20/work/'
RUN20 = W20 + 'r20-boxE/run/'
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
K = int(sys.argv[1]); secs = int(sys.argv[2]) if len(sys.argv) > 2 else 150
QUENCH = ('polish', 'harvest')
RK = 'r%d' % K; os.makedirs(W + RK, exist_ok=True)
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(B + 'gate/cand-round19-1112a/details.csv'))}
legs = {int(x) for x in os.environ.get('MIDM_LEGS', '').split(',') if x}
best = {}
for d in sorted(glob.glob(B + 'take-*-r20') + glob.glob(B + 'take-*-r21')):
    b = os.path.basename(d)
    if b in ('take-midm-r21',) or b.startswith('take-assemble') or not os.path.exists(d + '/take.tsv'):
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


def kicked20(n, f):
    for j in range(43, 100):
        g = W20 + 'r%d/%d.csv' % (j, n)
        if os.path.exists(g) and filecmp.cmp(f, g, shallow=False):
            for t in glob.glob(RUN20 + 's%d/scan-%d-*.tsv' % (j, n)):
                if sum(1 for l in open(t) if l[:1].isdigit()) >= 6:
                    return True
    return False


lines = ['n\tscore\tdir\tsource\tlicence\tclass']; q = []
out = {'held': 0, 'own': 0, 'own21': 0, 'kicked20': 0, 'earlier': 0, 'requenched': 0}
own21 = {}
if os.path.exists(B + 'take-midm-r21/take.tsv'):
    own21 = {int(r['n']): float(r['new']) for r in csv.DictReader(open(B + 'take-midm-r21/take.tsv'), delimiter='\t')}
own20 = {int(r['n']): float(r['new']) for r in csv.DictReader(open(B + 'take-midm-r20/take.tsv'), delimiter='\t')}
prev = {}       # n -> [(score, lane dir name)] of every earlier snapshot of round 20 and of this round
for WW, lo, hi in ((W20, 43, 100), (W, 21, K)):
    for j in range(lo, hi):
        if os.path.exists(WW + 'r%d.tsv' % j):
            for r in csv.DictReader(open(WW + 'r%d.tsv' % j), delimiter='\t'):
                if WW == W20 and not any(sum(1 for l in open(t) if l[:1].isdigit()) >= 6 for t in glob.glob(RUN20 + 's%d/scan-%s-*.tsv' % (j, r['n']))):
                    continue        # a round 20 snapshot line that never ran (the class 2 backlog at the deadline) is no kick
                prev.setdefault(int(r['n']), []).append((float(r['score']), os.path.basename(r['dir'])))
for n in sorted(best):
    sc, d, so, lic, f = best[n]
    if not sc < held[n] - 1e-10:
        out['held'] += 1; continue
    if n in own21 and not sc < own21[n] - 1e-10:
        out['own21'] += 1; continue
    lane = d[5:-4]
    if lane == 'midm':
        if n not in legs:
            out['own'] += 1; continue
        cl = 1 if n < 640 else 2
    elif lane in QUENCH and any(sum(1 for l in open(t) if l[:1].isdigit()) >= 6 for t in glob.glob(RUN20 + 's*/scan-%d-*.tsv' % n)):
        cl = 4          # a quench of a layout that had a kick scan in round 20
    elif n < 640:
        cl = 1
    elif d.endswith('-r21'):
        cl = 2
    else:
        cl = 3
    if d.endswith('-r20') and kicked20(n, f):
        out['kicked20'] += 1; print('kicked20', n, d); continue
    if any(os.path.exists(W + 'r%d/%d.csv' % (j, n)) and filecmp.cmp(f, W + 'r%d/%d.csv' % (j, n), shallow=False) for j in range(21, K)):
        out['earlier'] += 1; continue
    if any((pd == d or lane in QUENCH) and abs(ps - sc) < 1e-6 for ps, pd in prev.get(n, [])):
        # a re-post of the same lane, or a polish or harvest quench of a file an earlier snapshot holds (01:17Z: the
        # polish lane posts the harvest-r20 811 and 980 again 5e-10 lower)
        out['requenched'] += 1; print('requenched', n, d); continue
    if any(n in o and abs(o[n] - sc) < 1e-8 for o in (own20, own21)):
        # our own file joined or quenched again a hair lower (round 20: k123 posted our 910 and 584 2.9e-10 and 2.4e-9 lower)
        out['own21'] += 1; print('ownagain', n, d); continue
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
