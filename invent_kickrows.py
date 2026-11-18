#!/usr/bin/env python3
"""Pool the per-try rows of every kick scan table: which try pays for its seconds, and when a scan can stop.

Usage: invent_kickrows.py OUT.tsv KIND=DIR [KIND=DIR ...]
  OUT.tsv   one row for each cell (start kind, mode, flag set, kick size) with its tries, seconds, finds and gain;
            OUT-scans.tsv beside it has one row for each scan, with how many of its first 6 tries came back
  KIND=DIR  a name for the kind of start layout and a dir that holds scan-<n>-<seed>.tsv files of midm_scan.py
            at any depth (held = a layout of the held file, fresh = a new file of a lane, relay = a leg from a find)
            midm=DIR is the run dir of the midm lane: there the kind comes from the sub dir and the seed (s17 and
            later are the new files of other lanes, a seed of 21 to 23 or of 100 and more is a leg from a find, the
            control dirs are left out)

midm_scan.py writes one line for each try (index, mode, flag set, kick size, end side, seconds) and a "# FIND" line
when a try ends below the side the scan holds at that moment. This tool reads those tables and nothing else.
A scan counts as a scan with a find when it ends more than BAR of score below its start side: a scan that ends
about 5e-11 below only loses the padding of the held file. Only the finds of such scans count.

It prints: the pooled table by mode and flag set, the same on the scans of odd n and of even n (the control), the
table by kick size, the try index and the second of the first find, and what the first tries of a scan say about
the tries after them. Our own code.
"""
import collections, glob, math, os, re, sys

BAR = 1e-10      # of score: the bar of the take
NEAR = 5e-9      # of side: a try that ends this near its start side came back to the same layout
FIRST = 6        # the first tries of a scan that the stop rule reads

out = sys.argv[1]
scans = []; seen_scans = set(); dup = 0
for a in sys.argv[2:]:
    kind0, d = a.split('=', 1)
    for f in sorted(glob.glob(d + '/**/scan-*.tsv', recursive=True)):
        x = open(f).read(); kind = kind0
        if kind0 == 'midm':
            # the run dir of the midm lane: the kind comes from the sub dir and the seed of the scan
            sub = os.path.relpath(f, d).split(os.sep)[0]; sd = int(re.search(r'scan-\d+-(\d+)\.tsv$', f).group(1))
            if 'ctl' in sub: continue                                   # controls start from files we no longer hold
            kind = ('relay' if sub == 'relay' or sd >= 100 or sd in (21, 22, 23) else
                    'fresh' if re.match(r's(1[7-9]|2\d)$', sub) else 'held')
        h = re.search(r'^# n=(\d+) held=([\d.]+) ref=[\d.]+ modes=(\S+) seed=(\d+)', x, re.M)
        e = re.search(r'^# END n=\d+ tries (\d+) finds (\d+) best ([\d.]+) held ([\d.]+) seconds (\d+)', x, re.M)
        if not h or not e: continue
        n = int(h.group(1)); held = float(h.group(2)); best = float(e.group(3))
        tries = []; inc = held; found = {}
        for m in re.finditer(r'^# FIND try (\d+) .* side ([\d.]+) ', x, re.M): found[int(m.group(1))] = float(m.group(2))
        el = 0.0
        for l in x.splitlines():
            c = l.split('\t')
            if len(c) < 6 or not c[0].isdigit(): continue
            i = int(c[0]); side = float(c[4]); sec = float(c[5]); el += sec
            step = 0.0
            if i in found:
                step = (inc - found[i]) / math.sqrt(n); inc = found[i]
            tries.append(dict(i=i, mode=c[1], flags=c[2], what=c[3], side=side, sec=sec, el=el, find=i in found, step=step))
        if not tries: continue
        key = (n, int(h.group(4)), round(held, 9), h.group(3))
        if key in seen_scans: dup += 1; continue      # two lanes ran the same n, seed and start: the tries are the same
        seen_scans.add(key)
        scans.append(dict(f=f, kind=kind, n=n, held=held, best=best, gain=(held - best) / math.sqrt(n), modes=h.group(3),
                          seed=int(h.group(4)), tries=tries, real=(held - best) / math.sqrt(n) > BAR))


def size(t):
    if t['mode'] == 'kick': return t['what']
    m = re.search(r'r([\d.]+),s([\d.]+)', t['what'])
    return 'r%s,s%s' % (m.group(1), m.group(2)) if m else t['what']


def table(sel, key):
    """cells of the tries of the scans in sel: tries, seconds, finds (tries that step down by more than BAR in a scan
    with a find), first finds, gain of score"""
    T = collections.defaultdict(lambda: [0, 0.0, 0, 0, 0.0])
    for s in sel:
        first = True
        for t in s['tries']:
            c = T[key(s, t)]; c[0] += 1; c[1] += t['sec']
            if s['real'] and t['find'] and t['step'] > BAR:
                c[2] += 1; c[4] += t['step']
                if first: c[3] += 1; first = False
    return T


def show(title, T, minrows=1):
    tot = [sum(c[i] for c in T.values()) for i in range(5)]
    print('\n' + title)
    print('cell\ttries\tseconds\tfinds\tfirst_finds\tgain\tfinds_per_1000s\tgain_per_1000s')
    for k in sorted(T, key=lambda k: -T[k][2] / max(T[k][1], 1e-9)):
        c = T[k]
        if c[0] < minrows: continue
        print('%s\t%d\t%.0f\t%d\t%d\t%.3e\t%.2f\t%.3e' % (' '.join(k), c[0], c[1], c[2], c[3], c[4], 1000 * c[2] / max(c[1], 1e-9), 1000 * c[4] / max(c[1], 1e-9)))
    print('all\t%d\t%.0f\t%d\t%d\t%.3e\t%.2f\t%.3e' % (tot[0], tot[1], tot[2], tot[3], tot[4], 1000 * tot[2] / max(tot[1], 1e-9), 1000 * tot[4] / max(tot[1], 1e-9)))
    return tot


kk = [s for s in scans if set(s['modes'].split(',')) <= {'kick', 'lkick'}]
print('scan tables read: %d (and %d second copies left out); with kick and lkick only: %d; of those with a find over the bar: %d' % (len(scans), dup, len(kk), sum(s['real'] for s in kk)))
for kind in sorted({s['kind'] for s in kk}):
    g = [s for s in kk if s['kind'] == kind]
    print('kind %s: %d scans on %d n, %d tries, %.0f s, %d scans with a find, gain %.3e' % (
        kind, len(g), len({s['n'] for s in g}), sum(len(s['tries']) for s in g), sum(t['sec'] for s in g for t in s['tries']),
        sum(s['real'] for s in g), sum(s['gain'] for s in g if s['real'])))

mf = lambda s, t: (t['mode'], t['flags'])
show('by mode and flag set, every kick scan', table(kk, mf))
show('the same on odd n', table([s for s in kk if s['n'] % 2], mf))
show('the same on even n', table([s for s in kk if not s['n'] % 2], mf))
for kind in sorted({s['kind'] for s in kk}):
    show('by mode and flag set, kind %s' % kind, table([s for s in kk if s['kind'] == kind], mf))
show('by mode and kick size', table(kk, lambda s, t: (t['mode'], size(t))))
show('by mode, flag set and kick size, cells of 150 tries or more', table(kk, lambda s, t: (t['mode'], t['flags'], size(t))), 150)

with open(out, 'w') as h:
    h.write('kind\tmode\tflags\tkick_size\ttries\tseconds\tfinds\tfirst_finds\tgain_of_score\tfinds_per_1000s\n')
    T = table(kk, lambda s, t: (s['kind'], t['mode'], t['flags'], size(t)))
    for k in sorted(T):
        c = T[k]; h.write('%s\t%s\t%s\t%s\t%d\t%.0f\t%d\t%d\t%.3e\t%.3f\n' % (k + (c[0], c[1], c[2], c[3], c[4], 1000 * c[2] / max(c[1], 1e-9))))

# ---- when the first find comes
real = [s for s in kk if s['real']]
fi = sorted(next(t['i'] for t in s['tries'] if t['find'] and t['step'] > BAR) for s in real if any(t['find'] and t['step'] > BAR for t in s['tries']))
fe = sorted(next(t['el'] for t in s['tries'] if t['find'] and t['step'] > BAR) for s in real if any(t['find'] and t['step'] > BAR for t in s['tries']))
q = lambda v, p: v[min(len(v) - 1, int(p * len(v)))] if v else float('nan')
print('\nfirst find of a scan with a find (%d scans): try index median %s, 80%% %s, 95%% %s; fq seconds median %.0f, 80%% %.0f, 95%% %.0f' % (
    len(fi), q(fi, .5), q(fi, .8), q(fi, .95), q(fe, .5), q(fe, .8), q(fe, .95)))
for cut in (4, 6, 10, 15, 20, 30):
    long = [s for s in kk if len(s['tries']) > cut]
    late = [s for s in long if s['real'] and not any(t['find'] and t['step'] > BAR for t in s['tries'][:cut]) and any(t['find'] and t['step'] > BAR for t in s['tries'][cut:])]
    dry = [s for s in long if not any(t['find'] and t['step'] > BAR and s['real'] for t in s['tries'][:cut])]
    print('scans with more than %d tries and no find in the first %d: %d; a find later: %d (%.1f%%); tries after the cut: %d' % (
        cut, cut, len(dry), len(late), 100.0 * len(late) / max(len(dry), 1), sum(len(s['tries']) - cut for s in dry)))

# ---- what the first tries say
print('\nthe first %d tries of a scan against the tries after them (scans with more than %d tries)' % (FIRST, FIRST))
G = collections.defaultdict(lambda: [0, 0, 0, 0.0, 0])
for s in kk:
    if len(s['tries']) <= FIRST: continue
    head = s['tries'][:FIRST]; tail = s['tries'][FIRST:]
    back = sum(1 for t in head if abs(t['side'] - s['held']) < NEAR)
    hit = any(t['find'] and t['step'] > BAR and s['real'] for t in head)
    lowest = min(t['side'] for t in head) - s['held']
    key = ('a find in the first %d' % FIRST) if hit else ('came back %s of %d' % ('0' if back == 0 else '1 or 2' if back <= 2 else '3 or more', FIRST))
    g = G[key]; g[0] += 1
    later = [t for t in tail if t['find'] and t['step'] > BAR and s['real']]
    g[1] += 1 if later else 0; g[2] += len(tail); g[3] += sum(t['sec'] for t in tail); g[4] += len(later)
print('group\tscans\tscans_with_a_later_find\tlater_tries\tlater_seconds\tlater_finds\tfinds_per_1000s')
for k in sorted(G):
    g = G[k]; print('%s\t%d\t%d\t%d\t%.0f\t%d\t%.2f' % (k, g[0], g[1], g[2], g[3], g[4], 1000 * g[4] / max(g[3], 1e-9)))
G2 = collections.defaultdict(lambda: [0, 0, 0.0, 0])
for s in kk:
    if len(s['tries']) <= FIRST: continue
    head = s['tries'][:FIRST]; tail = s['tries'][FIRST:]
    if any(t['find'] and t['step'] > BAR and s['real'] for t in head): continue
    lowest = (min(t['side'] for t in head) - s['held']) / math.sqrt(s['n'])
    key = 'lowest of the first %d: %s' % (FIRST, 'at the start side' if lowest < NEAR / 20 else 'under 1e-7 of score above' if lowest < 1e-7 else 'under 1e-6 above' if lowest < 1e-6 else '1e-6 or more above')
    g = G2[key]; later = [t for t in tail if t['find'] and t['step'] > BAR and s['real']]
    g[0] += 1; g[1] += 1 if later else 0; g[2] += sum(t['sec'] for t in tail); g[3] += len(later)
print('group\tscans\tscans_with_a_later_find\tlater_seconds\tlater_finds\tfinds_per_1000s')
for k in sorted(G2):
    g = G2[k]; print('%s\t%d\t%d\t%.0f\t%d\t%.2f' % (k, g[0], g[1], g[2], g[3], 1000 * g[3] / max(g[2], 1e-9)))

# ---- the control of the kick size: the two halves
sz = lambda s, t: (t['mode'], size(t))
show('by mode and kick size, odd n', table([s for s in kk if s['n'] % 2], sz))
show('by mode and kick size, even n', table([s for s in kk if not s['n'] % 2], sz))

# ---- where the seconds pay: the phases of a scan
PH = collections.defaultdict(lambda: [0, 0.0, 0, 0.0, set()])
CUT = 10
for s in kk:
    seen = False
    for j, t in enumerate(s['tries']):
        hit = s['real'] and t['find'] and t['step'] > BAR
        if s['kind'] == 'relay': ph = 'a leg from a find'
        elif seen: ph = 'after a find of the same scan'
        elif j < CUT: ph = 'tries 1 to %d of a scan with no find yet' % CUT
        else: ph = 'tries after %d dry tries' % CUT
        ph = ('%s, %s' % (s['kind'], ph)) if s['kind'] != 'relay' else ph
        c = PH[ph]; c[0] += 1; c[1] += t['sec']
        if hit: c[2] += 1; c[3] += t['step']; c[4].add(s['n']); seen = True
print('\nwhere the seconds pay')
print('phase\ttries\tseconds\tfinds\tn_with_a_find\tgain\tfinds_per_1000s\tgain_per_1000s')
for k in sorted(PH):
    c = PH[k]; print('%s\t%d\t%.0f\t%d\t%d\t%.3e\t%.2f\t%.3e' % (k, c[0], c[1], c[2], len(c[4]), c[3], 1000 * c[2] / max(c[1], 1e-9), 1000 * c[3] / max(c[1], 1e-9)))

# ---- the largest steps
F = sorted(((t['step'], s['n'], s['kind'], t['mode'], t['flags'], size(t), t['i']) for s in kk if s['real'] for t in s['tries'] if t['find'] and t['step'] > BAR), reverse=True)
tot = sum(f[0] for f in F)
print('\nthe %d finds: total %.3e; the largest 5 hold %.0f%%, the largest 15 hold %.0f%%; median step %.2e; steps of 1e-6 or more: %d' % (
    len(F), tot, 100 * sum(f[0] for f in F[:5]) / tot, 100 * sum(f[0] for f in F[:15]) / tot, F[len(F) // 2][0], sum(1 for f in F if f[0] >= 1e-6)))
print('step\tn\tkind\tmode\tflags\tkick_size\ttry')
for f in F[:15]: print('%.3e\t%d\t%s\t%s\t%s\t%s\t%d' % f)
big = [f for f in F if f[0] >= 1e-6]
for m in ('kick', 'lkick'):
    sec = sum(t['sec'] for s in kk for t in s['tries'] if t['mode'] == m)
    b = [f for f in big if f[3] == m]
    print('%s: %d steps of 1e-6 or more in %.0f s, %.2f per 1000 s; all steps %d' % (m, len(b), sec, 1000 * len(b) / sec, sum(1 for f in F if f[3] == m)))
for h, nm in ((1, 'odd'), (0, 'even')):
    for m in ('kick', 'lkick'):
        sec = sum(t['sec'] for s in kk if s['n'] % 2 == h for t in s['tries'] if t['mode'] == m)
        b = [f for f in big if f[3] == m and f[1] % 2 == h]
        print('%s n, %s: %d steps of 1e-6 or more in %.0f s, %.2f per 1000 s' % (nm, m, len(b), sec, 1000 * len(b) / sec))

# ---- scans that the clock ended while they were still finding
last = [(len(s['tries']) - max(t['i'] for t in s['tries'] if t['find'] and t['step'] > BAR), s) for s in real if any(t['find'] and t['step'] > BAR for t in s['tries'])]
print('\nscans with a find: %d; ended with fewer than 10 dry tries after the last find: %d (on %d n); with fewer than 5: %d' % (
    len(last), sum(1 for d, s in last if d < 10), len({s['n'] for d, s in last if d < 10}), sum(1 for d, s in last if d < 5)))
h10 = [s for s in kk if s['kind'] == 'held']
print('held scans: %.1f s a try in tries 1 to 10; seconds after 10 dry tries: %.0f of %.0f' % (
    sum(t['sec'] for s in h10 for t in s['tries'][:10]) / max(1, sum(len(s['tries'][:10]) for s in h10)),
    sum(t['sec'] for s in h10 if not any(t['find'] and t['step'] > BAR and s['real'] for t in s['tries'][:10]) for t in s['tries'][10:]),
    sum(t['sec'] for s in h10 for t in s['tries'])))

# ---- which cells hold the largest steps
TOP = 15
top = F[:TOP]
isbig = lambda mode, sz: mode == 'kick' and sz in ('sig0.02', 'sig0.04')
secbig = sum(t['sec'] for s in kk for t in s['tries'] if isbig(t['mode'], size(t))); secall = sum(t['sec'] for s in kk for t in s['tries'])
b = [f for f in top if isbig(f[3], f[5])]; o = [f for f in top if not isbig(f[3], f[5])]
print('\nthe %d largest steps hold %.0f%% of the gain. From the full kick at sigma 0.02 or 0.04: %d steps on %d n, in %.0f s (%.0f%% of the seconds), %.2f per 1000 s. From every other try: %d steps on %d n, in %.0f s, %.2f per 1000 s' % (
    TOP, 100 * sum(f[0] for f in top) / tot, len(b), len({f[1] for f in b}), secbig, 100 * secbig / secall, 1000 * len(b) / secbig,
    len(o), len({f[1] for f in o}), secall - secbig, 1000 * len(o) / (secall - secbig)))
for h, nm in ((1, 'odd'), (0, 'even')):
    sb = sum(t['sec'] for s in kk if s['n'] % 2 == h for t in s['tries'] if isbig(t['mode'], size(t)))
    sa = sum(t['sec'] for s in kk if s['n'] % 2 == h for t in s['tries'])
    bb = [f for f in b if f[1] % 2 == h]; oo = [f for f in o if f[1] % 2 == h]
    print('%s n: %d steps on %d n in %.0f s (%.2f per 1000 s) against %d steps on %d n in %.0f s (%.2f per 1000 s)' % (
        nm, len(bb), len({f[1] for f in bb}), sb, 1000 * len(bb) / sb, len(oo), len({f[1] for f in oo}), sa - sb, 1000 * len(oo) / (sa - sb)))
print('gain per 1000 s by kick size, with and without the largest step of the cell')
C = collections.defaultdict(list)
for f in F: C[(f[3], f[5])].append(f[0])
S2 = collections.Counter()
for s in kk:
    for t in s['tries']: S2[(t['mode'], size(t))] += t['sec']
for k in sorted(C, key=lambda k: -sum(C[k]) / S2[k]):
    print('%s %s\tfinds %d\tseconds %.0f\twith %.2e\twithout %.2e\tsteps of 1e-6 or more %d' % (k[0], k[1], len(C[k]), S2[k], 1000 * sum(C[k]) / S2[k], 1000 * (sum(C[k]) - max(C[k])) / S2[k], sum(1 for v in C[k] if v >= 1e-6)))
print('pooled\twith %.2e\twithout the largest step %.2e' % (1000 * tot / secall, 1000 * (tot - F[0][0]) / secall))

# ---- a stop rule from the first tries: how many of them came back to the start side
print('\nthe stop rule: scans by how many of their first %d tries came back to the start side (within %.0e of side)' % (FIRST, NEAR))
print('group\thalf\tscans\tscans_with_a_find\tfinds_in_the_first_%d\tseconds_after\tfinds_after\tgain_after\tsteps_of_1e-6_after' % FIRST)
for h, nm in ((None, 'all'), (1, 'odd n'), (0, 'even n')):
    R = collections.defaultdict(lambda: [0, 0, 0, 0.0, 0, 0.0, 0])
    for s in kk:
        if len(s['tries']) < FIRST or (h is not None and s['n'] % 2 != h): continue
        head = s['tries'][:FIRST]; tail = s['tries'][FIRST:]
        back = sum(1 for t in head if abs(t['side'] - s['held']) < NEAR)
        g = R['%d or more came back' % ((FIRST + 1) // 2) if back >= (FIRST + 1) // 2 else 'fewer than %d came back' % ((FIRST + 1) // 2)]
        ok = lambda t: s['real'] and t['find'] and t['step'] > BAR
        g[0] += 1; g[1] += 1 if any(ok(t) for t in s['tries']) else 0; g[2] += sum(1 for t in head if ok(t))
        g[3] += sum(t['sec'] for t in tail); g[4] += sum(1 for t in tail if ok(t)); g[5] += sum(t['step'] for t in tail if ok(t))
        g[6] += sum(1 for t in tail if ok(t) and t['step'] >= 1e-6)
    for k in sorted(R):
        g = R[k]; print('%s\t%s\t%d\t%d\t%d\t%.0f\t%d\t%.3e\t%d' % (k, nm, g[0], g[1], g[2], g[3], g[4], g[5], g[6]))

# ---- a second scan at another seed after a dry first scan, by the same split of the first scan
base = collections.defaultdict(list)
for s in kk:
    if s['kind'] == 'relay': continue
    base[(s['n'], round(s['held'], 9))].append(s)
P2 = collections.defaultdict(lambda: [0, 0, 0.0])
for k, v in base.items():
    if len(v) < 2: continue
    v.sort(key=lambda s: s['seed'])
    a, b2 = v[0], v[1]
    if a['real'] or len(a['tries']) < FIRST: continue
    back = sum(1 for t in a['tries'][:FIRST] if abs(t['side'] - a['held']) < NEAR)
    g = P2['%d or more came back' % ((FIRST + 1) // 2) if back >= (FIRST + 1) // 2 else 'fewer than %d came back' % ((FIRST + 1) // 2)]
    g[0] += 1; g[1] += 1 if b2['real'] else 0; g[2] += b2['gain'] if b2['real'] else 0
print('\na second scan at another seed after a dry first scan, by the first scan')
print('group\tpairs\tsecond_scans_with_a_find\tgain')
for k in sorted(P2): print('%s\t%d\t%d\t%.3e' % (k, P2[k][0], P2[k][1], P2[k][2]))

# ---- one row for each scan, next to OUT: the table a kick lane sorts its next list by
out2 = out[:-4] + '-scans.tsv' if out.endswith('.tsv') else out + '-scans.tsv'
with open(out2, 'w') as h:
    h.write('kind\tn\tseed\ttries\tseconds\tcame_back_of_first_%d\tfinds\tgain_of_score\tlargest_step\n' % FIRST)
    for s in sorted(kk, key=lambda s: (s['n'], s['kind'], s['seed'])):
        back = sum(1 for t in s['tries'][:FIRST] if abs(t['side'] - s['held']) < NEAR) if len(s['tries']) >= FIRST else -1
        st = [t['step'] for t in s['tries'] if s['real'] and t['find'] and t['step'] > BAR]
        h.write('%s\t%d\t%d\t%d\t%.0f\t%s\t%d\t%.3e\t%.3e\n' % (s['kind'], s['n'], s['seed'], len(s['tries']), sum(t['sec'] for t in s['tries']),
                                                              back if back >= 0 else '', len(st), sum(st), max(st) if st else 0.0))
print('\nwrote %s and %s' % (out, out2))
