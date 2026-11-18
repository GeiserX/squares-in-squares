"""Round 29 numbers (round 28 copy; no window scanner this round, so its block runs only when wscan.tsv exists) for the doc and the report (light python, boxA)."""
import json, glob, os, re, math, csv, collections
csv.field_size_limit(10**9)
W = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(W)
st = open(os.path.join(T, 'STATE.txt'), errors='replace').read().splitlines()
idx = json.load(open(os.path.join(W, 'lp/index.json')))
lp_take = sum(1 for v in idx.values() if os.path.basename(v['path']).split('.')[0].isdigit())
lp_ran = sum(1 for k, v in idx.items() if os.path.exists(os.path.join(W, 'lp/nout', f"{k}_{v['n']}", 'DONE')))
nogain = len(set(re.search(r' LP (\d+ \w+):', l)[1] for l in st if re.search(r' LP \d+ \w+: no LP gain', l)))
cert = list({re.search(r' LP (\d+ \w+):', l)[1]: l for l in st if re.search(r' LP \d+ \w+: certified score', l)}.values())
below = [float(re.search(r', ([-0-9.e+]+) vs the live bar', l)[1]) for l in cert]
refused = len(set(re.search(r' LP (\d+ \w+):', l)[1] for l in st if 'below the bar but the walk refuses' in l))
print('lp inputs', len(idx), 'take inputs', lp_take, 'near inputs', len(idx) - lp_take, 'ran', lp_ran)
print('lp no gain', nogain, 'lp certified', len(cert), 'certified below live bar', sum(b < 0 for b in below),
      'best', min(below) if below else None, 'walk refused', refused)
fin = []
for p in glob.glob(os.path.join(W, 'final/*.job.done')):
    uid = os.path.basename(p)[:-9]; d = json.load(open(p)); j = json.load(open(os.path.join(W, 'final', uid + '.job.json')))
    src = j['manifest'].get('donor_source', '').split(', ', 1)[0]
    take = os.path.basename(src).split('.')[0].isdigit()
    kind = 'kick' if re.search(r'-k\d$', uid) else ('polish' if uid.endswith('-p') else 'default')
    sb = (j['certified_before'] + 1) * math.sqrt(j['n'])
    fin.append((kind, take, None if d['side'] is None else d['side'] - sb, d.get('seconds', 0)))
for kind in ('polish', 'default', 'kick'):
    for take in (True, False):
        v = [x[2] for x in fin if x[0] == kind and x[1] == take and x[2] is not None]
        if v:
            v.sort(); print('fq', kind, 'take' if take else 'near', len(v), 'raw lower', sum(x < 0 for x in v),
                            'min %.3e' % v[0], 'median %.3e' % v[len(v) // 2])
print('certified rows', [l[21:120] for l in st if re.search(r'Z certified \d+:', l)])
print('overtaken', [l[21:80] for l in st if 'overtaken or ineligible' in l])
if os.path.exists(os.path.join(W, 'wscan.tsv')):
    ws = [l.rstrip('\n').split('\t') for l in open(os.path.join(W, 'wscan.tsv'))]
    paths = set(r[6] for r in ws if len(r) > 6)
    rule = [r for r in ws if len(r) > 6 and r[5] and float(r[5]) < -math.sqrt(int(r[1])) * 1e-10]
    print('wscan scans', len(ws), 'layouts', len(paths), 'below rule', len(rule))
ki = json.load(open(os.path.join(W, 'kq/index.json')))
print('kq jobs', len([k for k, v in ki.items() if not v.get('skipped')]), 'boundary', len([1 for v in ki.values() if v.get('boundary')]))
take = list(csv.DictReader(open(os.path.join(T, 'take.tsv')), delimiter='\t'))
print('take rows', len(take), [(r['n'], r['gain']) for r in take])
