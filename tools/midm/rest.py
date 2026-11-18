"""rest.py: the queue of every n from 441 to 1000 whose held layout had no kick scan yet (work/qrest.q).

Left out: an n that round 16 replaced (its round 16 score differs from round 15), an n that a live round 17 take dir
holds (a newer layout exists, the snapshot queues kick that one), and the n already in qownrest.q or qsmrest.q.
Order: the classes of source by their measured find rate so far, then n upwards (a small n gets more tries a second).
Prints the find rate of every class from work/scanned-held.txt (n, dir, tries, finds, best, held)."""
import csv, glob, os, re, sys, collections
L = '.'; sys.path.insert(0, L)
import midm_take as mt
B = '$SCRATCH/bounties-squares/'; W = B + 'take-midm-r17/work/'
src = mt.held_sources(L + '/results')
r15 = {int(r['n']): float(r['score']) for r in csv.DictReader(open(B + 'gate/cand-round15-1112a/details.csv'))}
r16 = {int(r['n']): float(r['score']) for r in csv.DictReader(open(B + 'gate/cand-round16-1112a/details.csv'))}
live = set()
for d in glob.glob(B + 'take-*-r17'):
    if os.path.exists(d + '/take.tsv') and not d.endswith('midm-r17'):
        for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
            try: live.add(int(r['n']))
            except Exception: pass
def cls(n):
    s = src.get(n, ('seed merged0', '', ''))[0]
    m = re.match(r'(fq quench of |fq quench \([^)]*\) of )?([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+) ::', s)
    if m: return ('fq of ' if m.group(1) else '') + m.group(2)
    return re.sub(r'[0-9]+', '#', s)[:60]
scan = {}
for l in open(W + 'scanned-held.txt'):
    p = l.split()
    if len(p) < 6: scan.setdefault(int(p[0]), [0, 0, 0.0]); continue
    n = int(p[0]); e = scan.setdefault(n, [0, 0, 0.0]); e[0] += int(p[2]); e[1] += int(p[3]); e[2] = max(e[2], float(p[5]) - float(p[4]))
stat = collections.defaultdict(lambda: [0, 0, 0.0])
for n, (t, f, g) in scan.items():
    if n < 441: continue
    c = cls(n); stat[c][0] += 1; stat[c][1] += (g > 1e-9); stat[c][2] += g / n ** 0.5
queued = set(int(l.split()[1]) for q in ('qownrest', 'qsmrest') for l in os.popen("ssh boxE 'cat scratch/squares-midm/%s.q'" % q) if l.strip())
rest = [n for n in range(441, 1001) if n not in scan and n not in queued and abs(r16[n] - r15[n]) < 1e-13 and n not in live]
rc = collections.Counter(cls(n) for n in rest)
print('class | scanned n | n with a find | score found | not scanned')
for c in sorted(set(stat) | set(rc), key=lambda c: -(stat[c][1] / stat[c][0] if stat[c][0] else 0.5)):
    print('%-62s %3d %3d %.2e %3d' % (c, stat[c][0], stat[c][1], stat[c][2], rc.get(c, 0)))
print('scanned from the held file, n >= 441:', sum(1 for n in scan if n >= 441), '; replaced in round 16:', sum(1 for n in range(441, 1001) if abs(r16[n] - r15[n]) >= 1e-13), '; in a live take:', len([n for n in live if n >= 441]), '; rest:', len(rest))
def rate(n):
    s = stat[cls(n)]; return s[1] / s[0] if s[0] else 0.3
rest.sort(key=lambda n: (-round(rate(n), 2), n))
line = lambda n: 'scan %d round15-2026-11-12a.csv %d 1 kick,lkick 0\n' % (n, 90 if n < 700 else 120 if n < 850 else 150)
open(W + 'qrestc.q', 'w').write(''.join(line(n) for n in rest if not cls(n).startswith('seed merged')))
open(W + 'qrest.q', 'w').write(''.join(line(n) for n in rest if cls(n).startswith('seed merged')))
print('qrestc.q:', [n for n in rest if not cls(n).startswith('seed merged')])
print(' '.join(str(n) for n in rest))
