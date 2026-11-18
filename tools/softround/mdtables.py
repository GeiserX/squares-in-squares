#!/usr/bin/env python3
"""The tables of a round's section of avenues/methods.md from the fetched logs, plan.json and take.tsv (markdown)."""
import collections, csv, glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ctl import W, REMOTE
T = os.path.dirname(W)
pl = json.load(open(W + '/plan.json'))
take = {int(r['n']): r for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t')}
AGAIN = {(j['n'], j['tag']): j for j in pl['jobs'] if j.get('again')}
def legs_of(j):
    legs, fq = legs_dir(j)
    a = AGAIN.get((j['n'], j['tag']))
    if a and not j.get('again'):
        l2, f2 = legs_dir(a); legs.update(l2); fq = fq + f2
    return legs, fq
def legs_dir(j):
    ds = ['%s/%s/run/%d-%s' % (W, b, j['n'], j['tag']) for b in list(REMOTE) + ['boxA']]; legs = {}   # a chain may have legs on two boxes
    for p in sorted(p for d in ds for p in glob.glob(d + '/soft-*.log')):
        seed = int(p[:-4].split('-')[-1]); txt = open(p).read()
        m = re.search(r'^end n=\d+ kids (\d+) finds (\d+) restarts (\d+) L ([\d.]+) -> ([\d.]+) gain ([\d.e+-]+) .* seconds (\d+)', txt, re.M)
        fl = re.findall(r'^FIND t (\d+) kids \d+ move (\S+) .*?gain of score ([\d.e+-]+)\)( ladder)?', txt, re.M)
        ks = re.findall(r'^(?:t|FIND t) (\d+) kids (\d+)', txt, re.M)
        if m: k, f, s, g = int(m.group(1)), int(m.group(2)), int(m.group(7)), float(m.group(6))
        else: k = max([int(x[1]) for x in ks] or [0]); s = max([int(x[0]) for x in ks] or [0]); f = len(fl); g = float(fl[-1][2]) if fl else 0.0
        legs[seed] = dict(kids=k, finds=f, secs=s, gain=g, last=int(fl[-1][0]) if fl else None, ended=bool(m))
    ch = ''.join(open(d + '/chain.log').read() for d in ds if os.path.exists(d + '/chain.log'))
    fq = re.findall(r'^FQEND .* L ([\d.]+) -> ([\d.]+) gain of score ([\d.e+-]+) steps (\d+)', ch, re.M)
    return legs, fq
def group(j):
    """kind of start, and where its file was: the held file, a take dir at the plan, or written during the round"""
    k = {'soft': 'own soft result on a family layout', 'polish': 'polish (fq)', 'readers': 'family (readers)'}.get(j['kind'], j['kind'])
    if j.get('mode') == 'seed2': return '%s, in the held file, second seed (had its pass in the round before)' % k
    return '%s, %s' % (k, 'in the held file' if j['where'] == 'held' else 'written during the round' if j['added'] != 'plan' else 'in a take dir at the plan')
def base(j):
    return 20 if j.get('mode') == 'seed2' else 10
ORDER = ['family', 'readers', 'soft', 'modules', 'border', 'zones', 'polish', 'harvest', 'inflate']
groups = collections.OrderedDict()
for j in sorted(pl['jobs'], key=lambda j: (ORDER.index(j['kind']) if j['kind'] in ORDER else 99, j['where'] != 'held', j['added'] != 'plan')):
    groups.setdefault(group(j), dict(starts=0, passed=0, part=0, notrun=0, skipped=0, islands=0, kids=0, found=[], finds=0, secs=0))
notrun = []; skipped = []; part = []; findrows = []
for j in pl['jobs']:
    if j.get('again'): continue
    legs, fq = legs_of(j); g = groups[group(j)]; g['starts'] += 1
    done = all(sd in legs and legs[sd]['ended'] for sd in ((14,) if j.get('mode') == 'again' else (base(j) + 1, base(j) + 2)))
    if j.get('skipped'): g['skipped'] += 1; skipped.append('%d (%s)' % (j['n'], j['tag']))
    elif done: g['passed'] += 1
    elif legs: g['part'] += 1; part.append('%d (%s, %d children)' % (j['n'], j['tag'], sum(l['kids'] for l in legs.values())))
    else: g['notrun'] += 1; notrun.append('%d (%s)' % (j['n'], j['tag']))
    g['islands'] += len(legs); g['kids'] += sum(l['kids'] for l in legs.values()); g['secs'] += sum(l['secs'] for l in legs.values())
    f = sum(l['finds'] for l in legs.values()); g['finds'] += f
    if f: g['found'].append(j['n']); findrows.append((j, legs, fq))
print('| kind of start | starts | passed | cut short | not run | dropped | islands | children | n with a find | finds |')
print('|---|---|---|---|---|---|---|---|---|---|')
for k, g in groups.items():
    print('| %s | %d | %d | %d | %d | %d | %d | %s | %s | %d |' % (k, g['starts'], g['passed'], g['part'], g['notrun'], g['skipped'], g['islands'], format(g['kids'], ','), ('%d: %s' % (len(g['found']), ', '.join(map(str, g['found'])))) if g['found'] else '0', g['finds']))
tot = {x: sum(g[x] for g in groups.values()) for x in ('starts', 'passed', 'part', 'notrun', 'skipped', 'islands', 'kids', 'finds', 'secs')}
print('| **all** | %d | %d | %d | %d | %d | %d | %s | %d | %d |' % (tot['starts'], tot['passed'], tot['part'], tot['notrun'], tot['skipped'], tot['islands'], format(tot['kids'], ','), sum(len(g['found']) for g in groups.values()), tot['finds']))
print('cpu-hours %.1f' % (tot['secs'] / 3600))
print('cut short:', ', '.join(part)); print('not run:', ', '.join(notrun)); print('dropped:', ', '.join(skipped))
print()
print('| n | start | pass at `2e-4` | pass at `1e-4` | island | fq quench | own gain certified |')
print('|---|---|---|---|---|---|---|')
for j, legs, fq in findrows:
    def cell(s):
        l = legs.get(s)
        if not l: return 'not run'
        return '%s children, %d finds%s' % (format(l['kids'], ','), l['finds'], (', %.3e' % l['gain']) if l['finds'] else '')
    isl = [legs[s] for s in (base(j) + 3, 14) if s in legs]
    ic = '; '.join('%s children, %d finds, last at %s s of %d s, %.3e' % (format(l['kids'], ','), l['finds'], l['last'], l['secs'], l['gain']) for l in isl) or 'not run'
    fc = '; '.join('%s' % g for a, b, g, st in fq) or 'no gain'
    t = take.get(j['n']); own = ('%s' % t['polish_gain']) if t and abs(float(t['start']) - j['start']) < 1e-15 else 'not kept'
    print('| %d | %s (%s) | %s | %s | %s | %s | %s |' % (j['n'], group(j), j['tag'], cell(base(j) + 1), cell(base(j) + 2), ic, fc, own))
print()
print('| n | start | held side | start side | new side | gain against held | own gain |')
print('|---|---|---|---|---|---|---|')
tg = to = 0.0
for n, r in sorted(take.items()):
    sq = math.sqrt(n); j = [x for x in pl['jobs'] if x['n'] == n and abs(x['start'] - float(r['start'])) < 1e-15 and not x.get('again')][0]
    print('| %d | %s | %.9f | %.9f | %.9f | %s | %s |' % (n, group(j), (float(r['held']) + 1) * sq, (float(r['start']) + 1) * sq, (float(r['new']) + 1) * sq, r['gain'], r['polish_gain']))
    tg += float(r['held']) - float(r['new']); to += float(r['start']) - float(r['new'])
print('| **total** | | | | | **%.7f** | **%.7f** |' % (tg, to))
