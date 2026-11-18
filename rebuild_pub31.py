"""pub2.py ROWS.json: publish the rebuild r28 take without certifying a file twice.

ROWS.json: {n: {cert, source, licence}}, merged into work/published.json (the rows of the take). A cert file is
certified once by floatsafe (rebuild_take.cert) and its score kept in work/certcache.json under the file's sha256.
Every row stays only while it is below bar28 by more than 1e-10 and below the same n in every other live
take-*-r31/take.tsv by more than 1e-10. Writes <n>.csv first, then take.tsv by rename."""
import csv, glob, hashlib, json, math, os, shutil, sys
S = '$SCRATCH/bounties-squares/'
T = S + 'take-rebuild-r31/'
sys.path.insert(0, '.')
os.environ['SQ_ROUND'] = '31'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rt31 as rt  # noqa: E402
csv.field_size_limit(1 << 28)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
CC = T + 'work/certcache.json'
cache = json.load(open(CC)) if os.path.isfile(CC) else {}
PUB = T + 'work/published.json'
pub = json.load(open(PUB)) if os.path.isfile(PUB) else {}
new = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
for k, v in new.items():
    for c in ('source', 'licence'):
        v[c] = ' '.join(v[c].split())
    pub[str(int(k))] = v
other = rt.live(T)
keep = {}
for k, v in sorted(pub.items(), key=lambda kv: int(kv[0])):
    n = int(k)
    sha = hashlib.sha256(open(v['cert'], 'rb').read()).hexdigest()
    if sha not in cache:
        tmp = T + 'work/.c%d.csv' % n
        s = rt.cert(n, v['cert'], tmp, bar[n] + 1.0)  # floatsafe on the file; the bar test is below
        cache[sha] = s
        json.dump(cache, open(CC, 'w'))
        if s is not None:
            if hashlib.sha256(open(tmp, 'rb').read()).hexdigest() != sha:
                shutil.move(tmp, v['cert'] + '.fs.csv'); v['cert'] = v['cert'] + '.fs.csv'
                sha2 = hashlib.sha256(open(v['cert'], 'rb').read()).hexdigest(); cache[sha2] = s
                json.dump(cache, open(CC, 'w'))
            else:
                os.remove(tmp)
    s = cache.get(sha) if sha in cache else cache.get(hashlib.sha256(open(v['cert'], 'rb').read()).hexdigest())
    if s is None or not s < bar[n] - 1e-10:
        print('drop', n, s, bar[n]); continue
    o = other.get(n, (math.inf, ''))
    if not s < o[0] - 1e-10:
        print('beaten', n, s, o); continue
    keep[n] = (s, v, o[0])
for n, (s, v, o) in keep.items():
    shutil.copyfile(v['cert'], T + '.%d.csv.tmp' % n); os.replace(T + '.%d.csv.tmp' % n, T + '%d.csv' % n)
for f in glob.glob(T + '[0-9]*.csv'):
    if int(os.path.basename(f)[:-4]) not in keep:
        os.remove(f)
with open(T + '.take.tsv.tmp', 'w') as h:
    h.write('n\theld\tnew\tgain\tsource\tlicence\n')
    for n in sorted(keep):
        s, v, o = keep[n]
        h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, bar[n], s, bar[n] - s, v['source'], v['licence']))
os.replace(T + '.take.tsv.tmp', T + 'take.tsv')
json.dump(pub, open(PUB, 'w'), indent=1)
g1 = sum(bar[n] - keep[n][0] for n in keep); g2 = sum(min(bar[n], keep[n][2]) - keep[n][0] for n in keep)
print('kept', sorted(keep), 'gain %.6e beyond live %.6e' % (g1, g2))
