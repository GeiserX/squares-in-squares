"""autopub29.py: publish the final certs of collect29 that pass the walk (run after each collect pass).

For each final of work/collect-state.json (quench done and no lower, not beaten by a live take) whose key is not in
work/autopub.json yet: walk the pinned start's original path with rebuild_walk27.check (imported) and apply the
round 29 rule to its hits: a prvsiyan share hit counts only when the start is a public-first row
(quench_walk.harvest_type); a held 801 name is no hit (our own layout); every other hit or gone file holds the row
for review. Then the rule-a scan of rulea29 (joegun/penguin069 texts other than the jonathan1506 joegun-squares-packings
credit). A clean row goes through rows29.py and pub29.py; one handoff-r29 line per new certified layout.
Writes work/autopub.json {key: {verdict, why}} and one STATE line per decision."""
import csv, json, math, os, re, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r29/work/'
sys.path.insert(0, '.')
import rebuild_walk27 as w27  # noqa: E402
import quench_walk as qw  # noqa: E402
csv.field_size_limit(1 << 28)
now = lambda: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'round29-briefs/bar29.tsv'), delimiter='\t')}
st = json.load(open(W + 'collect-state.json')) if os.path.isfile(W + 'collect-state.json') else {'finals': {}}
AP = W + 'autopub.json'
ap = json.load(open(AP)) if os.path.isfile(AP) else {}
ql = {}
for l in open(W + 'queue-log.tsv'):
    f = l.rstrip('\n').split('\t')
    if len(f) >= 8:
        ql.setdefault(f[2], f)
import quench_audit as qa  # noqa: E402
# round 29 (main 07:34:54Z): the rule-a set is quench_audit.RULES (the 745/858 join narrowed to its two real donors and the
# 745r-858r names) plus the forensics r23 rectangle cut from the midm r23 639; the old directory-name and 800-7a2b
# alternatives were false matches
PAT = re.compile('|'.join('(?:%s)' % rx for _, rx in qa.RULES) + r'|take-forensics-r23/near/639-rect', re.I)
CREDIT = re.compile(r'jonathan1506/joegun-squares-packings|joegun-squares-packings', re.I)


def state(s):
    with open(W + '../STATE.txt', 'a') as h:
        h.write('%s boxA AUTOPUB %s\n' % (now(), s))


def start_of(key):
    """the original path of the start of a final (follow the chain of our own cert files back to a foreign start)"""
    q = ql.get(key)
    while q is not None:
        src = q[4]
        m = re.match(r'take-rebuild-r29/work/cert/(.+)\.csv$', src)
        if not m:
            return src, q
        base = re.sub(r'^q+-', '', m.group(1))
        nxt = ql.get(base)
        if nxt is None or nxt is q:
            return src, q
        q = nxt
    return None, None


todo = []
for key, fin in st['finals'].items():
    if key in ap or not fin.get('final') or fin.get('beaten') or fin.get('score') is None:
        continue
    if not fin['score'] < bar[fin['n']] - 1e-10:
        continue
    todo.append((key, fin))
for key, fin in todo:
    n = fin['n']
    src, q = start_of(key)
    notes = json.load(open(W + 'notes.json')) if os.path.isfile(W + 'notes.json') else {}
    if notes.get(key, {}).get('walk_start'):   # a re-opened file: walk the start its record names (it has the sidecars)
        src = notes[key]['walk_start']
    if src is None:
        ap[key] = {'verdict': 'hold', 'why': 'no queue-log line'}; continue
    path = src if src.startswith('/') else S + src
    if notes.get(key, {}).get('blocked'):
        ap[key] = {'verdict': 'hold', 'n': n, 'why': notes[key]['blocked'], 't': now()}
        state('HOLD %s n=%d: %s' % (key, n, notes[key]['blocked'])); json.dump(ap, open(AP, 'w'), indent=1); continue
    rv = notes.get(key, {}).get('reviewed')
    try:
        if rv:   # walked and reviewed by hand (the review text goes into the source cell)
            raise StopIteration
        r = w27.check(path)
    except StopIteration:
        r = {'clean': True, 'hits': [], 'gone': [], 'files': 0, 'reviewed': rv}
    except Exception as e:
        r = {'clean': False, 'hits': ['walk error %s' % e], 'gone': []}
    pub_first = False
    try:
        pub_first = qw.harvest_type(path, n)
    except Exception:
        pass
    hits = []
    for h in r.get('hits', []):
        if h.startswith('prvsiyan share within 1e-3') and not pub_first:
            continue
        if re.search(r'801h\b|held n = 801\b|held 801\b|n=801: prvsiyan/squares-verified-best-of-1105', h):
            continue   # main 00:19:03Z and the r29 brief: the held 801 is ours (its round 20 table row names the prvsiyan file)
        hits.append(h)
    gone = r.get('gone', [])
    texts, missing, seen, helds, refused = qw.walk(path, n) if not rv else ([], [], set(), [], [])
    ra = []
    for label, t in texts:
        if str(label).startswith('held 801 '):
            continue   # the held 801 is ours (quench_walk skips it the same way)
        for m in PAT.finditer(t):
            ctx = t[max(0, m.start() - 60):m.end() + 60]
            if CREDIT.search(ctx):
                continue
            ra.append('%s: %s' % (str(label).replace(S, '')[:80], ' '.join(ctx.split())))
    if hits or gone or ra:
        ap[key] = {'verdict': 'hold', 'n': n, 'score': fin['score'], 'start': src, 'hits': hits[:10], 'gone': gone[:10], 'rulea': ra[:10],
                   'pub_first': pub_first, 't': now()}
        state('HOLD %s n=%d score %r (gain %.3e): start %s; hits %s; gone %s; rule-a %s' % (key, n, fin['score'], bar[n] - fin['score'], src,
              hits[:3], gone[:3], ra[:2]))
        json.dump(ap, open(AP, 'w'), indent=1); continue
    rows = subprocess.run([sys.executable, '-I', W + 'tools/rows29.py', key], capture_output=True, text=True)
    fn = rows.stdout.strip().splitlines()[-1] if rows.stdout.strip() else ''
    if rows.returncode or not os.path.isfile(fn):
        ap[key] = {'verdict': 'hold', 'why': 'rows29 failed: ' + rows.stderr[-300:]}; state('HOLD %s rows29 failed %s' % (key, rows.stderr[-200:]))
        json.dump(ap, open(AP, 'w'), indent=1); continue
    d = json.load(open(fn))
    for v in d.values():
        v['source'] += (' Walk (rebuild_walk27.check under the round 29 rule): clean, %d files, pub_first %s, prvsiyan share %s.' % (
            r.get('files', 0), pub_first, (r.get('prvsiyan_share') or {}).get('share1e3'))) if not rv else ' Walk reviewed by hand: ' + rv
    json.dump(d, open(fn, 'w'), indent=1)
    pb = subprocess.run([sys.executable, '-I', W + 'tools/pub29.py', fn], capture_output=True, text=True)
    out = pb.stdout.strip().replace('\n', ' | ')
    ap[key] = {'verdict': 'published', 'n': n, 'score': fin['score'], 'start': src, 'rows': fn, 'pub': out[-500:], 't': now()}
    json.dump(ap, open(AP, 'w'), indent=1)
    kept = re.search(r'kept \[([^\]]*)\]', out)
    if kept and str(n) in [x.strip() for x in kept.group(1).split(',')]:
        state('PUBLISHED %s n=%d score %r gain %.3e (start %s); %s' % (key, n, fin['score'], bar[n] - fin['score'], src, out[-200:]))
        with open(S + 'handoff-r29.log', 'a') as h:
            h.write('%s rebuild -> all: certified n=%d, score=%r, gain=%.3e on bar29, our 900 s kick or quench (job %s) of %s, %s\n' % (
                now(), n, fin['score'], bar[n] - fin['score'], key, src, S + 'take-rebuild-r29/%d.csv' % n))
    else:
        state('NOT KEPT %s n=%d score %r: %s' % (key, n, fin['score'], out[-300:]))
json.dump(ap, open(AP, 'w'), indent=1)
