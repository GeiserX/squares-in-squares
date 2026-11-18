#!/usr/bin/env python3
"""quench: walk the whole recorded tree of one start file before a row counts.

Usage: quench_walk.py START.csv [START.csv ...]   (prints one JSON line per start)

Round 25 lost four quench rows to the skeptic: 860 and 921 reached the
Samanyu-dev seed 983 deeper than quench_audit.py looked, and 911 and 975 could
not be walked because their start files were gone or refused when the skeptic
read them. This walk follows what the round 25 skeptic followed (its walk8.py
and the assembler's deep25.py):
  - the sidecars of every csv (.json, .origin.json, .provenance.json, .source.json)
  - the ledger lines (*.tsv in the csv's dir and in its take dir's work/) that
    name the csv by its bare file name
  - the take.tsv row of a per-n take file (take-<lane>-rNN/<n>.csv)
  - ancestry/<sha256>.json records of every take-*-r22..r26 dir
  - bare csv names, resolved in the dir of the file that names them and in the
    near/ and work/ dirs of its take dir
  - held references (held n = X, held n = X of round K), through the results
    tables of the repo (the latest table at or below round K that holds n)
  - the producing lane's STATE.txt lines that name the start file, for a
    refusal or a withdrawal by that lane
It refuses a start when the text it reaches carries a positive Samanyu-dev seed
signal (negations removed, as deep25.py does), a withdrawn tree, the CC BY-SA
or penguin069 sources, the bare name of a withdrawn file, a refusal by the
producing lane, a missing start or start record, or no root at all (no held
reference and no public file reached).
"""
import csv, glob, json, os, re, sys, time

csv.field_size_limit(1 << 30)
S = '$SCRATCH/bounties-squares/'
LANE = '.'
sys.path.insert(0, LANE)
import forensics_policy  # noqa: E402
import quench_audit  # noqa: E402

PATH = re.compile(r'((?:$SCRATCH/bounties-squares/)?(?:take-[a-z0-9-]+-r\d+|harvest[\w.-]*|gather|seeds)/[^\s"\'<>;,()\[\]{}|\\]*?\.(?:csv|json))(?![\w.-])')
BARE = re.compile(r'(?<![/\w.-])([\w][\w.-]*\.csv)(?![\w.-])')
ANC = re.compile(r'(?<![0-9a-f])([0-9a-f]{64})\.json')
HELD = [(re.compile(r'held(?: packing)?(?: of)? n\s*=\s*(\d+)(?: of round (\d+))?', re.I), 0),
        (re.compile(r'held round\s*(\d+)b? n\s*=?\s*(\d+)', re.I), 1),
        (re.compile(r'n\s*=\s*(\d+) (?:from|of) held round\s*(\d+)', re.I), 0),
        (re.compile(r'round (\d+) packing of n\s*=\s*(\d+)', re.I), 1),
        (re.compile(r'gather/round(\d+)-2026-\d\d-\d\d[a-z]?\.csv[^|;]{0,40}?(?:n\s*=\s*|"n"\s*:\s*)(\d+)'), 1)]  # text or JSON ("path": ..., "n": 694)
NEG = re.compile(r'(?:max centre distance:[^)|\n]*'  # harvest's geometry check that a layout is no copy of an excluded source
                 r'|\[?Samanyu(?:-dev)?(?:\s+GitHub)?(?: seed)?(?: group)? ancestry\s*[:=]?\s*(?:no|none|false)\b[^;|\n\]"]*\]?'
                 r'|recorded ancestry has no Samanyu-dev seed layout|no (?:recorded )?Samanyu(?:-dev)?(?: GitHub)?(?: seed)?(?: ancestry| links?| inputs?| layouts?| input)'
                 r'|Samanyu(?:-dev)? seed ancestry: no|without (?:any )?Samanyu(?:-dev)?[\w ]{0,20}|distinct from (?:the )?Samanyu-dev[\w /]{0,40}'
                 r'|not (?:the )?Samanyu-dev[\w /]{0,40}|Samanyu-dev[\w /]{0,30}(?:is|are) (?:excluded|out)|Samanyu(?:-dev)?[^;|"]{0,40}seed[s]?[^;|"]{0,20}: (?:none|no)\b)', re.I)
POS = re.compile(r'(?!)')
NAMES = re.compile(r'squares-joegun-boxed|penguin069|squares-verified-best-of-1105|CC BY-SA|ShareAlike|801h\b|held n = 801\b|held 801\b', re.I)
PRV = re.compile(r'prvsiyan(?: best-of)?[ -]?1105\s*=\s*([0-9]*\.?[0-9]+)', re.I)
PRV_MIN = 0.55
PIN = re.compile(r'((?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/[^\s"\'<>;,()|]+?\.csv)\s*\(sha256 ([0-9a-fA-F]{12,64})', re.I)
_sha = {}


def file_sha(p):
    """sha256 of a file, cached by (path, mtime); '' when it is not there (the gone check reports that)."""
    try:
        k = (p, os.path.getmtime(p))
    except OSError:
        return ''
    if k not in _sha:
        import hashlib
        _sha[k] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return _sha[k]
REFUSE = re.compile(r'refus|withdr|withh[eo]ld|\bdrop|\bout\b|untrace|unwalk|not clean|superseded by a fix', re.I)
ROOT = re.compile(r'own construction|original.*construction|harvest[\w.-]*/|gather/round|/seeds/|seeds/|kaggle|sis-final-packings|sis-submit|a-square-deal|living-atlas|results/round\d+-best', re.I)
DROPK = {'producer_take_tsv', 'final_competing_takes', 'competing_takes', 'other_takes', 'live_takes', 'excluded', 'rejected',
         'refused', 'withdrawn', 'quarantine', 'quarantined', 'blocked_inputs', 'what_was_measured', 'next', 'coordinates', 'P',
         'points', 'rows', 'squares'}
ANCDIRS = sorted(glob.glob(S + 'take-*-r2[2-7]/work/ancestry')) + sorted(glob.glob(S + 'take-*-r2[2-7]/work/*/ancestry'))
LIVE = '27'
WITHDRAWN_LINES = []
for _h in sorted(glob.glob(S + 'handoff-r2[2-9].log')):
    for _l in open(_h, errors='replace'):
        if re.search(r'\bWITHDRAW|\bWITHHOLD|reclassif', _l):
            for _f in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)', _l):
                WITHDRAWN_LINES.append((_f, _l.strip()))


def withdraw_time(line):
    import calendar
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?)', line)
    if not m:
        return float('inf')
    t = m.group(1) + (':00' if len(m.group(1)) == 16 else '')
    return calendar.timegm(time.strptime(t, '%Y-%m-%dT%H:%M:%S'))


TABLES = {}
for _p in glob.glob(LANE + '/results/round*-best-*.tsv'):
    _k = int(re.search(r'round(\d+)-best', _p).group(1))
    TABLES[_k] = {int(r['n']): r for r in csv.DictReader(open(_p), delimiter='\t')}


def norm(p):
    return p if p.startswith('/') else S + p


_jt = {}


def jtext(p, n):
    key = (p, n, os.path.getmtime(p))
    if key not in _jt:
        _jt[key] = _jtext(p, n)
    return _jt[key]


def _jtext(p, n):
    raw = open(p, errors='replace').read()
    try:
        q = json.loads(raw)
    except ValueError:
        return raw
    if isinstance(q, dict) and q and all(str(k).isdigit() for k in q):
        q = q.get(str(n), {})

    def f(x):
        if isinstance(x, dict):
            return {k: f(v) for k, v in x.items() if k not in DROPK}
        if isinstance(x, list):
            return [f(v) for v in x]
        return x
    return json.dumps(f(q))


def take_row(d, n):
    p = S + d + '/take.tsv'
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, errors='replace'), delimiter='\t'):
            try:
                if int(r['n']) == n:
                    return (r.get('source') or '') + ' || ' + (r.get('licence') or '')
            except (ValueError, KeyError, TypeError):
                pass
    return None


HARVEST = []
for _name in ['harvest-best-2026-11-11.tsv', 'angle-harvest-2026-11-10.tsv', 'harvest-best-2026-11-09.tsv', 'harvest-best-2026-11-07.tsv']:
    if os.path.isfile(LANE + '/results/' + _name):
        HARVEST.append((_name, {int(r['n']): r for r in csv.DictReader(open(LANE + '/results/' + _name), delimiter='\t')}))
sys.path.insert(0, S + 'take-assemble-r21/bin')
from seedsrc import src as seedfile  # noqa: E402  (which public file the seed merged0 took n from)


def held(n, k=None):
    """The held row of n at round k, resolved the way the assembler's trace_base.held does:
    the round tables, then the harvest tables, then the original seed (Couzo or Samanyu-dev)."""
    for r in sorted(TABLES, reverse=True):
        if (k is None or r <= k) and n in TABLES[r]:
            row = TABLES[r][n]
            return 'results/round%d-best n=%d: %s || %s' % (r, n, row.get('source', ''), row.get('licence', ''))
    for name, tab in HARVEST:
        if n in tab and tab[n].get('source') != 'seed merged0':
            return 'results/%s n=%d: %s || %s' % (name, n, tab[n].get('source', ''), tab[n].get('licence', ''))
    return 'original seed: n = %d of %s' % (n, seedfile(n))


def sidecars(p):
    out = []
    for s in (p + '.json', p + '.origin.json', p[:-4] + '.json', p[:-4] + '.origin.json', p + '.provenance.json', p + '.source.json'):
        if s != p and os.path.isfile(s) and s not in out:
            out.append(s)
    return out


_led = {}


def ledger_lines(p):
    base, d = os.path.basename(p), os.path.dirname(p)
    m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', p)
    leds = glob.glob(d + '/*.tsv')
    if m:
        leds += glob.glob(S + m.group(1) + '/work/*.tsv') + glob.glob(S + m.group(1) + '/near/*.tsv')
    out = []
    if re.fullmatch(r'\d+\.csv', base):
        return out  # a per-n take file: its record is the take.tsv row, and the bare name is not distinctive
    rx = re.compile(r'(?<![\w.-])' + re.escape(base) + r'(?![\w.-])')
    for led in sorted(set(leds)):
        if led.endswith('/take.tsv') or os.path.getsize(led) > 100_000_000:
            continue
        if led not in _led:
            _led[led] = open(led, errors='replace').read().split('\n')
        out += [l for l in _led[led] if base in l and rx.search(l)]
    return out


def refusals(p):
    m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', p)
    if not m or not os.path.isfile(S + m.group(1) + '/STATE.txt'):
        return []
    if m.group(1).startswith('take-quench-'):
        return []  # our byte copy of another lane's start: that lane's refusals were read when the follow queued it
    if re.match(re.escape(S) + r'take-[a-z0-9-]+-r\d+/\d+\.csv$', p) and take_row(m.group(1), int(os.path.basename(p)[:-4])):
        return []  # a per-n take file its lane still lists in take.tsv is not refused by that lane
    base = os.path.basename(p)[:-4]
    stem = base.split('-', 1)[1] if '-' in base else base
    if re.fullmatch(r'\d+', base):
        # a per-n name such as 972.csv: the bare number matches lines about other files (bare972-..., public972),
        # so match the folder that names the start (deferred/n142104x972x385/972.csv), or dir/972.csv
        par = os.path.basename(os.path.dirname(p))
        base = stem = (par + '/' + base + '.csv') if re.fullmatch(r'take-[a-z0-9-]+-r\d+|near|work|deferred', par) else par
    out = []
    for l in open(S + m.group(1) + '/STATE.txt', errors='replace'):
        if (base in l or (len(stem) > 8 and stem in l)) and REFUSE.search(l) and not re.search(r'\b(?:QUEUE|START|FINISH|CLAIM)\b', l):
            k = l.find(base) if base in l else l.find(stem)
            if re.search(r'(?:parent|from|of|input|donor)\s+\S*$', l[max(0, k - 40):k]):
                continue  # the line is about a child of the start, not the start
            out.append(l.strip()[:300])
    return out


def walk(start, n, cap=3000):
    texts, missing, seen, helds, refused = [], [], set(), set(), []
    if not os.path.isfile(start):
        return texts, ['start ' + start], seen, helds, refused
    rec = sidecars(start) + [None]
    lines = ledger_lines(start)
    m0 = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', start)
    t0 = take_row(m0.group(1), int(m0.group(2))) if m0 else None
    if len(rec) == 1 and not lines and not t0:
        missing.append('no record of the start ' + start)
    refused += refusals(start)
    queue = [start]
    via = {}
    while queue and len(seen) < cap:
        p = queue.pop(0)
        parent = p if isinstance(p, tuple) else norm(p)
        if isinstance(p, tuple):
            kind, a, b = p
            key = '%s %s %s' % p
            if key in seen:
                continue
            seen.add(key)
            t = held(a, b)
            parent = p
            if t is None:
                missing.append('held n=%d round %s not in the results tables' % (a, b)); continue
            texts.append((key, t))
        else:
            p = norm(p)
            if p in seen:
                continue
            seen.add(p)
            t = ''
            m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', p)
            if m:
                t += take_row(m.group(1), int(m.group(2))) or ''
            if not os.path.isfile(p) and p.endswith('.json'):
                stem = re.sub(r'(?:\.origin|\.source|\.provenance)?\.json$', '', p)
                if stem != p and (os.path.isfile(stem) or os.path.isfile(stem + '.csv')):
                    continue  # a sidecar name a record lists but never wrote; the csv itself is walked
            if not os.path.isfile(p) and not t:
                from archive27 import metadata as archived
                original=re.sub(r'(?:\.origin|\.source|\.provenance)?\.json$', '', p)
                if not original.endswith('.csv'):original+='.csv'
                ps,pl,pr=archived(pathlib.Path(original),n) if False else archived(original,n)
                if ps:
                    t=ps+' || '+pl+'; source metadata '+pr
            if not os.path.isfile(p):
                if not t:
                    up, held_chain = p, False
                    for _ in range(60):
                        up = via.get(up)
                        if up is None:
                            break
                        if isinstance(up, tuple) and up[0] == 'held':
                            held_chain = True; break
                    tag = 'held-chain ' if held_chain else ''
                    missing.append(tag + p.replace(S, '') + ' (named by ' + str(via.get(p, '?')).replace(S, '')[:120] + ')')
                    continue
                # a per-n take file that is gone, with its take.tsv row still there: walk the row
            elif p.endswith('.json'):
                if os.path.getsize(p) < 20_000_000:
                    mm = re.match(r'(\d+)[-.]', os.path.basename(p))
                    t += jtext(p, int(mm.group(1)) if mm else n)
            elif p.endswith('.csv'):
                for c in sidecars(p):
                    queue.append(c); via.setdefault(c, p)
                t += '\n'.join(ledger_lines(p))
            texts.append((p, t))
        for q in PATH.findall(t):
            if norm(q) not in seen:
                queue.append(q); via.setdefault(norm(q), parent)
        for h in ANC.findall(t):
            for d in ANCDIRS:
                if os.path.isfile(d + '/' + h + '.json'):
                    queue.append(d + '/' + h + '.json')
        if not isinstance(p, tuple):
            here = os.path.dirname(p)
            mt = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', p)
            dirs = [here] + ([S + mt.group(1) + '/near', S + mt.group(1) + '/work'] if mt else [])
            for b in set(BARE.findall(t)):
                for d in dirs:
                    if os.path.isfile(d + '/' + b) and d + '/' + b not in seen:
                        queue.append(d + '/' + b); via.setdefault(d + '/' + b, parent); break
        for rx, flip in HELD:
            for g in rx.findall(t):
                a, b = (g[1], g[0]) if flip else (g[0], g[1])
                nn, k = int(a), (int(b) if b else None)
                if 1 <= nn <= 1000 and (nn, k) not in helds:
                    helds.add((nn, k)); queue.append(('held', nn, k)); via.setdefault(('held', nn, k), parent)
    return texts, missing, seen, helds, refused


def lifted(text):
    low=text.lower()
    return bool(re.search(r'samanyu|unlicensed.*921|921.*unlicensed|seed983|seed 983',low)) and not re.search(r'prvsiyan|by-sa|penguin|changed.*pin|missing.*parent|gone:',low)


def check(start):
    try:
        n = int(next(csv.DictReader(open(start)))['n'])
    except Exception:
        return {'start': start, 'clean': False, 'hits': ['unreadable start'], 'files': 0}
    texts, missing, seen, helds, refused = walk(start, n)
    hits = []
    for label, t in texts:
        # harvest's copy check: a layout this close to the prvsiyan best-of-1105 layout (CC BY-SA, rule b) stays out.
        # Backlog refused the harvest 695 row at 0.238 and named 0.55 to 0.85 as the range of the rows it keeps.
        # a record that pins a parent by its sha256: the file on disk must still be that version, or the
        # parent's own record is no longer the one the producer traced (midm withdrew 684 for this at 15:48 UTC)
        for m in PIN.finditer(t):
            path, want = m.group(1), m.group(2).lower()
            if not path.startswith('/'):
                path = S + path
            have = file_sha(path)
            if have and not have.startswith(want):
                hits.append('%s: changed since pinned: %s (sha256 %s, now %s)' % (label.replace(S, '')[:80], path.replace(S, ''), want[:16], have[:16]))
        c = NEG.sub(' ', t)
        for rx in (POS, NAMES):
            for m in rx.finditer(c):
                hits.append('%s: %s' % (label.replace(S, '')[:80], c[max(0, m.start() - 60):m.end() + 30].replace('\n', ' ')))
    alltext = '\n'.join(t for _, t in texts)
    for name, rx in quench_audit.RULES:
        m = re.search(rx, alltext, flags=re.I)
        if m:
            hits.append('%s: %s' % (name, alltext[max(0, m.start() - 60):m.end() + 20].replace('\n', ' ')))
    hits += ['refused by its lane: ' + r for r in refused if not lifted(r)]
    # a file the record names that no longer exists: the round 25 skeptic dropped
    # 860, 911, 921 and 975 for this (a start gone or replaced); rows it kept had none
    # Gone files under a held row (an accepted results-table row) are the held row's
    # business; every other gone file breaks the walk (927 of round 24 hid seed 811
    # behind a gone take-harvest-r23/866.csv).
    # A per-n take file of the live round that is gone was superseded by its lane (harvest dropped 972
    # and 910 at 14:11 UTC when midm beat them); the records that name it keep their own snapshots.
    # It refuses only when a WITHDRAW or WITHHOLD line names it.
    def superseded(x):
        m = re.match(r'(take-[a-z0-9-]+-r%s/\d+\.csv) ' % LIVE, x)
        return bool(m) and not any(m.group(1) == w for w, _ in WITHDRAWN_LINES)
    hits += ['gone: ' + x for x in missing if not x.startswith(('held ', 'held-chain ')) and not superseded(x)]
    for w, line in WITHDRAWN_LINES:
        if lifted(line):continue
        for f in seen:
            if isinstance(f, str) and f.endswith('/' + w) and os.path.isfile(f):
                # a path a lane reuses: only the version written before the line is withdrawn
                if os.path.getmtime(f) <= withdraw_time(line):
                    hits.append('withdrawn in a handoff line: ' + line[:200])
    if not helds and not ROOT.search(alltext):
        hits.append('no root: no held reference and no public file reached')
    return {'start': start, 'n': n, 'clean': not hits, 'hits': sorted(set(hits))[:40], 'files': len(seen),
            'helds': sorted('%d@%s' % h for h in helds)[:60], 'missing': sorted(set(missing))[:40]}


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    for p in sys.argv[1:]:
        print(json.dumps(check(p)), flush=True)
