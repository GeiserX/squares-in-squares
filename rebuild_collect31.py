"""collect28.py: one pass of the rebuild r28 collector (run it in a loop).
Reads done.jsonl of both boxes. A job whose best side is below its bar side by more than 2e-9 is fetched to
work/box/<key>.csv, certified by floatsafe (rebuild_take.cert) against bar28 into work/cert/<key>.csv, and a
'quench' job of the certified file is queued on the same box (key q-<key>). When that quench is done, its q.csv
is fetched; if it is lower than the cert by more than 3e-9 it is certified as the next cert (work/cert/<key>q.csv) and
quenched again, else the cert is final. Finals go to work/finals.json {key: {n, cert, score, start_key}}.
Prints one line per event. State in work/collect-state.json."""
import csv, hashlib, json, math, os, re, subprocess, sys, time
# quench jobs first, then kicks of our own rows (k2- and up), then follow kicks of fresh rows (f-), then insert, rectangle or held kicks (i-, x-, h-), then the rest
REORDER = "{ awk -F'\\t' '$5==\"quench\"' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^k[2-9]-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^s-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^f-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^[ixh]-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 !~ /^k[2-9]-/ && $1 !~ /^s-/ && $1 !~ /^f-/ && $1 !~ /^[ixh]-/' queue.tsv; } > queue.ord && mv queue.ord queue.tsv"
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
sys.path.insert(0, '.')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rt31 as rt  # noqa: E402
csv.field_size_limit(1 << 28)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild'), 'boxE': ('boxE', 'scratch/squares-rebuild'), 'boxD': ('boxD', 'scratch/squares-rebuild')}
STF = W + 'collect-state.json'
st = json.load(open(STF)) if os.path.isfile(STF) else {'seen': {}, 'finals': {}}
if os.path.isfile(W + 'reopen.jsonl'):
    for l in open(W + 'reopen.jsonl'):
        try:
            g = json.loads(l)
        except Exception:
            continue
        if g['key'] not in st['finals']:
            st['finals'][g['key']] = g['final']; st['seen'][g['key']] = g['seen']
own = {}  # my published rows: a kick result must beat them, not only the bar
if os.path.isfile(W + '../take.tsv'):
    for r in csv.DictReader(open(W + '../take.tsv'), delimiter='\t'):
        own[int(r['n'])] = (float(r['new']) + 1) * math.sqrt(int(r['n']))
os.makedirs(W + 'box', exist_ok=True); os.makedirs(W + 'cert', exist_ok=True)
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def log(s):
    print(now(), s, flush=True)


def queue(b, key, n, rel_local, mode):
    host, root = BOX[b]
    sha = hashlib.sha256(open(rel_local, 'rb').read()).hexdigest()
    rel = 'starts/%s-%s.csv' % (key, sha[:12])
    subprocess.run(['scp', '-q', rel_local, '%s:%s/%s' % (host, root, rel)], check=True)
    line = '\t'.join([key, str(n), '%.12f' % ((1 + bar[n]) * math.sqrt(n)), rel, mode])
    # quench jobs go first in the queue so they run next
    subprocess.run(['ssh', host, ('cd %s && { cat; cat queue.tsv; } > queue.new && mv queue.new queue.tsv && ' % root) + REORDER], input=(line + '\n').encode(), check=True)
    with open(W + 'queue-log.tsv', 'a') as h:
        h.write('\t'.join([time.strftime('%H:%M:%SZ', time.gmtime()), b, key, str(n), rel_local.replace(S, ''), sha, rel, mode]) + '\n')


for b, (host, root) in BOX.items():
    try:
        txt = subprocess.run(['ssh', host, 'cat %s/done.jsonl' % root], capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        log('unreachable %s %s' % (host, e)); continue
    for line in txt.splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        key = r['key']
        if key in st['seen']:
            continue
        st['seen'][key] = {'box': b, 'rec': r}
        n = r['n']; side = r.get('side'); room = r.get('room')
        log('done %s %s n=%d side=%s room=%s' % (b, key, n, side, room))
        isq = re.match(r'^q+-', key) is not None
        base = re.sub(r'^q+-', '', key)
        prev = st['finals'].get(base, {})
        if isq and prev.get('score') is not None and (side is None or side >= prev['side'] - 3e-9):
            prev['final'] = True; prev['quench'] = {'key': key, 'side': side, 'quench_ok': r.get('quench_ok')}
            log('final %s n=%d score %r (quench %s side %s, no lower)' % (base, n, prev['score'], key, side)); continue
        if side is None or room is None or room <= 2e-9:
            continue
        if not isq and n in own and side >= own[n] - 2e-9:
            log('no gain %s n=%d side %r not below my published side %r' % (key, n, side, own[n])); continue
        src = 'q.csv' if isq else 'best.csv'
        loc = W + 'box/%s.csv' % key
        subprocess.run(['scp', '-q', '%s:%s/out/%s/%s' % (host, root, key, src), loc], check=True)
        cp = W + 'cert/%s.csv' % key
        s = rt.cert(n, loc, cp, bar[n])
        if s is None:
            log('cert drop %s n=%d' % (key, n)); continue
        cs = (s + 1) * math.sqrt(n)
        hist = prev.get('chain', []) + [{'key': key, 'raw_side': side, 'cert': cp.replace(S, ''), 'score': s}]
        st['finals'][base] = {'n': n, 'cert': cp, 'score': s, 'side': cs, 'final': False, 'box': b, 'chain': hist,
                              'start': st['seen'].get(base, {}).get('rec', {}).get('start')}
        os.environ['SQ_ROUND'] = '31'
        lv = rt.live(S + 'take-rebuild-r31').get(n, (math.inf, ''))
        if not s < lv[0] - 1e-10:
            st['finals'][base]['final'] = True; st['finals'][base]['beaten'] = lv
            log('cert ok %s n=%d score %r but a live take holds %r (%s): no quench' % (key, n, s, lv[0], lv[1])); continue
        log('cert ok %s n=%d score %r gain %.3e, queue quench' % (key, n, s, bar[n] - s))
        queue(b, ('q' + key) if isq else ('q-' + key), n, cp, 'quench')
json.dump(st, open(STF, 'w'), indent=1)

# round 29: publish the finals that pass the walk (autopub29.py)
subprocess.run([sys.executable, "-I", W + "tools/autopub31.py"])
