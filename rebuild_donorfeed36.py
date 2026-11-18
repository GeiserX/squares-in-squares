"""donorfeed36.py: one pass of the round 36 rebuild donor feeder (override 8 second item, lesson 6c).
The pool: k123's 'certified near donor n=N, side=, score=S, ..., sha256=H, ..., <path>' lines of handoff-r36.log (the
latest line per sha). Room = (bar36 - board best) - (donor - bar36), board best from main-r17/gap-by-n.tsv board_L.
Skip: no room, donor 1e-4 or more of score above bar36, an n whose lowest live r36 take of another lane (or our own take
row) is more than 1e-6 below bar36 (rule 6i: a donor kick works against the live row of its n), two or more seed
claims already naming the sha (any lane, 16+ hex prefix), our own earlier seed of that sha. Order: room, largest first.
Before the first seed: the donor is walked (tools/qwalkcap.py at cap 100000; capped or any hit or gone file blocks it).
Queue: claim line (n, full sha, seed), wait 5 s, re-read; release if two other seed claims on the sha (or one on the n
of a held row) came first; else q36.py BOX d-<n>-<sha8>[-b] N PATH kick:900 on a box with an empty unclaimed queue.
State in work/donorfeed.json, one STATE line per action. DRY=1 prints the ranking only."""
import calendar, csv, hashlib, json, math, os, re, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r36/work/'
sys.path.insert(0, W + 'tools')
import rt36 as rt  # noqa: E402
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild', 2), 'boxC': ('boxC', 'scratch/squares-rebuild', 2)}
STOP = 1794957900   # 23:25Z: no new 900 s seed after this (box deadline 23:45Z)
LOG = os.environ.get('DF_LOG', S + 'handoff-r36.log')
DRY = os.environ.get('DRY') == '1'
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def state(s):
    if DRY: print('STATE', s); return
    with open(W + '../STATE.txt', 'a') as f: f.write(now() + ' boxA DONOR ' + s + '\n')
    print(now(), s, flush=True)
if time.time() > STOP and not DRY:
    sys.exit(0)
if not DRY and os.environ.get('DF_LOOP') != '1':
    sys.exit(0)   # 19:30Z: runs from its own loop (donorloop36.sh) so its walks never hold the collector
import fcntl
if not DRY:   # 19:38Z: two passes ran at once and queued one key on both boxes; one pass at a time
    _lk = open(W + 'donorfeed.lock', 'w')
    try: fcntl.flock(_lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: print(now(), 'another pass holds the lock'); sys.exit(0)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(W + 'bar36.tsv'), delimiter='\t')}
board = {int(r['n']): float(r['board_L']) / math.sqrt(int(r['n'])) - 1 for r in csv.DictReader(open(S + 'main-r17/gap-by-n.tsv'), delimiter='\t')}
FJ = W + 'donorfeed.json'
dj = json.load(open(FJ)) if os.path.isfile(FJ) else {}
live = rt.live(S + 'take-rebuild-r36')
if os.environ.get('DF_FAKE_LIVE'):   # control only: n:score
    _n, _s = os.environ['DF_FAKE_LIVE'].split(':'); live[int(_n)] = (float(_s), 'control')
own = {}
if os.path.isfile(W + '../take.tsv'):
    for r in csv.DictReader(open(W + '../take.tsv'), delimiter='\t'):
        own[int(r['n'])] = float(r['new'])
lines = open(LOG, errors='replace').read().splitlines()
DON = re.compile(r'certified near donor n=(\d+), side=([0-9.]+), score=([0-9.eE+-]+),.*?sha256=([0-9a-f]{64}).*?(/Volumes/\S+\.csv)')
pool = {}
for l in lines:
    m = DON.search(l)
    if m and os.path.isfile(m.group(5)):
        wf = re.search(r'walk_files=(\d+), capped=(True|False)', l)
        pool[m.group(4)] = dict(n=int(m.group(1)), side=float(m.group(2)), score=float(m.group(3)), sha=m.group(4), path=m.group(5), t=l[:20],
                                kwalk=(int(wf.group(1)), wf.group(2)) if wf else None)
# 21:05Z: the k123 pool is down to three 965 files; forensics' fresh rectangle near files (the lowest per n) join the pool
# once nearwalk36.py walked them clean (uncapped, cap 100000); their score is side/sqrt(n) - 1 of the side in the line
NJ = W + 'nearwalk.json'
for h, v in (json.load(open(NJ)) if os.path.isfile(NJ) else {}).items():
    if v.get('ok') and h not in pool and os.path.isfile(v['path']):
        pool[h] = dict(n=v['n'], side=v['side'], score=v['side'] / math.sqrt(v['n']) - 1, sha=h, path=v['path'], t='nearwalk ' + v['t'],
                       kwalk=(v.get('files') or 0, 'False'), kind='forensics near')
def claims(sha, n, before=None):
    """seed claims of other lanes naming the sha (16+ hex prefix); 'seeds [a, b]' or 'seeds a and b' count 2"""
    c = 0
    for l in lines if before is None else open(LOG, errors='replace').read().splitlines():
        m = re.match(r'^(\S+) (\S+) -> [^:]*: (.*)$', l)
        if not m or m.group(2) == 'rebuild' or not re.search(r'\bclaim', m.group(3), re.I) or re.search(r'\brelease', m.group(3), re.I):
            continue
        if before is not None and m.group(1)[:19] > before[:19]:
            continue
        hx = [h.lower() for h in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{16,64})(?![0-9a-fA-F])', m.group(3))]
        _p = pool.get(sha, {}).get('path')
        if not any(sha.startswith(h) for h in hx) and not (_p and os.path.basename(_p) in m.group(3)):
            continue
        if not re.search(r'\b900\b|900s|900 s', m.group(3)):
            continue
        k = 2 if re.search(r'seeds? \[\d+, \d+\]|seeds \d+ and \d+', m.group(3)) else 1
        c += k
    return c
def lowest(n):
    lv = live.get(n, (math.inf, ''))[0]
    return min(lv, own.get(n, math.inf), bar[n])
# same geometry under other bytes (same n, score equal to 1e-12): seed claims on any of them count for all
# 21:00Z: k123 posts many byte variants of one join a few 1e-10 of score apart (965: 8 files within 2e-10, 807: 5); a seed of
# one is a seed of all, so a geometry is a chain of donors of one n whose scores lie within 1e-9 of the next
geo = {}
for n0 in set(d['n'] for d in pool.values()):
    ds = sorted((d['score'], s) for s, d in pool.items() if d['n'] == n0)
    grp = []
    for i, (sc, s) in enumerate(ds):
        if i and sc - ds[i - 1][0] > 1e-9: grp = []
        grp.append(s)
        for s2 in grp: geo[(n0, s2)] = grp
_geo = geo
class _G(dict):
    def __getitem__(self, k): return _geo[(k[0], k[2])]
def gkey(n, sha): return (n, None, sha)
geo = _G()
rank = []
for sha, d in pool.items():
    n = d['n']
    room = (bar[n] - board.get(n, bar[n])) - (d['score'] - bar[n])
    gap = d['score'] - bar[n]
    why = None
    if room <= 0: why = 'no board room (%.3e)' % room
    elif gap >= 1e-4: why = 'donor %.3e above bar36 (1e-4 or more)' % gap
    elif lowest(n) < bar[n] - 1e-6: why = 'a live row %.3e below bar36 at n=%d (rule 6i: stop)' % (bar[n] - lowest(n), n)
    sib = geo[gkey(n, sha)]
    mine = [k for s2 in sib for k in dj.get(s2, {}).get('seeds', [])]
    oc = sum(claims(s2, n) for s2 in sib)
    if why is None and oc + len(mine) >= 2: why = 'two seeds claimed (%d other, %d ours)' % (oc, len(mine))
    if why is None and dj.get(sha, {}).get('closed'): why = dj[sha]['closed']
    rank.append((why is not None, -room, n, sha, gap, oc, len(mine), why))
rank.sort()
if DRY:
    for x in rank: print('%s n=%d room %.3e gap %.3e other %d ours %d %s %s' % ('SKIP' if x[0] else 'OK  ', x[2], -x[1], x[4], x[5], x[6], x[3][:12], x[7] or ''))
    sys.exit(0)
def walk(path):
    try:
        r = subprocess.run(['nice', '-n', '5', S + 'venv/bin/python', '-I', W + 'tools/qwalkcap.py', '100000', path], capture_output=True, text=True, timeout=1500)
        js = [json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
        return js[-1] if js else {'hits': ['walk printed nothing: ' + r.stderr[-200:]], 'gone': []}
    except subprocess.TimeoutExpired:
        return {'hits': ['walk timed out'], 'gone': []}
for b, (host, root, slots) in BOX.items():
    try:
        out = subprocess.run(['ssh', host, 'cd %s && cut -f1 queue.tsv | while read k; do [ -d "claims/$k" ] || echo "$k"; done | wc -l' % root],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        pend = int(out or 0)
    except Exception as e:
        print(now(), 'unreachable', b, e, flush=True); continue
    for x in rank:
        if pend >= 1: break
        if x[0]: continue
        _, mroom, n, sha, gap, oc, nm, _w = x
        d = pool[sha]; e = dj.setdefault(sha, {'n': n, 'path': d['path'], 'seeds': []})
        sibs = geo[gkey(n, sha)]
        nm = sum(len(dj.get(s2, {}).get('seeds', [])) for s2 in sibs)   # 19:41Z: live count (the rank tuple is from the pass start)
        if e.get('closed') or nm + oc >= 2: continue
        if any(time.time() - dj.get(s2, {}).get('tq', 0) < 1200 for s2 in sibs): continue   # our seed of these bytes queued under 20 min ago
        if any(k.startswith('d-%d-' % n) for s2, v in dj.items() for k in v.get('seeds', []) if s2 not in geo[gkey(n, sha)] and v.get('running', True) and time.time() - v.get('tq', 0) < 1200):
            if os.environ.get('DF_ONE_PER_N') == '1': continue   # 21:40Z: off by default (slots idled while other geometries of 965 waited)
        if 'walk' not in e and d.get('kwalk') and d['kwalk'][1] == 'False' and hashlib.sha256(open(d['path'], 'rb').read()).hexdigest() == sha:
            # 19:37Z: one quench_walk of a k123 donor takes over 12 minutes on boxA at load 30 while the boxes idle; k123's
            # certified line carries its own uncapped walk of these bytes (walk_files, capped=False), so that is the walk
            # before the kick, and our own uncapped walk runs on every find before it is published (autopub36 and the final walk)
            e['walk'] = {'ok': True, 'files': d['kwalk'][0], 'capped': False, 'by': 'k123 certified near donor line ' + d['t'], 't': now()}
            state('walk donor n=%d %s: record %s walked it clean (%d files, capped False); sha256 of the file equals the line' % (n, sha[:16], d['t'], d['kwalk'][0]))
        if 'walk' not in e:
            t0 = time.time(); j = walk(d['path'])
            bad = [h for h in j.get('hits', []) if not re.search(r'prvsiyan share|share within 1e-[23]', h)] + (j.get('gone') or [])
            if j.get('capped'): bad.append('walk capped at %s files' % j.get('files'))
            e['walk'] = {'ok': not bad, 'files': j.get('files'), 'capped': j.get('capped'), 'bad': bad[:5], 'secs': round(time.time() - t0), 't': now()}
            state('walk donor n=%d %s: %s (%s files, capped %s, %d s)%s' % (n, sha[:16], 'clean' if not bad else 'BLOCKED', j.get('files'), j.get('capped'),
                  time.time() - t0, '' if not bad else ': ' + '; '.join(str(z)[:120] for z in bad[:3])))
            if bad: e['closed'] = 'walk blocked'
            json.dump(dj, open(FJ, 'w'), indent=1)
            if bad: continue
        tag = 'a' if not nm else 'b'
        key = 'd-%d-%s' % (n, sha[:8]) + ('' if tag == 'a' else '-b')
        tclaim = now()
        with open(LOG, 'a') as h:
            h.write('%s rebuild -> all: claim: 900 s midm_scan lkick,kick (probe 0 s, seed %s of 2 on these bytes, job %s on %s) of n=%d, %s ranked by board room (brief 6c, override 8): room %.3e, donor %.3e above bar36, %d earlier seed claim(s), start bytes sha256 %s, walked %s files capped %s, %s\n' % (
                tclaim, tag, key, {'boxB': 'boxB', 'boxC': 'boxC'}[b], n, d.get('kind', 'k123 near donor'), -mroom, gap, oc, sha, e['walk']['files'], e['walk']['capped'], d['path']))
        time.sleep(5)
        oc2 = claims(sha, n, before=tclaim)
        if oc2 + nm >= 2:
            with open(LOG, 'a') as h:
                h.write('%s rebuild -> all: release: claim %s of n=%d withdrawn (earlier seed claims on sha256 %s fill its two seeds), nothing started\n' % (now(), key, n, sha[:16]))
            state('release %s: %d earlier seed claims' % (key, oc2)); e['closed'] = 'two seeds claimed by others'; json.dump(dj, open(FJ, 'w'), indent=1); continue
        r = subprocess.run([sys.executable, '-I', W + 'tools/q36.py', b, key, str(n), d['path'], 'kick:900'], capture_output=True, text=True, env=dict(os.environ, FRONT='0'))
        if r.returncode:
            state('queue failed %s: %s' % (key, r.stderr[-200:])); e['closed'] = 'queue failed'; json.dump(dj, open(FJ, 'w'), indent=1); continue
        e['seeds'].append(key); e['tq'] = time.time(); pend += 1
        notes = json.load(open(W + 'notes.json')) if os.path.isfile(W + 'notes.json') else {}
        notes[key] = {'donor_start': d['path'], 'donor_sha256': sha, 'walk': e['walk']}
        json.dump(notes, open(W + 'notes.json', 'w'), indent=1)
        state('queue %s on %s (seed %s, room %.3e, donor %.3e above bar36, start %s)' % (key, b, tag, -mroom, gap, d['path'].replace(S, '')))
        json.dump(dj, open(FJ, 'w'), indent=1)
json.dump(dj, open(FJ, 'w'), indent=1)
