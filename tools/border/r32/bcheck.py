"""r31 one-pass check: border-step (b1, b2) and corner-window (rev) picks of every fresh r31 take and near csv of other
lanes (and the harvest public files they name) against the live bars; prints any pick below the live bar (no chains)."""
import sys, glob, json, math, csv
sys.path.insert(0, '.')
import border_sweep as bs
bs.lib()
L = {int(k): v for k, v in json.load(open('bars.json')).items()}
files = sorted(set(glob.glob('$SCRATCH/bounties-squares/take-*-r32/[0-9]*.csv') + glob.glob('$SCRATCH/bounties-squares/take-*-r32/near/*.csv')))
files = [f for f in files if '/take-border-r32/' not in f]
best = []
for p in files:
    try: m, s, A = bs.read_near(p)
    except Exception as e: continue
    for c in range(4):
        ext = sorted(bs.extents(bs.corner(A, s, c)))
        for target in range(2, m):
            side = float(ext[target - 1]); mg = side - L[target]
            best.append((mg / math.sqrt(target), 'rev', m, target, c, p))
    f = math.floor(s)
    for target in range(m + 1, min(1000, m + 4 * f + 4) + 1):
        side = s + 1 if target <= m + 2 * f + 1 else s + 2
        mg = side - L[target]
        best.append((mg / math.sqrt(target), 'b1' if target <= m + 2 * f + 1 else 'b2', m, target, 0, p))
best.sort()
print(len(files), 'files')
for b in best[:15]: print('%.3e' % b[0], *b[1:5], b[5].split('bounties-squares/')[1])
