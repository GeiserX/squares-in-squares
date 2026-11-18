# rank21.py BAR.csv TAG OUT.list LIMIT QUEUE.tsv [...] [--done RAWDIR ...] [--per-n K] [--cut C]
# Round 21: rank20.py plus two measured filters for table states that no build reaches (round 20 next item 3).
# 1. A row predicted more than C (default 5e-3) of side below the bar is dropped: over the builds of rounds 19 and 20,
#    27 of 27 rows predicted more than 0.02 below the bar of 2026-11-13 01:10 UTC had no start, and no row between
#    0.002 and 0.02 below it was built. Every certified row of those rounds was predicted between 1.6e-3 below and
#    6.3e-4 above its bar.
# 2. A row whose corner had a build with no start within 3e-3 of the same f is dropped (the no-start states of
#    803fa19.Ct, 803in20.Ct, 549mi19.Ct and zc7x7-78f9944br.Ct sit at one f each, the end of the turned table).
# 4. (third run of round 21) an n where 3 or more builds ended at the bar (to 1e-7 of side) keeps only rows ranked
#    1e-4 or more below it: on 754, 703 and 505 every build of another corner rebuilt the bar layout.
# --skip FILE: lines "CORNER F" of corner states that modules.py check found with no start, dropped the same way.
import csv, collections, glob, hashlib, json, math, os, statistics, sys
a = sys.argv[1:]
done = a[a.index('--done') + 1:] if '--done' in a else []
a = a[:a.index('--done')] if '--done' in a else a
per_n = int(a[a.index('--per-n') + 1]) if '--per-n' in a else 99
cut = float(a[a.index('--cut') + 1]) if '--cut' in a else 5e-3
skipf = a[a.index('--skip') + 1] if '--skip' in a else None
a = [x for i, x in enumerate(a) if x not in ('--per-n', '--cut', '--skip') and not (i and a[i - 1] in ('--per-n', '--cut', '--skip'))]
barp, tag, out, limit = a[0], a[1], a[2], float(a[3]); qs = a[4:]
bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(barp))}
R = os.environ.get('MODULES_RESULTS', 'results/')
g = collections.defaultdict(list); built = set(); nost = collections.Counter(); okc = set(); nsf = collections.defaultdict(list); atbar = collections.Counter()
for f in ('modules-r16-2026-11-12.tsv', 'modules-r17-2026-11-12.tsv'):
    for r in csv.DictReader(open(R + f), delimiter='\t'):
        try: b = float(r['built_side']); p = float(r['predicted_side'])
        except Exception: continue
        g[r['corner']].append(b - p); built.add((int(r['n']), r['corner'], int(r['stacks1']), int(r['stacks2'])))
for d in done:
    for p in glob.glob(d + '/*.json') + glob.glob(d + '/*.nostart'):
        try: j = json.load(open(p))
        except Exception: continue
        ids = j.get('ids') or [x['id'] for x in j.get('modules', [])]
        st = j.get('stacks') or []
        if ids and len(st) >= 2:
            built.add((int(j['n']), ids[0], int(st[0]), int(st[1])))
            if j.get('built') is not None:
                g[ids[0]].append(j['built'] - j['predicted']); okc.add(ids[0])
                if abs(j['built'] - bar.get(int(j['n']), 0.0)) < 1e-7: atbar[int(j['n'])] += 1
            elif p.endswith('.nostart'):
                nost[ids[0]] += 1
                if j.get('predicted'): nsf[ids[0]].append(j['predicted'] - math.isqrt(int(j['n']) - 1))
import os
if skipf and os.path.exists(skipf):                      # 3. corner states that modules.py check found with no start: "CORNER F"
    for l in open(skipf):
        w = l.split()
        if len(w) >= 2: nsf[w[0]].append(float(w[1]))
glob_med = statistics.median(v for L in g.values() for v in L)
off = {c: statistics.median(L) for c, L in g.items() if len(L) >= 3}
rows = []; drop = collections.Counter()
for q in qs:
    if not os.path.exists(q): continue          # an unmatched shell glob arrives as itself (round 21: boxD-tq/q-*.tsv stopped every re-rank)
    for r in csv.DictReader(open(q), delimiter='\t'):
        if r['n'] == 'n': continue
        n = int(r['n']); c = r['corner']
        if nost[c] >= 2 and c not in okc: drop['corner no start'] += 1; continue
        fr = float(r['f'])
        if any(abs(fr - x) < 3e-3 for x in nsf.get(c, ())): drop['no start near this f'] += 1; continue
        o = off.get(c, 0.0 if c.endswith('t') else glob_med)
        src = ''.join(ch for ch in c.split('.')[0][:4] if ch.isdigit())[:3]
        if src.isdigit() and int(src) == n: o = max(o, glob_med) + 3e-4   # own n: rebuilds its own layout (r20: 340, 418, 652; r21: 340 twice, to 1e-9)
        cm = float(r['predicted_side']) + o - bar[n]
        if cm < -cut: drop['below the bar by more than cut'] += 1; continue
        if atbar[n] >= 3 and c in okc and cm > -1e-4: drop['n whose builds end at the bar'] += 1; continue   # 4. (round 21, third run) 754, 703, 505: 3 to 6 builds of other corners all ended at the bar to 1e-8
        if cm < limit: rows.append((cm, n, r))
rows.sort(key=lambda x: x[0])
seen = set(); cnt = collections.Counter(); outl = []
for cm, n, r in rows:
    key = (n, r['corner'], int(r['stacks1']), int(r['stacks2']))
    if key in built or key in seen: continue
    if cnt[n] >= per_n: continue
    seen.add(key); cnt[n] += 1
    nm = '%d-g%s' % (n, hashlib.sha1(('%s %s %s %s %s' % (r['corner'], r['far1'], r['far2'], r['stacks1'], r['stacks2'])).encode()).hexdigest()[:7])   # the same row keeps its name (and claim) in every pass
    outl.append('slp %s %d %s %s %s %s %s %s  # %+.6f\n' % (nm, n, r['corner'], r['far1'], r['far2'], r['stacks1'], r['stacks2'], r['f'], cm))
open(out, 'w').writelines(l.split('  #')[0] + '\n' for l in outl)
open(out + '.why', 'w').writelines(outl)
print('global median %.6f, corners with an offset %d, dropped %s, rows %d on %d n -> %d build lines' % (glob_med, len(off), dict(drop), len(rows), len({n for _, n, _ in rows}), len(outl)))
