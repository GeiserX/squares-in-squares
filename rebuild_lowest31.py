"""lowest31.py N: print the per-n csv of the lowest live round 31 take row of n (any lane, ours included), else the held extract."""
import csv, glob, sys
S = '$SCRATCH/bounties-squares/'
n = int(sys.argv[1]); best = None
for t in glob.glob(S + 'take-*-r31/take.tsv'):
    try:
        for r in csv.DictReader(open(t), delimiter='\t'):
            if r.get('n') == str(n) and (best is None or float(r['new']) < best[0]):
                best = (float(r['new']), t.replace('take.tsv', '%d.csv' % n))
    except Exception:
        pass
print(best[1] if best else S + 'take-rebuild-r31/work/held31/%d.csv' % n)
