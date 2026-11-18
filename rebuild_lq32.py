"""lq32.py BOX N [SECONDS] [--why TEXT]: queue one invent_rest.py lkick job (rebuild_run.py lk:SECONDS, default 150) on the held round 31 b row of n
(round 32: the twoshort kind, on held rows whose bytes no lkick claim of handoff-r29..r32 names). Otherwise as hq32.py:
(work/held32/<n>.csv, extracted byte for byte from gather/round31-2026-11-16b.csv) on BOX, after checking that no other lane
claimed the same bytes (sha256 prefix of 12+ hex digits or the path) in handoff-r32.log in the last 60 minutes, and that
the row's results-table source names neither prvsiyan/squares-verified-best-of-1105 nor penguin069 (rule 3). Writes
the reviewed note (source and licence from the latest round table that lists n) into work/notes.json, then one claim
line into handoff-r32.log. Key: h-<n>-<sha8>."""
import csv, glob, hashlib, json, os, re, subprocess, sys, time, calendar
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r32/work/'
args = [a for a in sys.argv[1:]]
why = ''
if '--why' in args:
    i = args.index('--why'); why = args[i + 1]; del args[i:i + 2]
box, n = args[0], int(args[1])
sec = args[2] if len(args) > 2 else '150'
p = W + 'held32/%d.csv' % n
sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
now = time.time()
for l in open(S + 'handoff-r32.log', errors='replace'):
    m = re.match(r'^(\S+) (\S+) -> [^:]*: (.*)$', l)
    if not m or m.group(2) == 'rebuild' or not re.search(r'\bclaim', m.group(3), re.I):
        continue
    try:
        t = calendar.timegm(time.strptime(m.group(1)[:19], '%Y-%m-%dT%H:%M:%S'))
    except ValueError:
        t = now
    if now - t > 3600:
        continue
    hx = [h.lower() for h in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{12,64})(?![0-9a-fA-F])', m.group(3))]
    # round 31: other lanes extract the same held row with other bytes (forensics held-inputs), so a claim naming the n
    # (n=N or a /N.csv start) also holds us off
    # BYTES=1 (rooms): a claim naming the n holds us off only when it names a held row; other bytes of the same n do not
    nhit = re.search(r'\bn ?= ?%d\b|/%d\.csv\b' % (n, n), m.group(3))
    if nhit and os.environ.get('BYTES') == '1' and not re.search(r'\bheld', m.group(3), re.I):
        nhit = None
    if any(sha.startswith(h) for h in hx) or p in m.group(3) or nhit:
        print('SKIP claimed by %s: %s' % (m.group(2), l.strip()[:200])); sys.exit(2)
# round 32: an lkick claim (invent_rest, or lkick without midm) of these bytes in any of handoff-r29..r32, by any lane, at any
# time, holds us off for good (twoshort skips lkick claims for good too)
for _k in (29, 30, 31, 32):
    for l in open(S + 'handoff-r%d.log' % _k, errors='replace'):
        if not ('invent_rest' in l or ('lkick' in l and 'midm' not in l)) or ' rebuild -> ' in l:
            continue
        if any(sha.startswith(h.lower()) for h in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{12,64})(?![0-9a-fA-F])', l)):
            print('SKIP lkicked before: %s' % l.strip()[:200]); sys.exit(2)
R = 'results/'
tabs = sorted(glob.glob(R + 'round*-best-*.tsv'), key=lambda f: int(re.search(r'round(\d+)-', f).group(1)))
row, tab = None, None
csv.field_size_limit(1 << 28)
for f in tabs:
    try:
        for r in csv.DictReader(open(f), delimiter='\t'):
            if r.get('n') == str(n):
                row, tab = r, f
    except Exception:
        pass
src = ' '.join((row or {}).get('source', '').split()); lic = ' '.join((row or {}).get('licence', '').split())
if re.search(r'squares-verified-best-of-1105', src + ' ' + lic) and n != 801:
    print('SKIP rule 3: the table source names prvsiyan/squares-verified-best-of-1105'); sys.exit(3)
if re.search(r'penguin069', src + ' ' + lic) and n in (639, 691, 745, 858, 918):
    print('SKIP rule 3: penguin069 boxed union at a listed n'); sys.exit(3)
notes = json.load(open(W + 'notes.json')) if os.path.isfile(W + 'notes.json') else {}
key = 'l-%d-%s' % (n, sha[:8]) + (('-' + os.environ['SEEDTAG']) if os.environ.get('SEEDTAG') else '')  # SEEDTAG: a second seed of the same start
tabr = tab.replace(S, '').replace('', '') if tab else 'no round table lists it (held since before round 7)'
notes[key] = {'reviewed': ('the start is the held round 31 b row of n = %d, extracted byte for byte from gather/round31-2026-11-16b.csv '
                           '(the submitted round 31 b file, gate/cand-round31-1116b) to take-rebuild-r32/work/held32/%d.csv (sha256 %s); '
                           'a held row is our own layout (rule 2 of round 32), and its record is its results-table row, %s n=%d' % (n, n, sha[:16], tabr, n)),
              'source': 'the held round 31 b row of n = %d (gather/round31-2026-11-16b.csv); its row in %s: %s' % (n, tabr, src or 'none'),
              'licence': lic or 'held row (our own layout)'}
json.dump(notes, open(W + 'notes.json', 'w'), indent=1)
mode = 'lk:%s' % sec
r = subprocess.run([sys.executable, '-I', W + 'tools/q32.py', box, key, str(n), p, mode], capture_output=True, text=True, env=dict(os.environ, FRONT='0'))
if r.returncode:
    print('queue failed', r.stderr[-300:]); sys.exit(1)
with open(S + 'handoff-r32.log', 'a') as h:
    h.write('%s rebuild -> all: claim: %s s invent_rest lkick of n=%d (job %s on %s), start bytes sha256 %s, the held round 31 b row%s, %s\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), sec, n, key,
        {'boxB': 'boxB', 'boxE': 'boxE', 'boxD': 'boxD'}[box], sha[:16], (' (' + why + ')') if why else '', p))
print('queued', key, box, mode, r.stdout.strip())
