"""Fill the round 26 doc draft from the final take, final26.py and the results table. Usage: fill26.py <results.tsv> <out.md>"""
from pathlib import Path
import csv, json, re, subprocess, sys
csv.field_size_limit(16000000)
W = Path(__file__).parent; T = W.parent; B = T.parent
fin = json.loads(subprocess.run([sys.executable, str(W / 'final26.py')], capture_output=True, text=True, check=True).stdout)
take = {int(r['n']): r for r in csv.DictReader(open(T / 'take.tsv'), delimiter='\t')}
res = [r for r in csv.DictReader(open(sys.argv[1]), delimiter='\t') if r['kind'] == 'kick']


def lane(tag):
    return re.match(r'(.+?)-\d+-', tag)[1]


def input_of(src):
    m = re.search(r'take-([a-z0-9-]+)-r26/', src)
    return m[1] if m else 'see take.tsv'


rows = '\n'.join('| %d | %.4g | %.4g | %s |' % (o['n'], o['gain'], o['beyond'], input_of(take[o['n']]['source'])) for o in fin['rows'])
by = {}
for r in res:
    d = by.setdefault(lane(r['run']), [0, 0, 0, 0.0])
    g = float(r['side_gain'])
    d[0] += 1; d[1] += int(r['tries']); d[2] += g > 0; d[3] = max(d[3], g)
lanes = '\n'.join('| %s | %d | %d | %d | %.2g |' % (k, *v) for k, v in sorted(by.items(), key=lambda kv: -kv[1][3]))
text = (W / 'doc-r26-draft.md').read_text()
text = (text.replace('TAKE_COUNT', str(len(fin['rows']))).replace('TAKE_LIST', ', '.join(str(o['n']) for o in fin['rows']))
        .replace('TAKE_GAIN', '%.6g' % fin['gain']).replace('BEYOND_GAIN', '%.4g' % fin['beyond'])
        .replace('KICK_RUNS', str(len(res))).replace('KICK_TRIES', str(sum(int(r['tries']) for r in res)))
        .replace('TAKE_TABLE', rows).replace('LANE_TABLE', lanes).replace('NEXT_LIST', (W / 'next26.md').read_text().strip()))
Path(sys.argv[2]).write_text(text)
print(json.dumps(dict(gain=fin['gain'], beyond=fin['beyond'], n=fin['improved_n'], runs=len(res), lanes=by)))
