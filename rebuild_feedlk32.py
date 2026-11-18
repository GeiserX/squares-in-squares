"""feedlk32.py (round 32, from feedheld32.py): 150 s invent_rest lkicks of work/lkorder.txt through lq32.py. feedheld32.py: keep every box slot fed with first kicks (900 s, probe 120 s, 180 s for n 700 and up) of held round 30 c
rows, in the order of work/heldorder.txt (one n per line, then a tab and the reason), through hq32.py (claim check, note,
claim line). A box gets a new job when its unclaimed queue holds fewer lines than it has slots. Stops queueing at
23:50Z. Records each n it tried in work/feedheld.json."""
import json, os, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r32/work/'
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild', 2), 'boxE': ('boxE', 'scratch/squares-rebuild', 1)}
if time.time() > 1794847800:   # 23:50Z
    sys.exit(0)
FJ = W + 'feedlk.json'
done = json.load(open(FJ)) if os.path.isfile(FJ) else {}
order = []
# round 31: rooms first (work/rooms.txt: n <tab> why), held rows of n where a lower layout is known but out for its
# source; they run 900 s with no probe (the 910 room kick paid 1.47e-5 with its first find at try 27, about 4 min)
ROOMS = set()
if False:
    for l in open(W + 'rooms.txt'):
        f = l.rstrip('\n').split('\t')
        if f and f[0].strip().isdigit():
            order.append((int(f[0]), f[1] if len(f) > 1 else '')); ROOMS.add(int(f[0]))
for l in open(W + 'lkorder.txt'):
    f = l.rstrip('\n').split('\t')
    if f and f[0].strip().isdigit():
        order.append((int(f[0]), f[1] if len(f) > 1 else ''))
# round 32 pass 2: work/lkorder2.txt, a second seed (key suffix -s2, 300 s) of list 1 rows whose first lkick was dry; it runs
# only after every pass 1 row is done (list 1 moved 4 of 61 first lkicks, list 2 0 of 19)
ORDER2 = []
if os.path.isfile(W + 'lkorder2.txt'):
    for l in open(W + 'lkorder2.txt'):
        f = l.rstrip('\n').split('\t')
        if f and f[0].strip().isdigit():
            ORDER2.append((int(f[0]), f[1] if len(f) > 1 else ''))
# n already queued by us in r31 (any key naming the n as h-<n>-)
ql = set(); ql2 = set()
if os.path.isfile(W + 'queue-log.tsv'):
    for l in open(W + 'queue-log.tsv'):
        f = l.split('\t')
        if len(f) > 3 and f[2].startswith('l-'):
            (ql2 if f[2].endswith('-s2') else ql).add(int(f[3]))
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
# n where another lane already certified a row below the bar in round 31 (a take row, or a 'certified n=' handoff line):
# a first kick of the held row there has to beat that row, so it waits (harvest's public 852 sits 1.7e-4 below the bar)
import csv, glob, re
SKIPN = set()
for t in glob.glob(S + 'take-*-r32/take.tsv'):
    if '/take-rebuild-r32/' in t:
        continue
    try:
        SKIPN.update(int(r['n']) for r in csv.DictReader(open(t), delimiter='\t'))
    except Exception:
        pass
for l in open(S + 'handoff-r32.log', errors='replace'):
    m = re.match(r'^\S+ (\S+) -> [^:]*: (.*)$', l)
    if m and m.group(1) != 'rebuild' and not re.search(r'WITHDRAW|refuse', m.group(2)):
        SKIPN.update(int(x) for x in re.findall(r'\bcertified n=(\d+)', m.group(2)))
for b, (host, root, slots) in BOX.items():
    try:
        out = subprocess.run(['ssh', host, 'cd %s && cut -f1 queue.tsv | while read k; do [ -d "claims/$k" ] || echo "$k"; done | wc -l' % root],
                             capture_output=True, text=True, timeout=60).stdout.strip()
        pend = int(out or 0)
    except Exception as e:
        print(now(), 'unreachable', b, e, flush=True); continue
    while pend < 3 * slots:   # round 31: probes end most kicks at 2 to 3 min, so keep a buffer of two jobs per slot between 5 min feeds
        nxt = None
        for n, why in order:
            if str(n) in done or n in ql or n in SKIPN:
                continue
            nxt = (n, why, ''); break
        if nxt is None:
            for n, why in ORDER2:
                if 's2-%d' % n in done or n in ql2 or n in SKIPN:
                    continue
                nxt = (n, why, 's2'); break
        if nxt is None:
            break
        n, why, tag = nxt
        r = subprocess.run([sys.executable, '-I', W + 'tools/lq32.py', b, str(n), '300' if tag else '150', '--why', why],
                           capture_output=True, text=True, env=dict(os.environ, BYTES="1" if n in ROOMS else "0", SEEDTAG=tag))
        if r.returncode == 2 and n in ROOMS:   # a room claimed by another lane: try again on a later pass (claims last 60 min)
            print(now(), 'room claimed, later', b, n, flush=True); order = [x for x in order if x[0] != n]; continue
        done[('s2-%d' % n) if tag else str(n)] = {'t': now(), 'box': b, 'rc': r.returncode, 'out': (r.stdout + r.stderr).strip()[-300:]}
        json.dump(done, open(FJ, 'w'), indent=1)
        print(now(), 'feed', b, n, r.returncode, (r.stdout + r.stderr).strip()[-200:], flush=True)
        if r.returncode == 0:
            pend += 1
