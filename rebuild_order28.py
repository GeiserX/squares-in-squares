"""order28.py IN OUT: reorder a box queue.tsv: quench jobs, kicks of our rows (k2- and up), insert jobs (i-),
kicks of fresh compositions named in FRESH, first kicks (k1-), then the rest; stable inside each group."""
import re, sys
FRESH = ('f-stair-c-805',)
L = [l for l in open(sys.argv[1]) if l.strip()]
def pri(l):
    k = l.split('\t'); key = k[0]; mode = k[4].strip() if len(k) > 4 else ''
    if mode == 'quench': return 0
    if re.match(r'^k[2-9]-', key): return 1
    if key.startswith('i-'): return 2
    if key.startswith(FRESH): return 3
    if key.startswith('k1-'): return 4
    return 5
open(sys.argv[2], 'w').write(''.join(sorted(L, key=pri)))
