#!/usr/bin/env python3
"""tables.py ENDS.txt TAKEDIR WORKDIR GAP.tsv [OUT.tsv]: the kick tables of avenues/midm.md.

ENDS.txt holds the END line of every kick scan (ends.sh on boxE writes it: "<run dir> # END n=... tries ...").
TAKEDIR holds take.tsv and TAGS.tsv. WORKDIR holds aspub.txt (the n whose held layout is a public file as published,
beyond those the results tables name by owner), r16.tsv and r17.tsv (the files of other lanes a kick started from).
It prints two markdown tables: the scans by kind of start, and the certified results. With OUT.tsv it also writes
one line per n and kind of start: scans, tries, seconds, the start side, the best side and the certified gain.
"""
import collections, csv, math, os, re, sys

L = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, L)
import midm_take as mt  # noqa: E402

ends, T, W, gapf = sys.argv[1:5]; outf = sys.argv[5] if len(sys.argv) > 5 else None
src = mt.held_sources(L + '/results')
aspub = set(int(l.split()[0]) for l in open(W + '/aspub.txt') if l.strip())
take = {int(r['n']): r for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t')}
gap = {int(r['n']): r for r in csv.DictReader(open(gapf), delimiter='\t')}
tags = dict(l.rstrip('\n').split('\t') for l in open(T + '/TAGS.tsv') if l.strip())


def table(name):
    p = '%s/%s' % (W, name)
    return {int(r['n']): r for r in csv.DictReader(open(p), delimiter='\t')} if os.path.exists(p) else {}


r16, r17 = table('r16.tsv'), table('r17.tsv')
SNAP = {}      # K -> the table of snapshot K of the round 17 files (r<K>.tsv, K from 18 up; run dir s<K>)


def snap(k):
    if k not in SNAP:
        SNAP[k] = table('r%d.tsv' % k)
    return SNAP[k]


def start_row(n, where):
    """The start-table line of n for a run dir or tag that ends in s<K>."""
    m = re.search(r's(\d+)$', where)
    k = int(m.group(1)) if m else 0
    return r17.get(n) if k == 17 else snap(k).get(n) if k >= 18 else r16.get(n) if k == 10 else None


def owner(n):
    s = src.get(n)
    m = re.match(r'([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+) ::', s[0]) if s else None
    return m.group(1) if m else None


def pub(n):
    return owner(n) is not None or n in aspub


KINDS = ('slice, a public file as published', 'slice, every other held layout',
         'outside the slice, a public file as published', 'outside the slice, other held layouts',
         'round 16 files', 'round 17 files of other lanes')


def grp(d, n):
    if d == 'run/relay':
        return None
    if d == 'run/s10':
        return KINDS[4]
    if d == 'run/s17':        # a relay from a find on a round 16 file also runs in this queue: its table line names the dir
        return KINDS[4] if r17.get(n, {}).get('dir', '').endswith('-r16') else KINDS[5]
    if re.fullmatch(r'run/s(1[89]|[2-9]\d)', d):       # the later snapshots of the round 17 files
        return KINDS[5]
    if 257 <= n <= 440:
        return KINDS[0] if pub(n) else KINDS[1]
    return KINDS[2] if pub(n) else KINDS[3]


def tag_grp(n):
    t = tags.get(str(n), '')
    if t.endswith('s17'):
        return KINDS[4] if r17.get(int(n), {}).get('dir', '').endswith('-r16') else KINDS[5]
    if re.search(r's(1[89]|[2-9]\d)$', t):
        return KINDS[5]
    return KINDS[4] if t.endswith('s10') else None


rows = []
for l in open(ends):
    if '# END' not in l:
        continue
    d = l.split()[0]
    m = re.search(r'n=(\d+) tries (\d+) finds (\d+) best ([\d.]+) held ([\d.]+) seconds (\d+)', l)
    if 'bkick' in l or 'melt' in l or d == 'run/wctl':
        continue
    f = re.search(r' file=scan-\d+-(\d+)\.tsv', l)
    if f and (int(f.group(1)) in (21, 22, 23) or int(f.group(1)) >= 100):
        continue        # a second leg from a find (mkrelay.sh): the doc counts the legs apart
    rows.append((d, int(m.group(1)), int(m.group(2)), int(m.group(6)), float(m.group(4)), float(m.group(5))))
G = collections.OrderedDict((k, [set(), 0, 0]) for k in KINDS)
per = collections.OrderedDict()
for d, n, tr, sec, best, start in rows:
    k = grp(d, n)
    if not k:
        continue
    G[k][0].add(n); G[k][1] += tr; G[k][2] += sec
    p = per.setdefault((n, k), [0, 0, 0, start, best])
    p[0] += 1; p[1] += tr; p[2] += sec; p[3] = max(p[3], start); p[4] = min(p[4], best)


def won(k, n):
    g = tag_grp(n)
    if k in KINDS[4:]:
        return g == k
    return g is None and n in G[k][0]


print('| start | n scanned | tries | core seconds | n certified | gain of score |\n|---|---|---|---|---|---|')
for k, (ns, tr, sec) in G.items():
    w = sorted(n for n in take if won(k, n))
    g = sum(float(take[n]['start']) - float(take[n]['new']) for n in w)
    print('| %s | %d | %s | %s | %s | %s |' % (k, len(ns), format(tr, ','), format(sec, ','),
                                         (', '.join(map(str, w)) if w else 'none'), ('%.3e' % g) if w else '0'))
print()
print('| n | held score | new score | gain | start | gap left to the board |\n|---|---|---|---|---|---|')
tot = 0.0; own = 0.0
for n in sorted(take):
    r = take[n]; h, s, st = float(r['held']), float(r['new']), float(r['start']); tot += h - s; own += st - s
    o = owner(n) or ('a public file as published' if n in aspub else 'our own layout')
    g = tag_grp(n)
    if g == KINDS[4]:
        o = 'the round 16 file in `%s`' % (r16.get(n) or r17[n])['dir'] + (', itself %.3e below the held score' % (h - st) if h - st > 1e-13 else '')
    elif g == KINDS[5]:
        o = 'the round 17 file in `%s`, itself %.3e below the held score' % (start_row(n, tags[str(n)])['dir'], h - st)
    b = ('%.1e' % (s + 1 - float(gap[n]['board_L']) / math.sqrt(n))) if n in gap else 'not in the gap table'
    print('| %d | %.12f | %.12f | %.3e | %s | %s |' % (n, h, s, h - s, o, b))
print('\ntotal vs held %.6e ; from our own step %.6e ; n %d ; slice n %s' % (tot, own, len(take), [n for n in take if 257 <= n <= 440]))
sl = set(n for d, n, *_ in rows if 257 <= n <= 440)
print('slice n kick-scanned', len(sl), 'missing', [n for n in range(257, 441) if n not in sl])
print('all scans', len(rows), 'tries', sum(r[2] for r in rows), 'seconds', sum(r[3] for r in rows), 'distinct n', len(set(r[1] for r in rows)))
allpub = [n for n in range(1, 1001) if pub(n)]
kicked = set(n for (n, k) in per if k in (KINDS[0], KINDS[2]))
print('public as published in the held file', len(allpub), 'kicked', len(kicked), 'not kicked', [n for n in allpub if n not in kicked])
if outf:
    with open(outf + '.tmp', 'w') as h:
        h.write('n\tstart\tscans\ttries\tseconds\tstart_side\tbest_side\tcertified_gain\tnew_score\n')
        for (n, k), (sc, tr, sec, start, best) in sorted(per.items()):
            w = won(k, n) and n in take
            h.write('%d\t%s\t%d\t%d\t%d\t%.12f\t%.12f\t%s\t%s\n' % (
                n, k, sc, tr, sec, start, best, ('%.3e' % (float(take[n]['start']) - float(take[n]['new']))) if w else '0', take[n]['new'] if w else ''))
    os.rename(outf + '.tmp', outf)
    print('wrote', outf, len(per), 'lines')
