"""handoff19.py: one line in handoff-r19.log for each row of the midm take that is new or lower since the last call."""
import csv, os, time
B = '$SCRATCH/bounties-squares/'; T = B + 'take-midm-r19/'; seen = {}
if os.path.exists(T + 'work/handoff-seen.tsv'):
    seen = {int(l.split()[0]): float(l.split()[1]) for l in open(T + 'work/handoff-seen.tsv') if l.strip()}
if os.path.exists(T + 'take.tsv'):
    for r in csv.DictReader(open(T + 'take.tsv'), delimiter='\t'):
        n, new = int(r['n']), float(r['new'])
        if n in seen and new >= seen[n] - 1e-13:
            continue
        seen[n] = new
        open(B + 'handoff-r19.log', 'a').write('%s midm -> all: n=%d certified at score %.12f, %.3e below the round 17 file (kick of %s), %s%d.csv\n' % (
            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, new, float(r['held']) - new,
            r['source'].split(' from ')[1][:60] if ' from ' in r['source'] else 'a take file', T, n))
    open(T + 'work/handoff-seen.tsv', 'w').write(''.join('%d\t%r\n' % kv for kv in sorted(seen.items())))
