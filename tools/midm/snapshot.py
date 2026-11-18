"""snapshot.py K [SECONDS]: snapshot K (18 or more) of the certified round 17 files of the other lanes as kick starts.

Writes work/r<K>/<n>.csv, work/r<K>.tsv (n, score, dir, source, licence) and work/q<K>.q (its own seed, so that a
claim of an earlier snapshot never hides a line). A file whose bytes are those of an earlier snapshot
(work/r17/<n>.csv to work/r<K-1>/<n>.csv) is left out: it had its kick. The score of a start is the lower of its
take.tsv line and the side of the copied csv. With several lanes on one n the lowest start wins.
"""
import csv, filecmp, glob, math, os, shutil, sys, time
B = '$SCRATCH/bounties-squares/'; W = B + 'take-midm-r17/work/'
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
K = int(sys.argv[1]); secs = int(sys.argv[2]) if len(sys.argv) > 2 else 150
seed = K + 1 if K < 20 else K + 10; RK = 'r%d' % K       # 21 to 23 and 100 up are the seeds of the second legs
os.makedirs(W + RK, exist_ok=True)
best = {}
for d in sorted(glob.glob(B + 'take-*-r17')):
    if d.endswith('take-midm-r17') or d.endswith('take-assemble-r17') or not os.path.exists(d + '/take.tsv'):
        continue
    for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
        try:
            n = int(r['n']); f = '%s/%d.csv' % (d, n)
            P = mlp.load(f, {n})[n]
            if len(P) != n:
                continue
            sc = min(float(r['new']), mlp.side(P) / math.sqrt(n) - 1)
        except Exception as e:
            print('skip', d, r.get('n'), e); continue
        if n not in best or sc < best[n][0]:
            best[n] = (sc, os.path.basename(d), r.get('source', ''), r.get('licence', ''), f)
old = {}
if os.path.exists(W + RK + '.tsv'):
    old = {int(r['n']): r for r in csv.DictReader(open(W + RK + '.tsv'), delimiter='\t')}
lines = ['n\tscore\tdir\tsource\tlicence']; q = []; same = []
for n in sorted(best):
    sc, d, so, lic, f = best[n]
    if any(os.path.exists(W + 'r%d/%d.csv' % (j, n)) and filecmp.cmp(f, W + 'r%d/%d.csv' % (j, n), shallow=False) for j in range(17, K)):
        same.append(n); continue
    if os.path.exists(W + RK + '/%d.csv' % n) and filecmp.cmp(f, W + RK + '/%d.csv' % n, shallow=False) and n in old:
        o = old[n]; lines.append('%s\t%s\t%s\t%s\t%s' % (o['n'], o['score'], o['dir'], o['source'], o['licence'])); continue
    shutil.copyfile(f, W + RK + '/%d.csv' % n)
    P = mlp.load(W + RK + '/%d.csv' % n, {n})[n]; sc = min(sc, mlp.side(P) / math.sqrt(n) - 1)
    lines.append('%d\t%r\t%s\t%s\t%s' % (n, float(sc), d, so.replace('\t', ' '), lic.replace('\t', ' ')))
    q.append('scan %d %s/%d.csv %d %d kick,lkick 0' % (n, RK, n, secs if n < 700 else int(secs * 1.5), seed))
open(W + RK + '.tsv.tmp', 'w').write('\n'.join(lines) + '\n'); os.rename(W + RK + '.tsv.tmp', W + RK + '.tsv')
open(W + 'q%d.q' % K, 'w').write('\n'.join(q) + '\n' if q else '')
print(len(best), 'files;', len(same), 'as in an earlier snapshot:', same)
print(len(q), 'new starts:', ' '.join('%d(%s)' % (int(l.split()[1]), best[int(l.split()[1])][1].replace('take-', '').replace('-r17', '')) for l in q))
