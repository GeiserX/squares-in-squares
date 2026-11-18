"""follow28.py: one pass of the rebuild r28 follow. Every row of another lane's live take-*-r31/take.tsv whose per-n csv
(byte snapshot, sha256) has not been queued yet gets one midm_scan lkick,kick job (KICK seconds, default 900) on the box
with the shortest queue per slot. Rows above bar28 are skipped. Also queues the near files that a handoff-r31 line names
as below the bar of that n ('margin -' or 'below'), when FOLLOW_NEAR=1. Writes work/follow-seen.json."""
import csv, glob, hashlib, json, math, os, re, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
KICK = os.environ.get('KICK', '900')   # 21:40Z: 900 s, no probe (finds of paying kicks came at 118 to 415 s; rule 6c probe dropped by measure)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
OUTN = {int(x.split()[0]) for x in open(W + 'outn.txt') if x.strip() and x.split()[0].isdigit()} if os.path.isfile(W + 'outn.txt') else set()
SEEN = W + 'follow-seen.json'
seen = json.load(open(SEEN)) if os.path.isfile(SEEN) else {}
seen = {k: v for k, v in seen.items() if not (isinstance(v, dict) and str(v.get('skip', '')).startswith('claimed by another lane'))}
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild', 2), 'boxE': ('boxE', 'scratch/squares-rebuild', 1), 'boxD': ('boxD', 'scratch/squares-rebuild', 1)}


def pending(b, pre=''):
    """unclaimed queue lines per slot on box b; with pre, only keys that start with it"""
    host, root, slots = BOX[b]
    out = subprocess.run(['ssh', host, 'cd %s && cut -f1 queue.tsv | grep "^%s" | while read k; do [ -d "claims/$k" ] || echo "$k"; done | wc -l' % (root, pre)],
                         capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out or 0) / slots


def drop_pending(b, rx, why):
    """remove the unclaimed queue lines of box b whose key matches rx; returns the keys removed"""
    host, root, slots = BOX[b]
    q = subprocess.run(['ssh', host, 'cd %s && cat queue.tsv; echo @@SPLIT@@; ls claims' % root], capture_output=True, text=True, timeout=60).stdout
    if '@@SPLIT@@' not in q:
        return []
    ql, cl = q.split('@@SPLIT@@', 1)
    claimed = set(cl.split())
    keep, gone = [], []
    for l in ql.splitlines():
        k = l.split('\t')[0]
        (gone if (k not in claimed and re.match(rx, k)) else keep).append(l if not (k not in claimed and re.match(rx, k)) else k)
    if gone:
        subprocess.run(['ssh', host, 'cd %s && cat > queue.new && mv queue.new queue.tsv' % root], input=('\n'.join(keep) + '\n'), text=True, check=True, timeout=60)
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'dropped', b, ' '.join(gone), why, flush=True)
    return gone


def public_over(p, n):
    """rule 3: a public-first start (quench_walk.harvest_type) whose best-of-1105 share is 0.4 or more at 1e-3 is out"""
    try:
        sys.path.insert(0, '.')
        import quench_walk as _qw, rebuild_walk27 as _w27
        if not _qw.harvest_type(p, n):
            return None
        sh = _w27.prv_share(p, n)
        return sh['share1e3'] if sh and sh['share1e3'] >= 0.4 else None
    except Exception:
        return None


# round 30: bytes a kick of ours already ran on (r29 and r30 queue logs, by sha256) are not queued again
KICKED = set()
for _qf in (S + 'take-rebuild-r30/work/queue-log.tsv', W + 'queue-log.tsv'):
    if os.path.isfile(_qf):
        for _l in open(_qf):
            _f = _l.rstrip('\n').split('\t')
            if len(_f) >= 8 and _f[7].startswith('kick'):
                KICKED.add(_f[5])
# round 30: start bytes another lane claims in handoff-r31 (a 'claim' line naming the sha256 or its prefix of 12 or more hex
# digits, or the path) are not queued (quench 12:22:58Z claimed its 694 while our follow of the same bytes was queued)
OCLAIM, OCLAIMP = [], set()
for _l in open(S + 'handoff-r31.log', errors='replace'):
    _m = re.match(r'^\S+ (\S+) -> [^:]*: (.*)$', _l)
    if not _m or _m.group(1) == 'rebuild' or not re.search(r'\bclaim', _m.group(2), re.I):
        continue
    # round 31 rule 6b: one kick per start: any claim of any lane in the last 60 minutes holds us off (backlog follows the
    # fresh rows; round 30 lost about 30 jobs per lane to duplicate kicks)
    try:
        import calendar as _cal
        if time.time() - _cal.timegm(time.strptime(_l[:19], '%Y-%m-%dT%H:%M:%S')) > 3600:
            continue
    except ValueError:
        pass
    OCLAIM += [h.lower() for h in re.findall(r'(?<![0-9a-fA-F])([0-9a-fA-F]{12,64})(?![0-9a-fA-F])', _m.group(2))]
    OCLAIMP.update(re.findall(r'(/Volumes/\S+?\.csv)\b', _m.group(2)))


def claimed_other(sha, p):
    return p in OCLAIMP or any(sha.startswith(h) for h in OCLAIM)


def claim_line(n, key, b, p, sha):
    with open(S + 'handoff-r31.log', 'a') as h:
        h.write('%s rebuild -> all: claim: 900 s midm_scan lkick,kick of n=%d (job %s on %s), start bytes sha256 %s, %s\n' % (
            time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, key, {'boxB': 'boxB', 'boxE': 'boxE', 'boxD': 'boxD'}[b], sha[:16], p))


# paths that a WITHDRAW line of handoff-r31 names (any lane): never queue them
WD = set()
for _l in open(S + 'handoff-r31.log', errors='replace'):
    if re.search(r'\bWITHDRAW\b', _l) and 'REINSTATE' not in _l:
        WD.update(re.findall(r'(/Volumes/\S+?\.csv)\b', _l))
        WD.update(S + x for x in re.findall(r'\b(take-[a-z0-9-]+-r\d+/\S+?\.csv)\b', _l))
FIRSTF = W + 'follow-firstseen.json'
FIRST = json.load(open(FIRSTF)) if os.path.isfile(FIRSTF) else {}
todo = []
for t in sorted(glob.glob(S + 'take-*-r31/take.tsv')):
    if '/take-rebuild-r31/' in t:
        continue
    lane = t.split('/')[-2]
    try:
        rows = list(csv.DictReader(open(t), delimiter='\t'))
    except Exception:
        continue
    for r in rows:
        try:
            n = int(r['n']); s = float(r['new'])
        except Exception:
            continue
        p = os.path.dirname(t) + '/%d.csv' % n
        if not os.path.isfile(p) or s >= bar[n] or p in WD:
            continue
        try:
            sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        except OSError:
            continue
        # round 31 rule 6b: backlog follows fresh rows; we wait 10 minutes for its claim. Timed from the first time we saw
        # these bytes (20:20Z: quench rewrites its per-n files every pass, so their mtime is always fresh)
        if time.time() - FIRST.setdefault(sha, min(time.time(), os.path.getmtime(p))) < 600:
            continue
        k = '%s-%d-%s' % (lane, n, sha[:12])
        todo.append((k, n, p, lane, sha, s))
json.dump(FIRST, open(FIRSTF, 'w'))
# only the lowest live row of each n, and only when it is lower than every row of that n queued before
low = {}
for x in todo:
    if x[1] not in low or x[5] < low[x[1]][5]:
        low[x[1]] = x
done_low = {}
for v in seen.values():
    if 'score' in v:
        done_low[v['n']] = min(done_low.get(v['n'], 9), v['score'])
todo = [x for x in low.values() if x[0] not in seen and x[4] not in KICKED and x[5] < done_low.get(x[1], 9) - 1e-10]
# a row within 1e-7 of a row whose follow kick of ours found no lower layout is skipped (round 29 10:37Z: 587 moved
# 5e-9 after our kick of it found nothing)
nolow = {}
try:
    _keys = {v.get('key'): v for v in seen.values() if isinstance(v, dict) and v.get('key')}
    for _l in open(W + 'collect.log'):
        _m = re.search(r' done \w+ (f-\S+) n=(\d+) side=None', _l)
        if _m and _m.group(1) in _keys and 'score' in _keys[_m.group(1)]:
            nolow[int(_m.group(2))] = min(nolow.get(int(_m.group(2)), 9), _keys[_m.group(1)]['score'])
except OSError:
    pass
for k, n, p, lane, sha, s in todo:
    if n in OUTN:   # n whose public-first rows are out under rule 3 (work/outn.txt): their follows would be out too
        continue
    # round 30: lane:n pairs whose lineage we found out (work/skip.txt, one 'take-<lane>-r30:<n>' per line)
    if os.path.isfile(W + 'skip.txt') and '%s:%d' % (lane, n) in open(W + 'skip.txt').read().split():
        seen[k] = {'n': n, 'path': p, 'sha256': sha, 'skip_score': s, 'skip': 'lineage out (work/skip.txt)'}; continue
    if n in nolow and s > nolow[n] - 1e-7:
        seen[k] = {'n': n, 'path': p, 'sha256': sha, 'skip_score': s, 'skip': 'within 1e-7 of a row our kick found no lower layout from'}
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'skipped near a no-lower kick', n, s, p, flush=True); continue
    if claimed_other(sha, p):
        pass  # 20:25Z: not kept in seen, so the row comes back once the claim is 60 min old (a second seed)
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'skipped claimed by another lane', n, p, flush=True); continue
    po = public_over(p, n)
    if po is not None:
        seen[k] = {'n': n, 'path': p, 'sha256': sha, 'skip_score': s, 'skip': 'public-first, share %.3f' % po}
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'skipped public-first share', '%.3f' % po, p, flush=True); continue
    for b0 in BOX:   # one take follow per n: a lower live row replaces the pending follow of a higher one
        drop_pending(b0, r'^f-(?!n-|h-)[a-z0-9-]+?-%d-[0-9a-f]{8}$' % n, 'replaced by the follow of %s (%.12g)' % (p.replace(S, ''), s))
    pb = {b: pending(b, 'f-') for b in BOX}
    b = min(pb, key=pb.get)
    key = 'f-%s-%d-%s' % (lane.replace('take-', '').replace('-r31', ''), n, sha[:8])
    r = subprocess.run([sys.executable, '-I', W + 'tools/q31.py', b, key, str(n), p, 'kick:' + KICK], capture_output=True, text=True, env=dict(os.environ, FRONT='1'))
    seen[k] = {'key': key, 'box': b, 'n': n, 'path': p, 'sha256': sha, 'score': s, 't': time.strftime('%H:%M:%SZ', time.gmtime()), 'rc': r.returncode}
    if r.returncode == 0:
        claim_line(n, key, b, p, sha)
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'queued', key, b, n, s, 'bar', bar[n], r.stdout.strip(), r.stderr.strip()[-200:], flush=True)
    json.dump(seen, open(SEEN, 'w'), indent=1)
json.dump(seen, open(SEEN, 'w'), indent=1)

# near files named in handoff-r31 lines of other lanes (any wording: the line's n=NNN and the last csv path in it), scored
# here against the bar29 side; the lowest file of each n within NEAR_MARGIN of the bar side is queued when it is lower
# than every file of that n queued before by 1e-9, not claimed by backlog, and the f- queue of the box is short
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
sys.path.insert(0, 'tools/harvest26')
import audit_ac  # noqa: E402
from share_ac import share  # noqa: E402
NEAR_MARGIN = float(os.environ.get('NEAR_MARGIN', '1e-6'))
NEAR_BELOW = float(os.environ.get('NEAR_BELOW', '1e-7'))   # round 30: r29 next 2 (near files paid only 1e-7 or more below)   # a near file must be below the bar29 side by more than this
txt = open(S + 'handoff-r31.log', errors='replace').read()
claimed = set(re.findall(r'backlog -> \S+: claims \S+, start \S+, (/\S+?\.csv)', txt))
SC = W + 'near-scored.json'
scored = json.load(open(SC)) if os.path.isfile(SC) else {}
best = {}
for line in txt.splitlines():
    m = re.match(r'^(\S+(?: \S+Z)?) (\S+) -> [^:]*: (.*)$', line)
    if not m or m.group(2) in ('rebuild', 'main'):
        continue
    body = m.group(3)
    if re.search(r'\bWITHDRAW|\bwithdrawn\b|\brefuse', body, re.I):
        continue
    # round 31 rule 6b: backlog follows the fresh certified rows of other lanes; a near file is ours to kick only when its
    # line is 10 minutes old and no lane claimed it since (the claim test below)
    try:
        import calendar as _cal
        if time.time() - _cal.timegm(time.strptime(m.group(1)[:19], '%Y-%m-%dT%H:%M:%S')) < 600:
            continue
    except ValueError:
        pass
    mn = re.search(r'\bn=(\d+)', body); mp = re.findall(r'(/Volumes/\S+?\.csv)\b', body)
    if not mn or not mp:
        continue
    n, p = int(mn.group(1)), mp[-1]
    if n not in bar or p in claimed or p in WD or not os.path.isfile(p):
        continue
    if '/gather/' in p or os.path.getsize(p) > 2000000:   # a whole submission file (midm names gather/round28 b as a start): not a near file; reading it all took 3.3 GB
        continue
    try:
        st_ = os.stat(p); ck = '%s|%d|%d' % (p, st_.st_size, int(st_.st_mtime))
        if ck not in scored:
            P = mlp.load(p, {n})[n]
            scored[ck] = float(mlp.side(P)) if len(P) == n and mlp.min_gap(P) > -1e-9 else None
        side = scored[ck]
    except Exception:
        scored[ck] = None; side = None
    if side is None:
        continue
    margin = side - (1 + bar[n]) * math.sqrt(n)
    if margin > NEAR_MARGIN or margin > -NEAR_BELOW:   # round 29 08:55Z: 0 of 9 kicks of near files at the bar side (within 2e-9) moved
        continue
    # a near file that is the bar row itself (0.9 or more of its centres within 1e-3 of the bar29 row, best of 8
    # symmetries) adds nothing to a kick of that row: skip it (round 29: the stair-c base rebuilds at the bar side)
    sk = ck + '|share'
    if sk not in scored:
        try:
            a = audit_ac.centres(list(csv.DictReader(open(p))))
            b = audit_ac.centres(list(csv.DictReader(open(W + 'bar31rows/%d.csv' % n))))
            scored[sk] = share(a, b)[1]
        except Exception:
            scored[sk] = None
    if scored[sk] is not None and scored[sk] >= 0.9:
        continue
    if n not in best or side < best[n][0]:
        best[n] = (side, p, m.group(2), margin)
json.dump(scored, open(SC, 'w'))
qlow = {}
for v in seen.values():
    if 'side' in v:
        qlow[v['n']] = min(qlow.get(v['n'], 1e9), v['side'])
for n, (side, p, lane, margin) in sorted(best.items(), key=lambda kv: kv[1][3]):
    if n in OUTN:   # n whose public-first rows are out under rule 3 (work/outn.txt): their follows would be out too
        continue
    if side >= qlow.get(n, 1e9) - 1e-9:
        continue
    try:
        sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except OSError:
        continue   # the lane moved or removed the file since it was scored
    k = 'near-%s-%d-%s' % (lane, n, sha[:12])
    if k in seen or sha in KICKED or sha in {v.get('sha256') for v in seen.values()}:
        continue
    if claimed_other(sha, p):
        continue  # 20:25Z: not kept in seen (comes back after 60 min)
    if public_over(p, n) is not None:
        seen[k] = {'n': n, 'path': p, 'sha256': sha, 'margin': margin, 'skip': 'public-first share 0.4 or more'}; continue
    pb = {b: pending(b, 'f-n-') for b in BOX}
    b = min(pb, key=pb.get)
    if pb[b] >= 3:
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'near skipped (queues full)', k, flush=True); continue
    key = 'f-n-%s-%d-%s' % (lane, n, sha[:8])
    r = subprocess.run([sys.executable, '-I', W + 'tools/q31.py', b, key, str(n), p, 'kick:' + KICK], capture_output=True, text=True, env=dict(os.environ, FRONT='1'))
    seen[k] = {'key': key, 'box': b, 'n': n, 'path': p, 'sha256': sha, 'margin': margin, 'side': side, 't': time.strftime('%H:%M:%SZ', time.gmtime()), 'rc': r.returncode}
    if r.returncode == 0:
        claim_line(n, key, b, p, sha)
    qlow[n] = side
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'queued near', key, b, n, '%.3e' % margin, r.stdout.strip(), r.stderr.strip()[-200:], flush=True)
    json.dump(seen, open(SEEN, 'w'), indent=1)
