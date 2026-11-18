"""Rewrite near-pub/queue-fresh.tsv as the starts of queue-fresh-all.tsv measured clean in excl-share.tsv (share1e3 < 0.4)."""
import csv, os, sys
d = sys.argv[1]
csv.field_size_limit(1 << 26)
m = {r['start']: float(r['share1e3']) for r in csv.DictReader(open(f'{d}/excl-share.tsv'), delimiter='\t')}
lines = open(f'{d}/queue-fresh-all.tsv').read().splitlines()
head, keep, out, wait = lines[0], [], 0, 0
for l in lines[1:]:
    s = l.split('\t')[4]
    if s not in m:
        wait += 1
    elif m[s] >= 0.4:
        out += 1
    else:
        keep.append(l)
open(f'{d}/queue-fresh.tsv.tmp', 'w').write('\n'.join([head] + keep) + '\n')
os.replace(f'{d}/queue-fresh.tsv.tmp', f'{d}/queue-fresh.tsv')
print('kept', len(keep), 'out', out, 'not measured yet', wait)
