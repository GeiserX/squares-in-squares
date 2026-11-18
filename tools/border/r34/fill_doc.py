"""Fill the numbers of doc-r28.md from the work dir (same counts as stats.py) -> doc-r28.final.md."""
import json, glob, os, re, math, csv
csv.field_size_limit(10**9)
W = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(W)
st = open(os.path.join(T, 'STATE.txt'), errors='replace').read().splitlines()
idx = json.load(open(os.path.join(W, 'lp/index.json')))
take_in = sum(1 for v in idx.values() if os.path.basename(v['path']).split('.')[0].isdigit())
ran = sum(1 for k, v in idx.items() if os.path.exists(os.path.join(W, 'lp/nout', f"{k}_{v['n']}", 'DONE')))
cert = list({re.search(r' LP (\d+ \w+):', l)[1]: l for l in st if re.search(r' LP \d+ \w+: certified score', l)}.values())
below = sum(1 for l in cert if float(re.search(r', ([-0-9.e+]+) vs the live bar', l)[1]) < 0)
refused = len(set(re.search(r' LP (\d+ \w+):', l)[1] for l in st if 'below the bar but the walk refuses' in l))
fin = []
for p in glob.glob(os.path.join(W, 'final/*.job.done')):
    uid = os.path.basename(p)[:-9]; d = json.load(open(p)); j = json.load(open(os.path.join(W, 'final', uid + '.job.json')))
    if re.search(r'-k\d$|-self-|-ns[0-9a-f]{6}$|-fs$', uid) or d['side'] is None: continue
    take = os.path.basename(j['manifest'].get('donor_source', '').split(', ', 1)[0]).split('.')[0].isdigit()
    fin.append(('polish' if uid.endswith('-p') else 'default', take, d['side'] - (j['certified_before'] + 1) * math.sqrt(j['n'])))
def cnt(kind, take):
    v = [x[2] for x in fin if x[0] == kind and x[1] == take]; return sum(x < 0 for x in v), len(v)
ws = [l.rstrip('\n').split('\t') for l in open(os.path.join(W, 'wscan.tsv'))]
rows = list(csv.DictReader(open(os.path.join(T, 'take.tsv')), delimiter='\t'))
gain = sum(float(r['gain']) for r in rows)
sub = {'@LPIN@': len(idx), '@LPTAKE@': take_in, '@LPNEAR@': len(idx) - take_in, '@LPRAN@': ran, '@LPBELOW@': below, '@LPREF@': refused,
       '@PTL@': cnt('polish', True)[0], '@PTN@': cnt('polish', True)[1], '@PNL@': cnt('polish', False)[0], '@PNN@': cnt('polish', False)[1],
       '@DTL@': cnt('default', True)[0], '@DTN@': cnt('default', True)[1], '@WS@': f'{len(ws):,}', '@WL@': f'{len(set(r[6] for r in ws if len(r) > 6)):,}'}
res = os.environ.get('RESULT') or (f"{len(rows)} rows, {', '.join(r['n'] for r in rows)}, {gain:.4g} of score below bar28." if rows else 'no row.')
s = open(os.path.join(W, 'doc-r28.md')).read().replace('@RESULT@', res)
for k, v in sub.items(): s = s.replace(k, str(v))
open(os.path.join(W, 'doc-r28.final.md'), 'w').write(s)
print(json.dumps({k: v for k, v in sub.items()}), res, 'left:', re.findall(r'@[A-Z]+@', s))
