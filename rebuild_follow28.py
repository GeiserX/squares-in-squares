"""follow28.py: one pass of the rebuild r28 follow. Every row of another lane's live take-*-r28/take.tsv whose per-n csv
(byte snapshot, sha256) has not been queued yet gets one midm_scan lkick,kick job (KICK seconds, default 900) on the box
with the shortest queue per slot. Rows above bar28 are skipped. Also queues the near files that a handoff-r28 line names
as below the bar of that n ('margin -' or 'below'), when FOLLOW_NEAR=1. Writes work/follow-seen.json."""
import csv, glob, hashlib, json, math, os, re, subprocess, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r28/work/'
KICK = os.environ.get('KICK', '900')
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'round28-briefs/bar28.tsv'), delimiter='\t')}
SEEN = W + 'follow-seen.json'
seen = json.load(open(SEEN)) if os.path.isfile(SEEN) else {}
BOX = {'boxB': ('boxB', '$SCRATCH/squares-rebuild', 2), 'boxE': ('boxE', 'scratch/squares-rebuild', 1)}


def pending(b):
    host, root, slots = BOX[b]
    out = subprocess.run(['ssh', host, 'cd %s && cut -f1 queue.tsv | while read k; do [ -d "claims/$k" ] || echo "$k"; done | wc -l' % root],
                         capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out or 0) / slots


todo = []
for t in sorted(glob.glob(S + 'take-*-r28/take.tsv')):
    if '/take-rebuild-r28/' in t:
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
        if not os.path.isfile(p) or s >= bar[n]:
            continue
        try:
            sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        except OSError:
            continue
        k = '%s-%d-%s' % (lane, n, sha[:12])
        todo.append((k, n, p, lane, sha, s))
# only the lowest live row of each n, and only when it is lower than every row of that n queued before
low = {}
for x in todo:
    if x[1] not in low or x[5] < low[x[1]][5]:
        low[x[1]] = x
done_low = {}
for v in seen.values():
    if 'score' in v:
        done_low[v['n']] = min(done_low.get(v['n'], 9), v['score'])
todo = [x for x in low.values() if x[0] not in seen and x[5] < done_low.get(x[1], 9) - 1e-10]
for k, n, p, lane, sha, s in todo:
    pb = {b: pending(b) for b in BOX}
    b = min(pb, key=pb.get)
    key = 'f-%s-%d-%s' % (lane.replace('take-', '').replace('-r28', ''), n, sha[:8])
    r = subprocess.run([sys.executable, '-I', W + 'tools/q28.py', b, key, str(n), p, 'kick:' + KICK], capture_output=True, text=True, env=dict(os.environ, FRONT='1'))
    seen[k] = {'key': key, 'box': b, 'n': n, 'path': p, 'sha256': sha, 'score': s, 't': time.strftime('%H:%M:%SZ', time.gmtime()), 'rc': r.returncode}
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'queued', key, b, n, s, 'bar', bar[n], r.stdout.strip(), r.stderr.strip()[-200:], flush=True)
    json.dump(seen, open(SEEN, 'w'), indent=1)
json.dump(seen, open(SEEN, 'w'), indent=1)

# near files named in handoff-r28 lines with a small margin above (or below) the bar side, not claimed by backlog
NEAR_MARGIN = float(os.environ.get('NEAR_MARGIN', '1e-6'))
txt = open(S + 'handoff-r28.log', errors='replace').read()
claimed = set(re.findall(r'backlog -> \S+: claims \S+, start \S+, (/\S+?\.csv)', txt))
for m in re.finditer(r'^(\S+) (\S+) -> [^:]*: [^\n]*?near n=(\d+), side ([0-9.]+), margin ([-+0-9.e]+), (/\S+?\.csv)\s*$', txt, re.M):
    lane, n, margin, p = m.group(2), int(m.group(3)), float(m.group(5)), m.group(6)
    if lane == 'rebuild' or margin > NEAR_MARGIN or p in claimed or not os.path.isfile(p):
        continue
    sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    k = 'near-%s-%d-%s' % (lane, n, sha[:12])
    if k in seen:
        continue
    pb = {b: pending(b) for b in BOX}
    b = min(pb, key=pb.get)
    if pb[b] >= 3:
        print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'near skipped (queues full)', k, flush=True); continue
    key = 'n-%s-%d-%s' % (lane, n, sha[:8])
    r = subprocess.run([sys.executable, '-I', W + 'tools/q28.py', b, key, str(n), p, 'kick:' + KICK], capture_output=True, text=True)
    seen[k] = {'key': key, 'box': b, 'n': n, 'path': p, 'sha256': sha, 'margin': margin, 't': time.strftime('%H:%M:%SZ', time.gmtime()), 'rc': r.returncode}
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'queued near', key, b, n, margin, r.stdout.strip(), r.stderr.strip()[-200:], flush=True)
    json.dump(seen, open(SEEN, 'w'), indent=1)
