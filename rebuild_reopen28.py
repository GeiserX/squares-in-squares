"""reopen28.py BOX KEY N PATH: re-open one near file. Pin it (byte copy, sha256, work/pins), certify it by floatsafe against
bar28 (rebuild_take.cert, work/cert/<KEY>.csv), add it to the collect28 finals (not final) and queue one quench of the
certified file first on BOX (job q-<KEY>). collect28 makes it final when the quench is no lower."""
import csv, hashlib, json, math, os, shutil, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r28/work/'
sys.path.insert(0, '.')
import rebuild_take as rt  # noqa: E402
csv.field_size_limit(1 << 28)
box, key, n, p = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'round28-briefs/bar28.tsv'), delimiter='\t')}
b = open(p, 'rb').read(); sha = hashlib.sha256(b).hexdigest()
pin = W + 'pins/%d-%s.csv' % (n, sha[:16])
if not os.path.isfile(pin):
    open(pin, 'wb').write(b)
for ext in ('.json', '.origin.json'):
    if os.path.isfile(p + ext) and not os.path.isfile(pin + ext):
        shutil.copy2(p + ext, pin + ext)
cp = W + 'cert/%s.csv' % key
s = rt.cert(n, pin, cp, bar[n])
if s is None:
    sys.exit(1)
# collect28 merges work/reopen.jsonl into its state at the start of each pass (append only: no race with a running pass)
reg = {'key': key, 'seen': {'box': box, 'rec': {'key': key, 'n': n, 'start': p, 'start_side': None, 'side': None, 'reopen': True}},
       'final': {'n': n, 'cert': cp, 'score': s, 'side': (s + 1) * math.sqrt(n), 'final': False, 'box': box,
                 'chain': [{'key': key, 'raw_side': None, 'cert': cp.replace(S, ''), 'score': s}], 'start': p, 'reopen': True}}
with open(W + 'reopen.jsonl', 'a') as h:
    h.write(json.dumps(reg) + '\n')
with open(W + 'queue-log.tsv', 'a') as h:
    h.write('\t'.join([time.strftime('%H:%M:%SZ', time.gmtime()), box, key, str(n), p.replace(S, ''), sha, pin.replace(S, ''), 'reopen']) + '\n')
r = subprocess.run([sys.executable, '-I', W + 'tools/q28.py', box, 'q-' + key, str(n), cp, 'quench'], capture_output=True, text=True,
                   env=dict(os.environ, FRONT='1'))
print('reopen', key, n, repr(s), 'gain %.3e' % (bar[n] - s), r.stdout.strip(), r.stderr.strip()[-300:])
