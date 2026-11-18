#!/usr/bin/env python3
"""Counts of the round from the fetched logs: per kind of start, the n searched, islands, children, finds; per find n, the island and the quench."""
import collections, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ctl import W, REMOTE
pl = json.load(open(W + '/plan.json'))
tot = collections.OrderedDict(); rows = []; moves = collections.Counter(); ladder = 0
box = collections.defaultdict(lambda: [0, 0, 0])
for j in pl['jobs']:
    ds = {b: '%s/%s/run/%d-%s' % (W, b, j['n'], j['tag']) for b in list(REMOTE) + ['boxA']}   # a chain may have legs on two boxes
    legs = {}
    for b, p in sorted((b, p) for b, d in ds.items() for p in glob.glob(d + '/soft-*.log')):
        seed = int(p[:-4].split('-')[-1]); txt = open(p).read()
        m = re.search(r'^end n=\d+ kids (\d+) finds (\d+) restarts (\d+) L ([\d.]+) -> ([\d.]+) gain ([\d.e+-]+) .* seconds (\d+)', txt, re.M)
        fl = re.findall(r'^FIND t (\d+) kids \d+ move (\S+) .*?gain of score ([\d.e+-]+)\)( ladder)?', txt, re.M)
        if m:
            k, f, s, g = int(m.group(1)), int(m.group(2)), int(m.group(7)), float(m.group(6))
        else:
            ks = re.findall(r'^(?:t|FIND t) (\d+) kids (\d+)', txt, re.M)
            k = max([int(x[1]) for x in ks] or [0]); s = max([int(x[0]) for x in ks] or [0]); f = len(fl); g = float(fl[-1][2]) if fl else 0.0
        for t, mv, gg, lad in fl:
            moves[mv] += 1; ladder += bool(lad)
        legs[seed] = dict(kids=k, finds=f, secs=s, gain=g, last=int(fl[-1][0]) if fl else None, ended=bool(m))
        box[b][0] += 1; box[b][1] += k; box[b][2] += s
    ch = ''.join(open(d + '/chain.log').read() for d in ds.values() if os.path.exists(d + '/chain.log'))
    fq = re.findall(r'^FQEND .* L ([\d.]+) -> ([\d.]+) gain of score ([\d.e+-]+) steps (\d+)', ch, re.M)
    done = all(sd in legs and legs[sd]['ended'] for sd in ((14,) if j.get('mode') == 'again' else (21, 22) if j.get('mode') == 'seed2' else (11, 12)))
    rows.append((j, legs, fq, done))
    t = tot.setdefault(j['kind'] + ('-seed2' if j.get('mode') == 'seed2' else ''), dict(n=0, passed=0, islands=0, kids=0, found=0, finds=0, secs=0, started=0))
    t['n'] += 1; t['started'] += bool(legs); t['passed'] += done; t['islands'] += len(legs); t['kids'] += sum(l['kids'] for l in legs.values())
    t['secs'] += sum(l['secs'] for l in legs.values()); t['finds'] += sum(l['finds'] for l in legs.values()); t['found'] += any(l['finds'] for l in legs.values())
print('kind      jobs started passed islands children   n-with-find finds cpu-s')
for k, t in tot.items():
    print('%-9s %4d %7d %6d %7d %9d %11d %5d %6d' % (k, t['n'], t['started'], t['passed'], t['islands'], t['kids'], t['found'], t['finds'], t['secs']))
print('all       %4d %7d %6d %7d %9d %11d %5d %6d  cpu-h %.1f' % tuple([sum(t[x] for t in tot.values()) for x in ('n', 'started', 'passed', 'islands', 'kids', 'found', 'finds', 'secs')] + [sum(t['secs'] for t in tot.values()) / 3600]))
print('by box (islands, children, seconds):', dict(box))
print('finds by move:', dict(moves), 'through the ladder:', ladder)
print()
for j, legs, fq, done in rows:
    if any(l['finds'] for l in legs.values()) or fq:
        print('n=%d %s %s %s start %.12f' % (j['n'], j['tag'], j['kind'], j['box'], j['start']))
        for s in sorted(legs):
            l = legs[s]
            print('   seed %d kids %d finds %d last find at %s s, ran %d s, gain %.3e%s' % (s, l['kids'], l['finds'], l['last'], l['secs'], l['gain'], '' if l['ended'] else ' (not ended)'))
        for a, b, g, st in fq:
            print('   fq %s -> %s gain %s steps %s' % (a, b, g, st))
if '-v' in sys.argv:
    for j, legs, fq, done in rows:
        print(j['n'], j['tag'], j['kind'], j['box'], 'passed' if done else ('started' if legs else 'not started'), {s: (l['kids'], l['finds']) for s, l in legs.items()})
