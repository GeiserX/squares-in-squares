"""scanq31.py BOX N MODES DONOR SECONDS [--why TEXT]: queue one midm_scan job of MODES (drop1 or grow1) for n on BOX with the
held round 30 c row of n as the incumbent (--sub work/held31/<n>.csv) and DONOR (a per-n csv holding the layout of n+1 or
n-1, a fresh row of another lane or ours) as --donors. The donor is pinned by sha256 into work/donors/ and copied to the box
as donors/<file>. Key: s-<mode>-<n>-<donor sha8>. Writes a note naming the donor and its take.tsv row (source and licence),
and one claim line in handoff-r31.log."""
import csv, hashlib, json, os, shutil, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
a = sys.argv[1:]
why = ''
if '--why' in a:
    i = a.index('--why'); why = a[i + 1]; del a[i:i + 2]
box, n, modes, donor, sec = a[0], int(a[1]), a[2], os.path.abspath(a[3]), a[4]
HOST = {'boxB': ('boxB', '$SCRATCH/squares-rebuild'), 'boxE': ('boxE', 'scratch/squares-rebuild'), 'boxD': ('boxD', 'scratch/squares-rebuild')}
host, root = HOST[box]
b = open(donor, 'rb').read(); dsha = hashlib.sha256(b).hexdigest()
os.makedirs(W + 'donors', exist_ok=True)
dpin = W + 'donors/%s-%s.csv' % (os.path.basename(donor)[:-4], dsha[:16])
if not os.path.isfile(dpin):
    open(dpin, 'wb').write(b)
    for ext in ('.json', '.origin.json'):
        if os.path.isfile(donor + ext):
            shutil.copy2(donor + ext, dpin + ext)
import re, calendar
now = time.time()
for l in open(S + 'handoff-r31.log', errors='replace'):
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\S* (\S+) ->', l)
    if not m or m.group(2) == 'rebuild' or 'claim' not in l.lower():
        continue
    t = calendar.timegm(time.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S'))
    if now - t > 3600:
        continue
    if dsha[:10] in l and re.search(r'n=%d\b' % n, l) and modes.split(',')[0] in l:
        print('claimed by another lane within 60 min:', l[:200]); sys.exit(2)
subprocess.run(['ssh', host, 'mkdir -p %s/donors' % root], check=True)
subprocess.run(['scp', '-q', dpin, '%s:%s/donors/%s' % (host, root, os.path.basename(dpin))], check=True)
dn = None; row = None
for r in csv.DictReader(open(donor)):
    dn = int(r['n']); break
tk = os.path.join(os.path.dirname(donor), 'take.tsv')
if os.path.isfile(tk):
    for r in csv.DictReader(open(tk), delimiter='\t'):
        if r.get('n') == str(dn):
            row = r
p = W + 'held31/%d.csv' % n
sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
key = 's-%s-%d-%s' % (modes.replace(',', ''), n, dsha[:8])
notes = json.load(open(W + 'notes.json')) if os.path.isfile(W + 'notes.json') else {}
src = ('our midm_scan.py %s (%s s) for n = %d: the layouts tried are the layout of n = %d in %s (sha256 %s, byte copy take-rebuild-r31/work/donors/%s) '
       'with one square removed (drop1) or one square added in its widest hole (grow1), each then one fq quench; the incumbent is the held round 30 c row '
       'of n = %d (take-rebuild-r31/work/held31/%d.csv, sha256 %s). The donor: its take.tsv row: %s' % (
           modes, sec, n, dn, donor.replace(S, ''), dsha[:16], os.path.basename(dpin), n, n, sha[:16],
           ' '.join((row or {}).get('source', 'no take row (see its record)').split())))
notes[key] = {'reviewed': 'scan of a donor layout of n = %d (%s); the walk is the donor walk named in the source' % (dn, donor.replace(S, '')),
              'source': src, 'licence': ' '.join((row or {}).get('licence', '').split()) or 'see the donor record', 'donor': donor, 'donor_sha256': dsha}
json.dump(notes, open(W + 'notes.json', 'w'), indent=1)
mode = 'scan:%s:%s:donors/%s' % (sec, modes, os.path.basename(dpin))
r = subprocess.run([sys.executable, '-I', W + 'tools/q31.py', box, key, str(n), p, mode], capture_output=True, text=True, env=dict(os.environ, FRONT='1'))
if r.returncode:
    print('queue failed', r.stderr[-300:]); sys.exit(1)
with open(S + 'handoff-r31.log', 'a') as h:
    h.write('%s rebuild -> all: claim: %s s midm_scan %s of n=%d from the layout of n=%d in %s (donor sha256 %s; job %s on %s)%s\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), sec, modes, n, dn, donor, dsha[:16], key,
        {'boxB': 'boxB', 'boxE': 'boxE', 'boxD': 'boxD'}[box], (' (' + why + ')') if why else ''))
print('queued', key, box, mode)
