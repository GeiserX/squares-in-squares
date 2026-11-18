#!/usr/bin/env python3
"""backlog_ctl: the controller of the backlog lane (avenues/backlog.md, Rounds 25 and 26). Light python on boxA.

Every 20 s: collect finished runs from the boxes, certify them, then fill each idle slot. Before an item goes to a slot
it is claimed in the handoff log ("<UTC> backlog -> <owner>: claims <item id>, <queue file>") and in STATE.txt. An item
whose id the owner names in its own take-<owner>-r<R>/STATE.txt, or that another lane claims in the log, is skipped.

Round 26 (BACKLOG_ROUND, default 26): slots boxB/1, boxB/2 and boxC/1 (SLOTS). The queue is work/queue.json
(backlog_queue26.py), work/extra.json (legs and handed items) and the follow items: every certified row of a live
take-*-r26 dir below the bar gets one invent lkick from its own file, once per file content. boxB/1 and boxC/1 take
follow items first, boxB/2 the queue. An item whose start is more than 3e-5 above the bar or a live take is skipped.

Certification: floatsafe at 2.2e-11 of the run's final file (the worker already ran one fq quench from the certified
file), kept when its score is below the base bar (BACKLOG_BASE, gate/cand-round25-1114b/details.csv) by more than
1e-10 and below the same n in every live take-*-r<R> dir, and when the independent walk of the round 25 assembler
(take-assemble-r25/deep25.py) finds no out source. Kept rows go to the take dir as <n>.csv first, then take.tsv by
rename, with one handoff line each. A find gets a leg while a leg gains 1e-6 of score, three at most.

  backlog_ctl.py            (paths fixed below; stop: touch TAKE/work/STOPCTL)
"""
import csv, glob, json, math, os, re, subprocess, sys, time

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402
import backlog_gate27  # noqa: E402,F401  round 29: narrows quench_audit's 'r22 745/858 join' rule in memory (main 07:34:54Z)

S = '$SCRATCH/bounties-squares'
R = os.environ.get('BACKLOG_ROUND', '27')
T = S + '/take-backlog-r' + R; W = T + '/work'
LOG = S + '/handoff-r%s.log' % R
BASE_DETAILS = os.environ.get('BACKLOG_BASE', S + '/gate/cand-round25-1114b/details.csv')
# round 26: slots on several boxes, (box, scratch dir, slot); the budget is boxB 2 and boxC 1
SLOTS = [('boxB', '$SCRATCH/squares-backlog', '1'), ('boxB', '$SCRATCH/squares-backlog', '2'),
         ('boxC', '/Users/boxC/scratch/squares-backlog', '1')]
if int(R) == 31:                         # round 31: the modules slot on boxB comes to backlog (brief 6e); round 32: boxB 2, boxC 1
    SLOTS.insert(2, ('boxB', '$SCRATCH/squares-backlog', '3'))
if int(R) >= 33:                         # round 33 (brief 6h, 8): the retired midm lane's boxE slot comes to backlog
    SLOTS.append(('boxE', '$SCRATCH/squares-backlog', '1'))
if int(R) >= 36:                         # round 36 (brief 6l): boxE 1, boxC 2, boxB 1
    SLOTS = [('boxB', '$SCRATCH/squares-backlog', '1'), ('boxC', '/Users/boxC/scratch/squares-backlog', '1'),
             ('boxC', '/Users/boxC/scratch/squares-backlog', '2'), ('boxE', '$SCRATCH/squares-backlog', '1')]
if int(R) >= 37:                         # round 37 (brief 8): boxE 1, boxC 2, boxB 2
    SLOTS.insert(1, ('boxB', '$SCRATCH/squares-backlog', '2'))
if int(R) >= 38:                         # round 38 (brief 8): boxE 1, boxC 3, boxB 2
    SLOTS.insert(4, ('boxC', '/Users/boxC/scratch/squares-backlog', '3'))
BOX = 'boxB'; RD = '$SCRATCH/squares-backlog'
SEARCH_END = float(open(W + '/deadline').read())          # no job starts that cannot end by then
MEASURE = 90 * 60
csv.field_size_limit(1 << 30)


GATE_CACHE = {}


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def state(s):
    with open(T + '/STATE.txt', 'a') as h:
        h.write('%s boxA %s\n' % (now(), s))


def handoff(s):
    with open(LOG, 'a') as h:
        h.write('%s backlog -> %s\n' % (now(), s))


def sh(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def load(p, default):
    try:
        return json.load(open(p))
    except Exception:
        return default


_SHA = {}


def sha_of(path):
    import hashlib
    try:
        k = (path, os.path.getmtime(path), os.path.getsize(path))
    except OSError:
        return ''
    if k not in _SHA:
        _SHA[k] = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    return _SHA[k]


def claimed_by_other(h, pats=(), window=3600, before=None):
    """Round 31 (brief 6b): the claim line of another lane, written in the last 60 minutes (and before BEFORE when
    given), that names these exact bytes by their sha256 (the first 12 hex digits) or matches one of the regexes
    PATS (the path of the start, or the held row of its n). None when no lane claimed them."""
    cut = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(time.time() - window))
    h12 = (h or '')[:12].lower()
    rx = [re.compile(p, re.I) for p in pats if p]
    lines = open(LOG, errors='replace').readlines()
    rel = ''
    if int(R) >= 33 and h12:
        # round 33: a later RELEASE line of another lane that names these bytes ends its claims on them (forensics ->
        # backlog 19:19:04Z: release of the 789 kick claims, sha256 6db0d7295a75, its 900 s probe dry at 122 s)
        for line in lines:
            if re.search(r'\brelease', line, re.I) and h12 in line.lower() and not line.split(' ', 2)[1:2] == ['backlog']:
                rel = max(rel, line[:19])
    for line in lines:
        parts = line.split(' ', 2)
        if len(parts) < 3 or parts[1].startswith('backlog') or line[:19] < cut or (before and line[:19] > before):
            continue
        if rel and line[:19] <= rel:
            continue
        if not re.search(r'\bclaim', line, re.I) or re.search(r'\brelease', line, re.I):
            continue
        if int(R) >= 35 and HAND.match(line) and not re.search(r'\bclaim', line.split(' -> ', 1)[-1].split(': ', 1)[-1][:60], re.I):
            continue                   # round 35: a hand line that only says other lanes may claim the row is no claim                   # only a claim line counts: a certified line that says 'fresh build for kicks' is no claim
        if h12 and h12 in line.lower():
            return line.strip()[:220]
        if any(r.search(line) for r in rx):
            if int(R) >= 32 and h12 and not any(r.pattern.startswith('^(?=') for r in rx if r.search(line)):
                # round 32: a path claim whose line names other bytes (a sha256 that is not ours) claims those bytes, not a
                # later file at the same path (forensics 973 at 11:35Z: midm claimed 4794f797, we skipped d8a2a60c)
                toks = re.findall(r'[0-9a-f]{12,64}', line.lower())
                if toks and not any(t.startswith(h12) or h12.startswith(t[:12]) for t in toks):
                    continue
            return line.strip()[:220]
    return None


# round 27 on: the bar of the round brief (round 28: the lower of the held r26 b file and the best certified r27 take row)
BAR27 = S + '/round%s-briefs/bar%s.tsv' % (R, R) if int(R) >= 27 else S + '/round27-briefs/bar27.tsv'


def base():
    g29 = S + '/gate/cand-round29-1115b/details.csv'
    if R == '30' and os.path.exists(g29):   # main 13:31:18Z: the round 30 bar is now the submitted round 29 b gate
        return {int(r['n']): float(r['score']) for r in csv.DictReader(open(g29))}
    if int(R) >= 27:                 # round 27: the lower of the held r25 b file and the best certified r26 take row
        return {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BAR27), delimiter='\t')}
    if R == '25':
        return {int(r['n']): float(r['clean_score']) for r in csv.DictReader(open(W + '/base.tsv'), delimiter='\t')}
    return {int(r['n']): float(r['score']) for r in csv.DictReader(open(BASE_DETAILS))}


def live_r25(n):
    best = math.inf
    for t in glob.glob(S + '/take-*-r%s/take.tsv' % R):
        if t.startswith(T):
            continue
        try:
            for r in csv.DictReader(open(t), delimiter='\t'):
                if r.get('n', '').isdigit() and int(r['n']) == n:
                    best = min(best, float(r['new']))
        except Exception:
            pass
    return best


def taken_elsewhere(item):
    short = item['id'].split(':', 1)[1]
    if item['id'].startswith('nearpub:'):
        base = 'near-pub/' + os.path.basename(item['start'])
        for line in open(LOG, errors='replace'):
            if base in line and not line.split(' ', 2)[1].startswith('backlog') and re.search(r'claim|kick', line, re.I):
                return True
        return False
    p = '%s/take-%s-r%s/STATE.txt' % (S, item.get('claim', item['owner']), R)
    if item.get('claim', item['owner']) == 'backlog':
        p = ''                               # round 29: a re-open of our own frozen file (its QUEUE line is in our STATE)
    if p and os.path.exists(p) and short in open(p, errors='replace').read():
        return True
    for line in open(LOG, errors='replace'):
        if 'claims' in line and short in line and not line.split(' ', 2)[1].startswith('backlog'):
            return True
    return False


def rebuild_has(item):
    if int(R) >= 30 and item['id'].endswith('-rl') and item.get('orig'):
        # round 30: a rectangle that another lane claims by its path after the file was last written is taken
        try:
            mt = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(os.path.getmtime(item['orig'])))
        except OSError:
            mt = ''
        for line in open(LOG, errors='replace'):
            if item['orig'] in line and re.search(r'claim', line, re.I) and not line.split(' ', 2)[1].startswith('backlog') and line[:19] >= mt:
                return True
    m = re.search(r'-([0-9a-f]{12})(?:-m|-rl)?$', item['id'])
    p = '%s/take-rebuild-r%s/work/queue-log.tsv' % (S, R)
    if not m or not os.path.exists(p):
        return False
    h12 = m.group(1)
    for line in open(p, errors='replace'):
        c = line.rstrip('\n').split('\t')
        if len(c) > 5 and c[5].startswith(h12):
            return True
    # the quench lane claims its 900 s kicks in the handoff log by the start's sha256 prefix ("claim: ... sha256 fc7305f8e0b8ef0c")
    for line in open(LOG, errors='replace'):
        if h12 in line and re.search(r'claim', line, re.I) and not line.split(' ', 2)[1].startswith('backlog'):
            return True
    return False


def source_of(item):
    """Source and licence cells: the owner's own record of the start, read from its frozen queue file."""
    if item.get('source_text'):
        return item['source_text'], item.get('licence_text', '')
    if item['owner'] == 'midm':
        return item.get('record_source', ''), item.get('record_licence', '')
    short = item['id'].split(':', 1)[1]
    if item['owner'] == 'invent':
        for e in json.load(open(item['queue'])):
            if e['id'] == short:
                return str(e.get('source', '')), str(e.get('licence', ''))
    if item['owner'] == 'readers':
        spec = open(item['spec']).read()
        donors = [l.split('\t')[0] for l in spec.splitlines()[1:] if l.strip()]
        src = readers_sources()
        return ('readers walk spec %s (%s); donors: %s' % (os.path.basename(item['spec']), spec.replace('\n', ' | '),
                 '; '.join('%s <%s>' % (d, src.get(d, ('unrecorded', ''))[0]) for d in donors)),
                '; '.join(src.get(d, ('', 'unrecorded'))[1] for d in donors))
    if item['owner'] == 'harvest':
        for e in json.load(open(item['queue'])):
            if e['key'].startswith(short):
                return str(e['row'].get('source', '')), str(e['row'].get('licence', ''))
    return '', ''


RBOX = S + '/take-readers-r25/work/box'
_rsrc = {}


def readers_sources():
    if not _rsrc:
        p = S + '/take-readers-r25/work/sources-all.tsv'
        for r in csv.DictReader(open(p), delimiter='\t'):
            _rsrc[r['donor']] = (r.get('source', ''), r.get('licence', ''))
    return _rsrc


def readers_items(claimed):
    """Readers' carried b-specs that its slots will not reach: cut 0 specs from rank 300 on (readers ran about
    20 b-specs in its first 30 minutes, so it reaches about rank 150 by the deadline), then the cut 1 tail."""
    names = {os.path.basename(q): q for q in glob.glob(RBOX + '/q[0-9]/b*.tsv')}
    c0 = sorted(k for k in names if k.endswith('-c0.tsv') and int(k[1:9]) >= 300)
    c1 = sorted((k for k in names if not k.endswith('-c0.tsv')), reverse=True)
    out = []
    for k in c0 + c1:
        stem = k[:-4]; iid = 'readers:' + stem
        if iid in claimed:
            continue
        try:
            n = int(stem.split('-')[1]); rnd = int(stem.split('-')[2][1:3])
        except (IndexError, ValueError):
            continue
        if n in (639, 691, 745, 858, 918, 980, 981, 801) or (n in (735, 790, 228, 985) and rnd <= 23):
            claimed[iid] = 'dropped: out-count or 735-tree donor'; continue
        out.append(dict(owner='readers', id=iid, n=n, spec=names[k], queue=names[k], start='', gap=0.0, pred=0.0,
                        seconds=1200, tool='family_readers.py walk (readers run25.sh settings)'))
        if len(out) >= 40:
            break
    return out


def write_take(rows):
    with open(T + '/take.tsv.tmp', 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for n in sorted(rows):
            r = rows[n]
            h.write('%d\t%r\t%r\t%.12e\t%s\t%s\n' % (n, r['held'], r['new'], r['held'] - r['new'], r['source'], r['licence']))
    os.replace(T + '/take.tsv.tmp', T + '/take.tsv')



DEEP = S + '/take-assemble-r25'


LAST = {}


def deep_check(n, src, lic):
    """The r25 assembler's independent walk (take-assemble-r25/deep25.py, imported, never edited, no bytecode written):
    every file, sidecar, ledger row, ancestry record and held reference the cells name. Returns (ok, note)."""
    sys.dont_write_bytecode = True
    if DEEP not in sys.path:
        sys.path.insert(0, DEEP)
    import deep25
    texts, missing, files, helds = deep25.walk(dict(n=n, source=src, licence=lic))
    # the harvest lane records "not a layout of rules a-d (max centre distance: prvsiyan 1105=X samanyu_22249=Y
    # samanyu_bestfit=Z)": a negative finding, which the walk's samanyu_bestfit pattern reads as a seed. Drop that
    # clause only when every distance is 0.55 or more (a different layout); a closer one stays a signal.
    def far(m):
        d = [float(x) for x in re.findall(r'=([0-9.]+)', m.group(0))]
        return '(distances checked)' if d and min(d) >= 0.55 else m.group(0)
    texts = [(a, b, re.sub(r'\(max centre distance:[^)]*\)', far, t), c) for a, b, t, c in texts]
    if int(R) >= 27:
        # round 27: the Samanyu-dev seed no longer refuses (pos, merged0 and the withdrawn trees of deep25 are all that
        # seed); the CC BY-SA and penguin069 signals stay, after the measurement clauses that only name the prvsiyan
        # file as the layout a distance or share was measured to are taken out
        meas = re.compile(r'\(max centre distance:[^)]*\)|prvsiyan[^;|\n"]{0,40}\(CC BY-SA\)\s*=\s*[0-9.e-]+|share[^;|\n"]{0,80}prvsiyan[^;|\n"]{0,80}'
                          r'|prvsiyan[^;|\n"]{0,80}share[^;|\n"]{0,40}|excluded layout of rules a-d[^;|\n"]{0,60}'
                          # round 31: the harvest r31 evidence blocks of its public rows, a share measured against each
                          # harvested 1105 table: {"label": "prvsiyan1105 <zip> sha256 ...", "share1e6": .., "share1e3": .., ...}
                          r'|\{\s*"label":\s*"prvsiyan1105[^{}]*\}|"label":\s*"prvsiyan1105[^"]*"', re.I)
        texts = [(a, b, meas.sub(' ', t), c) for a, b, t, c in texts]
        sg = deep25.signals(texts)
        bad = {k: len(v) for k, v in sg.items() if v and k in ('bysa', 'penguin')}
        if int(R) >= 28:
            def held799(lab, t, ch, m):
                # round 31: the forensics r22 donor 799-986b3b6d reached through the held round 22 799 (the classfill r22
                # rectangle row, results/round22-best-2026-11-13.tsv) is held ancestry (main 13:32:00Z of round 30)
                if int(R) >= 33 and any(re.search(r'take-assemble-r\d+/held-roots\.json|(?:^|/)gather/round\d+|results/round\d+-best', c)
                                        for c in ch):
                    # round 33 (brief rule 3): a withdrawn file counts only when the tree takes it directly; one reached
                    # through a held round record (the chain passes the assembler's held-roots.json or a held table) is held
                    # ancestry (k123 r33 734 at 18:51Z: 799-986b3b6d six steps under take-assemble-r32/held-roots.json)
                    return True
                if int(R) < 31 or m.group(0) != '799-986b3b6d':
                    return False
                ctx = ' '.join(ch) + ' ' + lab + ' ' + t[max(0, m.start() - 3000):m.start()]
                return bool(re.search(r'take-classfill-r22/(?:799\.csv|take\.tsv|work/799-lineage)', ctx))
            hit = sorted({m.group(0) for lab, _, t, ch in texts for m in TAINT.finditer(t) if not held799(lab, t, ch, m)}
                         | {m.group(0) for m in TAINT.finditer(src)})
            if hit:
                bad['withdrawn tree (handoff-r27/r28): ' + ', '.join(hit[:4])] = len(hit)
            # the rule a files and the other out sources of the assembler audit (quench_audit.RULES, imported): the 743
            # of 00:41Z kicked a forensics rectangle whose part B was the r23 forensics 858 donor
            import quench_audit
            alltext = ' '.join(t for _, _, t, _ in texts) + ' ' + src
            for name, rx in quench_audit.RULES:
                if re.search(rx, alltext, flags=re.I):
                    bad['audit rule ' + name] = 1
            LAST['helds'] = len(helds)
        miss = sorted(set(missing))
        note = 'deep25 walk (round 27, seed signals lifted): %d texts, %d files, %d held refs, signals %s, unwalked %d%s' % (
            len(texts), len(files), len(helds), bad or 'none', len(miss), (' (' + '; '.join(miss[:6]) + ')') if miss and int(R) < 37 else '')
        # round 37: the names deep25 could not walk stay out of the record (lesson 6n: quench_walk reads every path in a
        # record as ancestry, and a relative name it cannot find reads as gone; the 683 tree at 03:52Z)
        if miss and int(R) >= 37:
            state('DEEP25 n=%d unwalked names (kept out of the record): %s' % (n, '; '.join(miss[:6])[:600]))
        hard = [m for m in miss if m.startswith(('cap reached', 'oversized'))]
        return (not bad and not hard), note
    sg = deep25.signals(texts)
    bad = {k: len(v) for k, v in sg.items() if v}
    miss = sorted(set(missing))
    note = 'deep25 walk: %d texts, %d files, %d held refs, signals %s, unwalked %d%s' % (
        len(texts), len(files), len(helds), bad or 'none', len(miss), (' (' + '; '.join(miss[:6]) + ')') if miss else '')
    hard = [m for m in miss if m.startswith(('cap reached', 'oversized'))]
    # round 26: the held rows of these counts name the far zone 811h.F1 of the Samanyu-dev seed (rebuild -> backlog,
    # handoff-r26.log 13:22:38Z); a row at one of them, or a text naming 811h, stays out of the take
    alltext = ' '.join(t for _, _, t, _ in texts)
    if n in SEED811 or re.search(r'811h\b|811h\.|921-29e12ff3|924-0f6bdd36', alltext):
        bad['seed 811h far zone or a bare seed file'] = 1
        note += ', refused: n or a parent names the 811h far zone or a bare seed file of the Samanyu-dev seed'
    tainted = sorted({nn for k, nn in helds if nn in AUDIT})
    if tainted:
        bad['held parent in the rebuild audit'] = 1
        note += ', refused: walks to the held layout of n=%s, which the rebuild audit of 13:35Z traces to an out source' % tainted
    if n in AUDIT and re.search(r'gather/round|held', src):
        bad['held start at an audited n'] = 1
        note += ', refused: n=%d is in the rebuild audit and the cell names a held layout' % n
    return (not bad and not hard), note


# round 28: trees withdrawn in handoff-r27.log and handoff-r28.log for a reason that still holds (a prvsiyan share of
# 0.4 or more in the layout or a complete ancestor, an unresolved public trace). A row whose walked texts name one of
# these files stays out: the 684 donor of the 23:50:47Z invent withdrawal and its 910/972 descendants, the seed 503
# k123 699/932, the classfill 927 and 982 branches, the 742 ancestor of the k123 798 tree, the forensics r27 near
# withdrawals of 21:41Z and 23:06Z, the harvest r27 639/916/918 and the harvest r26 499 tree
TAINT = re.compile(r'take-harvest-r27/(?:639|916|918)\.csv|take-harvest-r26/499\.csv|take-twoshort-r27/(?:near/)?499'
                   # the harvest r27 916 geometry (withdrawn 22:16Z and 22:31Z: inherited source, no per-n trace), also as
                   # the collector copy remote-074276bf that the round 28 re-open gate passed at 00:23:40Z
                   r'|074276bfcd18c9d02a71|992b9c222054|take-border-r27/near/916-withdrawn'
                   # round 30 (main -> all 13:32:00Z): withdrawn public-first files that were never held stay out when a tree
                   # takes them directly, even when it also reaches held rows: take-harvest-r26/695.csv, the harvest r26 814
                   # collector file 5a4c0cdb, and the forensics r22 donor 799-986b3b6d
                   r'|take-harvest-r26/695\.csv|take-harvest-r26/814\.csv|5a4c0cdb|799-986b3b6d')
# round 28 from 00:19:03Z (main -> all): withdrawals for an ancestor's or an original seed's prvsiyan share no longer hold
# (the 684 donor tree, k123 699/932/798, classfill 927/982, the forensics r27 near files); TAINT keeps the public rows
# withdrawn for an untraced source or for their own share (harvest r27 639/916/918, the harvest r26 499 tree)

# round 26 from 14:12Z: every slot takes follow items first (measured: follow 5 certified of 14, held lkick 0 of 3,
# midm pending 0 of 3); the queue fills a slot only when no follow item waits
FOLLOW_FIRST = (('boxB', '1'), ('boxB', '2'), ('boxB', '3'), ('boxC', '1'), ('boxC', '2'), ('boxE', '1'))
# near-pub first on boxC until 16:02Z: 0 certified of 8 kicks (4 dry, 2 refused near the prvsiyan rows, 696 6.8e-14 above)
NEARPUB_FIRST = False
SEED811 = {698, 753, 809, 810, 811, 868, 869, 870, 929, 931}
# rebuild -> main,modules,backlog 13:35:26Z (take-rebuild-r26/work/pools/B3.audit): held r25b rows whose walked
# ancestry reaches the Samanyu-dev seeds 811, 503/504, 983, 861 or the bare 921 file, or names penguin069
AUDIT = {698, 752, 753, 809, 810, 811, 868, 869, 870, 929, 930, 931, 992, 993, 994, 598, 601, 649, 700, 701, 754, 755,
         756, 812, 813, 932, 995, 996, 804, 860, 862, 863, 924, 987, 921, 815, 875, 876, 936, 999, 800, 802}


def certify(done, item, bars, take, st, n=None, box=None):
    n = n or done['n']; rid = done['rid']; f = '%s/runs/%s/final/%d.csv' % (W, rid, n)
    if not os.path.exists(f):
        return None
    if int(R) >= 31 and n in out31():
        # round 31: an n of the out list takes no new row (911: our leg of 22:07Z read 0.429 at 1e-2 after the row
        # before it read 0.350; the take keeps the row that passed share31)
        state('CERT skipped %s n=%d: the n is in the round 31 out list (work/out31.txt)' % (rid, n)); return None
    fin = (done.get('finals') or {}).get(str(n), {})
    if int(R) >= 27 and 'shares' in fin:
        # round 27: the box worker ran floatsafe at 2.2e-11 and the share test on this file (boxA is too loaded
        # for a second floatsafe); its certified rows are the final file and its score is in done.json
        fr = list(csv.DictReader(open(f))); sc = fin['new']; e = None
        import backlog_gate27 as G
        if abs(G.quick(n, fr) - sc) > 1e-9:
            state('CERT refused %s n=%d: the final file side %r does not match the worker score %r' % (rid, n, G.quick(n, fr), sc)); return None
    else:
        import backlog_finesafe            # round 29: the bisected dilation (border r28), as the box worker
        _, fr, sc, e = backlog_finesafe.work((n, list(csv.DictReader(open(f)))))
    if fr is None:
        state('CERT refused %s n=%d floatsafe failed %s' % (rid, n, e)); return None
    bar = bars[n]; live = live_r25(n)
    gain = bar - sc
    st['score_gain'][item['owner']] = st['score_gain'].get(item['owner'], 0.0)
    src, lic = source_of(item)
    if not sc < bar - 1e-10 or not sc < live - 1e-10:
        why = 'above bar' if not sc < bar - 1e-10 else 'not below live r%s take %r' % (R, live)
        state('CERT %s %s n=%d score %r bar %r (gap %.3e)' % (why, rid, n, sc, bar, sc - bar))
        if int(R) >= 37 and item['id'].startswith('join:') and abs(sc - bar) < 1e-9:
            FELL[n] = 'our %s ended %.1e of score from the bar' % (rid, sc - bar)
            state('FELLBACK n=%d: %s; no more donor seeds at this n (brief 6c)' % (n, FELL[n]))
        if (sc - min(bar, live)) * math.sqrt(n) < 2e-5:          # near: within 2e-5 of side
            nf = '%s/near/%d-backlog-%s.csv' % (T, n, rid)
            with open(nf, 'w', newline='') as h:
                w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(fr)
            json.dump(dict(n=n, score=sc, bar=bar, live=live, item=item['id'], queue=item['queue'], tool=item['tool'],
                           start=item['start'], source=src[:20000], licence=lic[:4000]), open(nf + '.json', 'w'))
        return sc
    if n in take and take[n]['new'] <= sc:
        state('CERT not below own take %s n=%d' % (rid, n)); return sc
    if item['id'].startswith('nearpub:'):
        # harvest -> backlog 16:12Z/16:36Z: only the starts left in the rewritten queue-fresh.tsv are measured clean
        # (share of squares within 1e-3 of a rule a-d layout under 0.4); a result of any other near-pub start is out
        clean = {r['start'] for r in csv.DictReader(open(NEARPUB), delimiter='\t')} if os.path.exists(NEARPUB) else set()
        if 'near-pub/' + os.path.basename(item['start']) not in clean:
            state('CERT refused %s n=%d score %r: its near-pub start is not in the measured-clean queue-fresh.tsv' % (rid, n, sc))
            return None
    if item['owner'] == 'midm' and not item.get('source_text'):
        cell = ('backlog lane: midm_scan.py --modes kick,lkick --kicks %s --stop6, %d s, seed %d (the midm r25 worker25.py '
                'settings) from the frozen midm r25 queue item %s (%s), start %s, then floatsafe at 2.2e-11 and one fq quench '
                'from the certified file (midm_fqonce.py) on %s; start record: %s'
                % (item.get('sigma', 0.04), item['seconds'], item['seed'], item['id'], item['queue'], item['start'], box or BOX, src))
    elif item.get('source_text'):
        cell = 'backlog lane: %s, then floatsafe and one fq quench from the certified file on %s; %s' % (item['tool'], box or BOX, src)
    else:
        cell = ('backlog lane: %s from the frozen %s queue item %s (%s), start %s, then floatsafe and one fq quench from '
                'the certified file (midm_fqonce.py); start source: %s' % (item['tool'], item['owner'], item['id'], item['queue'],
                                                                         item['start'], src))
    cell = cell.replace('\t', ' ').replace('\n', ' ')
    lic = (lic or 'see the start source').replace('\t', ' ').replace('\n', ' ')
    ok, note = deep_check(n, cell, lic)
    if int(R) >= 27 and 'shares' in fin:
        sh = fin['shares']
        gok = not any(b >= 0.4 for l, a, b, d in sh)

        gnote = 'share test on the box (backlog_gate27.py, out at 0.4 of the squares within 1e-3): %s' % (
            '; '.join('%s share 1e-3 %.3f' % ('prvsiyan 1105 row' if 'prvsiyan' in l else 'rule a file', b) for l, a, b, d in sh)
            or 'no excluded layout of this n')
    else:
        gok, gnote = excluded_far(n, fr)
    if int(R) >= 28 and not gok:
        import backlog_gate27 as G
        import quench_walk
        o = item.get('orig') or item['start']
        try:
            ht = quench_walk.harvest_type(o, n)
        except Exception:
            ht = True
        # quench_walk round 28: the test applies to a harvest-type start and to a tree that reaches no held reference
        # (backlog_gate27.public_first read any harvest name in the cell, which also caught our own k123 joins with a
        # harvest part: the k123 756 follow at 01:43Z, 10 held references, share 0.653; the walk's own test is used)
        if not (ht or LAST.get('helds', 0) == 0 or '/take-harvest-r' in o):
            gok = True                       # main -> all 00:19:03Z: the share test refuses only public-first rows
            gnote += ' (not applied: no public first source, rule of 00:19:03Z)'
        elif int(R) >= 29 and not (ht or '/take-harvest-r' in o):
            # round 29 rule 3: a share match of our own layouts or their descendants never refuses; a walk that finds no held
            # reference is a record gap, not a public first source (r28 refused our 421 kick of soft's own rectangle row,
            # share 0.42, for that gap alone). The deep25 walk above still refuses a tree that names the prvsiyan file.
            gok = True
            gnote += ' (not applied: no public first source, round 29 rule 3)'
        elif int(R) >= 30 and LAST.get('helds', 0) > 0:
            # main -> all 12:40:55Z of round 30: a row built on a held row is built on our own layout; the share test
            # applies only to a row whose own first source is a fetched public file and that reaches no held row
            gok = True
            gnote += ' (not applied: the tree reaches %d held rows, main ruling 12:40:55Z of round 30)' % LAST.get('helds', 0)
    if int(R) >= 32:
        # round 32: the old box share (one 1105 table, 1e-3) is a note only; rule 3 is share32 below, on public-first trees
        gok = True
    note += '; ' + gnote
    if not gok:
        ok = False; note += ', refused: share test' if int(R) >= 27 else ', refused: within 0.55 of an excluded layout'
    if int(R) >= 32 and ok:
        wh = withdrawn_hit(cell + ' ' + (item.get('source_text') or ''), sha_of(item.get('start', '')))
        if wh:
            ok = False; note += ', refused: descends from withdrawn bytes (%s; lesson 6d)' % wh
    if not ok:
        state('CERT ancestry refused %s n=%d score %r: %s' % (rid, n, sc, note))
        nf = '%s/near/%d-backlog-%s-ancestry-refused.csv' % (T, n, rid)
        with open(nf, 'w', newline='') as h:
            w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(fr)
        json.dump(dict(n=n, score=sc, bar=bar, refused=note, source=cell[:20000], licence=lic[:4000]), open(nf + '.json', 'w'))
        return None                          # no leg from a refused row
    if int(R) >= 32:
        o = item.get('orig') or item.get('start') or ''
        pf = bool(PUBFIRST.search(cell) or PUBFIRST.search(o) or '/take-harvest-r' in o or item.get('pubfirst'))
        if not pf and item.get('orig'):
            try:
                import quench_walk
                pf = bool(quench_walk.harvest_type(item['orig'], n))   # the start's first recorded source is owner/slug ::
            except Exception:
                pass
        if pf:
            # round 32 rule 3 (lesson 6c): every certified row of a public-first tree is measured with the assembler's
            # frozen share (share32.py), not only its root; 0.4 or more at 1e-3 or 1e-2 against a table that is not our
            # own layout refuses it
            r32 = share32(n, fr, rid)
            snote = 'share32 (public-first tree) %.3f at 1e-3 and %.3f at 1e-2 against tables not our seed (%s)' % (
                r32['max_notown_1e3'], r32['max_notown_1e2'], r32['json'])
            if r32['verdict'] != 'in':
                state('CERT share refused %s n=%d score %r: %s, verdict %s' % (rid, n, sc, snote, r32['verdict']))
                nf = '%s/near/%d-backlog-%s-share32-out.csv' % (T, n, rid)
                os.replace(r32['tmp'], nf)
                json.dump(dict(n=n, score=sc, bar=bar, refused=snote, source=cell[:20000], licence=lic[:4000]), open(nf + '.json', 'w'))
                return None
            note += '; ' + snote
        else:
            note += '; share32 not run: no public first source in the record (rule 2: a held or own root)'
    elif int(R) >= 31 and n in share31_ns():
        # round 31 rule 3 at certify time for the public-first n of work/share31-n.txt (share31.py: the round 30
        # assembler's share30, bbox centring and ICP, 1e-3 and 1e-2, own-seed tables flagged): our 911 leg of 22:07Z read
        # 0.429 at 1e-2 while the row before it read 0.350, so each new row of such an n is measured before it is taken
        tmp = '%s/share/cert-%s-%d.csv' % (W, rid, n); oj = tmp[:-4] + '.json'
        with open(tmp, 'w', newline='') as h:
            w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(fr)
        try:
            subprocess.run(['nice', '-n', '5', sys.executable, '-I', W + '/scripts/share31.py', oj, 'c=%s:%d' % (tmp, n)],
                           capture_output=True, text=True, timeout=900)
            r31 = json.load(open(oj))[0]
        except Exception as ex:
            r31 = dict(verdict='error %s' % ex, max_notown_1e3=-1, max_notown_1e2=-1)
        snote = 'share31 %.3f at 1e-3 and %.3f at 1e-2 against tables not our seed (%s)' % (r31['max_notown_1e3'], r31['max_notown_1e2'], oj)
        if r31['verdict'] != 'in':
            state('CERT share refused %s n=%d score %r: %s, verdict %s' % (rid, n, sc, snote, r31['verdict']))
            nf = '%s/near/%d-backlog-%s-share31-out.csv' % (T, n, rid)
            os.replace(tmp, nf)
            json.dump(dict(n=n, score=sc, bar=bar, refused=snote, source=cell[:20000], licence=lic[:4000]), open(nf + '.json', 'w'))
            return None
        note += '; ' + snote
    st['score_gain'][item['owner']] += gain
    lic = lic + ' [' + note + ']'
    with open('%s/%d.csv.tmp' % (T, n), 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(fr)
    os.replace('%s/%d.csv.tmp' % (T, n), '%s/%d.csv' % (T, n))
    take[n] = dict(held=bar, new=sc, source=cell, licence=lic)
    write_take(take)
    state('CERT certified n=%d score %r bar %r gain %.6e (below live r%s takes %r) %s/%d.csv; %s' % (n, sc, bar, gain, R, live, T, n, note))
    if int(R) >= 38 and not item.get('ownfollow'):
        # round 38 (brief 6b, 8): our own 180 s lkick follow of the find runs before its certified line
        HOLD[n] = dict(t=time.time(), owner=item['owner'], id=item['id'])
        own_follow(n, sc, rid, item, bars)
        state('HOLD the certified line of n=%d until our own 180 s follow of %s ends (brief 6b)' % (n, rid))
        return sc
    HOLD.pop(n, None)
    handoff('all: certified n=%d score %r gain %.3e on the base bar (%s queue item %s), %s/%d.csv'
            % (n, sc, gain, item['owner'], item['id'], T, n))
    return sc


HOLD = {}                              # round 38: n -> a certified row whose line waits for our own follow


def own_follow(n, sc, rid, item, bars):
    """Round 38 (brief 6b, 8): one 180 s invent lkick (seed item seed + 50) from our certified find, ahead of every
    other item; the certified line of n is posted when it ends."""
    import shutil
    os.makedirs(W + '/legs', exist_ok=True)
    lp = '%s/legs/%d-own-%s.csv' % (W, n, rid)
    shutil.copy('%s/%d.csv' % (T, n), lp)
    sd = int(item.get('seed', 11)) + 50
    it = dict(owner='invent', id='ownf:%d-%s' % (n, rid), n=n, start=lp, orig=lp, start_score=sc, gap=sc - bars[n], pred=1.0,
              seconds=180, seed=sd, fq=False, queue='own follow of %s' % rid, ownfollow=True,
              tool='invent_rest.py lkick (own follow, 180 s, seed %d, no fq inside)' % sd,
              source_text=('own 180 s follow (invent_rest.py lkick, seed %d) from the certified row of backlog run %s (%s, byte copy %s '
                           '(sha256 %s), its final file %s/runs/%s/final/%d.csv): %s' % (sd, rid, item['id'], lp, sha_of(lp), W, rid, n, item.get('source_text', ''))),
              licence_text=item.get('licence_text', ''))
    ex = load(W + '/extra.json', []); ex.append(it)
    json.dump(ex, open(W + '/extra.json.tmp', 'w')); os.replace(W + '/extra.json.tmp', W + '/extra.json')
    state('DECIDE own follow for n=%d (180 s, seed %d): %s' % (n, sd, lp))


def release_holds(take, items, st, force=False):
    """Round 38: post the held certified line of n once no own follow of n waits or runs (or after 20 minutes)."""
    dn = set(st['done'])
    items = list(items) + [o for o in load(W + '/extra.json', []) if o.get('ownfollow')]   # an own follow queued this loop
    for n in list(HOLD):
        h = HOLD[n]
        busy = any(o.get('ownfollow') and o['n'] == n and (o['id'] not in st['claimed'] or
                   (str(st['claimed'][o['id']]).startswith('b') and st['claimed'][o['id']] not in dn)) for o in items)
        if busy and not force and time.time() - h['t'] < 1200:
            continue
        HOLD.pop(n)
        if n not in take:
            continue
        bars = base()
        handoff('all: certified n=%d score %r gain %.3e on the base bar (%s queue item %s, after our own 180 s follow), %s/%d.csv'
                % (n, take[n]['new'], bars[n] - take[n]['new'], h['owner'], h['id'], T, n))
        state('POST certified line of n=%d (score %r)%s' % (n, take[n]['new'], '' if not busy else ' (own follow still waiting, posted after 20 minutes or at the end)'))


PARENT = re.compile(r'byte copy (\S+) \(sha256 ([0-9a-f]{64})\), taken at queue time from the (?:certified round \d+ take |round \d+ near file '
                    r'$SCRATCH/bounties-squares/)(take-[a-z0-9-]+-r\d+/(?:near/)?[^\s;]+?\.csv)')


def withdraw_check(take):
    """Round 29: a row of ours whose followed parent take file another lane WITHDRAWs (by its sha256 prefix, or by its
    path when the line names no sha256) leaves our take: the per-n file moves to near/, take.tsv is rewritten by rename,
    one handoff line. A later REINSTATE of the same bytes cancels the withdrawal (soft 747 at 07:48Z)."""
    if int(R) < 29 or not take:
        return
    last = {}
    for line in open(LOG, errors='replace'):
        parts = line.split(' ', 2)
        if len(parts) < 3 or parts[1].startswith('backlog') or 'not a withdrawal' in line:
            continue
        if int(R) >= 30 and re.search(r'RETENTION|not the withheld|\bkeeps\b|retention note', line, re.I):
            continue                                 # round 30 brief: a retention note is not a withdrawal
        kind = 'w' if re.search(r'\bWITHDRAW\b', line) and not (NOWD.search(line) and int(R) >= 33) else ('r' if re.search(r'\bREINSTATE\b', line) else None)
        if not kind:
            continue
        shas = [h[:12] for h in re.findall(r'sha256 ([0-9a-f]{12,64})', line)]
        for h in shas:
            last['sha:' + h] = (kind, line.strip()[:300])
        if not shas:
            for f in re.findall(r'(take-[a-z0-9-]+-r\d+/\d+\.csv)', line):
                last['path:' + f] = (kind, line.strip()[:300])
    changed = False
    for n in sorted(take):
        m = PARENT.search(take[n]['source'])
        if not m:
            continue
        hit = last.get('sha:' + m.group(2)[:12]) or last.get('path:' + m.group(3))
        if not hit or hit[0] != 'w':
            continue
        import hashlib, shutil
        f = '%s/%d.csv' % (T, n)
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest() if os.path.exists(f) else 'gone'
        nf = '%s/near/%d-backlog-withdrawn-parent-%s.csv' % (T, n, h[:12])
        if os.path.exists(f):
            shutil.move(f, nf)
        json.dump(dict(n=n, row=take[n], parent=m.group(3), parent_sha256=m.group(2), withdrawal=hit[1]), open(nf + '.json', 'w'))
        r = take.pop(n); changed = True
        state('WITHDRAW our n=%d (score %r): its parent %s (sha256 %s) is withdrawn: %s; file now %s' % (n, r['new'], m.group(3), m.group(2)[:12], hit[1][:200], nf))
        handoff('all: WITHDRAW n=%d (our r%s row, score %r, file now %s): it is a kick of %s (sha256 %s), withdrawn by its lane: %s, %s/take.tsv'
                % (n, R, r['new'], nf, m.group(3), m.group(2)[:12], hit[1][:160], T))
    if changed:
        write_take(take)


def own_items(take, bars, seen):
    """Round 29: each certified row of ours that is the lowest live row of its n gets one more kick of each tool from a
    byte copy, once per file content: a 600 s midm kick (seed 5800 + n) and a 300 s lkick (seed 211). They rank behind
    the follows and the legs and ahead of the near kicks (by 09:12Z legs certified 1 of 12, near kicks 0 of 80)."""
    import hashlib, shutil
    out = []
    if int(R) < 29 or int(R) >= 34:        # round 34 (brief 8): no own chains (0 of 13 in round 33)
        return out
    for n in sorted(take):
        f = '%s/%d.csv' % (T, n)
        if n not in bars or not os.path.exists(f) or not take[n]['new'] < live_r25(n) - 1e-10:
            continue
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        key = 'own-%d-%s' % (n, h[:12])
        if key in seen:
            continue
        p = '%s/starts/%d-own-%s.csv' % (W, n, h[:12])
        shutil.copy(f, p)
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
            continue
        seen[key] = take[n]['new']
        sc = take[n]['new']
        lic = (take[n].get('licence') or '').split(' [deep25')[0]
        # no "taken at queue time" words here: withdraw_check then reads the first parent from the nested row
        base = ('from the byte copy %s (sha256 %s) of our own certified round %s row %s/%d.csv; its take.tsv row: %s'
                % (p, h, R, T, n, (take[n].get('source') or '').replace('\t', ' ')))
        ms = 900 if int(R) >= 31 else 600
        out.append(dict(owner='midm', claim='backlog', id='own:' + key + '-m', n=n, start=p, orig=f, start_score=sc,
                        gap=sc - bars[n], pred=bars[n] - sc, seconds=ms, probe=120 if int(R) >= 31 else 0, seed=5800 + n + len(seen), sigma=0.04,
                        queue=T + '/take.tsv', tool='midm_scan.py kick,lkick (sigma 0.04, %d s%s)' % (ms, ', probe 120 s' if int(R) >= 31 else ''),
                        source_text='midm_scan.py kick,lkick (sigma 0.04, %d s, seed %d) %s' % (ms, 5800 + n + len(seen), base), licence_text=lic))
        out.append(dict(owner='invent', claim='backlog', id='own:' + key, n=n, start=p, orig=f, start_score=sc,
                        gap=sc - bars[n], pred=bars[n] - sc, seconds=300, seed=211, fq=False, queue=T + '/take.tsv',
                        tool='invent_rest.py lkick (300 s, seed 211, no fq inside)',
                        source_text='invent_rest.py lkick (300 s, seed 211) %s' % base, licence_text=lic))
    return out


FSKIP = set()
RUNSHA = set()                         # round 31: sha256 prefixes of the starts we dispatched
# round 31: n whose public-first trees read 0.4 or more against a 1105 table that is not our own layout (rule 3; share31.py,
# the round 30 assembler's share30 with ICP): 851 (the jazivxt public file 0.464 at 1e-2, our follow 0.400 at 1e-3 and
# 0.447 at 1e-2), 972 (the soft r30 tree 0.483 at 1e-2). work/out31.txt adds more without a restart.
OUT31 = {851, 972}


def share31_ns():
    try:
        return {int(x) for x in open(W + '/share31-n.txt').read().split() if x.isdigit()}
    except OSError:
        return set()


def out31():
    if int(R) >= 32:
        # round 32: no standing out list. The held r31b rows at 851 911 972 are ours (rule 2); a public-first tree at any n
        # is measured by share32 at certify time. work/out.txt still takes an n out without a restart.
        try:
            return {int(x) for x in open(W + '/out.txt').read().split() if x.isdigit()}
        except OSError:
            return set()
    o = set(OUT31)
    try:
        o |= {int(x) for x in open(W + '/out31.txt').read().split() if x.isdigit()}
    except OSError:
        pass
    return o


# round 32 (rule 3, lesson 6c): a tree is public-first when its first start is a fetched public file; the source cells
# of such rows name the harvest lane's files (quench: "of the file 791-cert31-....csv that the harvest lane wrote at or
# before 2026-11-15T19:06:54Z"). The round 31 harvest roots that the round 31 b file took are held now (rule 2), and the
# cells of held-rooted r31 rows nest such names deep inside (backlog r31 686 761 818 990), so only the round 32 harvest
# files mark a cell; quench_walk.harvest_type and a start under take-harvest-r* still mark a start of any round.
PUBFIRST = re.compile(r'that the harvest lane wrote at or before 2026-11-1[67]|take-harvest-r3[234]/|-public3[234]-|-cert3[234]-'
                      # round 36: the public files of this round's hourly harvest (quench), not yet held
                      r'|take-quench-r3[6-9]/work/harvest/|-public3[6-9]-|-cert3[6-9]-', re.I)
# round 33: the round 33 harvest files mark a cell too (round 32 harvest files that the held r32 a file did not take stay
# public-first; a share32 run on a tree that is in fact held-rooted only costs time)
_WD = {'t': 0, 'sha': set(), 'path': set()}
# round 33: a line that says it is no withdrawal ("no WITHDRAW or kick claim", forensics 16:54:50Z of round 32, and two
# quench_walk notes of round 31) withdraws nothing; it blocked the forensics r33 789 follow at 19:27Z
NOWD = re.compile(r'\b(?:no|not|nor|without)\s+(?:a\s+)?WITHDRAW', re.I)


def withdrawn():
    """Round 32 (lesson 6d): the bytes of every WITHDRAW line of handoff-r31.log and handoff-r32.log (sha256 prefixes of
    12 hex digits; for a line that names no sha256, the frozen take paths it names). A later REINSTATE of the same bytes
    cancels it. Lines are read again every 60 s."""
    if time.time() - _WD['t'] < 60:
        return _WD
    last = {}
    lgs = (S + '/handoff-r31.log', S + '/handoff-r32.log', LOG) if int(R) >= 33 else (S + '/handoff-r31.log', LOG)
    if int(R) >= 34:                       # round 34: the WITHDRAW lines of round 33 hold too
        lgs = (S + '/handoff-r31.log', S + '/handoff-r32.log', S + '/handoff-r33.log', LOG)
    if int(R) >= 35:                       # round 35: and those of round 34
        lgs = tuple(S + '/handoff-r%d.log' % k for k in range(31, int(R))) + (LOG,)
    for lg in lgs:
        try:
            lines = open(lg, errors='replace').readlines()
        except OSError:
            continue
        for line in lines:
            parts = line.split(' ', 2)
            if len(parts) < 3 or 'not a withdrawal' in line or re.search(r'RETENTION|not the withheld|retention note', line, re.I):
                continue
            kind = 'w' if re.search(r'\bWITHDRAW', line) and not (NOWD.search(line) and int(R) >= 33) else ('r' if re.search(r'\bREINSTATE\b', line) else None)
            if not kind:
                continue
            shas = {h[:12].lower() for h in re.findall(r'sha256[ :=]*([0-9a-fA-F]{12,64})', line)}
            shas |= {h[:12].lower() for h in re.findall(r'\b([0-9a-f]{12})[0-9a-f]{0,52}\b', line) if re.search(r'[a-f]', h)}
            for h in shas:
                last['sha:' + h] = kind
            if not shas:
                for f in re.findall(r'(take-[a-z0-9-]+-r3[1-9]/(?:near/)?\d+\.csv)', line):
                    last['path:' + f] = kind
    _WD['sha'] = {k[4:] for k, v in last.items() if v == 'w' and k.startswith('sha:')}
    _WD['path'] = {k[5:] for k, v in last.items() if v == 'w' and k.startswith('path:')}
    _WD['t'] = time.time()
    return _WD


def withdrawn_hit(text, start_sha=''):
    wd = withdrawn()
    if start_sha and start_sha[:12].lower() in wd['sha']:
        return 'start bytes sha256 %s are withdrawn' % start_sha[:12]
    low = (text or '').lower()
    for m in re.finditer(r'[0-9a-f]{12,64}', low):
        h = m.group(0)
        if h[:12] not in wd['sha']:
            continue
        pre = low[max(0, m.start() - 160):m.start()]
        # a provenance claim names a parent as "sha256 X" or inside a file name; a narrative note (the held 911 record:
        # "replaces the backlog row bd788481, which the skeptic dropped because it is an lkick of the quench fq
        # c171f6d83c60") names withdrawn bytes it does not descend from (13:38Z: two rebuild 911 follows skipped for it)
        prov = re.search(r'sha256[ :=]{1,3}$', pre) or low[m.start() - 1:m.start()] in ('-', '/', '_')
        if prov and not re.search(r'replac|dropp|withdr|instead|rather than|not the |skeptic', pre[-120:]):
            return 'the record names withdrawn bytes %s' % h[:12]
    for p in wd['path']:
        if p in (text or ''):
            return 'the record names the withdrawn file %s' % p
    return None


def share32(n, fr, rid):
    """Round 32: share32.py (the r31 assembler's frozen measure) on one certified row. Returns the result dict."""
    tmp = '%s/share/cert-%s-%d.csv' % (W, rid, n); oj = tmp[:-4] + '.json'
    with open(tmp, 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader(); w.writerows(fr)
    try:
        subprocess.run(['nice', '-n', '5', sys.executable, '-I', W + '/scripts/share32.py', oj, 'c=%s:%d' % (tmp, n)],
                       capture_output=True, text=True, timeout=900)
        r = json.load(open(oj))[0]
    except Exception as ex:
        r = dict(verdict='error %s' % ex, max_notown_1e3=-1, max_notown_1e2=-1)
    r['tmp'] = tmp; r['json'] = oj
    return r


# round 33 (brief 6c): a 45-degree lattice row (every square at exactly 45 degrees) returns its start side to a kick
# (785 and 786: 568 of 586 and 644 of 675 tries); these n are known lattice rows, and any other row is checked by its angles
LATTICE_N = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
# round 33 (brief 6d): fresh takes of the self-chaining lanes are theirs to follow; we take one only when it is 10 minutes
# old and no lane claimed its bytes in the meantime
SELF_CHAIN = ('take-border-', 'take-harvest-', 'take-classfill-', 'take-soft-')


def lattice45(f):
    try:
        a = [float(r['angle']) for r in csv.DictReader(open(f))]
    except Exception:
        return False
    if not a:
        return False
    q = 45.0 if max(abs(x) for x in a) > 2 * math.pi + 1e-6 else math.pi / 4   # degrees or radians (the gather files)
    k = [x / q for x in a]
    # every square axis-aligned or at exactly 45 degrees, and at least one at 45 (785: 496 at 0, 289 at pi/4)
    return all(abs(v - round(v)) < 1e-7 for v in k) and any(round(v) % 2 for v in k)


def own_take_score(n):
    try:
        for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t'):
            if r.get('n', '').isdigit() and int(r['n']) == n:
                return float(r['new'])
    except OSError:
        pass
    return math.inf


def r33_follow_block(lane, n, f, sc):
    """Round 33: the reason a fresh row of another lane gets no follow now, or None."""
    if n in LATTICE_N or lattice45(f):
        return 'a 45-degree lattice row (brief 6c: a kick returns the start side)'
    if sc > min(live_r25(n), own_take_score(n)) + 1e-12:
        return 'not the lowest live row of n (brief 6d)'
    if lane.startswith(SELF_CHAIN) and int(R) < 38:   # round 38 (brief 6b): the producer follows before its line
        try:
            age = time.time() - os.path.getmtime(f)
        except OSError:
            return 'wait: file gone'
        if age < 600:
            return 'wait: a self-chaining lane row younger than 10 minutes'
    return None


def producer_done(hit, lane):
    """Round 38 (rule 6b): the producer runs its own 180 s follow before its certified line; after that the 180 s
    follow is ours. A claim line of the producer lane itself (take-<lane>-r38) that is 7 minutes old or more no longer
    blocks our follow of the same bytes."""
    if int(R) < 38 or not hit:
        return False
    import calendar
    who = hit.split(' ', 2)[1] if len(hit.split(' ', 2)) > 1 else ''
    if who != lane.split('-')[1]:
        return False
    try:
        t = calendar.timegm(time.strptime(hit[:19], '%Y-%m-%dT%H:%M:%S'))
    except ValueError:
        return False
    return time.time() - t >= 420


def parent_src(d, r):
    """The take.tsv source cell of a followed row, as our record quotes it. Round 37: a path that the producer wrote
    relative to its own take dir ('work/...') is written in full, so the walker finds it from our take dir (the 683 tree
    at 03:25Z: 'work/harvest/near/683-public34-...csv' read as gone from every descendant)."""
    t = (r.get('source') or '').replace('\t', ' ')
    if int(R) >= 37:
        t = re.sub(r'(?<![\w/.-])work/', d + '/work/', t)
    return t


def follow_items(bars, seen):
    """Round 26: every certified row of a live take-*-r26 dir (not ours) that is below the bar gets one invent lkick
    from its own file, once per file content. The held item of that n is then superseded: the follow starts lower."""
    import hashlib, shutil
    out = []
    for t in sorted(glob.glob(S + '/take-*-r%s/take.tsv' % R)):
        d = os.path.dirname(t); lane = os.path.basename(d)
        if d == T:
            continue
        try:
            rows = list(csv.DictReader(open(t), delimiter='\t'))
        except Exception:
            continue
        for r in rows:
            try:
                n = int(r['n']); sc = float(r['new'])
            except (KeyError, ValueError):
                continue
            f = '%s/%d.csv' % (d, n)
            if n not in bars or not sc < bars[n] - 1e-10 or not os.path.exists(f):
                continue
            if int(R) >= 31 and n in out31():
                continue                       # no follow (and no claim line) at an n of the round 31 out list
            if int(R) >= 33:
                why = r33_follow_block(lane, n, f, sc)
                if why:
                    k33 = 'r33-%s-%d-%s' % (lane, n, why[:20])
                    if k33 not in FSKIP and not why.startswith('wait'):
                        FSKIP.add(k33)
                        state('SKIP follow of %s/%d.csv (score %r): %s' % (lane, n, sc, why))
                    continue                   # not marked seen: checked again next loop (a wait ends, a lower row may go)
            h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
            key = '%s-%d-%s' % (lane, n, h[:12])
            if key in seen:
                continue
            seen[key] = sc
            if int(R) >= 31:
                hit = claimed_by_other(h, [re.escape('%s/%d.csv' % (lane, n))])
                if hit and producer_done(hit, lane):
                    hit = None
                if hit:
                    seen.pop(key, None)            # checked again each loop: the claim may lapse after 60 minutes
                    if key not in FSKIP:
                        FSKIP.add(key)
                        state('SKIP follow of %s/%d.csv (sha256 %s): another lane claimed it first: %s' % (lane, n, h[:16], hit))
                    continue
            p = '%s/starts/%d-%s-%s.csv' % (W, n, lane, h[:12])
            shutil.copy(f, p)
            if hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
                seen.pop(key); continue
            k0 = len(out)
            out.append(dict(owner='invent', id='follow:' + key, n=n, start=p, orig=f, start_score=sc, gap=sc - bars[n], pred=bars[n] - sc,
                            seconds=180, seed=11, fq=False, queue=t, tool='invent_rest.py lkick (180 s, seed 11, no fq inside)',
                            source_text=('invent_rest.py lkick from the byte copy %s (sha256 %s), taken at queue time from the certified '
                                         'round %s take %s/%d.csv; its take.tsv row: %s' % (p, h, R, lane, n, parent_src(d, r))),
                            licence_text=(r.get('licence') or '')))
            kl = re.match(r'take-(midm|twoshort|invent)-', lane)
            if int(R) >= 32:
                kl = True                      # round 32 (brief 6a, our r31 next 4): the 900 s kick only for rows 1e-5 or more below
            if int(R) >= 38:
                pass                           # round 38 (brief 6b): forensics owns the composer and the first 900 s seed
            elif int(R) >= 34 and bars[n] - sc >= 1e-5:
                # round 34 (brief 6c, 8): a fresh row 1e-5 or more below the bar gets two unprobed 900 s midm kicks, two seeds
                # (border's 753 and 998 came on the second seed; a 120 s probe stopped 7 of 13 of our r33 kicks)
                for suf, sd in (('-m', 3100 + n), ('-m2', 3300 + n)):
                    out.append(dict(owner='midm', claim=lane, id='follow:' + key + suf, n=n, start=p, orig=f, start_score=sc,
                                    gap=sc - bars[n], pred=bars[n] - sc, seconds=900, probe=0, seed=sd, sigma=0.04, queue=t,
                                    tool='midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d)' % sd,
                                    source_text=('midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d) from the byte copy %s (sha256 %s), '
                                                 'taken at queue time from the certified round %s take %s/%d.csv; its take.tsv row: %s'
                                                 % (sd, p, h, R, lane, n, parent_src(d, r))),
                                    licence_text=(r.get('licence') or '')))
            elif int(R) >= 34:
                pass
            elif int(R) >= 31 and (bars[n] - sc >= 1e-5 or (bars[n] - sc >= 1e-7 and not kl)):
                # round 31 (brief 6b, 6c): backlog is the follow lane; a fresh row 1e-7 or more below the bar (1e-5 for a
                # kick lane's row) gets one 900 s midm kick, stopped at 120 s when no try improved
                out.append(dict(owner='midm', claim=lane, id='follow:' + key + '-m', n=n, start=p, orig=f, start_score=sc,
                                gap=sc - bars[n], pred=bars[n] - sc, seconds=900, probe=120, seed=3100 + n, sigma=0.04, queue=t,
                                tool='midm_scan.py kick,lkick (sigma 0.04, 900 s, probe 120 s)',
                                source_text=('midm_scan.py kick,lkick (sigma 0.04, 900 s, probe 120 s, seed %d) from the byte copy %s (sha256 %s), '
                                             'taken at queue time from the certified round %s take %s/%d.csv; its take.tsv row: %s'
                                             % (3100 + n, p, h, R, lane, n, parent_src(d, r))),
                                licence_text=(r.get('licence') or '')))
            if 31 <= int(R) < 34 and bars[n] - sc >= 1e-4 and not os.path.exists(W + '/NO_M2'):
                # (work/NO_M2 since 20:46Z: the -m2 scans certified 0 of 7, 6 stopped at the probe; brief 6e)
                # round 31: a fresh row 1e-4 or more below the bar (the harvest public jazivxt rows after their quench fq,
                # 1.7e-4 to 7.4e-4) is fresh geometry; it gets a second probe-gated 900 s scan with the wider moves
                # (bkick, melt) and another seed (brief 6a: two more seeds for a row that gained 1e-5 or more)
                out.append(dict(owner='midm', claim=lane, id='follow:' + key + '-m2', n=n, start=p, orig=f, start_score=sc,
                                gap=sc - bars[n], pred=bars[n] - sc, seconds=900, probe=120, seed=3300 + n, sigma=0.04, queue=t,
                                modes='lkick,bkick,melt,kick', tool='midm_scan.py lkick,bkick,melt,kick (sigma 0.04, 900 s, probe 120 s)',
                                source_text=('midm_scan.py lkick,bkick,melt,kick (sigma 0.04, 900 s, probe 120 s, seed %d) from the byte copy %s '
                                             '(sha256 %s), taken at queue time from the certified round %s take %s/%d.csv; its take.tsv row: %s'
                                             % (3300 + n, p, h, R, lane, n, parent_src(d, r))),
                                licence_text=(r.get('licence') or '')))
            if int(R) >= 31:
                pass
            elif int(R) >= 28 and bars[n] - sc >= 1e-7 and not kl:
                # round 28: a fresh design of a non-kick lane (1e-7 or more below the bar) also gets one midm kick from
                # the same byte copy, behind the lkick; it takes the slots the near kicks held (0 of 34 in round 27)
                # round 29: a row 1e-5 or more below the bar gets its kick at 900 s (the big first-kick wins of round 28,
                # 684 748 910 971, were all such rows; rebuild measured 3.1e-5 on 748 from one 900 s kick)
                ks = 900 if int(R) >= 29 and bars[n] - sc >= 1e-5 else 240
                out.append(dict(owner='midm', claim=lane, id='follow:' + key + '-m', n=n, start=p, orig=f, start_score=sc,
                                gap=sc - bars[n], pred=bars[n] - sc, seconds=ks, seed=2800 + n, sigma=0.04, queue=t,
                                tool='midm_scan.py kick,lkick (sigma 0.04, %d s)' % ks,
                                source_text=('midm_scan.py kick,lkick (sigma 0.04, %d s, seed %d) from the byte copy %s (sha256 %s), taken '
                                             'at queue time from the certified round %s take %s/%d.csv; its take.tsv row: %s'
                                             % (ks, 2800 + n, p, h, R, lane, n, parent_src(d, r))),
                                licence_text=(r.get('licence') or '')))
            if int(R) >= 31:
                ts = now()[:19]
                for it in out[k0:]:
                    it['preclaimed'] = ts
                handoff('%s: claims the follow of %s/%d.csv (sha256 %s): %s, start %s' % (
                    lane.split('-')[1], lane, n, h, ' and '.join(it['tool'] for it in out[k0:]), p))
    return out


def refollow_items(bars, take, st, seen):
    """Round 31: the lowest live row of each n (another lane's, below the bar, not passed by ours) whose 180 s lkick
    follow (seed 11) finished without a certified row gets one more lkick from the same byte copy: 300 s, seed 12. It
    takes the fill slots the held, mine and fresh kicks held (0 of 20 by 20:45Z), behind the follows and the legs; lkick
    follows certified 10 of 29 by then."""
    import hashlib
    out = []
    if int(R) < 31 or int(R) >= 35 or os.path.exists(W + '/NO_REFOLLOW'):
        return out                         # round 35 (brief 6b, 8): the 300 s refollow after a dry follow gave 0 of 8 in round 34
    done = set(st['done'])
    for t in sorted(glob.glob(S + '/take-*-r%s/take.tsv' % R)):
        d = os.path.dirname(t); lane = os.path.basename(d)
        if d == T:
            continue
        try:
            rows = list(csv.DictReader(open(t), delimiter='\t'))
        except Exception:
            continue
        for r in rows:
            try:
                n = int(r['n']); sc = float(r['new'])
            except (KeyError, ValueError):
                continue
            f = '%s/%d.csv' % (d, n)
            if n not in bars or not sc < bars[n] - 1e-10 or not os.path.exists(f) or n in out31():
                continue
            if sc > live_r25(n) + 1e-15 or (n in take and take[n]['new'] < sc - 1e-12):
                continue
            h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
            fkey = '%s-%d-%s' % (lane, n, h[:12])
            rid = str(st['claimed'].get('follow:' + fkey, ''))
            if not rid.startswith('b') or rid not in done or fkey in seen:
                continue
            p = '%s/starts/%d-%s-%s.csv' % (W, n, lane, h[:12])
            if not os.path.exists(p) or hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
                continue
            seen[fkey] = sc
            out.append(dict(owner='invent', claim=lane, id='refollow:' + fkey, n=n, start=p, orig=f, start_score=sc, gap=sc - bars[n],
                            pred=bars[n] - sc, seconds=300, seed=12, fq=False, queue=t, walked=True,
                            tool='invent_rest.py lkick (300 s, seed 12, no fq inside)',
                            source_text=('invent_rest.py lkick from the byte copy %s (sha256 %s), taken at queue time from the certified '
                                         'round %s take %s/%d.csv; its take.tsv row: %s' % (p, h, R, lane, n, parent_src(d, r))),
                            licence_text=(r.get('licence') or '')))
    return out


# round 35 (brief 6c, 6d, 6f, 6i, 8): the deep-kick rows that an owner lane hands over in the handoff log
HELD35 = S + '/gather/round34-2026-11-17a.csv'
HELD35_TXT = 'held round 34 a row of n = %d (gather/round34-2026-11-17a.csv, Kaggle ref 58465126, bar35)'
if int(R) >= 36:                       # round 36: the held file is round 35 a (bar36)
    HELD35 = S + '/gather/round35-2026-11-17a.csv'
    HELD35_TXT = 'held round 35 a row of n = %d (gather/round35-2026-11-17a.csv, Kaggle ref 58477861, bar36)'
if int(R) >= 37:                       # round 37: the held file is round 36 b (bar37)
    HELD35 = S + '/gather/round36-2026-11-18b.csv'
    HELD35_TXT = 'held round 36 b row of n = %d (gather/round36-2026-11-18b.csv, Kaggle ref 58489503, bar37)'
if int(R) >= 38:                       # round 38: the held file is round 37 a (bar38)
    HELD35 = S + '/gather/round37-2026-11-18a.csv'
    HELD35_TXT = 'held round 37 a row of n = %d (gather/round37-2026-11-18a.csv, Kaggle ref 58500381, bar38)'
_HROWS = {}
HAND = re.compile(r'^(\S+) ([a-z0-9-]+) -> ([^:]+): .*?\bhand(?:s|ed|ing)?\b.{0,40}?\bdeep[- ]?kick.{0,40}?\bn ?= ?(\d+)\b', re.I)
BACK = re.compile(r'^(\S+) ([a-z0-9-]+) -> [^:]+: .*?\btak(?:es|ing|en) back\b.{0,60}?\bn ?= ?(\d+)\b', re.I)
ONE_DONE = re.compile(r'exactly one|\bone (?:unprobed |dry )?(?:900 s )?(?:deep )?kick|\b1 (?:unprobed |dry )?(?:900 s )?(?:deep )?kick|'
                      r'second seed|needs? (?:its|the|a|one) (?:second|2nd)|one seed (?:done|ran|dry)|1 of 2', re.I)
HANDWALK = {}
PREWALK = {}


def held35_rows(n):
    if not _HROWS:
        for r in csv.DictReader(open(HELD35)):
            _HROWS.setdefault(int(r['n']), []).append(r)
    return _HROWS.get(n, [])


def hand_lines():
    """Hand lines of other lanes in this round's log, minus the rows the same lane took back later: {n: (ts, lane, line)}."""
    out = {}
    for line in open(LOG, errors='replace'):
        m = HAND.match(line)
        msg = line.split(' -> ', 1)[-1].split(': ', 1)[-1]
        k = msg.lower().find('hand')
        if m and not m.group(2).startswith('backlog') and k >= 0 and not re.search(r'\bclaim|\brelease', msg[:k], re.I):
            out.setdefault(int(m.group(4)), (m.group(1), m.group(2), line.strip()))
            continue
        b = BACK.match(line)
        if b and int(b.group(3)) in out and out[int(b.group(3))][1] == b.group(2):
            out.pop(int(b.group(3)))
    return out


def hand_items(bars, take, st, seen):
    """Round 35 (brief 6d, 8): a row an owner hands over ('<lane> -> ...: hands deep kick n=N ...') becomes unprobed 900 s
    midm kicks of the held round 34 a row (the bar35 row, our submitted file), on idle slots behind the follows and the
    legs. One kick (seed 3700+n) when the hand line says the row already had one unprobed 900 s kick since its geometry
    (its second seed paid every time in round 34), two (seeds 3500+n, 3700+n) otherwise. The row is walked at dispatch
    (quench_walk.check through a held-reference sidecar, rule 6i) and claimed by its bytes 5 s before the start (6f)."""
    import hashlib
    out = []
    if int(R) < 35 or os.path.exists(W + '/NO_HAND'):
        return out
    for n, (ts, lane, line) in sorted(hand_lines().items()):
        if str(n) in seen or n not in bars:
            continue
        rows = held35_rows(n)
        if len(rows) != n:
            continue
        import backlog_gate27 as G
        sc = G.quick(n, rows)
        if abs(sc - bars[n]) > 1e-12:
            seen[str(n)] = 'held row %r is not the bar %r' % (sc, bars[n])
            state('SKIP hand n=%d from %s: the held round 34 a row scores %r, not the bar35 %r' % (n, lane, sc, bars[n])); continue
        p = '%s/starts/%d-held34a.csv' % (W, n)
        if not os.path.exists(p):
            with open(p + '.tmp', 'w', newline='') as h:
                w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in rows:
                    w.writerow([n, r['square_id'], r['x'], r['y'], r['angle']])
            os.replace(p + '.tmp', p)
            json.dump({'source': HELD35_TXT % n, 'licence': 'ours (held round 34 a row, a file we submitted)'}, open(p[:-4] + '.json', 'w'))
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        seen[str(n)] = h[:12]
        one = bool(ONE_DONE.search(line))
        seeds = [('-h2', 3700 + n)] if one else [('-h1', 3500 + n), ('-h2', 3700 + n)]
        for suf, sd in seeds:
            out.append(dict(owner='midm', claim=lane, id='hand:%s-%d-%s%s' % (lane, n, h[:12], suf), n=n, start=p, orig=p, start_score=sc,
                            gap=sc - bars[n], pred=(2.0 if one else 1.0) - (0.5 if suf == '-h2' and not one else 0.0), seconds=900, probe=0,
                            seed=sd, sigma=0.04, queue=LOG, hand_line=line[:400], hand_ts=ts,
                            tool='midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d)' % sd,
                            source_text=('midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d) from the byte copy %s (sha256 %s) of the '
                                         '%s, handed over by %s at %s' % (sd, p, h, HELD35_TXT % n, lane, ts)),
                            licence_text='ours: held round 34 a row'))
        state('QUEUE hand n=%d from %s (%s): %d unprobed 900 s seed(s) %s of the held row %r, start %s' % (
            n, lane, ts, len(seeds), [s for _, s in seeds], sc, p))
    return out


def hand_walk(it):
    """Rule 6i: walk the handed held row before the kick (quench_walk.check reads the sidecar's held reference and walks the
    results table row of round 34 and below to its roots). Cached per n. Returns (ok, note)."""
    wp = it.get('walk', it['start'])
    if wp in HANDWALK:
        return HANDWALK[wp]
    if int(R) >= 36:
        # round 36: the walk runs in its own process (backlog_prewalk.py); None means it is still running
        import hashlib
        key = hashlib.sha256(wp.encode()).hexdigest()[:16] + '-' + sha_of(wp)[:12]
        oj = '%s/walkcache/%s.json' % (W, key)
        r = load(oj, None)
        if r is None:
            if key not in PREWALK or PREWALK[key].poll() is not None:
                if key in PREWALK:
                    HANDWALK[wp] = (False, 'walk process ended with no result (rc %s)' % PREWALK[key].returncode)
                    return HANDWALK[wp]
                if sum(1 for q in PREWALK.values() if q.poll() is None) >= 2:
                    return (None, 'waiting for a walk slot')      # at most two walks at once on boxA
                PREWALK[key] = subprocess.Popen(['nice', '-n', '5', sys.executable, '-I', LANE + '/backlog_prewalk.py', wp, oj],
                                                stdout=subprocess.DEVNULL, stderr=open(oj[:-5] + '.err', 'w'))
            return (None, 'walking')
        ok = r['clean'] and not r['capped']
        HANDWALK[wp] = (ok, ('; '.join(r['hits'])[:400] or 'clean') + ', files %s, capped %s (%.0f s)' % (r['files'], r['capped'], r['seconds']))
        return HANDWALK[wp]
    import quench_walk
    t0 = time.time()
    try:
        g = quench_walk.check(wp)
        if int(R) >= 36 and g.get('clean') and g.get('capped'):
            # round 36 (brief 6g): a clean walk that stopped at the 3000-file cap is no proof; walk again with cap 100000
            g = quench_walk.check(wp, cap=100000)
        ok = bool(g.get('clean')) and not (int(R) >= 36 and g.get('capped'))
        note = '; '.join(g.get('hits') or [])[:400] or 'clean'
        if int(R) >= 36:
            note += ', files %s, capped %s' % (g.get('files'), g.get('capped'))
    except Exception as ex:
        ok, note = False, 'walk failed: %r' % (ex,)
    HANDWALK[wp] = (ok, note + ' (%.0f s)' % (time.time() - t0))
    return HANDWALK[wp]


JOIN = re.compile(r'^(\S+) k123 -> all: uncounted [\w -]*?donor n=(\d+), side=([0-9.]+), above bar by ?([0-9.e-]+); ordinary fq already run.*?($SCRATCH/bounties-squares/take-k123-r\d+/near/\S+?\.csv)')
# round 36: k123's new donor line ('certified near donor n=N, side=S, score=..., gap_to_bar=G, board_room=..., sha256=..., <path>')
JOIN2 = re.compile(r'^(\S+) k123 -> all: certified near donor n=(\d+), side=([0-9.]+), score=[0-9.e-]+, gap_to_bar=([0-9.e-]+),.*?($SCRATCH/bounties-squares/take-k123-r\d+/near/\S+?\.csv)')
JOIN_MAX = 1e-4                       # 14:43Z: 0 of 11 donors 1e-4 or more above the bar certified; they held slots that follows need
if int(R) >= 38:
    JOIN_MAX = 1e-7                   # round 38 (brief 6d): only donors within 1e-7 of score of the bar paid (793); 1e-6 or more gave 0 of 30
SPENT38 = {372, 367, 591, 642}        # round 38 (brief 6g): spent donor n


def join_items(bars, seen):
    """Round 35 (11:50Z decision, take-backlog-r35/STATE.txt): a quenched k123 join donor ('uncounted ... donor n=N ...
    ordinary fq already run, <path>') that lies less than 3e-4 of score above bar35 and that no lane claimed 20 minutes
    after its post gets one unprobed 900 s midm_scan lkick,kick (seed 3900+n) on an idle slot, behind follows, legs and
    handed rows. invent's fresh 900 s search of such donors gave the round 34 790 (1.154e-4); invent lost its boxE
    slots at 11:29Z, and our slots stood idle. The start is our byte copy, pinned by sha256 at queue time."""
    import hashlib, shutil
    out = []
    if int(R) < 35 or os.path.exists(W + '/NO_JOIN'):
        return out
    import backlog_gate27 as G, calendar
    for k, v in list(seen.items()):
        if k.startswith('geom:') and int(k[5:]) not in GEOM:
            GEOM[int(k[5:])] = list(v)
    lines = open(LOG, errors='replace').readlines()
    prev = ''
    if int(R) >= 36:
        # round 36 (brief 6c, 8): the round 35 k123 donors nobody claimed in round 35 join the shared pool too
        prev = open(S + '/handoff-r%d.log' % (int(R) - 1), errors='replace').read()
        lines = [l for l in prev.splitlines(True) if JOIN.match(l)] + lines
    for line in lines:
        m = JOIN.match(line) or (JOIN2.match(line) if int(R) >= 36 else None)
        if not m:
            continue
        if prev and line in prev:
            f0 = m.group(5)
            try:
                h0 = hashlib.sha256(open(f0, 'rb').read()).hexdigest()[:12]
            except OSError:
                continue
            if any((h0 in l or os.path.basename(f0) in l) and ' k123 -> ' not in l[:40] for l in prev.splitlines()):
                continue               # claimed (and kicked) in the round before
        ts, n, f = m.group(1), int(m.group(2)), m.group(5)
        if f in seen or n not in bars or time.time() - calendar.timegm(time.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S')) < (60 if int(R) >= 36 else 1200):
            continue
        if not os.path.exists(f):
            seen[f] = 'gone'; continue
        rows = list(csv.DictReader(open(f)))
        try:
            sc = G.quick(n, rows)
        except Exception:
            seen[f] = 'unreadable'; continue
        seen[f] = sc
        if int(R) >= 38 and n in SPENT38:
            continue                   # round 38 (brief 6g): spent donor n
        if len(rows) != n or not sc - bars[n] < JOIN_MAX or live_r25(n) < bars[n] - 1e-10:
            continue                   # too far above the bar, or a lane already certified this n this round (brief 6e)
        if 36 <= int(R) < 38:          # round 38 (rule 6l): count by geometry, not by score (the GEOM test below)
            if sc > seen.get('best:%d' % n, math.inf) - 1e-9:
                continue               # round 36: a donor of this n no lower than one already queued (k123 posts several per n)
            seen['best:%d' % n] = sc
        room = None
        if int(R) >= 36:
            # round 36 (brief 6c): board room = (bar - board best) - (donor - bar); no room gave 0 of 11, so skip it
            bb = board36().get(n)
            room = (bars[n] - bb) - (sc - bars[n]) if bb is not None else 0.0
            if room <= 0:
                state('SKIP join n=%d donor %s: no board room (%.3e; board %r, bar %r, donor %r)' % (n, f, room, bb, bars[n], sc)); continue
        if int(R) >= 37:
            # round 37 (brief 6c): kick a donor only when its held share at 1e-3 is under 0.5 and no donor of this n
            # already fell back to the bar this round
            why = fellback(n)
            if why:
                seen.pop('best:%d' % n, None)
                state('SKIP join n=%d donor %s: a donor of this n already fell back to the bar this round: %s' % (n, f, why)); continue
            try:
                sh3 = held_share(f, n)
            except Exception as ex:
                state('SKIP join n=%d donor %s: held share failed %r' % (n, f, ex)); continue
            if sh3 >= 0.5:
                seen.pop('best:%d' % n, None)
                state('SKIP join n=%d donor %s: held share at 1e-3 %.3f (rule 6c: under 0.5 only)' % (n, f, sh3)); continue
            same = [g for g in GEOM.get(n, []) if pair_share(f, g) >= 0.9]
            if int(R) >= 38 and not same:
                # round 38 (rule 6d, 6l): one seed per endpoint too: k123 posts several donors of one side (973: five at
                # 31.688379939339, pair share under 0.9 between them); a donor within 1e-11 of score of one we queued is
                # that endpoint again
                same = [g for g in GEOM.get(n, []) if isinstance(seen.get(g), float) and abs(seen[g] - sc) < 1e-11]
            if same:
                state('SKIP join n=%d donor %s: same geometry as the donor %s we queued (0.9 or more of the centres within 1e-3; rule 6c, one seed per geometry)' % (n, f, same[0]))
                continue
            GEOM.setdefault(n, []).append(f)
            seen['geom:%d' % n] = GEOM[n]      # round 38: the geometries we queued survive a ctl restart
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        p = '%s/starts/%d-k123join-%s.csv' % (W, n, h[:12])
        shutil.copy(f, p)
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
            continue
        seeds = ((3900 + n, ''), (4100 + n, '-2')) if int(R) >= 36 else ((3900 + n, ''),)
        if int(R) >= 37:
            seeds = ((5300 + n, ''),)        # round 37 (brief 6c, our r36 next 3): one seed per donor geometry
        for sd, suf in seeds:
            out.append(dict(owner='midm', claim='k123', id='join:k123-%d-%s%s' % (n, h[:12], suf), n=n, start=p, orig=f, walk=f, start_score=sc,
                        gap=sc - bars[n], pred=(room - (1.0 if suf else 0.0)) if room is not None else -(sc - bars[n]), seconds=900, probe=0,
                        seed=sd, sigma=0.04, queue=LOG, hand_ts=ts,
                        claim_pats=[re.escape(os.path.basename(f))],
                        tool='midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d)' % sd,
                        source_text=('midm_scan.py kick,lkick (sigma 0.04, 900 s, no probe, seed %d) from the byte copy %s (sha256 %s) of the '
                                     'k123 round %s join donor %s (posted %s, uncounted, %.3e of score above bar%s)' % (sd, p, h, R, f, ts, sc - bars[n], R)),
                        licence_text=''))
        state('QUEUE join n=%d from k123 (%s): %.3e of score above bar%s, board room %s, unprobed 900 s seed(s) up to %d, start %s' % (
            n, ts, sc - bars[n], R, '%.3e' % room if room is not None else '-', sd, p))
    return out


FELL = {}                              # round 37: n -> why, a donor of this n that fell back to the bar this round
FELLRX = re.compile(r'\bfell back\b.{0,80}?\bn ?= ?(\d+)\b|\bn ?= ?(\d+)\b.{0,160}?\bfell back\b', re.I)


def fellback(n):
    """Round 37 (brief 6c(3)): our own join run of n that ended within 1e-9 of score of the bar, or a line of another
    lane in handoff-r37.log that says a donor of n fell back."""
    if n in FELL:
        return FELL[n]
    for line in open(LOG, errors='replace'):
        m = FELLRX.search(line)
        if m and int(m.group(1) or m.group(2)) == n and not line.split(' ', 2)[1].startswith('backlog'):
            return line.strip()[:160]
    return None


GEOM = {}                              # round 37: n -> donor files we queued (one seed per geometry)


def pair_share(f, g):
    """Round 37: fraction of the centres of F within 1e-3 of a centre of G (corner aligned, best of 8 symmetries)."""
    import numpy as np
    from scipy.spatial import cKDTree
    def pts(p):
        a = np.array([[float(r['x'].lstrip('s')), float(r['y'].lstrip('s'))] for r in csv.DictReader(open(p))]); return a - a.min(0)
    A, B = pts(f), pts(g); t = cKDTree(B); best = 0.0
    for k in range(8):
        X = A.copy()
        if k & 1:
            X[:, 0] = A[:, 0].max() - X[:, 0]
        if k & 2:
            X[:, 1] = A[:, 1].max() - X[:, 1]
        if k & 4:
            X = X[:, ::-1]
        best = max(best, float((t.query(X)[0] < 1e-3).mean()))
    return best


_HS = {}


def held_share(f, n):
    """Round 37 (brief 6c(1)): invent's heldshare.py (tools/invent/round36) against the held round 36 b row of n."""
    import importlib.util
    if 'm' not in _HS:
        sp = importlib.util.spec_from_file_location('heldshare36', LANE + '/tools/invent/round36/heldshare.py')
        m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        for r in csv.DictReader(open(HELD35)):
            m._h.setdefault(int(r['n']), []).append((float(r['x'].lstrip('s')), float(r['y'].lstrip('s'))))
        _HS['m'] = m
    return _HS['m'].share(f, n)[1][0]


NEARPUB = S + '/take-harvest-r26/work/near-pub/queue-fresh.tsv'
_BOARD = {}


def board36():
    """Round 36 (brief 6c): the board's best score per n (main-r17/gap-by-n.tsv, the per-puzzle board of 2026-11-09)."""
    if not _BOARD:
        for r in csv.DictReader(open(S + '/main-r17/gap-by-n.tsv'), delimiter='\t'):
            try:
                _BOARD[int(r['n'])] = float(r['board_L']) / math.sqrt(int(r['n'])) - 1
            except (KeyError, ValueError):
                pass
    return _BOARD


def nearpub_items(seen):
    """Round 26: harvest's fresh public near misses (harvest -> backlog,midm 14:46Z), 2e-10 to 6e-5 above the bar and
    not moved by one fq: one midm kick each, nearest first, the first design of each n before the second."""
    out = []
    if int(R) >= 27 or not os.path.exists(NEARPUB):    # round 26: 0 of 30 near-pub kicks certified
        return out
    rows = list(csv.DictReader(open(NEARPUB), delimiter='\t'))
    rows.sort(key=lambda r: (r['start'].endswith('-1.csv'), float(r['gap'])))
    for r in rows:
        n = int(r['n']); key = 'nearpub-' + os.path.basename(r['start'])[:-4]
        if key in seen or n in AUDIT or n in SEED811:
            continue
        seen[key] = 1
        start = S + '/take-harvest-r26/work/' + r['start']
        out.append(dict(owner='midm', id='nearpub:' + key, n=n, start=start, start_score=float(r['score']), gap=float(r['gap']),
                        pred=0.0, seconds=240, seed=2600 + n, sigma=0.04, queue=NEARPUB, tool='midm_scan.py kick,lkick',
                        record_source=('harvest fresh public near miss %s (row of take-harvest-r26/work/near-pub/queue-fresh.tsv: '
                                       'public file %s, updated %s, gap %s above the r25b bar, share of squares within 1e-3 of the '
                                       'held layout %s)' % (start, r['file'], r['updated'], r['gap'], r['share1e3'])),
                        record_licence=r['licence']))
    return out


REOPEN = W + '/reopen-gate.jsonl'
# round 27: near files of the lanes whose raw designs paid when kicked within minutes (round 26: forensics rectangle
# compositions moved in 27 of 38 kicks, k123 raw joins in 12 of 17); quench and twoshort have no round 27 dir
NEARGLOBS = ['take-forensics-r%s/near/*.csv', 'take-k123-r%s/near/*.csv']
# fresh builds of the design lanes only when they are at the bar already (stair-c 804 came 1.4e-9 of side below the
# base at 20:30Z); their many builds 2e-4 of side above the bar stay with their owners
NEARGLOBS_TIGHT = ['take-stair-c-r%s/near/*.csv', 'take-modules-r%s/near/*.csv', 'take-border-r%s/near/*.csv', 'take-invent-r%s/near/*.csv']
_nq = {}


def near_items(bars, seen):
    """One midm kick (kick,lkick, sigma 0.04, 240 s) of each new near file of NEARGLOBS whose side as it stands is
    within 2e-5 of score of the bar or a live take, pinned as a byte snapshot with its sha256 at queue time."""
    import hashlib, shutil
    import backlog_gate27 as G
    out = []
    globs = NEARGLOBS + NEARGLOBS_TIGHT
    if int(R) >= 31 and os.path.exists(W + '/NO_NEAR'):
        return out                             # round 31 from 20:46Z: near kicks certified 0 of 13 (r29 0 of 103), brief 6e
    if int(R) >= 31:
        # round 31: a near file of any other lane that is already below the bar and every live take (quench r30 694 came
        # from a twoshort raw near file); k123 three-way near files stay out (border r30: 0 of 13)
        globs = ['take-%s-r%%s/near/*.csv' % l for l in ('forensics', 'quench', 'twoshort', 'rebuild', 'soft', 'midm',
                                                        'border', 'invent', 'stair-c', 'classfill')]
    for g in globs:
        lim = 1e-8 if g in NEARGLOBS_TIGHT else 2e-5
        for f in sorted(glob.glob(S + '/' + g % R)):
            try:
                k = (f, os.path.getmtime(f))
            except OSError:
                continue
            if k in _nq:
                continue
            _nq[k] = 1
            try:
                rows = list(csv.DictReader(open(f)))
                n = int(rows[0]['n'])
                if n not in bars or len(rows) != n:
                    continue
                q = G.quick(n, rows)
            except Exception:
                continue
            low = min(bars[n], live_r25(n))
            if q - low > lim:
                continue
            rect = int(R) >= 30 and '/take-forensics-r' in f and '-rect' in os.path.basename(f) and q - low <= 3e-5
            if int(R) >= 31:
                # round 31: rectangle lkicks above the bar certified 1 of 18 in r30, k123 three-way near files 0 of 13
                # (border r30); only a near file below the bar and every live take gets its probe-gated 900 s kick
                rect = False
                if '/take-k123-r' in f:
                    continue
            if int(R) >= 30 and q - low > -1e-9 and not rect:
                # round 30: near kicks at or above the bar certified 0 of 103 in round 29 (rebuild: 0 of 9 at the bar
                # side); only a near file already below the bar and every live take gets its kick, at 900 s
                continue
            h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
            key = 'near-%d-%s' % (n, h[:12])
            if key in seen:
                continue
            if int(R) >= 31 and h[:12] in RUNSHA:
                seen[key] = 1                  # round 31: a lane moved a file we already ran to its near/ (quench 974)
                continue
            if int(R) >= 29 and g in NEARGLOBS_TIGHT:
                # round 29: stair-c posts a dozen rebuilds of one count at the bar side (995: 15 files by 06:20Z, most
                # 4.9e-11 under it, the bar layout itself); one kick per count of the tight lanes per round
                if 'tightn-%d' % n in seen:
                    continue
                seen['tightn-%d' % n] = 1
            seen[key] = 1
            p = '%s/starts/%d-near-%s.csv' % (W, n, h[:12])
            shutil.copy(f, p)
            lane = re.search(r'take-([a-z0-9-]+)-r\d+', f).group(1)
            rec = ''
            for side in (f + '.json', f[:-4] + '.json'):
                if os.path.exists(side):
                    rec = 'its record %s (sha256 %s): %s' % (side, hashlib.sha256(open(side, 'rb').read()).hexdigest(),
                                                             open(side, errors='replace').read()[:6000])
                    break
            if int(R) >= 30 and q - low > -1e-9:
                # round 30 fill: a forensics rectangle within 3e-5 above the bar gets a 180 s lkick, and legs while a leg
                # moves 1e-6 (twoshort r29: 180 s lkick chains on such rectangles moved 50 of 77 and gave 737 and 412;
                # midm r29: its one surviving row, 747, came from rect files 1e-5 to 3e-5 above the bar)
                out.append(dict(owner='invent', claim=lane, id='near:' + key + '-rl', n=n, start=p, orig=f, start_score=q, gap=q - bars[n],
                                pred=-(q - low), seconds=180, seed=2900 + n, fq=False, queue=f, walked=True,
                                tool='invent_rest.py lkick (180 s, seed %d, no fq inside)' % (2900 + n),
                                source_text=('invent_rest.py lkick (180 s, seed %d) of the byte copy %s (sha256 %s), taken at queue time from '
                                             'the round %s near file %s; %s' % (2900 + n, p, h, R, f, rec.replace('\t', ' ').replace('\n', ' '))),
                                licence_text='see the record of the near file'))
                continue
            ks = 900 if int(R) >= 30 else 240
            out.append(dict(owner='midm', claim=lane, id='near:' + key, n=n, start=p, orig=f, start_score=q, gap=q - bars[n],
                            pred=(low - q) if int(R) >= 30 else 0.0, seconds=ks, probe=120 if int(R) >= 31 else 0, seed=2700 + n, sigma=0.04, queue=f,
                            tool='midm_scan.py kick,lkick (sigma 0.04, %d s)' % ks,
                            source_text=('midm_scan.py kick,lkick (sigma 0.04, %d s, seed %d) of the byte copy %s (sha256 %s), taken at '
                                         'queue time from the round %s near file %s; %s' % (ks, 2700 + n, p, h, R, f, rec.replace('\t', ' ').replace('\n', ' '))),
                            licence_text='see the record of the near file'))
    return out


def reopen_items(seen):
    """Round 27: frozen per-n files that backlog_reopen27.py gated clean under the round 27 rule (the Samanyu-dev
    seed lifted, share test, assembler walk). Each gets one invent lkick with the start itself among the raw files,
    so the worker's floatsafe and fq quench certify the file as it is when the kick finds nothing lower."""
    import hashlib, shutil
    out = []
    if not os.path.exists(REOPEN):
        return out
    for line in open(REOPEN):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not r.get('ok'):
            continue
        n = int(r['n']); h = r['sha256']; key = 'reopen-%d-%s' % (n, h[:12])
        if key in seen:
            continue
        seen[key] = 1
        f = r['path']; m = re.search(r'/(take-([a-z0-9-]+)-r(\d+))/', f)
        lane = m.group(2) if m else 'unknown'
        p = '%s/starts/%d-reopen-%s.csv' % (W, n, h[:12])
        os.makedirs(W + '/starts', exist_ok=True)
        shutil.copy(f, p)
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
            state('SKIP reopen %s: changed since its gate (sha256 %s)' % (f, h[:16])); continue
        rec = ''
        mt = re.match(re.escape(S) + r'/(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', f)
        if mt:
            for row in csv.DictReader(open(S + '/' + mt.group(1) + '/take.tsv'), delimiter='\t'):
                if row.get('n') == str(n):
                    rec = 'its take.tsv row: %s; licence: %s' % ((row.get('source') or '')[:6000], (row.get('licence') or '')[:2000])
        lic = ''
        for side in (f + '.json', f[:-4] + '.json'):
            if not rec and os.path.exists(side):
                try:
                    j = json.load(open(side))
                    rec = 'its record %s: %s' % (side, json.dumps(j)[:6000])
                    lic = str(j.get('licence', ''))[:2000] if isinstance(j, dict) else ''
                except Exception:
                    rec = 'its record %s' % side
        if int(R) >= 28 and (TAINT.search(f) or TAINT.search(rec)):
            state('SKIP reopen %s n=%d: its record names the withdrawn tree file %s' % (f, n, (TAINT.search(f) or TAINT.search(rec)).group(0)))
            continue
        out.append(dict(owner='invent', claim=lane, id='reopen:' + key, n=n, start=p, orig=f, start_score=r['score'],
                        gap=r['score'] - r['bar'], pred=r['bar'] - r['score'], seconds=180, seed=27, fq=False, include_start=True,
                        walked=True, queue=REOPEN, tool='invent_rest.py lkick (180 s, seed 27, no fq inside) with the start among the raw files',
                        source_text=('round %s re-open (the Samanyu-dev rule lifted) of the byte copy %s (sha256 %s) of the frozen file %s; '
                                     'gate27 at queue time: %s; %s' % (R, p, h, f, ('; '.join(x for x in r.get('lifted', [])[:3] if 'share' not in x)[:600]
                                                                          or 'no hit') if int(R) >= 28 else ('; '.join(r.get('lifted', [])[:3])[:600] or 'no hit'), rec)),
                        licence_text=lic or 'see the record of the frozen file'))
    return out


def excluded_far(n, rows):
    """Geometry guard (harvest's take-harvest-r26/work/tools/audit_ac.py, imported): the smallest symmetric centre
    distance from the result to each excluded layout of rules a-d that exists for n (prvsiyan best-of-1105, the
    Samanyu-dev seeds, the out-count files). Below 0.55 the result is refused (the quench lane's line of 15:01Z)."""
    sys.dont_write_bytecode = True
    if int(R) >= 27:
        import backlog_gate27 as G
        sh = G.shares(n, rows)
        bad = [(l, b) for l, a, b, dd in sh if b >= 0.4]
        txt = '; '.join('%s share 1e-3 %.3f' % ('prvsiyan 1105 row' if 'prvsiyan' in l else 'rule a file', b) for l, a, b, dd in sh)
        return (not bad), 'share test (backlog_gate27.py, out at 0.4 of the squares within 1e-3): %s' % (txt or 'no excluded layout of this n')
    d = S + '/take-harvest-r26/work/tools'
    if d not in sys.path:
        sys.path.insert(0, d)
    import audit_ac
    c = audit_ac.centres(rows)
    ds = [(l, audit_ac.distance(c, audit_ac.centres(r))) for l, r in audit_ac.excluded(n)]
    bad = [(l, x) for l, x in ds if x < 0.55]
    # the note names no excluded source: the r26 assembler's walk (quench_walk NAMES and POS) reads such names as positive signals
    return (not bad), ('geometry guard (audit_ac.py): smallest centre distance to an excluded layout of rules a-d %.3g, refused below 0.55'
                       % min(x for _, x in ds)) if ds else 'geometry guard (audit_ac.py): no excluded layout of rules a-d for this n'


def box_sh(box, cmd, timeout=120):
    return sh(['ssh', '-o', 'ConnectTimeout=15', box, cmd], timeout)


def r34_guard(st, boxes):
    """Round 34 (brief 6e, 6g): (1) a running job whose n got a row of another lane more than 1e-6 of score below the
    job's start gets RUN/KILL on its box (the worker stops the search; the raw files so far still certify). (2) every
    slot's worker pid is checked; a dead worker is restarted with RD/start_worker.sh, and its unfinished job goes back
    to next.json (or is dropped when its done.json exists)."""
    rdof = {b: d for b, d, _ in SLOTS}
    dn = set(st['done'])
    for rid, run in st['runs'].items():
        if rid in dn or run.get('kill') or run.get('box') not in rdof:
            continue
        j = load('%s/runs/%s/job.json' % (W, rid), None)
        if not j or str(j.get('id', '')).startswith('control:') or j.get('start_score') is None:
            continue
        low = live_r25(j['n'])
        if low < j['start_score'] - 1e-6:
            why = 'another lane posted n=%d at %r, %.3e below this start %r (brief 6e)' % (j['n'], low, j['start_score'] - low, j['start_score'])
            box_sh(run['box'], 'test -d %s/runs/%s && echo %s > %s/runs/%s/KILL' % (rdof[run['box']], rid, json.dumps(why), rdof[run['box']], rid))
            run['kill'] = now()
            state('KILL %s %s on %s: %s' % (rid, j['id'], run['box'], why))
    if time.time() > SEARCH_END - 300:
        return
    for box, rd in boxes:
        sl = [x for b, _, x in SLOTS if b == box]
        cmd = 'cd %s && for s in %s; do p=$(cat slot$s/pid 2>/dev/null); c=$(grep -o \'"rid": "[^"]*"\' slot$s/current.json 2>/dev/null | head -1); ' \
              'if [ -n "$p" ] && ps -p $p > /dev/null 2>&1; then echo "S $s alive $p"; else echo "S $s dead $p $c"; fi; done' % (rd, ' '.join(sl))
        r = box_sh(box, cmd)
        if r.returncode != 0:
            state('LIVENESS %s unreachable (rc %s): %s' % (box, r.returncode, (r.stderr or '')[-200:])); continue
        for line in r.stdout.splitlines():
            parts = line.split(' ', 4)
            if len(parts) < 3 or parts[0] != 'S' or parts[2] != 'dead':
                continue
            slot = parts[1]; cj = parts[4] if len(parts) > 4 else ''
            fix = ''
            rid = None
            m = re.search(r'"rid": "([^"]+)"', cj); rid = m.group(1) if m else None
            if rid:
                fix = ('if [ -f runs/%s/done.json ]; then rm -f slot%s/current.json; else rm -f runs/%s/KILL; mv slot%s/current.json slot%s/next.json; fi; '
                       % (rid, slot, rid, slot, slot))
            r2 = box_sh(box, 'cd %s && %s sh start_worker.sh %s; sleep 3; cat slot%s/pid' % (rd, fix, slot, slot))
            state('LIVENESS %s/slot%s worker %s was dead; %s; restarted, new pid %s' % (
                box, slot, parts[3] if len(parts) > 3 else '?', ('job %s re-queued on the slot (or dropped if done)' % rid) if rid else 'no job in flight',
                (r2.stdout.split() or ['?'])[-1]))


def main():
    q = load(W + '/queue.json', {'items': []})
    items = q['items']; byid = {it['id']: it for it in items}
    st = load(W + '/ctl-state.json', {'claimed': {}, 'done': [], 'start': time.time(), 'slot_sec': {}, 'score_gain': {},
                                      'runs': {}, 'seq': 0})
    restored = []                                                 # follow and near-pub items survive a restart, in order
    for it in st.get('follow_items', []):
        if it['id'] not in byid:
            restored.append(it); byid[it['id']] = it
    items[0:0] = restored
    for k, v in st['claimed'].items():
        if str(v).startswith('b'):
            m = re.search(r'-([0-9a-f]{12})(?:-m2?|-rl)?$', k)
            if m:
                RUNSHA.add(m.group(1))
    for k, v in st.get('hold', {}).items():
        HOLD[int(k)] = v                                          # round 38: held lines survive a restart
    take = {}
    if os.path.exists(T + '/take.tsv'):
        for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t'):
            take[int(r['n'])] = dict(held=float(r['held']), new=float(r['new']), source=r['source'], licence=r['licence'])
    state('CTL start pid %d, %d items, slots %s, search end %s' % (os.getpid(), len(items), ['%s/%s' % (b, x) for b, _, x in SLOTS],
                                                                     time.strftime('%H:%M:%SZ', time.gmtime(SEARCH_END))))
    boxes = sorted(set((b, d) for b, d, _ in SLOTS))
    while not os.path.exists(W + '/STOPCTL'):
        try:
            loop(st, items, byid, take, boxes)
            if int(R) >= 38:
                release_holds(take, items, st, force=time.time() > SEARCH_END)   # after this loop's certify
        except Exception as ex:                  # one bad item or file must not stop the lane (21:00Z crash on a removed take file)
            import traceback
            state('CTL loop error %s: %s' % (type(ex).__name__, str(ex)[:300]))
            traceback.print_exc()
        st['hold'] = {str(k): v for k, v in HOLD.items()}
        json.dump(st, open(W + '/ctl-state.json.tmp', 'w')); os.replace(W + '/ctl-state.json.tmp', W + '/ctl-state.json')
        if time.time() > SEARCH_END + 900:
            break
        time.sleep(20)
    try:
        release_holds(take, items, st, force=True)
    except Exception as ex:
        state('CTL release error %r' % ex)
    state('CTL stop')


def loop(st, items, byid, take, boxes):
    if True:
        bars = base()
        for it in reversed(load(W + '/extra.json', [])):          # legs and handed items go ahead of the queue, once each
            if it['id'] not in byid:
                items.insert(0, it); byid[it['id']] = it
        for it in load(W + '/fill.json', []):                         # round 31: own r30 rows, r30c rows, held rows
            if it['id'] not in byid:
                items.append(it); byid[it['id']] = it
        st.setdefault('nearpub_seen', {})
        for it in nearpub_items(st['nearpub_seen']):
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
        st.setdefault('follow_seen', {})
        for it in follow_items(bars, st['follow_seen']):              # new certified r26 layouts go first, after controls
            k = 0
            while k < len(items) and items[k]['id'].startswith('control:'):
                k += 1
            items.insert(k, it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
            hid = 'invent:r25b-held-%d' % it['n']
            if hid in byid and hid not in st['claimed']:
                st['claimed'][hid] = 'superseded by ' + it['id']
            state('QUEUE %s n=%d score %r (bar %r) from %s' % (it['id'], it['n'], it['start_score'], bars[it['n']], it['queue']))
        st.setdefault('near_seen', {})
        for it in near_items(bars, st['near_seen']):
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
            state('QUEUE %s n=%d quick score %r (bar %r, gap %.3e) from %s' % (it['id'], it['n'], it['start_score'], bars[it['n']], it['gap'], it['orig']))
        st.setdefault('reopen_seen', {})
        for it in reopen_items(st['reopen_seen']):
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
            state('QUEUE %s n=%d quick score %r (bar %r, gap %.3e) from %s' % (it['id'], it['n'], it['start_score'], bars[it['n']], it['gap'], it['orig']))
        withdraw_check(take)
        st.setdefault('refollow_seen', {})
        for it in refollow_items(bars, take, st, st['refollow_seen']):
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
            state('QUEUE %s n=%d score %r (bar %r, gap %.3e), 300 s lkick seed 12 after a dry follow' % (it['id'], it['n'], it['start_score'], bars[it['n']], it['gap']))
        st.setdefault('hand_seen', {})
        for it in hand_items(bars, take, st, st['hand_seen']):     # round 35: handed deep-kick rows (brief 6d, 8)
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
        st.setdefault('join_seen', {})
        for it in join_items(bars, st['join_seen']):     # round 35: unclaimed k123 join donors on idle slots
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
        st.setdefault('own_seen', {})
        for it in own_items(take, bars, st['own_seen']):
            items.append(it); byid[it['id']] = it
            st.setdefault('follow_items', []).append(it)
            state('QUEUE %s n=%d own row %r (bar %r, gap %.3e), %d s' % (it['id'], it['n'], it['start_score'], bars[it['n']], it['gap'], it['seconds']))
        # collect
        pending = []
        for box, rd in boxes:
            r = box_sh(box, 'cd %s && for d in runs/*/done.json; do echo $d; done' % rd)
            for line in r.stdout.split():
                rid = line.split('/')[1]
                if rid in st['done'] or rid == '*':
                    continue
                sh(['rsync', '-a', '--exclude', 'start.csv', '--exclude', 'tmp', '%s:%s/runs/%s/' % (box, rd, rid), '%s/runs/%s/' % (W, rid)], 300)
                done = load('%s/runs/%s/done.json' % (W, rid), None)
                if done is None:
                    continue
                item = byid.get(done['id']) or load('%s/runs/%s/job.json' % (W, rid), None)
                st['done'].append(rid)
                run = st['runs'].get(rid, {})
                sec = time.time() - run.get('t0', time.time())
                st['slot_sec'][done['owner']] = st['slot_sec'].get(done['owner'], 0.0) + sec
                state('FINISH %s %s n=%d on %s %s' % (rid, done['id'], done['n'], box, json.dumps({k: done.get(k) for k in ('raw', 'start_score', 'prequench', 'new', 'rc', 'fq_rc', 'error', 'note')})))
                pending.append((done, item, box, rid))
        if int(R) >= 34:
            r34_guard(st, boxes)

        # fill idle slots
        for box, rd in boxes:
            r = box_sh(box, 'cd %s && ls slot1 slot2 slot3 2>/dev/null' % rd)
            busy = {}; cur = None
            for line in r.stdout.splitlines():
                if line.startswith('slot'):
                    cur = line[4]
                elif line.strip() in ('next.json', 'current.json') and cur:
                    busy[cur] = True
            for b, _, slot in SLOTS:
                if b != box or busy.get(slot):
                    continue
                job = None
                # boxB/1 takes the follow items of live r26 takes first; the other slots take the queue and the legs
                # first, so the crowded follow of k123 and twoshort files does not fill every slot
                ff = (box, slot) in FOLLOW_FIRST
                # a file of a kick lane (midm, twoshort, invent) was kicked by its owner already: it waits behind the
                # files of the other lanes, and after three follow runs on one n it is skipped
                def kicker(it):
                    return it['id'].startswith(('follow:take-midm-', 'follow:take-twoshort-', 'follow:take-invent-'))
                def rank(it):
                    if it['id'].startswith('ownf:'):
                        return -2                     # round 38: our own follow of a find before its certified line
                    if int(R) >= 35 and it['id'].startswith('hand:'):
                        return 3                      # round 35 (brief 8): handed deep-kick rows fill idle slots last
                    if int(R) >= 35 and it['id'].startswith('join:'):
                        return 4                      # round 35: k123 join donors nobody claimed, behind everything
                    if int(R) >= 34 and it.get('leg'):
                        return 2                      # round 34: legs (1 of 12 in round 33) fill idle slots behind follows and kicks
                    if int(R) >= 31:
                        i = it['id']
                        if it.get('leg') or (i.startswith('follow:') and not i.endswith(('-m', '-m2') if int(R) >= 34 else '-m')):
                            return 0                  # legs of fresh finds and the 180 s lkick follows first
                        if i.startswith(('follow:', 'near:')):
                            return 1                  # the probe-gated 900 s kick of a fresh row
                        if i.startswith(('own:', 'refollow:')):
                            return 2
                        if i.startswith(('held:', 'mine:', 'fresh:')):
                            return 3                  # 0 of 20 by 20:45Z: the fill behind everything
                        if i.startswith('heldfill:'):
                            return 5                  # round 32: 150 s lkick of an unkicked held row, only when nothing else waits
                        return 4
                    if NEARPUB_FIRST and box == 'boxC' and it['id'].startswith('nearpub:'):
                        return -1                     # boxC measured the near-pub queue first (15:00Z to 16:02Z)
                    if it['id'].startswith('reopen:'):
                        return 0
                    if int(R) >= 30 and it['id'].startswith('near:') and it['id'].endswith('-rl'):
                        return 3                      # round 30 fill: forensics rectangles above the bar, behind own and seed items
                    if int(R) >= 30 and it['id'].startswith('near:'):
                        return 1                      # round 30: only near files below the bar are queued (rebuild r29: 747 907 412)
                    if int(R) >= 30 and it['id'].startswith('fresh:'):
                        return 1                      # round 30: the round 29 rows that set bar30 and missed their 900 s kick
                    if int(R) >= 29:
                        # round 29: near kicks go last (0 certified of 49 by 08:57Z, r28 3 of 70); the follows of the kick
                        # lanes waited behind 116 forensics near items (twoshort 504, 2.1e-5 under the bar, among them)
                        if it['id'].startswith('follow:') or it.get('leg'):
                            return 0 if not (kicker(it) or it['id'].endswith('-m') or it.get('leg')) else 1
                        if it['id'].startswith(('own:', 'seed:')):
                            return 2                  # seed: the open held seed rows (quench -> all 10:19:44Z, 587 gave 3.9e-5)
                        if it['id'].startswith('near:') and re.search(r'take-(forensics|k123)-r', it.get('orig', '')):
                            return 3
                        return 4
                    if it['id'].startswith('follow:') and not kicker(it):
                        return 0
                    if int(R) >= 28 and it['id'].startswith('follow:') and it['id'].endswith('-m'):
                        return 1                      # the midm kick of a fresh take waits behind the lkicks
                    if int(R) >= 28 and it['id'].startswith('near:') and re.search(r'take-(forensics|k123)-r', it.get('orig', '')):
                        return 1                      # round 28: fresh forensics rectangles paid at once (689 and 743 by 00:42Z)
                    if int(R) >= 28 and it['id'].startswith(('nearpub:', 'near:')):
                        return 3                      # round 27: near kicks certified 0 of 34 (round 26 near-pub 0 of 30)
                    if it['id'].startswith(('nearpub:', 'near:')) or it.get('leg'):
                        return 1
                    if it['id'].startswith('follow:'):
                        return 2
                    return 3
                # round 29: within a rank the larger predicted gain goes first (at 07:45Z the harvest 848 take, 4.9e-4 under
                # the bar, waited behind follows of rows 1e-10 under it; the newest item used to go first)
                order = sorted(items, key=lambda it: (rank(it), -(it.get('pred') or 0.0)) if int(R) >= 29 else rank(it))
                o31 = out31() if int(R) >= 31 else set()
                dn = set(st['done'])
                running_n = {int(r.rsplit('-', 1)[1]) for r in st['runs'] if r not in dn and r.rsplit('-', 1)[1].isdigit()}
                for it in order:
                    if it['id'] in st['claimed']:
                        continue
                    if it['id'].startswith('join:'):
                        # round 35: stop when a lane certified the n (brief 6e), walk the donor, claim it by bytes and path
                        if live_r25(it['n']) < bars[it['n']] - 1e-10 or (it['n'] in take):
                            st['claimed'][it['id']] = 'stale: a certified row of this n came in (brief 6e)'
                            state('SKIP %s n=%d: a certified r%s row of this n came in (brief 6e)' % (it['id'], it['n'], R)); continue
                        if int(R) >= 36 and it.get('preclaimed'):
                            # round 36: claimed first, walked after (a donor walk takes 4 to 7 minutes here, and quench took
                            # 9 donors while we walked); no start before the walk is clean (rule 6r)
                            okw, notew = hand_walk(it)
                            if okw is None:
                                continue
                            if not okw:
                                st['claimed'][it['id']] = 'refused at dispatch: ' + notew[:200]
                                handoff('all: RELEASE of the n=%d donor claim sha256 %s (seed %d): the walk refuses it (%s)' % (it['n'], sha_of(it['start'])[:16], it['seed'], notew[:200]))
                                state('SKIP %s n=%d: the walk of the donor refuses it: %s' % (it['id'], it['n'], notew)); continue
                            if not it.get('walk_noted'):
                                it['walk_noted'] = True; state('WALK %s n=%d: %s' % (it['id'], it['n'], notew))
                        if not it.get('preclaimed'):
                            if int(R) >= 38:
                                why = fellback(it['n'])
                                if why:
                                    st['claimed'][it['id']] = 'dropped: a donor of this n fell back (rule 6d)'
                                    state('SKIP %s n=%d: a donor of this n fell back to the bar this round: %s' % (it['id'], it['n'], why)); continue
                                fl = sum(1 for o in items if o['id'].startswith('join:') and o['n'] == it['n'] and o.get('preclaimed') and (
                                    o['id'] not in st['claimed'] or (str(st['claimed'][o['id']]).startswith('b') and st['claimed'][o['id']] not in dn)))
                                if fl >= 2:
                                    continue   # round 38: two of our donor seeds of one n in flight at most; the next waits for their end
                            if sum(1 for o in items if o['id'].startswith(('hand:', 'join:')) and o.get('preclaimed') and o['id'] not in st['claimed']) >= (4 if int(R) >= 36 else 1):
                                continue
                            hit = claimed_by_other(sha_of(it['start']), it.get('claim_pats', []), window=86400)
                            if hit:
                                st['claimed'][it['id']] = 'taken: another lane claimed this donor'
                                state('SKIP %s n=%d: another lane claimed this donor: %s' % (it['id'], it['n'], hit)); continue
                            okw, notew = (True, 'walk after the claim (round 36)') if int(R) >= 36 else hand_walk(it)
                            if int(R) >= 36:
                                hand_walk(it)          # starts the walk process
                            if okw is None:
                                continue       # round 36: the walk still runs in its own process
                            if not okw:
                                st['claimed'][it['id']] = 'refused at dispatch: ' + notew[:200]
                                state('SKIP %s n=%d: the walk of the donor refuses it: %s' % (it['id'], it['n'], notew)); continue
                            it['preclaimed'] = now()[:19]
                            handoff('k123,invent: claims n=%d sha256 %s, 900 s midm_scan lkick,kick UNPROBED (probe 0 s), seed %d, of the uncounted k123 '
                                    'join donor %s (%.3e of score above bar%s, posted %s, no claim in %s), start %s; stops when a lane certifies n=%d'
                                    % (it['n'], sha_of(it['start']), it['seed'], it['orig'], it['gap'], R, it['hand_ts'], '1 minute' if int(R) >= 36 else '20 minutes', it['start'], it['n']))
                            state('CLAIM %s n=%d seed %d; walk: %s' % (it['id'], it['n'], it['seed'], notew))
                            continue
                    if it['id'].startswith('hand:'):
                        # round 35 (brief 6d, 6e, 6f, 6i): a handed held row; still handed, still the lowest live row, walked,
                        # then one claim line that names its bytes; the start waits 5 s and a re-read of the log (below)
                        if it['n'] not in hand_lines():
                            st['claimed'][it['id']] = 'taken back by its owner'
                            state('SKIP %s n=%d: the owner took the row back' % (it['id'], it['n'])); continue
                        if min(live_r25(it['n']), take[it['n']]['new'] if it['n'] in take else math.inf) < it['start_score'] - 1e-12:
                            st['claimed'][it['id']] = 'stale: a lower live row of this n (brief 6e)'
                            state('SKIP %s n=%d: a lower live row of this n came in (brief 6e)' % (it['id'], it['n'])); continue
                        if not it.get('preclaimed'):
                            to = (HAND.match(it.get('hand_line', '')) or [None] * 4)[3] or 'all'
                            if not re.search(r'\b(?:all|backlog)\b', to) and time.time() - __import__('calendar').timegm(time.strptime(it['hand_ts'][:19], '%Y-%m-%dT%H:%M:%S')) < 1200:
                                continue       # a row handed to another lane by name: that lane has 20 minutes to claim it first
                            if any(o['id'].startswith(('hand:', 'join:')) and o.get('preclaimed') and o['id'] not in st['claimed'] for o in items):
                                continue       # one claimed, unstarted hand seed at a time: the next idle slot takes it (10:47Z: 10 seeds claimed for 4 slots)
                            okw, notew = hand_walk(it)
                            if okw is None:
                                continue
                            if not okw:
                                st['claimed'][it['id']] = 'refused at dispatch: ' + notew[:200]
                                state('SKIP %s n=%d: the walk of the handed held row refuses it: %s' % (it['id'], it['n'], notew)); continue
                            hit = claimed_by_other(sha_of(it['start']), [r'^(?=.*\bn ?= ?%d\b)(?=.*held)' % it['n']], window=86400)
                            if hit:
                                st['claimed'][it['id']] = 'taken: another lane claimed this held row'
                                state('SKIP %s n=%d: another lane claimed this held row: %s' % (it['id'], it['n'], hit)); continue
                            it['preclaimed'] = now()[:19]
                            handoff('all: claims n=%d sha256 %s, deep kick 900 s midm_scan lkick,kick UNPROBED (probe 0 s), seed %d, of the %s, '
                                    'start %s; handed over by: %s' % (it['n'], sha_of(it['start']), it['seed'], HELD35_TXT % it['n'], it['start'],
                                                                      it.get('hand_line', '')[:160]))
                            state('CLAIM %s n=%d seed %d; walk: %s' % (it['id'], it['n'], it['seed'], notew))
                            continue
                    if int(R) >= 34 and it.get('preclaimed') and time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(time.time() - 5)) < it['preclaimed']:
                        continue               # round 34 (brief 6f): 5 s after our claim line, then the log is read again below
                    if int(R) >= 32 and it.get('leg') and it.get('start_score') is not None and it['start_score'] - min(
                            live_r25(it['n']), take[it['n']]['new'] if it['n'] in take else math.inf) > 1e-6:
                        # round 32: a leg whose start another row passed by more than 1e-6 since the leg was queued is another
                        # basin now (13:44Z: the 866 leg of b066 ran 2.3e-5 above the k123 866)
                        st['claimed'][it['id']] = 'stale: a lower row of this n passed the leg start by more than 1e-6'; continue
                    if int(R) >= 37 and it['id'].startswith('heldfill:') and sum(
                            1 for r, v in st['claimed'].items() if r.startswith('heldfill:') and str(v).startswith('b') and v not in dn) >= 2:
                        continue               # round 37 (brief 6d): held-row seeds on two slots at most, the rest wait for fresh rows
                    if int(R) >= 32 and it['n'] in running_n and (it.get('leg') or it['id'].startswith(('own:', 'heldfill:'))):
                        continue               # round 32: a leg or own kick waits while another run of the same n is on a slot
                                               # (12:47Z: all three slots on 864, a basin 2e-9 under our finds)
                    if int(R) >= 31 and (box, slot) == ('boxB', '3') and not it['id'].startswith('follow:'):
                        continue               # round 31: boxB/3 waits for follows (soft 686, 3.9e-4, waited 4 to 7 min at 20:00Z)
                    if it['n'] in o31 and not it['id'].startswith('control:'):
                        st['claimed'][it['id']] = 'out: rule 3 share of a public-first tree (work/out31.txt)'
                        state('SKIP %s n=%d: the n is in the round 31 out list (rule 3 share, work/out31.txt)' % (it['id'], it['n'])); continue
                    if int(R) >= 32 and not it['id'].startswith('control:'):
                        wh = withdrawn_hit(it.get('source_text') or '', sha_of(it['start']))
                        if wh:
                            st['claimed'][it['id']] = 'out: withdrawn bytes (%s)' % wh
                            state('SKIP %s n=%d: %s (WITHDRAW lines of handoff-r31/r32, lesson 6d)' % (it['id'], it['n'], wh)); continue
                    if int(R) >= 31 and ((it['id'].endswith('-m2') and os.path.exists(W + '/NO_M2'))
                                         or (it['id'].startswith('near:') and os.path.exists(W + '/NO_NEAR'))):
                        st['claimed'][it['id']] = 'dropped: the kind measured zero this round (brief 6e)'; continue
                    if it['id'].startswith('heldfill:') and (live_r25(it['n']) < it['start_score'] - 1e-12 or it['n'] in take
                                                             or any(o['n'] == it['n'] and str(st['claimed'].get(o['id'], '')).startswith('b')
                                                                    for o in items if o['id'] != it['id'])):
                        st['claimed'][it['id']] = 'stale: a live r%s row, our own row or another run of ours at this n' % R; continue
                    if it['id'].startswith('refollow:') and (live_r25(it['n']) < it['start_score'] - 1e-12
                                                             or (it['n'] in take and take[it['n']]['new'] < it['start_score'] - 1e-12)):
                        st['claimed'][it['id']] = 'stale: a lower live row or our own lower row'; continue
                    if not it.get('leg') and taken_elsewhere(it):
                        st['claimed'][it['id']] = 'owner'; continue
                    if int(R) >= 31 and not it.get('leg') and not it['id'].startswith('own:'):
                        # a held row (the r30c rows included) counts as claimed when any other lane's claim line this round
                        # names n= and the word held: the lanes pin the same held row as different bytes (rebuild held31/,
                        # classfill held/, forensics held-inputs/, twoshort starts/)
                        hk = it['id'].startswith(('held:', 'fresh:', 'mine:', 'heldfill:', 'hand:'))
                        pp = list(it.get('claim_pats', ())) + ([r'^(?=.*\bn ?= ?%d\b)(?=.*held)' % it['n']] if hk else [])
                        if int(R) >= 34 and it['id'].startswith('follow:') and it.get('orig'):
                            # round 34 (brief 6f): an earlier claim of another lane on the followed take file by its path
                            pp.append(re.escape('/'.join(it['orig'].split('/')[-2:])))
                        hit = claimed_by_other(sha_of(it['start']), pp, window=86400 if hk else 3600, before=it.get('preclaimed'))
                        if hit and it['id'].startswith('follow:') and it.get('orig') and producer_done(hit, os.path.basename(os.path.dirname(it['orig']))):
                            hit = None
                        if hit and int(R) >= 38 and it['id'].startswith('follow:') and it.get('orig') and \
                                hit.split(' ', 2)[1] == os.path.basename(os.path.dirname(it['orig'])).split('-')[1]:
                            continue           # round 38 (rule 6b): the producer's own follow runs; ours goes after it (not dropped)
                        if hit:
                            st['claimed'][it['id']] = 'taken: another lane claimed the same start in the last 60 minutes'
                            state('SKIP %s n=%d: another lane claimed the same start in the last 60 minutes: %s' % (it['id'], it['n'], hit))
                            continue
                    if 29 <= int(R) < 31 and (it['id'].startswith('near:') or it['id'].endswith('-m')) and rebuild_has(it):
                        if it['id'].endswith('-rl'):
                            st['claimed'][it['id']] = 'taken: another lane claims this rectangle'
                            state('SKIP %s n=%d: another lane claims this rectangle (path or sha256)' % (it['id'], it['n']))
                            continue
                        # round 29: rebuild kicks fresh take rows and bar-side near files with the same midm tool at 900 s
                        # (its queue-log pins each start by sha256); our 240 s kick of the same bytes would only repeat it
                        st['claimed'][it['id']] = 'taken: rebuild queue-log holds the same bytes (900 s midm kick)'
                        state('SKIP %s n=%d: rebuild kicks the same bytes at 900 s (take-rebuild-r%s/work/queue-log.tsv)' % (it['id'], it['n'], R))
                        continue
                    if it['id'].startswith('seed:') and any(
                            re.search(r'claim', l, re.I) and not l.split(' ', 2)[1].startswith('backlog')
                            and re.search(r'held2[789]/%d\.csv|\bheld\b[^;]{0,40}\bn ?= ?%d\b' % (it['n'], it['n']), l)
                            for l in open(LOG, errors='replace') if len(l.split(' ', 2)) > 2):
                        st['claimed'][it['id']] = 'owner: another lane claims this held seed row'
                        state('SKIP %s n=%d: another lane claims this held seed row' % (it['id'], it['n'])); continue
                    if it['id'].startswith('own:') and (it['n'] not in take or abs(take[it['n']]['new'] - it['start_score']) > 1e-15
                                                        or live_r25(it['n']) <= it['start_score'] + 1e-10):
                        st['claimed'][it['id']] = 'stale: our row changed or another live row is at or below it'; continue
                    if it['id'].startswith('reopen:') and live_r25(it['n']) <= it['start_score'] + 1e-12:
                        # another lane already holds this file or a lower one in its r27 take: the follow item of that
                        # take kicks it, so the re-open would only repeat it
                        st['claimed'][it['id']] = 'taken: a live r%s take is at or below the re-opened file' % R
                        state('SKIP %s n=%d: a live r%s take %r is at or below it' % (it['id'], it['n'], R, live_r25(it['n'])))
                        continue
                    if not it['id'].startswith('control:'):
                        low = min(bars[it['n']], live_r25(it['n']))
                        if it.get('start_score') is not None and it['start_score'] - low > (JOIN_MAX if it['id'].startswith('join:') else 3e-5):
                            st['claimed'][it['id']] = 'superseded: start %.3e above the live best' % (it['start_score'] - low)
                            state('SKIP %s n=%d: start %.3e above the bar or a live r%s take' % (it['id'], it['n'], it['start_score'] - low, R))
                            continue
                    if int(R) >= 28 and it['id'].startswith('follow:') and it['n'] in take and it['start_score'] > take[it['n']]['new'] + 1e-9:
                        # round 28: our own row of this n is lower than the followed file (the invent 499 at 00:19Z was a
                        # kick of a file above ours); the legs of our row cover that n
                        st['claimed'][it['id']] = 'skipped: our own take is lower'
                        state('SKIP %s n=%d: our own take %r is lower than its start %r' % (it['id'], it['n'], take[it['n']]['new'], it['start_score']))
                        continue
                    if int(R) >= 33 and it['id'].startswith(('follow:', 'refollow:')) and not it.get('leg') and \
                            it['start_score'] > min(live_r25(it['n']), take[it['n']]['new'] if it['n'] in take else math.inf) + 1e-12:
                        # round 33 (brief 6d): kick only the lowest live row of an n; a lower row came in while this waited
                        st['claimed'][it['id']] = 'skipped: not the lowest live row of n any more'
                        state('SKIP %s n=%d: start %r is not the lowest live row of n (brief 6d)' % (it['id'], it['n'], it['start_score']))
                        continue
                    if kicker(it):
                        ran = sum(1 for r in st['runs'] if r.split('-')[-1] == str(it['n']) and '-inv-' in r)
                        if ran >= 3:
                            st['claimed'][it['id']] = 'skipped: %d follow runs on n=%d already' % (ran, it['n']); continue
                    elif int(R) >= 30 and it['id'].startswith('follow:') and not it['id'].endswith(('-m', '-m2')):
                        # round 30: quench posts a new fq step of 694 every few minutes (4 rows by 12:44Z); our 180 s lkick of
                        # each was dry. After 3 lkick follows of one n, only a start 1e-6 or more below the lowest start
                        # already followed gets a run
                        prev = [o['start_score'] for o in items if o['id'].startswith('follow:') and o['n'] == it['n'] and not o['id'].endswith(('-m', '-m2'))
                                and str(st['claimed'].get(o['id'], '')).startswith('b')]
                        if len(prev) >= 3 and it['start_score'] > min(prev) - 1e-6:
                            st['claimed'][it['id']] = 'skipped: %d lkick follows of n=%d already, start not 1e-6 below them' % (len(prev), it['n'])
                            state('SKIP %s n=%d: %d lkick follows of this n already and the start is not 1e-6 below them' % (it['id'], it['n'], len(prev)))
                            continue
                    if int(R) == 27 and it['id'].startswith(('follow:', 'near:')):
                        it['walked'] = True        # round 27: no dispatch walk (2 to 3 minutes each on the loaded boxA);
                                                   # the walk of the result at certify time is the gate
                    # round 28: the dispatch walk is back (boxA at load 12): quench_walk reads the WITHDRAW lines of
                    # handoff-r27/r28, so a start that descends from a withdrawn parent (k123 699/932 seed 503, the
                    # classfill 927 branch, the invent 910 tree on the 684 donor) is refused before it takes a slot
                    if int(R) >= 30 and it['id'].startswith(('follow:', 'near:')):
                        # round 30: no dispatch walk for a follow of a live take row. In round 29 it refused 20 of 70 follow
                        # starts, among them 747 910 737 689 916 802, which the assembler then held (bar30); each walk held
                        # a slot about 90 s on the loaded boxA. The walk of the result at certify time is the gate.
                        it['walked'] = True
                    if it['id'].startswith(('follow:', 'nearpub:', 'near:')) and not it.get('walked'):
                        if int(R) >= 27 and it.get('orig'):
                            import backlog_gate27 as G
                            try:
                                # round 29: one walk per start file (the plain and -m follows of a row share it; 90 s each)
                                gk = (it['orig'], os.path.getmtime(it['orig']), os.path.getsize(it['orig']))
                                g = GATE_CACHE.get(gk)
                                if g is None:
                                    g = GATE_CACHE[gk] = G.check(it['orig'], n=it['n'], cert=False, share=False)   # the share test runs on the result, on the box
                                okw, notew = g['ok'], '; '.join(g['hits'])[:600] + ' | ' + G.note(g)
                                if int(R) >= 28 and not okw and it['id'].startswith('follow:'):
                                    # round 28: a live take row of another lane is its owner's certified row; a record gap of
                                    # that owner (a parent changed since pinned, a gone file, no root) does not stop the follow,
                                    # since the assembler judges both rows on the same chain. A WITHDRAW line, a lane refusal or
                                    # a prvsiyan or penguin name still does (rebuild 748 at 00:47Z was refused on a pin note)
                                    rest = [h for h in g['hits'] if not re.match(r'(?:gone: |no root|[^:]*: changed since pinned)', h)]
                                    if not rest:
                                        okw = True
                                    elif re.search(r're-?open\w* under the main rule|main rule of 2026-11-15 00:19', it.get('source_text') or '', re.I):
                                        okw = True   # the owner re-opened this row under the 00:19Z rule and answers for it
                            except Exception as ex:          # the producer replaced or removed the file since the queue
                                okw, notew = False, 'the original file cannot be walked now: %s' % ex
                        else:
                            src0, lic0 = source_of(it)
                            okw, notew = deep_check(it['n'], src0, lic0)
                        it['walked'] = True
                        if int(R) >= 28 and okw:
                            tm = TAINT.search((it.get('source_text') or '') + ' ' + notew)
                            if tm:
                                okw, notew = False, 'its record names the withdrawn tree file %s' % tm.group(0)
                        if not okw:
                            st['claimed'][it['id']] = 'refused at dispatch'
                            state('SKIP %s n=%d: the start fails the ancestry gate: %s' % (it['id'], it['n'], notew[-300:]))
                            continue
                    if int(R) >= 31 and it['id'].startswith('follow:'):
                        # round 31: two lanes post the same basin of one n (border LP of the quench 851, 5e-10 apart); one
                        # follow of each kind per basin: skip when a follow of the same kind within 1e-8 already ran, and
                        # let the lowest unstarted one go first
                        def kind(o):
                            return o['id'].rsplit('-', 1)[-1] if o['id'].endswith(('-m', '-m2')) else ''
                        same = [o for o in items if o['id'].startswith('follow:') and o['n'] == it['n'] and o['id'] != it['id']
                                and kind(o) == kind(it) and abs(o['start_score'] - it['start_score']) < 1e-8]
                        ran = [o['id'] for o in same if str(st['claimed'].get(o['id'], '')).startswith('b')]
                        if ran:
                            st['claimed'][it['id']] = 'skipped: same basin already followed by ' + ran[0]
                            state('SKIP %s n=%d: a follow of the same kind ran on a start within 1e-8 (%s)' % (it['id'], it['n'], ran[0]))
                            continue
                        if any(o['id'] not in st['claimed'] and o['start_score'] < it['start_score'] for o in same):
                            continue
                    if it['id'].startswith('follow:'):
                        lane_n = it['id'].rsplit('-', 1)[0]
                        if int(R) >= 32:
                            # round 32: the -m kick id ends in -m, so the plain rsplit kept the sha256 and a newer, lower file
                            # of the same take never superseded a waiting kick
                            lane_n = re.sub(r'-m2?$', '', it['id']).rsplit('-', 1)[0]
                        if any(o['id'].startswith(lane_n + '-') and o['id'] != it['id'] and o['start_score'] < it['start_score']
                               for o in items if o['id'].startswith('follow:')):
                            st['claimed'][it['id']] = 'superseded by a newer file of the same take'; continue
                    job = it; break
                if job is None:
                    continue
                need = job.get('seconds', 120) + 400
                if int(R) >= 30:
                    # round 30: the worker cuts a job to the deadline itself (seconds = deadline - now - 300), so a job
                    # starts while 450 s are left (round 29: the 400 s margin refused a 300 s leg at 11:35Z)
                    need = min(need, 450)
                if time.time() + need > SEARCH_END:
                    continue
                st['seq'] += 1; rid = 'b%03d-%s-%d' % (st['seq'], job['owner'][:3], job['n'])
                if not job.get('leg') and int(R) >= 31:
                    if not job['id'].startswith(('own:', 'hand:', 'join:', 'ownf:')):     # round 35: a hand item posted its claim before the 5 s wait
                        handoff('%s: claims %s (n=%d), %s, start %s (sha256 %s), %s' % (job.get('claim', job['owner']).replace('take-', '').split('-r')[0],
                                job['id'], job['n'], job['tool'], job['start'], sha_of(job['start']), job.get('orig') or job['queue']))
                elif not job.get('leg'):
                    handoff('%s: claims %s, start %s, %s' % ('harvest,midm' if job['id'].startswith('nearpub:') else job.get('claim', job['owner']),
                                                             job['id'], job['start'], job['queue']))
                st['claimed'][job['id']] = rid
                RUNSHA.add(sha_of(job['start'])[:12])
                j = dict(job); j['rid'] = rid
                j['bar_side'] = (bars[job['n']] + 1) * math.sqrt(job['n'])
                os.makedirs('%s/runs/%s' % (W, rid), exist_ok=True)
                json.dump(j, open('%s/runs/%s/job.json' % (W, rid), 'w'))
                box_sh(box, 'mkdir -p %s/runs/%s' % (rd, rid))
                sh(['scp', '-q', job['start'], '%s:%s/runs/%s/start.csv' % (box, rd, rid)])
                sh(['scp', '-q', '%s/runs/%s/job.json' % (W, rid), '%s:%s/slot%s/next.json.tmp' % (box, rd, slot)])
                box_sh(box, 'mv %s/slot%s/next.json.tmp %s/slot%s/next.json' % (rd, slot, rd, slot))
                busy[slot] = True
                st['runs'][rid] = {'t0': time.time(), 'slot': slot, 'box': box}
                state('START %s %s/slot%s %s n=%d gap %.3e on %s:%s/runs/%s, log run.log, deadline %s'
                      % (rid, box, slot, job['id'], job['n'], job['gap'], box, rd, rid, time.strftime('%H:%M:%SZ', time.gmtime(SEARCH_END))))
        # certify after the slots are filled, so a slow walk on the loaded boxA does not leave a slot idle
        for done, item, box, rid in pending:
            if not item or not done.get('finals'):
                continue
            for m in sorted(int(x) for x in done['finals']):
                sc = certify(done, item, bars, take, st, m, box)
                if item['owner'] not in ('midm', 'invent') or int(m) != done['n'] or sc is None or str(item['id']).startswith('control:'):
                    continue
                # a leg: kick again from the find while a leg moves the side by 1e-6 of score or more, three at most,
                # and only while the find is within 1e-4 of score of the bar
                depth = item.get('leg', 0); s0 = done.get('start_score') or item.get('start_score')
                step = (s0 - sc) if s0 is not None else 0.0
                near_miss = depth == 0 and (-1e-10 if int(R) >= 30 else 0) <= sc - bars[m] < 1e-8      # a near miss above the bar gets one leg
                if int(R) >= 35:
                    near_miss = False         # round 35 (brief 6h): no leg from an endpoint within 1e-10 of the bar (29 legs moved 0)
                # (round 30: also a find less than 1e-10 below the bar, which the rule does not count: rect 591 at 13:18Z, -3.5e-11)
                if int(R) >= 31:
                    # round 31 (brief 6a): a leg from every find that moves the side by more than 1e-6, six deep; a first
                    # scan that gained 1e-5 of score gets two seeds (midm r30: on 412 leg 2 gained 7e-6 after leg 1 gave 1.6e-7)
                    go = depth < 6 and (step * math.sqrt(m) > 1e-6 or near_miss) and sc - bars[m] < 1e-4
                    # no leg from a find that sits more than 1e-6 of score above the lowest live row of n (the soft 686
                    # lkick find at 20:14Z was 1e-4 above the midm 686 row, another basin)
                    go = go and sc - min(bars[m], live_r25(m), take[m]['new'] if m in take else math.inf) < 1e-6
                    if int(R) >= 35:
                        go = go and abs(sc - bars[m]) >= 1e-10   # brief 6h: an endpoint within 1e-10 of the bar is the held basin
                    if int(R) >= 36 and depth == 0 and step * math.sqrt(m) >= 1e-3 and sc - bars[m] < 3e-4 and sc - bars[m] >= 1e-10:
                        go = True                     # round 36 (brief 6c): a find that moved 1e-3 of side or more gets a leg above the bar
                    seeds = [item['seed'] + 100] + ([item['seed'] + 200] if depth == 0 and step >= 1e-5 else [])
                else:
                    go = depth < 3 and (step >= 1e-6 or near_miss) and sc - bars[m] < 1e-4
                    seeds = [item['seed'] + 100]
                for k_s, sd in enumerate(seeds if go else []):
                    lp = '%s/legs/%d-leg%d-%s%s.csv' % (W, m, depth + 1, rid, '' if k_s == 0 else '-s%d' % k_s)
                    os.makedirs(W + '/legs', exist_ok=True)
                    import shutil; shutil.copy('%s/runs/%s/final/%d.csv' % (W, rid, m), lp)
                    lsec = 900 if (int(R) >= 31 and item['owner'] == 'midm') else 300
                    if int(R) >= 34:
                        lsec = 300                    # round 34: every leg is a 300 s lkick (probe-gated 900 s legs gave 0 in round 33)
                    leg = dict(item); leg.pop('ownfollow', None); leg.update(id='%s:leg%d-%s%s' % (item['owner'], depth + 1, rid, '' if k_s == 0 else '-s%d' % k_s), leg=depth + 1,
                                                 start=lp, start_score=sc, gap=sc - bars[m], pred=1.0 + step, seed=sd, seconds=lsec,
                                                 probe=120 if lsec == 900 else 0, queue='own leg of %s' % rid)
                    if int(R) >= 34:
                        leg.update(owner='invent', fq=False, probe=0)
                        leg['tool'] = 'invent_rest.py lkick (leg %d, seed %d, 300 s, no fq inside)' % (depth + 1, sd)
                        leg['source_text'] = ('leg %d from the result of backlog run %s (%s, final file %s/runs/%s/final/%d.csv): %s'
                                              % (depth + 1, rid, item['id'], W, rid, m, item.get('source_text', '')))
                    elif item['owner'] == 'midm' and not item.get('source_text'):
                        leg['record_source'] = 'leg %d of backlog run %s (%s); %s' % (depth + 1, rid, item['id'], item.get('record_source', ''))
                    elif item['owner'] == 'midm':
                        leg['tool'] = 'midm_scan.py kick,lkick (leg %d, sigma 0.04, %d s%s)' % (depth + 1, lsec, ', probe 120 s' if lsec == 900 else '')
                        leg['source_text'] = ('leg %d (midm_scan.py kick,lkick, seed %d, %d s) from the result of backlog run %s (%s, final file '
                                              '%s/runs/%s/final/%d.csv): %s' % (depth + 1, sd, lsec, rid, item['id'], W, rid, m,
                                                                                item.get('source_text', '')))
                    else:
                        leg['tool'] = 'invent_rest.py lkick (leg %d, seed %d, 300 s, no fq inside)' % (depth + 1, sd)
                        leg['source_text'] = ('leg %d from the result of backlog run %s (%s, final file %s/runs/%s/final/%d.csv): %s'
                                              % (depth + 1, rid, item['id'], W, rid, m, item.get('source_text', '')))
                    ex = load(W + '/extra.json', []); ex.append(leg)
                    json.dump(ex, open(W + '/extra.json.tmp', 'w')); os.replace(W + '/extra.json.tmp', W + '/extra.json')
                    state('DECIDE leg %d for n=%d (step %.3e of score, %.3e of side, gap %.3e, seed %d, %d s): %s' % (
                        depth + 1, m, step, step * math.sqrt(m), sc - bars[m], sd, lsec, lp))


if __name__ == '__main__':
    main()
