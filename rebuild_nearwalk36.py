"""nearwalk36.py: one pass of the round 36 near-file walker. Pool: forensics 'near n=N side S (+G side over the live bar) ...
<path>' lines of handoff-r36.log, the lowest file per n. A file with fewer than two seed claims naming its sha256 (16 hex) or
basename and with board room gets one quench_walk through tools/qwalkcap.py at cap 100000 (a capped walk, any hit other than
a prvsiyan share, or any gone file blocks it). Results in work/nearwalk.json {sha256: {n, path, side, ok, files, capped, bad}}.
donorfeed36.py seeds only files this walker marked ok. One walk per pass, smallest score gap first."""
import csv, hashlib, json, math, os, re, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r36/work/'
NJ = W + 'nearwalk.json'
nj = json.load(open(NJ)) if os.path.isfile(NJ) else {}
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(W + 'bar36.tsv'), delimiter='\t')}
board = {int(r['n']): float(r['board_L']) / math.sqrt(int(r['n'])) - 1 for r in csv.DictReader(open(S + 'main-r17/gap-by-n.tsv'), delimiter='\t')}
L = open(S + 'handoff-r36.log', errors='replace').read().splitlines()
cl = [l for l in L if re.search(r'\bclaim', l, re.I) and not re.search(r'\brelease', l, re.I)]
best = {}
for l in L:
    m = re.search(r'forensics -> [^:]*: near n=(\d+) side ([0-9.]+) \(\+([0-9.e-]+) side.*?(/Volumes/\S+\.csv)', l)
    if not m or not os.path.isfile(m.group(4)): continue
    n = int(m.group(1)); side = float(m.group(2)); sc = side / math.sqrt(n) - 1
    if n not in best or sc < best[n][0]: best[n] = (sc, side, m.group(4))
todo = []
for n, (sc, side, f) in best.items():
    h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
    if h in nj: continue
    room = (bar[n] - board.get(n, bar[n])) - (sc - bar[n])
    c = sum(1 for l in cl if h[:16] in l or os.path.basename(f) in l)
    if room <= 0 or c >= 2 or sc - bar[n] >= 1e-4: continue
    todo.append((sc - bar[n], n, h, f, side))
todo.sort()
# 21:28Z: two walker loops run side by side (three slots idled for want of walked files); a busy marker per sha keeps them apart
BZ = W + 'nearwalk-busy/'; os.makedirs(BZ, exist_ok=True)
todo = [x for x in todo if not (os.path.isfile(BZ + x[2]) and time.time() - os.path.getmtime(BZ + x[2]) < 1800)]
for gap, n, h, f, side in todo[:1]:
    try:
        fd = os.open(BZ + h, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd)
    except FileExistsError:
        break
    t0 = time.time()
    try:
        r = subprocess.run(['nice', '-n', '5', S + 'venv/bin/python', '-I', W + 'tools/qwalkcap.py', '100000', f], capture_output=True, text=True, timeout=1700)
        js = [json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
        j = js[-1] if js else {'hits': ['walk printed nothing: ' + r.stderr[-200:]], 'gone': []}
    except subprocess.TimeoutExpired:
        j = {'hits': ['walk timed out'], 'gone': []}
    bad = [x for x in j.get('hits', []) if not re.search(r'prvsiyan share|share within 1e-[23]', x)] + (j.get('gone') or [])
    if j.get('capped'): bad.append('capped')
    nj = json.load(open(NJ)) if os.path.isfile(NJ) else {}
    nj[h] = dict(n=n, path=f, side=side, ok=not bad, files=j.get('files'), capped=j.get('capped'), bad=bad[:5], secs=round(time.time() - t0), t=now())
    _tmp = NJ + '.tmp%d' % os.getpid(); json.dump(nj, open(_tmp, 'w'), indent=1); os.replace(_tmp, NJ)
    with open(W + '../STATE.txt', 'a') as g:
        g.write('%s boxA NEARWALK n=%d %s %s: %s (%s files, capped %s, %d s)%s\n' % (now(), n, os.path.basename(f), h[:16], 'clean' if not bad else 'BLOCKED',
                j.get('files'), j.get('capped'), time.time() - t0, '' if not bad else ': ' + '; '.join(str(z)[:100] for z in bad[:2])))
print(now(), 'todo', [(t[1], '%.2e' % t[0]) for t in todo])
