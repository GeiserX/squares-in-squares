#!/usr/bin/env python3
"""The controller of a round of the soft-box lane, on boxA. The constants below are the round.

  ctl.py plan      the starts and one queue per box: every n the held file moved that has not had the pass on that
                   packing (the plan and logs of the round before say which have), the n of EXTRA from the held
                   file, and the n of the watched take dirs whose file is below the held score, from that file
  ctl.py watch     new wins of the other lanes since the plan: a start file and a line at the head of a box queue
  ctl.py split A B every second waiting line of box A's queue goes to box B (a box that starts late)
  ctl.py add N FILE KIND BOX   a start from a file a lane hands over, at the head of the queue of BOX
  ctl.py collect   fetch run/ of every box, certify every raw file (floatsafe at 2.2e-11), write the take dir
  ctl.py cq N TAG  the fq quench of the take file of N (float-safe rows) under W/cq; collect reads it as a box
  ctl.py where     print the work dir of the round (the shell scripts read it)

A result counts when it is more than 1e-10 below the held score and below the file it started from, and no
other lane holds a file for that n that is more than 1e-10 below it at the time of the collect.
"""
import csv, glob, hashlib, json, os, re, subprocess, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import policy

S = '$SCRATCH/bounties-squares'
LANE = '.'
RN = 33
T = S + '/take-soft-r%d' % RN; W = T + '/work'
PREV_W = S + '/take-soft-r32/work'                      # the last round of this lane: which packings have had the pass
HELD_FILE = S + '/gather/round32-2026-11-16a.csv'; GATE = S + '/gate/cand-round32-1116a'
BEST_TSV = LANE + '/results/round32-best-2026-11-16.tsv'
HANDOFF = S + '/handoff-r%d.log' % RN                   # collect writes one line here for each new certified layout
sys.path.insert(0, LANE)

REMOTE = {'boxC': 'boxC', 'boxD': 'boxD'}               # rounds 19 and 20: no boxE slot (round 17: 'boxE': 'boxE')
RDIR = 'scratch/squares-soft-r33'
START_SLOTS = ['boxC', 'boxD', 'boxC']                  # one entry per process that runs when the round starts
WORKERS = {'boxC': 2, 'boxD': 1}                        # round 33 budget: processes per box
WATCH_SLOTS = ['boxC', 'boxD', 'boxC']                  # a new file goes to these in turn, to the boxes of W/active.txt
_L = ('twoshort', 'two'), ('family', 'fam'), ('readers', 'rea'), ('band', 'ban'), ('modules', 'mod'), ('classfill', 'cfl'), \
     ('midm', 'mid'), ('rigidsoft', 'rig'), ('k123', 'k12'), ('invent', 'inv'), ('stair-b', 'stb'), ('stair-c', 'stc'), \
     ('border', 'bor'), ('corners', 'cor'), ('polish', 'pol'), ('farend', 'far'), ('harvest', 'hav'), ('forensics', 'for'), \
     ('gap', 'gap'), ('backlog', 'bkl'), ('rebuild', 'reb'), ('quench', 'qch')
# Round 33 follows fresh geometry with a clean ancestry record.
DIRS = [(k, t + r, 'take-%s-r%s' % (k, r)) for r in ('33',) for k, t in _L]
LEAD = ()                                               # round 31: k123 three-way near files out (lesson 6e)
SECOND = ('rigidsoft',)
FIRST = LEAD + SECOND
NEW_STEP = 9e-5
MIN_STEP = {k: 1e-10 if k in FIRST else float('inf') for k, _ in _L}
KICKED = ()
LIVE = ('take-*-r%d' % RN,)
KINDS = ('family', 'readers')                           # a held n starts only when its newest step is of these kinds
                                                        # (rounds 11 to 13: 9 of 103 such starts found, 0 of 57 others)
EXTRA = ()                                              # held family layouts that still wait for their pass, after the
                                                        # family files of the round before
ISLAND = {}                                             # one island from the held packing, find or no find:
                                                        # again = the island only, full = after the two 140 s islands
REST = ()                                               # no start from the held packing
SHORT = ()                                              # the two 140 s islands only
RESEED = False                                          # a held packing of KINDS that had its pass in the round before
                                                        # gets a pass with the seeds 21 to 23, last in the queue
KEYS = ('n', 'square_id', 'x', 'y', 'angle')
BAR = 1e-10
SAME = 1e-7                                             # the watch starts a file only this far below the starts of its n
                                                        # (round 17: the family lane's quench of a twoshort file sits 1e-8 to 3e-8 below it)
                                                        # (a file a few 1e-9 below a start is the same packing)


def rows_of(path):
    return [{k: r[k] for k in KEYS} for r in csv.DictReader(open(path, newline=''))]


def cert(a):
    """(key, path) -> (key, score or None, float-safe rows or None)"""
    key, path = a
    try:
        rows = rows_of(path); n = int(rows[0]['n'])
        if len(rows) != n or any(int(r['n']) != n for r in rows):
            return key, None, None
        sys.path.insert(0, LANE + '/tools/border/r28')
        import finesafe                  # round 29: bisected dilation, 3e-10 to 8e-10 of side below the ladder (border r28)
        _, fr, score, e = finesafe.work((n, rows))
        return key, (score if fr is not None else None), fr
    except Exception as ex:  # a half-written file
        return key, None, None


def write_rows(path, rows):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(KEYS)
        for r in rows:
            w.writerow([r[k] for k in KEYS])
    os.rename(tmp, path)


def held_scores():
    gate = open(W + '/base-gate.txt').read().strip() if os.path.exists(W + '/base-gate.txt') else GATE
    out = {int(r['n']): float(r['score']) for r in csv.DictReader(open(gate + '/details.csv'))}
    if gate == GATE and os.path.exists(W + '/base-extra.json'):
        for n, v in json.load(open(W + '/base-extra.json')).items():
            out[int(n)] = min(out[int(n)], float(v['score']))
    return out


def store_ancestry(proof):
    """Round 24 kept every proof inside plan.json (45 MB). Keep it once by hash and a small reference."""
    blob = json.dumps(proof, sort_keys=True).encode()
    key = hashlib.sha256(blob).hexdigest()[:20]
    d = W + '/anc'; os.makedirs(d, exist_ok=True)
    if not os.path.exists('%s/%s.json' % (d, key)):
        open('%s/%s.json.tmp' % (d, key), 'wb').write(blob); os.rename('%s/%s.json.tmp' % (d, key), '%s/%s.json' % (d, key))
    return dict(ok=bool(proof.get('ok')), ref=key, reason=proof.get('reason', ''))


def load_ancestry(ref):
    if isinstance(ref, dict) and 'ref' in ref and len(ref) <= 3:
        try:
            return json.load(open('%s/anc/%s.json' % (W, ref['ref'])))
        except (OSError, ValueError):
            return dict(ok=False, reason='missing stored ancestry')
    return ref


def source_dir(path):
    match = re.search(r'/((?:take-)[^/]+-r\d+)(?:/|$)', path)
    return match[1] if match else os.path.basename(os.path.dirname(path))


def take_meta(d):
    out = {}
    p = '%s/%s/take.tsv' % (S, d)
    if os.path.exists(p):
        for r in csv.DictReader(open(p), delimiter='\t'):
            try:
                out[int(r['n'])] = (r.get('source') or '', r.get('licence') or '')
            except Exception:
                pass
    return out


def donor_source(path, n, fallback):
    """Keep a near file's explicit ancestry instead of borrowing another row's source."""
    from provenance import metadata
    source, licence, record = metadata(path, n)
    if source:
        return source + ' (donor metadata ' + record + ')', licence or fallback[1]
    return fallback


def live_dirs():
    """every live take dir of the round but ours, as (kind, tag, dir)"""
    own = os.path.basename(T); known = {d: (k, t) for k, t, d in DIRS}
    return [known.get(d, (d, d)) + (d,) for d in sorted(os.path.basename(x) for x in sum((glob.glob('%s/%s' % (S, l)) for l in LIVE), [])) if d != own]


def ledger_scores():
    """Preserve competing take bars while their per-n files are being replaced."""
    out = {}
    for _, _, d in live_dirs():
        path = '%s/%s/take.tsv' % (S, d)
        try:
            for row in csv.DictReader(open(path), delimiter='\t'):
                n = int(row['n']); score = float(row.get('new') or row.get('score'))
                out[n] = min(out.get(n, float('inf')), score)
        except (OSError, KeyError, ValueError, TypeError):
            continue
    return out


def pending_competitors(seen, ns):
    """An unverified recent replacement delays publication until the next scan."""
    pending = set()
    for _, _, d in live_dirs():
        for n in ns:
            path = '%s/%s/%d.csv' % (S, d, n)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if time.time() - st.st_mtime < 15 and (seen.get(path, [])[:2] != [st.st_mtime_ns, st.st_size] or seen[path][2] is None):
                pending.add(n)
    return pending


def scan(seen, jobs=4, dirs=None, ns=None, settle=True):
    """every top-level N.csv of the watched take dirs -> {n: [(score, kind, tag, path)]}; seen caches the scores"""
    todo = []; found = []
    for kind, tag, d in (DIRS if dirs is None else dirs):
        for p in sorted(glob.glob('%s/%s/*.csv' % (S, d))):
            if not re.match(r'^\d+\.csv$', os.path.basename(p)):
                continue
            if ns is not None and int(os.path.basename(p)[:-4]) not in ns:
                continue
            st = os.stat(p); sig = [st.st_mtime_ns, st.st_size]
            if p in seen and seen[p][:2] == sig:
                found.append((p, kind, tag, seen[p][2])); continue
            if settle and time.time() - st.st_mtime < 15:
                if p in seen and seen[p][2] is not None:
                    found.append((p, kind, tag, seen[p][2]))
                continue                      # preserve the last certified bar during replacement
            todo.append((p, kind, tag, sig))
    if todo:
        with Pool(jobs) as pool:
            res = dict((k, s) for k, s, _ in pool.imap_unordered(cert, [(t[0], t[0]) for t in todo]))
        for p, kind, tag, sig in todo:
            seen[p] = sig + [res.get(p)]
            found.append((p, kind, tag, res.get(p)))
    out = {}
    for p, kind, tag, score in found:
        if score is not None:
            out.setdefault(int(os.path.basename(p)[:-4]), []).append((score, kind, tag, p))
    return out


def load_plan():
    return json.load(open(W + '/plan.json'))


def save_plan(pl):
    tmp = W + '/plan.json.tmp'
    json.dump(pl, open(tmp, 'w'), indent=0); os.rename(tmp, W + '/plan.json')


def kind_of(src):
    if src.startswith('own soft-box'): return 'soft'
    if src.startswith('family_step'): return 'family'
    if src.startswith('family_readers'): return 'readers'
    if src.startswith('modules.py'): return 'modules'
    if src.startswith('fq quench of one border') or 'border_sweep' in src: return 'border'
    if src.startswith('fq quench'): return 'polish'
    if src.startswith('inflate.py'): return 'inflate'
    return 'harvest'


def source_of(n):
    """source and licence of the held n, from the newest results table that names it"""
    ps = glob.glob(LANE + '/results/round*-best-*.tsv')
    for p in sorted(ps, key=lambda p: int(re.search(r'round(\d+)-', p).group(1)), reverse=True) + sorted(glob.glob(LANE + '/results/harvest-best-*.tsv'), reverse=True):
        for r in csv.DictReader(open(p), delimiter='\t'):
            if int(r['n']) == n and r.get('source'):
                return r['source'], r.get('licence') or ''
    return 'the held packing', ''


def prev_passes():
    """{n: [start score]} of the chains of the round before whose two 140 s islands both ended"""
    out = {}
    if not os.path.exists(PREV_W + '/plan.json'):
        return out
    for j in json.load(open(PREV_W + '/plan.json'))['jobs']:
        for b in ('boxC', 'boxD', 'boxE', 'boxA'):     # a job that changed box has its logs on the box that ran it
            d = '%s/%s/run/%d-%s' % (PREV_W, b, j['n'], j['tag'])
            logs = ['%s/soft-%d-best-%d.log' % (d, j['n'], sd) for sd in ((21, 22) if j.get('mode') == 'seed2' else (11, 12))]
            if all(os.path.exists(l) and re.search(r'^end n=', open(l).read(), re.M) for l in logs):
                out.setdefault(j['n'], []).append(j['start'])
    return out


def box_dir(b):
    return '%s/%s' % (W, b)


def push(box, sp, line, tail=False):
    """a start file and a line at the head of a box queue (at its tail with tail); True when both arrived"""
    ins = '{ cat queue.txt; echo "%s"; }' % line if tail else '{ echo "%s"; cat queue.txt; }' % line
    if box not in REMOTE:
        d = box_dir(box); os.makedirs(d + '/starts', exist_ok=True)
        write_rows('%s/starts/%s' % (d, os.path.basename(sp)), rows_of(sp))
        r = subprocess.run(['sh', '-c', 'cd %s && until mkdir qlock 2>/dev/null; do sleep 1; done; %s > queue.tmp; mv queue.tmp queue.txt; rmdir qlock' % (d, ins)])
        return r.returncode == 0
    r1 = subprocess.run(['scp', '-q', '-o', 'ConnectTimeout=10', sp, '%s:%s/starts/' % (REMOTE[box], RDIR)])
    r2 = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', REMOTE[box],
                         'cd %s || exit 1; until mkdir qlock 2>/dev/null; do sleep 1; done; %s > queue.tmp; if ./py qorder.py queue.tmp; then mv queue.tmp queue.txt; else rmdir qlock; exit 1; fi; rmdir qlock' % (RDIR, ins)])
    return not (r1.returncode or r2.returncode)


def unqueue(box, n, tag):
    """take every waiting line of n tag out of a box queue; True when one was there"""
    cmd = ("until mkdir qlock 2>/dev/null; do sleep 1; done; if grep -Eq '^%d %s( |$)' queue.txt; then "
           "grep -Ev '^%d %s( |$)' queue.txt > queue.tmp; mv queue.tmp queue.txt; echo removed; fi; rmdir qlock") % (n, tag, n, tag)
    if box in REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', REMOTE[box], 'cd %s && %s' % (RDIR, cmd)], capture_output=True, text=True)
    else:
        r = subprocess.run(['sh', '-c', 'cd %s && %s' % (box_dir(box), cmd)], capture_output=True, text=True)
    return 'removed' in r.stdout


def stop_run(box, n, tag):
    """round 21: a running chain of n tag stops: a STOP file in its run dir ends the chain before its next leg, and its
    soft process dies now. True when a process of it was there (round 20: 448, 601, 803 and 910 each ran twice at once)"""
    cmd = ("if [ -d run/%d-%s ] && ! grep -Eq 'CHAINEND|^DRY|STOPPED' run/%d-%s/chain.log 2>/dev/null; then touch run/%d-%s/STOP; "
           "pkill -f 'methods_soft.py .* run/%d-%s ' || :; pkill -f 'invent_rest.py .* run/%d-%s ' || :; "
           "pkill -f 'midm_scan.py .*run/%d-%s' || :; pkill -f 'fqjob.py %d %s$' || :; echo stopped; fi") % (
               n, tag, n, tag, n, tag, n, tag, n, tag, n, tag, n, tag)
    if box in REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', REMOTE[box], 'cd %s && %s' % (RDIR, cmd)], capture_output=True, text=True)
    else:
        r = subprocess.run(['sh', '-c', 'cd %s && %s' % (box_dir(box), cmd)], capture_output=True, text=True)
    return 'stopped' in r.stdout


def pick(n, c, held, seen_pass=()):
    """round 19: the start of n from its files c = [(score, kind, tag, path)] of every watched dir. n qualifies when a file
    of some kind is more than MIN_STEP of that kind below held; the start is then the lowest file of n in any dir (the
    family lane's quench of a twoshort file, say). Returns (design kind, (score, kind, tag, path)) or None."""
    c = sorted(c)
    q = [x for x in c if x[0] < held[n] - max(BAR, MIN_STEP.get(x[1], 1e-4))]
    if not q and n in KICKED:
        q = [x for x in c if x[1] == 'midm' and x[0] < held[n] - 1e-5]
    if not q:
        return None
    design = min(q, key=lambda x: (FIRST.index(x[1]) if x[1] in FIRST else 9, x[0]))[1]
    start = min(x for x in q if x[1] == design)
    if start[0] > c[0][0] + SAME:
        return None
    return design, start


def rank_of(design, n, gain, kicked):
    if design in LEAD: return (0, -gain)
    if kicked: return (2, -gain)
    if design in SECOND: return (1, -gain)
    return (3, -gain)


def plan():
    held = held_scores()
    had = prev_passes()
    seen = {}
    if os.path.exists(PREV_W + '/plan.json'):          # the scores of the frozen r19 files the last round certified
        seen = {k: v for k, v in json.load(open(PREV_W + '/plan.json'))['seen'].items() if '-r19/' in k}
    cands = scan(seen, jobs=1, dirs=[x for x in DIRS if x[0] in FIRST])
    os.makedirs(W + '/starts', exist_ok=True)
    jobs = []; done = []; wait = []; reserve = []
    for n in sorted(cands):
        r = pick(n, cands[n], held)
        if r is None:
            continue
        design, (score, kind, tag, p) = r
        if any(abs(x - score) <= SAME for x in had.get(n, [])):
            done.append('%d:%s' % (n, design)); continue
        if design == 'twoshort' and kind == 'twoshort' and not any(x[1] == 'family' for x in cands[n]):
            wait.append(n)                            # round 17: wait for the family lane's quench of a twoshort file
        src, lic = take_meta(os.path.basename(os.path.dirname(p))).get(n, (kind, ''))
        kicked = n in KICKED and held[n] - score <= NEW_STEP
        j = dict(n=n, tag=tag, kind=design, filekind=kind, where='take', start=score, held=held[n], path=p, source=src,
                 licence=lic, mode='short', layout_gain=held[n] - score, kicked=kicked)
        jobs.append(j)
    jobs.sort(key=lambda j: rank_of(j['kind'], j['n'], j['layout_gain'], j['kicked']))
    ks = [j for j in jobs if j['kicked']]             # the kicked midm finds: 3 first, the rest only if 1 of 3 finds
    for j in ks[3:]:
        jobs.remove(j); reserve.append(j)
    jobs = [j for j in jobs if j['n'] not in wait]
    for j in jobs:
        write_rows('%s/starts/%d-%s.csv' % (W, j['n'], j['tag']), rows_of(j['path']))
    q = {b: [] for b in list(REMOTE) + ['boxA']}
    for i, j in enumerate(jobs):
        j['box'] = START_SLOTS[i % len(START_SLOTS)]; j['rank'] = i; j['added'] = 'plan'
        q[j['box']].append('%d %s short' % (j['n'], j['tag']))
    for b in q:
        open('%s/queue-%s.txt' % (W, b), 'w').write(''.join(l + '\n' for l in q[b]))
    save_plan(dict(jobs=jobs, seen=seen, had=done, wait=wait, reserve=reserve, t0=time.time(),
                   had_scores={str(n): v for n, v in had.items()}, kicked_go=False))
    for j in jobs:
        print('%3d %-4s n=%d %-6s %-9s file %-9s start %.12f held %.12f step %.3e%s' % (
            j['rank'], j['box'], j['n'], j['tag'], j['kind'], j['filekind'], j['start'], j['held'], j['layout_gain'], ' kicked' if j['kicked'] else ''))
    print('soft previous round passed this packing already (%d): %s' % (len(done), ' '.join(done)))
    print('twoshort files that wait for the family quench (%d): %s' % (len(wait), ' '.join(map(str, wait))))
    print('kicked midm in reserve (%d): %s' % (len(reserve), ' '.join(str(j['n']) for j in reserve)))
    print('jobs', len(jobs), {b: len(q[b]) for b in q})


def active():
    p = W + '/active.txt'
    return open(p).read().split() if os.path.exists(p) else sorted(set(START_SLOTS))


def unique_tag(base, tags):
    candidate = base
    index = 0
    while candidate in tags:
        index += 1
        candidate = base + str(index)
    return candidate


def watch():
    pl = load_plan(); held = held_scores(); jobs = pl['jobs']; n0 = len(jobs)
    cands = scan(pl['seen'], jobs=1, dirs=[x for x in DIRS if x[0] in FIRST])
    new = []
    for n in sorted(cands):
        r = pick(n, cands[n], held)
        if r is None:
            continue
        design, (score, kind, tag, p) = r
        if n in KICKED and held[n] - score <= NEW_STEP and not pl.get('kicked_go'):
            continue                                  # the rest of the kicked midm finds wait for a find of the sample
        own = json.load(open(W + '/kept.json')) if os.path.exists(W + '/kept.json') else {}
        mine = min([j['start'] for j in jobs if j['n'] == n] + pl.get('had_scores', {}).get(str(n), [])
                   + ([own[str(n)]] if str(n) in own else []) or [9.0])
        if str(n) in own and kind == 'polish':
            continue                                  # round 20: the polish quench of our own file found nothing in 2 starts
        if not score < mine - SAME:
            continue
        if design == 'twoshort' and kind == 'twoshort' and not any(x[1] == 'family' for x in cands[n]) \
                and time.time() - max(os.stat(p).st_mtime, pl.get('t0', 0)) < 1800:
            continue                                  # wait up to 30 min for the family lane's quench of a twoshort file
        new.append((-rank_of(design, n, held[n] - score, False)[0], held[n] - score, n, score, design, tag, p, mine))
    slots = [b for b in WATCH_SLOTS if b in active()]; skips = {}
    # the slots wait for files most of the round and an idle worker takes a line within 10 s of its push: push the
    # largest step first (round 16: a 1e-10 step pushed first ran ahead of a 4.2e-5 step)
    for first, gain, n, score, kind, tag, p, mine in sorted(new, reverse=True):
        tags = {j['tag'] for j in jobs if j['n'] == n}
        t = unique_tag(tag, tags)
        src, lic = take_meta(os.path.basename(os.path.dirname(p))).get(n, (kind, ''))
        box = slots[sum(1 for j in jobs if j['added'] != 'plan') % len(slots)]
        sp = '%s/starts/%d-%s.csv' % (W, n, t); write_rows(sp, rows_of(p))
        if not push(box, sp, '%d %s short' % (n, t), tail=kind not in FIRST):
            print('WATCH push failed', n, t, box, flush=True); continue
        jobs.append(dict(n=n, tag=t, kind=kind, where='take', start=score, held=held[n], path=p, source=src, licence=lic, mode='short',
                         layout_gain=held[n] - score, box=box, rank=len(jobs), added=time.strftime('%H:%M:%S', time.gmtime())))
        print('WATCH new n=%d %s %s start %.12f held %.12f (mine before %.12f) -> %s %s' % (n, t, kind, score, held[n], mine, box, p), flush=True)
        for j in jobs[:-1]:                           # an older start of this n that has not begun is dropped
            if j['n'] == n and not j.get('skipped') and j['start'] > score + SAME and unqueue(j['box'], n, j['tag']):
                skips[(n, j['tag'])] = 'replaced before it began by %d %s, a lower file of the %s lane' % (n, t, kind)
                print('WATCH drop n=%d %s on %s: %s' % (n, j['tag'], j['box'], skips[(n, j['tag'])]), flush=True)
            elif j['n'] == n and not j.get('skipped') and j['start'] > score + SAME and stop_run(j['box'], n, j['tag']):
                skips[(n, j['tag'])] = 'stopped while it ran by %d %s, a lower file of the %s lane' % (n, t, kind)
                print('WATCH stop n=%d %s on %s: %s' % (n, j['tag'], j['box'], skips[(n, j['tag'])]), flush=True)
    now = load_plan()                                 # the scan takes minutes: keep the edits made to plan.json meanwhile
    now['jobs'] += jobs[n0:]; now['seen'] = pl['seen']
    for j in now['jobs']:
        if (j['n'], j['tag']) in skips: j['skipped'] = skips[(j['n'], j['tag'])]
    save_plan(now)
    print('WATCH %s new %d jobs %d' % (time.strftime('%H:%M:%S', time.gmtime()), len(new), len(jobs)), flush=True)


NEAR_ONLY_OK = ('refused parent', 'missing source record', 'missing donor file', 'unreadable pinned donor groups')


def add(n, path, kind, box, mode='short', prefix='x', near_only=False):
    """a start from any file of n that a lane hands over (the handoff log of the round), at the head of a box queue. A file that
    does not certify (or sits above the held score) counts from the held score: a result must beat both anyway."""
    global LAST_ADMISSION_REASON
    LAST_ADMISSION_REASON = ''
    from provenance import trace
    proof = trace(path, n)
    if proof['ok']:
        import r28check
        why = r28check.withdrawn_in(proof, path)
        if why:
            LAST_ADMISSION_REASON = why
            print('REFUSE withdrawn', path, why, flush=True)
            return False
    if not proof['ok']:
        # Round 27: a top-level take file of a live lane that our walk cannot finish (a parent named by a live path that
        # its lane rewrote, or a parent our imported readers still refuse) may start a search whose finds go back to that
        # lane as near files only. An excluded source marker or path still refuses it.
        from provenance import r26_check
        live = re.search(r'/take-[a-z0-9-]+-r%d/\d+\.csv$' % RN, path)
        if not (near_only and live and proof.get('reason') in NEAR_ONLY_OK and
                r26_check(proof, proof.get('source', '') or '', proof.get('licence', '') or '') is None):
            LAST_ADMISSION_REASON = proof['reason']
            print('REFUSE ancestry', path, proof['reason'], flush=True)
            return False
        proof = dict(proof, near_only=True)
        print('NEAR-ONLY admit', path, proof['reason'], flush=True)
    if proof['ok']:
        import r28check
        if r28check.public_first(proof, path) and not reaches_held(proof, path):
            LAST_ADMISSION_REASON = 'round 31: public-first tree with no held row (round 30 assembler dropped 910 and 972 at 1e-2)'
            print('REFUSE', path, LAST_ADMISSION_REASON, flush=True)
            return False
    if n in OUT_N and not (proof.get('ok') and reaches_held(proof, path)):
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n
        print('REFUSE', path, LAST_ADMISSION_REASON, flush=True)
        return False
    isha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    who = claimed_by_other(isha) if mode in ('kick', 'lpq', 'lk', 'deep') else None    # round 31: the claim rule is for kicks
    if who:
        LAST_ADMISSION_REASON = 'claimed: ' + who
        print('REFUSE claimed', path, who, flush=True)
        return False
    pl = load_plan(); held = held_scores(); jobs = pl['jobs']
    source_policy = policy.classify(proof.get('source',''), proof.get('licence',''), proof)
    reference = policy.reference(n, source_policy, held[n])
    _, score, _ = cert((path, path))
    start = reference if score is None or score > reference else score
    tags = {j['tag'] for j in jobs if j['n'] == n}
    t = unique_tag(prefix + kind[:3], tags)
    sp = '%s/starts/%d-%s.csv' % (W, n, t); write_rows(sp, rows_of(path))
    if not push(box, sp, '%d %s %s' % (n, t, mode), tail=kind not in FIRST and '/near/' in path):
        print('ADD push failed', n, t, box); return
    # the source and licence of the lane's take table now: a lane may drop the n from its table later (round 16: modules 549)
    src, lic = donor_source(path, n, ('%s lane handoff %s; source recorded in %s/%s/take.tsv and avenues/%s.md' % (kind, path, S, source_dir(path), 'zones' if kind == 'corners' else kind), 'own design; upstream source as recorded by the donor lane'))
    jobs.append(dict(n=n, tag=t, kind=kind, where='take', start=start, held=held[n], path=path, source=src,
                     licence=lic, ancestry=store_ancestry(proof), source_policy=source_policy, mode=mode, layout_gain=held[n] - start, box=box, rank=len(jobs),
                     near_only=bool(proof.get('near_only')),
                     start_sha256=hashlib.sha256(open('%s/starts/%d-%s.csv' % (W, n, t), 'rb').read()).hexdigest(),
                     input_sha256=hashlib.sha256(open(path, 'rb').read()).hexdigest(),
                     added=time.strftime('%H:%M:%S', time.gmtime()), file_score=score))
    save_plan(pl)
    if mode in ('kick', 'lpq', 'lk', 'deep'):    # round 31: an island is not a kick; its kick leg runs only from its own find
        post_claim(n, isha, path, mode)
    print('ADD n=%d %s %s file score %s held %.12f start %.12f -> %s %s' % (n, t, kind, score, held[n], start, box, path))
    return True


# Round 31 lesson b: one kick per start. A start whose exact bytes another lane claimed in the last 60 minutes is skipped,
# and every start we queue gets a claim line with its sha256 (our chains end in 900 s kick legs).
OUT_N = (582, 972)
HELD_MARKS = ('round23-2026-11-13a.csv', 'round23-2026-11-13b.csv', 'round24-2026-11-13a.csv', 'round25-2026-11-14b.csv',
              'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv', 'round28-2026-11-15b.csv', 'round29-2026-11-15b.csv',
              'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv', 'round32-2026-11-16a.csv')


def reaches_held(proof, path=None):
    """True when the trace names a held file (a row of a file we submitted): our own layout, no share test."""
    text = json.dumps(proof, default=str) + ' ' + (path or '')
    return any(m in text for m in HELD_MARKS)
CLAIM_TTL = 3600


def claimed_by_other(sha):
    import calendar
    try:
        lines = open(HANDOFF).read().splitlines()
    except OSError:
        return None
    now = time.time()
    for line in lines:
        if 'claim' not in line.lower():
            continue
        # other lanes write the full sha256 or a prefix of 12 to 16 hex digits (rebuild, border, backlog tags)
        if sha not in line and not any(len(x) >= 12 and sha.startswith(x) for x in re.findall(r'[0-9a-f]{12,64}', line)):
            continue
        m = re.match(r'(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)', line)
        if not m:
            continue
        lane = re.match(r'\S+\s+(?:\S+\s+)?([a-z0-9-]+)\s*->', line)
        if lane and lane[1] == 'soft':
            continue
        t = calendar.timegm(time.strptime(m[1] + ' ' + m[2], '%Y-%m-%d %H:%M:%S'))
        if now - t <= CLAIM_TTL:
            return line[:160]
    return None


def post_claim(n, sha, path, mode):
    what = ('150 s invent_rest.py lkick legs while a leg moves 1e-8 of side, up to 8, then fq' if mode == 'lk'
            else 'one unprobed 900 s midm_scan kick,lkick seed of the held round 32 a row (shared deep-kick queue), legs only while it moves, then the full fq loop' if mode == 'deep'
            else 'island or kick legs, then fq')
    line = '%s soft -> all: claims kick n=%d sha256=%s, start %s (soft %s chain: %s)\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sha, path, mode, what)
    with open(HANDOFF, 'a') as f:
        f.write(line)


def add_pinned(n, path, kind, box, mode, prefix, proof, source, licence, reopen=False):
    """Round 27: a start whose ancestry was traced by hand over pinned snapshots (proof: the stored dict, ok True).
    reopen: the start itself is also a result (W/cq/run/N-TAG/raw), and a result counts against the bar, not the start."""
    if not proof.get('ok'):
        print('REFUSE pinned', path, proof.get('reason')); return False
    from provenance import r26_check
    why = r26_check(proof, source, licence)
    if why:
        print('REFUSE pinned', path, why); return False
    pl = load_plan(); held = held_scores(); jobs = pl['jobs']
    rows = rows_of(path)
    _, score, _ = cert((path, path))
    if score is None or len(rows) != n:
        print('REFUSE pinned', path, 'does not certify'); return False
    t = unique_tag(prefix + kind[:3], {j['tag'] for j in jobs if j['n'] == n})
    sp = '%s/starts/%d-%s.csv' % (W, n, t); write_rows(sp, rows)
    if reopen:
        raw = '%s/cq/run/%d-%s/raw' % (W, n, t); os.makedirs(raw, exist_ok=True)
        write_rows('%s/%d-reopen-0.csv' % (raw, n), rows)
    if not push(box, sp, '%d %s %s' % (n, t, mode)):
        print('ADD push failed', n, t, box); return False
    sp_ = policy.classify(source, licence, proof)
    pl = load_plan()
    pl['jobs'].append(dict(n=n, tag=t, kind=kind, where='take', start=score, held=held[n], path=path, source=source,
                           licence=licence, ancestry=store_ancestry(proof), source_policy=sp_, mode=mode,
                           layout_gain=held[n] - score, box=box, rank=len(pl['jobs']), added=time.strftime('%H:%M:%S', time.gmtime()),
                           file_score=None if reopen else score, monitor_bar=held[n], reopened=bool(reopen)))
    save_plan(pl)
    print('ADD pinned n=%d %s %s score %.12f held %.12f -> %s %s' % (n, t, kind, score, held[n], box, path), flush=True)
    return True


def split(a, b):
    """every second waiting line of box a's queue goes to box b, with its start file; plan.json follows"""
    def run(box, cmd):
        if box in REMOTE:
            return subprocess.run(['ssh', '-o', 'ConnectTimeout=10', REMOTE[box], 'cd %s && %s' % (RDIR, cmd)], capture_output=True, text=True)
        return subprocess.run(['sh', '-c', 'cd %s && %s' % (box_dir(box), cmd)], capture_output=True, text=True)
    lock = 'until mkdir qlock 2>/dev/null; do sleep 1; done; '
    r = run(a, lock + "awk 'NR % 2 == 0' queue.txt > moved.txt; awk 'NR % 2 == 1' queue.txt > queue.tmp; mv queue.tmp queue.txt; rmdir qlock; cat moved.txt")
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    pl = load_plan(); ok = 0
    for line in reversed(lines):                      # pushed to the head one by one: the last pushed is first
        f = line.split(); n, tag = int(f[0]), f[1]
        if push(b, '%s/starts/%d-%s.csv' % (W, n, tag), line):
            ok += 1
            for j in pl['jobs']:
                if (j['n'], j['tag']) == (n, tag): j['box'] = b
        else:
            print('SPLIT push failed, line lost from both queues:', line)
    save_plan(pl)
    print('SPLIT %s -> %s: %d of %d lines moved: %s' % (a, b, ok, len(lines), '; '.join(lines)))


def quench_complete(j, md5):
    qp = W + '/certquench.json'
    pending = json.load(open(qp)) if os.path.exists(qp) else {}
    q = pending.get(j.get('cq_origin') or md5)
    if not q:
        return False
    log = '%s/%s/run/%d-%s/chain.log' % (W, q['box'], q['n'], q['tag'])
    return os.path.exists(log) and 'CHAINEND' in open(log).read() and re.search(
        r'^FQCHECK .* successful [1-9]', open(log).read(), re.M) is not None


def certified_quench(j, md5):
    """Queue a float-safe file on its worker. Return true after that quench finishes."""
    qp = W + '/certquench.json'
    pending = json.load(open(qp)) if os.path.exists(qp) else {}
    if j.get('cq_origin'):
        md5 = j['cq_origin']
    if md5 not in pending:
        if os.path.exists(W + '/REMOTES_CLEAN'):
            return False
        tag = 'cert' + md5[:12]
        sp = '%s/starts/%d-%s.csv' % (W, j['n'], tag)
        write_rows(sp, rows_of('%s/cert/%s.csv' % (W, md5)))
        if not push(j['box'], sp, '%d %s certified' % (j['n'], tag)):
            return False
        pending[md5] = dict(box=j['box'], n=j['n'], tag=tag)
        json.dump(pending, open(qp + '.tmp', 'w')); os.rename(qp + '.tmp', qp)
        print('CERTQUENCH queued', j['n'], tag, j['box'], flush=True)
    q = pending[md5]
    log = '%s/%s/run/%d-%s/chain.log' % (W, q['box'], q['n'], q['tag'])
    return os.path.exists(log) and 'CHAINEND' in open(log).read() and re.search(r'^FQCHECK .* successful [1-9]', open(log).read(), re.M) is not None


def second_quench(j, md5):
    """Round 27: one more fq quench from the certified file of a kept row that came out of a certified quench (depth 1).
    It does not hold the row back: the next collect reads its steps through certquench.json like the first quench."""
    if j.get('cq_depth', 0) != 1 or os.path.exists(W + '/REMOTES_CLEAN'):
        return
    qp = W + '/certquench.json'
    pending = json.load(open(qp)) if os.path.exists(qp) else {}
    if md5 in pending:
        return
    tag = 'cert' + md5[:12]
    sp = '%s/starts/%d-%s.csv' % (W, j['n'], tag)
    write_rows(sp, rows_of('%s/cert/%s.csv' % (W, md5)))
    if push(j['box'], sp, '%d %s certified' % (j['n'], tag)):
        pending[md5] = dict(box=j['box'], n=j['n'], tag=tag, second=True)
        json.dump(pending, open(qp + '.tmp', 'w')); os.rename(qp + '.tmp', qp)
        print('CERTQUENCH second queued', j['n'], tag, j['box'], flush=True)


PRV_SHARE = {}


def _share_values(it):
    # round 32 rule 2: the share that counts is the one against 1105 versions that are not our own seed (share31.py
    # max_nonown; 0.0 when every version of the row is our own seed)
    if isinstance(it.get('max_nonown'), dict):
        return [float(v) for v in it['max_nonown'].values()]
    out = []
    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ('0.001', '0.01') and isinstance(x, (int, float)):
                    out.append(float(x))
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(it.get('share', it))
    return out


def prv_share_out(n, path):
    """Round 27 rule b: a layout is out when 0.4 or more of its squares lie within 1e-3 of the prvsiyan best-of-1105 row
    of n (classfill tools/classfill/round26/prvsim26.py, run as a script on a data file)."""
    key = hashlib.md5(open(path, 'rb').read()).hexdigest()
    if key not in PRV_SHARE:
        # round 31: the round 30 assembler's share30.py (ICP, max of 1e-3 and 1e-2 over every harvested 1105 version)
        d = W + '/share'; os.makedirs(d, exist_ok=True)
        items = '%s/item-%s.json' % (d, key); outp = '%s/out-%s.json' % (d, key)
        json.dump([dict(label='soft33-%d' % n, path=path, n=n)], open(items, 'w'))
        r = subprocess.run([sys.executable, '-I', S + '/take-assemble-r31/scripts/share31.py', items, outp],
                           capture_output=True, text=True, timeout=1800)
        try:
            res = json.load(open(outp))
            res = res.get('items', res) if isinstance(res, dict) else res
            vals = [v for it in res if isinstance(it, dict) and it.get('n') == n for v in _share_values(it)]
            PRV_SHARE[key] = max(vals) if vals else None
        except (OSError, ValueError):
            PRV_SHARE[key] = None
        with open(W + '/prv-share.tsv', 'a') as f:
            f.write('%d\t%s\t%s\t%s\n' % (n, path, PRV_SHARE[key], r.stdout.strip()[-200:]))
    v = PRV_SHARE[key]
    if v is None:
        return 'prvsiyan share not measured'
    return 'prvsiyan 1105 share %.3f >= 0.4' % v if v >= 0.4 else None


def export_near(files, cache, held, others):
    """Hand over legal soft improvements that remain within .015 side of the current bar."""
    import math
    meta_path = W + '/near-exported.json'
    saved = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    best = {}
    for j, p, md5 in files:
        n = j['n']; score = cache.get(md5)
        start = j.get('file_score') if j.get('file_score') is not None else j['start']
        bar = min(held[n], others.get(n, held[n]))
        no = bool(j.get('near_only'))
        if score is None or score >= start - BAR or (score < bar - BAR and not no):
            continue
        if (score - bar) * math.sqrt(n) > .015:
            continue
        if n not in best or score < best[n][0]:
            best[n] = (score, j, md5, bar)
    os.makedirs(T + '/near', exist_ok=True)
    for n, (score, j, md5, bar) in best.items():
        if str(n) in saved and score >= saved[str(n)]['score'] - BAR:
            continue
        path = '%s/near/%d-soft-r33.csv' % (T, n)
        sp_ = '%s/starts/%d-%s.csv' % (W, n, j['tag'])
        meta = dict(n=n, score=score, source=j['source'], licence=j['licence'], input_file=j['path'], start_snapshot=sp_,
                    start_sha256=hashlib.sha256(open(sp_, 'rb').read()).hexdigest() if os.path.exists(sp_) else None,
                    near_only=bool(j.get('near_only')))
        sidecar = os.path.splitext(path)[0] + '.json'
        with open(sidecar + '.tmp', 'w') as f:
            json.dump(meta, f, indent=2)
        os.rename(sidecar + '.tmp', sidecar)
        write_rows(path, rows_of('%s/cert/%s.csv' % (W, md5)))
        saved[str(n)] = dict(n=n, score=score, side=(1 + score) * math.sqrt(n),
                            margin=(score - bar) * math.sqrt(n), source=j['source'], licence=j['licence'], input=j['path'])
        line = '%s soft -> all: legal soft near n=%d side=%.12f margin=+%.3e, from %s %s, %s\n' % (
            time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime()), n, (1 + score) * math.sqrt(n),
            (score - bar) * math.sqrt(n), j['kind'], j['tag'], path)
        if j.get('near_only'):
            line = ('%s soft -> %s,quench,backlog: near-only find n=%d score %.12f (%+.3e of score against the live bar) from an '
                    'island on your take file %s (byte snapshot %s in the sidecar); our walk stops at "%s", so walk it and publish '
                    'it yourselves, %s\n') % (time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime()), j['kind'], n, score, score - bar,
                    j['path'], sp_, load_ancestry(j.get('ancestry')).get('reason', ''), path)
        with open(HANDOFF, 'a') as f: f.write(line)
        with open(T + '/STATE.txt', 'a') as f: f.write(line.rstrip() + '; deadline 00:15Z\n')
        print('NEAR', line.strip(), flush=True)
    if saved:
        json.dump(saved, open(meta_path + '.tmp', 'w')); os.rename(meta_path + '.tmp', meta_path)
        fields = ('n', 'score', 'side', 'margin', 'source', 'licence', 'input')
        with open(T + '/near/near.tsv.tmp', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t'); writer.writeheader()
            writer.writerows(saved[k] for k in sorted(saved, key=int))
        os.rename(T + '/near/near.tsv.tmp', T + '/near/near.tsv')


def walk_gate(n, j):
    """Round 29: the assembler-style walk (backlog's quench_walk.check) on the input file of a job before its row is kept.
    At 07:10Z backlog refused our 747 (input forensics r29 near/747-rect.csv): its tree reaches the held 800 of round 23 and
    the r24 donor 800-7a2b family that the round 28 assembler marked OUT (a 639 and readers 858 donor chain), which our own
    trace (pinned forensics ancestry: roots 590 and k123 r23 917) did not show. Cached by the sha256 of the input bytes.
    W/walk-allow.json {sha256: reason} lets a hit we traced by hand as a false reading pass; W/exclude.json {"N:TAG": reason}
    drops a job outright."""
    ex = json.load(open(W + '/exclude.json')) if os.path.exists(W + '/exclude.json') else {}
    if '%d:%s' % (n, j['tag']) in ex:
        return 'excluded by hand: ' + ex['%d:%s' % (n, j['tag'])]
    path = j.get('path', '')
    if not os.path.isfile(path):
        return None
    sha = j.get('input_sha256') or hashlib.sha256(open(path, 'rb').read()).hexdigest()
    cp = W + '/walk-cache.json'
    cache = json.load(open(cp)) if os.path.exists(cp) else {}
    if sha not in cache:
        start = '%s/starts/%d-%s.csv' % (W, n, j['tag'])
        # the walk reads the records beside the file, so it walks the input path; the pinned start bytes must match it
        if os.path.exists(start) and hashlib.sha256(open(start, 'rb').read()).hexdigest() != hashlib.sha256(open(path, 'rb').read()).hexdigest():
            print('walk gate: input %s changed since the start was pinned; walking the current file' % path, flush=True)
        # walkcheck.py: quench_walk.check with the 745/858 rule narrowed as main's 07:34:54Z note asks
        r = subprocess.run([sys.executable, '-I', os.path.dirname(os.path.abspath(__file__)) + '/walkcheck.py', path],
                           capture_output=True, text=True, timeout=900)
        try:
            res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            res = {'clean': False, 'hits': ['walk failed: ' + (r.stderr or '')[-300:]]}
        cache[sha] = dict(clean=bool(res.get('clean')), hits=res.get('hits', [])[:12], path=path, n=n)
        json.dump(cache, open(cp + '.tmp', 'w'), indent=0); os.rename(cp + '.tmp', cp)
    c = cache[sha]
    allow = json.load(open(W + '/walk-allow.json')) if os.path.exists(W + '/walk-allow.json') else {}
    if c['clean'] or sha in allow:
        return None
    return 'assembler-style walk (quench_walk.check) refuses the input %s: %s' % (path, ' | '.join(h[:160] for h in c['hits'][:4]))


def collect(fetch=True):
    pl = load_plan(); held = held_scores(); jobs = pl['jobs']
    for j in jobs:
        if 'source_policy' not in j:
            j['source_policy'] = policy.classify(j['source'], j['licence'], load_ancestry(j.get('ancestry')))
        ref = policy.reference(j['n'], j['source_policy'], held[j['n']])
        fs = j.get('file_score')
        j['effective_start'] = ref if fs is None else min(ref, fs)
    if fetch:
        for b, h in REMOTE.items():
            os.makedirs('%s/%s/run' % (W, b), exist_ok=True)
            r = subprocess.run(['rsync', '-a', '--exclude', 'softfree', '-e', 'ssh -o ConnectTimeout=10', '%s:%s/run/' % (h, RDIR), '%s/%s/run/' % (W, b)])
            r2 = subprocess.run(['rsync', '-a', '--include=queue.txt', '--include=taken.txt', '--include=drv.out', '--include=deadline', '--include=fqdeadline',
                                 '--exclude=*', '-e', 'ssh -o ConnectTimeout=10', '%s:%s/' % (h, RDIR), '%s/%s/' % (W, b)])
            if r.returncode or r2.returncode:
                print('FETCH FAILED', b)
    os.makedirs(W + '/cert', exist_ok=True)
    cpath = W + '/cert-cache.json'
    cache = json.load(open(cpath)) if os.path.exists(cpath) else {}
    files = []
    for j in jobs:
        for b in list(REMOTE) + ['boxA', 'cq']:        # a job that changed box may have files on both; cq: quench of the take file
            for p in sorted(glob.glob('%s/%s/run/%d-%s/raw/%d-*.csv' % (W, b, j['n'], j['tag'], j['n']))):
                md5 = hashlib.md5(open(p, 'rb').read()).hexdigest()
                files.append((j, p, md5))
    qp = W + '/certquench.json'
    pending = json.load(open(qp)) if os.path.exists(qp) else {}
    i = 0; walked = set()
    while i < len(files):
        j, p, md5 = files[i]; i += 1
        q = pending.get(md5)
        if q and (md5, j.get('cq_depth', 0)) not in walked:
            walked.add((md5, j.get('cq_depth', 0)))
            log = '%s/%s/run/%d-%s/chain.log' % (W, q['box'], q['n'], q['tag'])
            if os.path.exists(log) and 'CHAINEND' in open(log).read():
                for cp in glob.glob('%s/%s/run/%d-%s/raw/*.csv' % (W, q['box'], q['n'], q['tag'])):
                    if j.get('cq_depth', 0) >= 2:
                        break
                    cj = dict(j, cq_origin=md5, cq_depth=j.get('cq_depth', 0) + 1)
                    files.append((cj, cp, hashlib.md5(open(cp, 'rb').read()).hexdigest()))
    todo = {}
    for j, p, md5 in files:
        if md5 not in cache:
            todo[md5] = p
    if todo:
        with Pool(1) as pool:
            for md5, score, fr in pool.imap_unordered(cert, list(todo.items())):
                cache[md5] = score
                if fr is not None:
                    write_rows('%s/cert/%s.csv' % (W, md5), fr)
        tmp = cpath + '.tmp'; json.dump(cache, open(tmp, 'w')); os.rename(tmp, cpath)
    others = ledger_scores()
    lp = W + '/live-seen.json'
    live_seen = json.load(open(lp)) if os.path.exists(lp) else dict(pl['seen'])
    if files:
        for n, c in scan(live_seen, jobs=1, dirs=live_dirs(), ns={j['n'] for j, p, md5 in files}, settle=False).items():
            others[n] = min(others.get(n, float('inf')), min(x[0] for x in c))
        json.dump(live_seen, open(lp + '.tmp', 'w')); os.rename(lp + '.tmp', lp)
    unsettled = pending_competitors(live_seen, {j['n'] for j, p, md5 in files})
    export_near(files, cache, held, others)
    best = {}
    for j, p, md5 in files:
        score = cache.get(md5); n = j['n']
        untraced = not j.get('ancestry', {}).get('ok')
        if untraced and not j.get('near_only'):
            print('drop untraced ancestry', n, j['tag']); continue
        if score is None:
            print('drop', n, j['tag'], 'not certified', p); continue
        reference = policy.reference(n, j['source_policy'], held[n])
        if j['source_policy']['status'] != 'none' and not policy.LIFTED:
            print('drop seed or unresolved ancestry', n, j['tag']); continue
        if not (score < reference - BAR and score < j['effective_start'] - BAR):
            print('drop', n, j['tag'], 'score', score, 'held', held[n], 'start', j['start'], os.path.basename(p)); continue
        if untraced:
            # round 31: a near-only start (a fresh take row of a lane whose records our trace cannot finish) counts when the
            # assembler-style walk (quench_walk.check through walkcheck.py, round 31 share policy included) passes its input
            why = walk_gate(n, j)
            if why:
                print('drop untraced ancestry (walk)', n, j['tag'], why[:160]); continue
            j['promoted'] = 'near-only start, assembler-style walk clean'
            print('PROMOTE near-only', n, j['tag'], 'walk clean', flush=True)
        group = 0 if False and j['source_policy']['status']=='none' else 1
        previous_group = (0 if False and best[n][1]['source_policy']['status']=='none' else 1) if n in best else 2
        if n not in best or (group, score) < (previous_group, best[n][0]):
            best[n] = (score, j, p, md5)
    kept = {}
    for n, (score, j, p, md5) in sorted(best.items()):
        if n in unsettled:
            print('pending competing file replacement', n, flush=True)
            continue
        competing = policy.floor(n, j['source_policy'], held[n], others)
        if not score < competing - BAR:   # round 17: a result must beat every live take dir, a tie is not a gain
            print('superseded', n, j['tag'], 'score', score, 'another lane holds', others[n]); continue
        if not certified_quench(j, md5):
            print('pending certified quench', n, md5, flush=True)
            ready = [(cache[m], jj, pp, m) for jj, pp, m in files if jj['n'] == n
                     and cache.get(m) is not None and (policy.LIFTED or jj['source_policy']['status'] == 'none')
                     and cache[m] < policy.reference(n, jj['source_policy'], held[n]) - BAR
                     and cache[m] < jj['effective_start'] - BAR
                     and cache[m] < policy.floor(n, jj['source_policy'], held[n], others) - BAR
                     and quench_complete(jj, m)]
            if not ready:
                continue
            score, j, p, md5 = min(ready, key=lambda x: x[0])
            print('keep completed certificate while lower candidate waits', n, score, flush=True)
        import r28check
        anc = load_ancestry(j.get('ancestry'))
        # Rule change of 00:19:03Z: the output share test only for rows whose first source is a fetched public file.
        why = prv_share_out(n, '%s/cert/%s.csv' % (W, md5)) if (r28check.public_first(anc, j.get('path', ''))
                                                                and not reaches_held(anc, j.get('path', ''))
                                                                and not j.get('promoted')) else None
        if not why:
            why = r28check.publish_check(anc, j.get('path', ''), W)
        if not why:
            why = walk_gate(n, j)
        if why:
            print('drop', n, j['tag'], why, flush=True); continue
        second_quench(j, md5)
        kept[n] = (score, j, p, md5)
    tot = 0.0; ptot = 0.0; otot = 0.0
    for n, (score, j, p, md5) in kept.items():
        write_rows('%s/%d.csv' % (T, n), rows_of('%s/cert/%s.csv' % (W, md5)))
    for p in glob.glob(T + '/*.csv'):
        if int(os.path.basename(p)[:-4]) not in kept:
            os.remove(p)
    tmp = T + '/take.tsv.tmp'
    with open(tmp, 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\tstart\tpolish_gain\n')
        for n, (score, j, p, md5) in kept.items():
            step = 'own soft-box search (methods_soft.py) and fq quench' if '-fq-' in os.path.basename(p) else 'own soft-box search (methods_soft.py)'
            if '-sfq-' in os.path.basename(p):
                step = 'own soft-box search (methods_soft.py, a soft-free member below the legal side) and fq quench of that member (sfq.py)'
            src, lic = j['source'], j['licence']
            original = '%s/starts/%d-%s.csv' % (W, n, j['tag'])
            if j['where'] == 'take' and os.path.exists(j['path']) and open(original, 'rb').read() == open(j['path'], 'rb').read():
                src, lic = donor_source(j['path'], n, (src, lic))
            lic = (lic or 'own search') + '; ' + policy.label(j['source_policy'])
            # Round 28: W/source-notes.json, keyed "N:TAG", adds the upstream chain the lane resolved by hand from the round
            # tables (held parts of a composition) and replaces the licence cell with the named terms.
            sn = json.load(open(W + '/source-notes.json')) if os.path.exists(W + '/source-notes.json') else {}
            note = sn.get('%d:%s' % (n, j['tag']))
            if note:
                src = src + '; ' + note['source']
                lic = note['licence']
            h.write('%d\t%r\t%r\t%.3e\t%s from %s\t%s\t%r\t%.3e\n' % (n, held[n], score, held[n] - score, step, src + ' (input ' + j['path'] + '; source table ' + S + '/' + source_dir(j['path']) + '/take.tsv)' , lic, j['start'], j['start'] - score))
            tot += held[n] - score; ptot += j['start'] - score
            otot += policy.floor(n, j['source_policy'], held[n], others) - score
            print('keep n=%d %s %s held %.12f start %.12f new %.12f gain %.3e own gain %.3e %s' % (
                n, j['tag'], j['kind'], held[n], j['start'], score, held[n] - score, j['start'] - score, os.path.basename(p)))
    os.rename(tmp, T + '/take.tsv')
    print('kept %d n, gain against held %r, own gain on top of the starts %r, gain over all other takes %r' % (len(kept), tot, ptot, otot))
    json.dump(dict(improved_n=len(kept), held_gain=tot, start_gain=ptot, other_gain=otot), open(W + '/totals.json', 'w'))
    # the interim take: one line in the handoff log for each n that is new or lower since the collect before
    kp = W + '/kept.json'
    before = json.load(open(kp)) if os.path.exists(kp) else {}
    now = {str(n): kept[n][0] for n in kept}
    with open(HANDOFF, 'a') as h:
        for n, (score, j, p, md5) in kept.items():
            if str(n) not in before or score < before[str(n)] - BAR:
                h.write('%s soft -> all: certified soft-box layout n=%d score %.12f, %.3e below held, from the %s %s, %s/%d.csv\n' % (
                    time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime()), n, score, held[n] - score, j['kind'], j['where'], T, n))
                print('HANDOFF n=%d' % n)
    json.dump(now, open(kp + '.tmp', 'w')); os.rename(kp + '.tmp', kp)


def cq(n, tag):
    """the fq quench (fqjob.py) of the take file T/N.csv, the certified rows of the best result of n so far, in a fresh
    dir W/cq/N-TAG-K on boxA. A quench from the raw rows can stop at exact contacts where the same quench from the
    float-safe rows (centres scaled apart to a 2.2e-11 gap) goes on. Its steps land in W/cq/run/N-TAG/raw as N-fq-cK-J.csv,
    and collect reads W/cq/run like a box. Round 15: nothing on 746 and 802 past the float-safe scaling (1.4e-9 of side)."""
    out = '%s/cq/run/%d-%s/raw' % (W, n, tag); os.makedirs(out, exist_ok=True)
    k = len(glob.glob('%s/cq/%d-%s-*' % (W, n, tag))) + 1
    d = '%s/cq/%d-%s-%d' % (W, n, tag, k); os.makedirs(d + '/starts'); os.makedirs(d + '/tmp')
    for f in ('fq', 'fqjob.py', 'bestof.py', 'methods_lp.py'):
        subprocess.run(['cp', '-p', '%s/box/%s' % (W, f), d + '/'])
    open(d + '/py', 'w').write('#!/bin/sh\nexec %s -I "$@"\n' % sys.executable); os.chmod(d + '/py', 0o755)
    subprocess.run(['cp', '-p', W + '/boxA/fqdeadline', d + '/fqdeadline'])
    write_rows('%s/starts/%d-%s.csv' % (d, n, tag), rows_of('%s/%d.csv' % (T, n)))
    r = subprocess.run([d + '/py', d + '/fqjob.py', str(n), tag], capture_output=True, text=True)
    open(d + '/fq.log', 'w').write(r.stdout + r.stderr)
    for p in sorted(glob.glob('%s/run/%d-%s/raw/%d-fq-*.csv' % (d, n, tag, n))):
        os.rename(p, '%s/%d-fq-c%d-%s' % (out, n, k, os.path.basename(p).split('-fq-')[1]))
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'where': print(W)
    elif cmd == 'plan': plan()
    elif cmd == 'watch': watch()
    elif cmd == 'split': split(sys.argv[2], sys.argv[3])
    elif cmd == 'add': add(int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == 'cq': cq(int(sys.argv[2]), sys.argv[3])
    elif cmd == 'collect': collect(fetch=len(sys.argv) < 3 or sys.argv[2] != 'nofetch')
