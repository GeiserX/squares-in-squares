"""chain740.py v2: one pass of the 740 drop1 pipeline (round 33). v1 measured: our drop1 of the held 741 came to 2.7e-5 of side
above the bar side of 740 (best of 6 seeds), its first 600 s invent_rest lkick moved 1.46e-5 more, then 6 more lkick seeds of the
new best moved nothing (only the first lkick of a geometry pays, lesson 6b). v2: a pool of fresh near misses. A free slot runs the
first 600 s lkick of the lowest pool file within 5e-5 of the bar side that has had none; with none left, a new 900 s drop1 seed
(scan mode, the scaled held 740 as the marker, so the best try is saved). Every lower lkick result joins the pool. State:
work/chain740.json. Stops queueing at 23:50Z."""
import json, os, subprocess, sys, time, hashlib
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r33/work/'
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild', 2), 'boxE': ('boxE', 'scratch/squares-rebuild', 1)}
BAR = 27.705882354282
SF = W + 'chain740.json'
st = json.load(open(SF))
st.setdefault('pool', {st['best_path']: {'side': st['best_side'], 'lk': 6}})
st.setdefault('jobs', {})
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def log(s):
    print(now(), s, flush=True)
busy = {}
for b, (host, root, slots) in BOX.items():
    r = subprocess.run(['ssh', host, 'cd %s && for k in $(cut -f1 queue.tsv | grep "^c740-"); do [ -f out/$k/done.json ] || echo "P $k"; done; '
                        'grep -h "\\"c740-" done.jsonl || true' % root], capture_output=True, text=True, timeout=60)
    busy[b] = 0
    for l in r.stdout.splitlines():
        if l.startswith('P '):
            busy[b] += 1; continue
        try:
            d = json.loads(l)
        except Exception:
            continue
        if d['key'] in st['seen']:
            continue
        st['seen'].append(d['key'])
        sd = d.get('side')
        log('done %s %s side %s (best %.12f)' % (b, d['key'], sd, st['best_side']))
        start_side = st['jobs'].get(d['key'], {}).get('start_side', 99)
        if sd is not None and sd < min(start_side, BAR + 5e-5) - 1e-9:
            p = S + 'take-rebuild-r33/near/740-c-%s.csv' % d['key']
            subprocess.run(['scp', '-q', '%s:%s/out/%s/best.csv' % (host, root, d['key']), p], check=True)
            st['pool'][p] = {'side': sd, 'lk': 0, 'from': d['key']}
            log('pool add %.12f from %s' % (sd, d['key']))
            if sd < st['best_side']:
                st['best_side'] = sd; st['best_path'] = p; st['gen'] += 1
                log('new best %.12f from %s' % (sd, d['key']))
json.dump(st, open(SF, 'w'), indent=1)
if time.time() > 1794873000:
    sys.exit(0)
base = json.load(open(W + 'notes.json'))['d1-740-574e09ff-l']
for b, (host, root, slots) in BOX.items():
    while busy[b] < slots:
        st['k'] += 1
        c = sorted((v['side'], p) for p, v in st['pool'].items() if v['lk'] == 0 and v['side'] < BAR + 5e-5)
        notes = json.load(open(W + 'notes.json'))
        if c:
            side, p = c[0]; st['pool'][p]['lk'] = 1
            key = 'c740-l%d' % st['k']; mode = 'lk:600'; src = p
            sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            notes[key] = dict(base)
            notes[key]['reviewed'] = base['reviewed'] + '; pipeline step: the first 600 s invent_rest lkick of our near miss %s (sha256 %s)' % (p.replace(S, ''), sha[:16])
            notes[key]['source'] = 'our invent_rest lkick of our drop1 near miss %s, from ' % p.replace(S, '') + base['source']
            what = '600 s invent_rest lkick of n=740 (job %s on %s), our drop1 near miss sha256 %s, %s' % (key, host, sha[:16], p)
        else:
            key = 'c740-d%d' % st['k']; mode = 'scan:900:drop1:donors/741-eefe03a085e4ea34.csv'; src = W + 'inc/740-held-x1.00005.csv'; side = 99
            notes[key] = dict(json.load(open(W + 'notes.json'))['s-drop1-740-eefe03a0-f'])
            what = '900 s midm_scan drop1 of n=740 from the held 741 (donor sha256 eefe03a085e4ea34; job %s on %s), %s' % (key, host, W + 'held33/741.csv')
        json.dump(notes, open(W + 'notes.json', 'w'), indent=1)
        r = subprocess.run([sys.executable, '-I', W + 'tools/q33.py', b, key, '740', src, mode], capture_output=True, text=True, env=dict(os.environ, FRONT='1'))
        log('queue %s %s %s rc %d %s' % (b, key, mode, r.returncode, (r.stdout + r.stderr).strip()[-100:]))
        if r.returncode:
            break
        st['jobs'][key] = {'start_side': side, 'mode': mode}
        busy[b] += 1
        with open(S + 'handoff-r33.log', 'a') as h:
            h.write('%s rebuild -> all: claim: %s\n' % (now(), what))
json.dump(st, open(SF, 'w'), indent=1)
