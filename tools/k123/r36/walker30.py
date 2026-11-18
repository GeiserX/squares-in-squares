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
It refuses a start when the text it reaches names a withdrawn tree, the CC BY-SA
or penguin069 sources, the bare name of a withdrawn file, a refusal by the
producing lane, a missing start or start record, or no root at all (no held
reference and no public file reached).

Round 27: the Samanyu-dev rule is lifted (the main session, 2026-11-14), so a
Samanyu-dev seed signal no longer refuses, and a refusal or withdrawal line whose
only reason is that seed is not read. The prvsiyan test is the share test: the
start is out when 0.4 or more of its squares lie within 1e-3 of the prvsiyan
best-of-1105 row of the same n (harvest share_ac.share, best of 8 symmetries),
or when its recorded ancestry names that file. The 0.55 distance cut is gone.
"""
import csv, glob, json, os, re, sys, time

sys.dont_write_bytecode=True
csv.field_size_limit(1 << 30)
S = '$SCRATCH/bounties-squares/'
LANE = '.'
sys.path.insert(0, LANE)
import quench_audit  # noqa: E402

PATH = re.compile(r'((?:$SCRATCH/bounties-squares/)?(?:take-[a-z0-9-]+-r\d+|harvest[\w.-]*|gather|seeds)/[^\s"\'<>;,()\[\]{}|\\]*?\.(?:csv|json))(?![\w.-])')
BARE = re.compile(r'(?<![/\w.-])([\w][\w.-]*\.csv)(?![\w.-])')
ANC = re.compile(r'(?<![0-9a-f])([0-9a-f]{64})\.json')
HELD = [(re.compile(r'held(?: packing)?(?: of)? n\s*=\s*(\d+)(?: of round (\d+))?', re.I), 0),
        (re.compile(r'held round\s*(\d+)b? n\s*=?\s*(\d+)', re.I), 1),
        (re.compile(r'n\s*=\s*(\d+) (?:from|of) held round\s*(\d+)', re.I), 0),
        (re.compile(r'round (\d+) packing of n\s*=\s*(\d+)', re.I), 1),
        (re.compile(r'held round\s*(\d+)\s*[a-z]?\s+row of n\s*=\s*(\d+)', re.I), 1),  # round 31: midm 'the held round 28 b row of n = 854'
        (re.compile(r'gather/round(\d+)-2026-\d\d-\d\d[a-z]?\.csv[^|;]{0,40}?(?:n\s*=\s*|"n"\s*:\s*)(\d+)'), 1)]  # text or JSON ("path": ..., "n": 694)
NEG = re.compile(r'(?:max centre distance:[^)|\n]*'  # harvest's geometry check that a layout is no copy of an excluded source
                 r'|\[?Samanyu(?:-dev)?(?:\s+GitHub)?(?: seed)?(?: group)? ancestry\s*[:=]?\s*(?:no|none|false)\b[^;|\n\]"]*\]?'
                 r'|recorded ancestry has no Samanyu-dev seed layout|no (?:recorded )?Samanyu(?:-dev)?(?: GitHub)?(?: seed)?(?: ancestry| links?| inputs?| layouts?| input)'
                 r'|Samanyu(?:-dev)? seed ancestry: no|without (?:any )?Samanyu(?:-dev)?[\w ]{0,20}|distinct from (?:the )?Samanyu-dev[\w /]{0,40}'
                 r'|not (?:the )?Samanyu-dev[\w /]{0,40}|Samanyu-dev[\w /]{0,30}(?:is|are) (?:excluded|out)|Samanyu(?:-dev)?[^;|"]{0,40}seed[s]?[^;|"]{0,20}: (?:none|no)\b)', re.I)
POS = None  # round 27: the Samanyu-dev seed signals no longer refuse
# the round 25 skeptic's explicit names (walk8.py SIG), as positive signals
# round 28: the r27 assembler dropped backlog 642 because the penguin069 boxed51 union names the prvsiyan file upstream
NAMES = re.compile(r'squares-joegun-boxed|joegun-boxed-certified-union|squares-boxed51-certified-current-union|squares-verified-best-of-1105|CC BY-SA|ShareAlike'
                   r'|areebbb[^|]{0,160}?donor n = (?:639|691|745|858|918)\b|per_n\.csv, donor n = (?:639|691|745|858|918)\b', re.I)
# round 27: a refusal or withdrawal line whose only reason is the Samanyu-dev seed (and the names that stood for it) is not read
SAMANYU = re.compile(r'samanyu|29e12ff3|921r25c921|bare ?921|\b747r\b|seeds? (?:n\s*=\s*)?(?:338|365|503|504|704|804|811|861|934|983|995)\b|735 tree|seed merged0|\b931h\b|local_bank|rule \(?d\)?', re.I)
OTHER = re.compile(r'prvsiyan|1105|BY-SA|ShareAlike|penguin|joegun|areebbb|\b801\b|rule \(?[abc]\)?\b|overlap|gone|missing|not found|no root|cycle|rewritten|replaced|changed since', re.I)


# round 30 override 3: our own layouts. The 801 row, original seeds 503 and 983, the Samanyu-dev seed counts the
# SAMANYU pattern names, and the held rows that resolve to the Samanyu-dev seed (computed lazily in check()).
OWN_N = {801, 503, 983, 338, 365, 504, 704, 804, 811, 861, 934, 995}


def samanyu_only(line):
    return bool(SAMANYU.search(line)) and not OTHER.search(line)
PRV_ZIP = S + 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
SHARE_MAX = 0.4  # round 27 rule: out at a share of 0.4 or more within 1e-3 of the prvsiyan 1105 row of n
# a record that compares a layout with the prvsiyan row ("prvsiyan 1105 (CC BY-SA) share 0.002 within 1e-3", "prvsiyan
# 1105 (CC BY-SA)=0.672") names the file as a measure, not as ancestry (k123 21:29:50Z on modules r27 597); a share
# of 0.4 or more is left in the text and still refuses
CMP = re.compile(r'prvsiyan[\w /.-]{0,40}?\(CC BY-SA\)\s*(?:(share)\s*(\d+(?:\.\d+)?)|=\s*\d|distances?\s*[=:]?\s*\d)', re.I)


def _cmp(m):
    return m.group(0) if m.group(1) and float(m.group(2)) >= SHARE_MAX else ' '


_prv = {}


def prv_centres(n):
    """Centres of the prvsiyan 1105 row of n (its submission.csv only), centred on the bounding box."""
    if not _prv:
        import io, zipfile
        import numpy as np
        rows = {}
        with zipfile.ZipFile(PRV_ZIP) as z:
            for r in csv.DictReader(io.StringIO(z.read('submission.csv').decode('utf-8-sig'))):
                rows.setdefault(int(r['n']), []).append((float(r['x']), float(r['y'])))
        for k, v in rows.items():
            a = np.array(v)
            _prv[k] = a - (a.min(0) + a.max(0)) / 2
        _prv[-1] = None
    return _prv.get(n)


_shc = {}


def prv_share(path, n):
    """(share within 1e-6, share within 1e-3, max distance) of the layout in path against the prvsiyan 1105 row of n."""
    import numpy as np
    sys.path.insert(0, LANE + '/tools/harvest26')
    from share_ac import share  # harvest's measure, read only
    key = (path, n, os.path.getmtime(path))
    if key not in _shc:
        b = prv_centres(n)
        a = np.array([[float(r['x']), float(r['y'])] for r in csv.DictReader(open(path)) if int(r['n']) == n])
        if b is None or len(b) != n or len(a) != n:
            _shc[key] = (0.0, 0.0, float('inf'), 0.0)
        else:
            a = a - (a.min(0) + a.max(0)) / 2
            r = share(a, b)
            _shc[key] = (r[0], r[1], r[3], r[2])  # round 31: the share within 1e-2 last (the r29 and r30 skeptics dropped 582 and 972 at 1e-2)
    return _shc[key]
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
ROOT = re.compile(r'harvest[\w.-]*/|gather/round|/seeds/|seeds/|kaggle|sis-final-packings|sis-submit|a-square-deal|living-atlas|results/round\d+-best', re.I)
DROPK = {'producer_take_tsv', 'final_competing_takes', 'competing_takes', 'other_takes', 'live_takes', 'excluded', 'rejected',
         'refused', 'withdrawn', 'quarantine', 'quarantined', 'blocked_inputs', 'what_was_measured', 'next', 'coordinates', 'P',
         'points', 'rows', 'squares', 'checked_paths', 'admission_receipt'}
# round 31: 'checked_paths' is the list of files another lane's audit visited (k123 r26 sources-licensed40000.json, n=910
# lists forensics r26 850 and harvest r26 972), not a source claim; the record's ancestry_file names the real tree
ANCDIRS = sorted(glob.glob(S + 'take-*-r2[2-9]/work/ancestry') + glob.glob(S + 'take-*-r3[0-9]/work/ancestry')) + sorted(glob.glob(S + 'take-*-r2[2-9]/work/*/ancestry') + glob.glob(S + 'take-*-r3[0-9]/work/*/ancestry'))  # round 30: r3x too
_ancestor_path_cache31={}
def ancestor_paths31(h):
    if h not in _ancestor_path_cache31:
        found=[d+'/'+h+'.json' for d in ANCDIRS if os.path.isfile(d+'/'+h+'.json')]
        if found:_ancestor_path_cache31[h]=found
        return found
    return _ancestor_path_cache31[h]
LIVE = os.environ.get('QUENCH_LIVE_ROUND', '36')
WITHDRAWN_LINES = []
_wl_key = [None]
RETAIN = re.compile(r'\b(?:not|never|no longer) (?:the |a |an |its )?(?:withheld|withdrawn|refused|excluded)\b[^,;)]*'
                    r'|\bkeep(?:s|ing)?\b[^,;)]*', re.I)  # round 30 override 6: 'keeps X' is a retention note, not a withdrawal


NOT_WITHDRAW = re.compile(r'^\S+\s+[a-z0-9-]+\s+->\s*[\w,.-]+:\s*(?:claims?\b|PRIORITY\b)|\bretention of\b|\bthis is retention\b', re.I)

def load_withdrawn():
    """The WITHDRAW, WITHHOLD and reclassify lines of the handoff logs, read again when a log changes
    (a long follow must see the withdrawals of its own round)."""
    logs = sorted(glob.glob(S + 'handoff-r2[2-9].log') + glob.glob(S + 'handoff-r3[0-9].log'))  # round 30: r3x too
    key = tuple((h, os.path.getmtime(h)) for h in logs)
    if key == _wl_key[0]:
        return
    out, back = [], []
    for _h in logs:
        rnd = re.search(r'handoff-(r\d+)\.log$', _h).group(1)
        for _l in open(_h, errors='replace'):
            if re.search(r'REINSTATE|reinstat|withdrawal (?:is )?lifted', _l, re.I):
                # classfill 20:06:05Z: REINSTATE n982 ... prior temporary withdrawal lifted (harvest saw the walk
                # refuse 982 on that line): a reinstatement cancels the earlier withdrawals of what it names
                back.append((_l.strip(), withdraw_time(_l), set(re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)', _l)),
                             re.match(r'\S+\s+([a-z0-9-]+)\s+->', _l), set(re.findall(r'\bn\s*=?\s*(\d{1,4})\b', _l))))
                continue
            # round 28: a retention note is not a withdrawal. modules 13:12:57Z of round 26 wrote 'certified n=975 ...
            # (own turned corner from twoshort-r24 973, not the withheld twoshort-r25/975.csv)', and the old read withdrew
            # the certified take-modules-r26/975.csv the line announces. The phrase 'not the withheld X' (or withdrawn,
            # refused) is cut before the test, so only a line that still says withdraw or withhold withdraws.
            _l = RETAIN.sub(' ', _l)
            if share_only(_l):
                continue
            if NOT_WITHDRAW.search(_l) and not re.search(r'WITHDR|WITHH[EO]LD', _l):
                continue
            # case-insensitive since round 27: harvest wrote 'withdrawn near file 988-pubfq-...' in lower case
            if re.search(r'withdr|withh[eo]ld|reclassif', _l, re.I) and not samanyu_only(_l):
                for _m in re.finditer(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)', _l):
                    # round 31: a path the line names as the parent of the withdrawn file ('a lkick of X', 'built on X',
                    # 'from X') is not withdrawn by it (backlog 13:47:02Z of round 30 withdrew its 802, 'a lkick of
                    # take-rebuild-r29/802.csv', and the walk refused every tree that reached rebuild's 802)
                    if re.search(r'(?:\b(?:a |an |the )?l?kick of|\bbuilt (?:on|from)|\bfrom|\bparent|\bstart(?:ed)? (?:of|from))\s+\S*$', _l[max(0, _m.start() - 40):_m.start()], re.I):
                        continue
                    out.append((_m.group(1), _l.strip()))
                # a line that names counts and no paths: 'harvest -> ...: harvest withdrew 416 499 646 654 695 814
                # from its take', 'midm -> all: withdrew 546 642 694 684 from the midm take', 'WITHDRAW n982'
                lm = re.match(r'\S+\s+([a-z0-9-]+)\s+->', _l)
                mm = re.search(r'withdr\w*\s+(?:n\s*=?\s*)?((?:\d{1,4}(?:\s*,\s*|\s+and\s+|\s+)?)+)', _l, re.I)
                if lm and mm:
                    for nn in re.findall(r'\d{1,4}', mm.group(1)):
                        out.append(('take-%s-%s/%s.csv' % (lm.group(1), rnd, nn), _l.strip()))
    keep = []
    for f, l in out:
        tw = withdraw_time(l)
        lane_n = re.match(r'take-([a-z0-9-]+)-r\d+/(\d+)\.csv$', f)
        cancelled = False
        for bl, tb, paths, blm, bns in back:
            if tb <= tw:
                continue
            if f in paths or (lane_n and blm and blm.group(1) == lane_n.group(1) and lane_n.group(2) in bns):
                cancelled = True
        if not cancelled:
            keep.append((f, l))
    WITHDRAWN_LINES[:] = keep
    _wl_key[0] = key




SHARE_WHY = re.compile(r'share\s*[=:]?\s*[01]?\.\d|share\s*[01]\b|prvsiyan[\w ]{0,30}share|>=\s*0\.4|threshold\s*0\.4|out at 0\.4|numeric share|original-seed', re.I)  # round 30: 'out at 0.4' (twoshort r29 on backlog CERT lines)
SHARE_OTHER = re.compile(r'unresolv|untrace|trace is|SOURCE_NOTICES|names squares-verified|penguin|joegun|areebbb|\bgone\b|missing', re.I)


def share_only(line):
    """Round 28 (main 00:19:03Z): a withdrawal whose only reason is a prvsiyan share match (of our own layout, an
    ancestor, an original seed, or a harvest-type parent) is not read; main reopened k123 798, whose withdrawn
    ancestor was the harvest r22 742 at 0.454. A harvest-type start still meets the share test itself in check().
    A line with another reason (an unresolved trace, a source notice, the excluded unions) is still read."""
    return bool(SHARE_WHY.search(line)) and not SHARE_OTHER.search(line)


def withdraw_time(line):
    import calendar
    m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?)', line)
    if not m:
        return float('inf')
    t = m.group(1) + (':00' if len(m.group(1)) == 16 else '')
    return calendar.timegm(time.strptime(t, '%Y-%m-%dT%H:%M:%S'))


load_withdrawn()
TABLES = {}
for _p in glob.glob(LANE + '/results/round*-best-*.tsv'):
    _k = int(re.search(r'round(\d+)-best', _p).group(1))
    TABLES[_k] = {int(r['n']): r for r in csv.DictReader(open(_p), delimiter='\t')}


HELD_PIN = {}  # round 33: the first file each round-table row names, with the sha256 prefix it pins ('' when unpinned)
HELD_SHAS = set()
for _r in TABLES.values():
    for _row in _r.values():
        _m = re.search(r'(take-[a-z0-9-]+-r\d+/[^\s,;()|]+?\.csv)(?:\s*\(sha256 ([0-9a-f]{12,64}))?', _row.get('source') or '')
        if _m:
            HELD_PIN.setdefault(_m.group(1), set()).add(_m.group(2) or '')
            if _m.group(2):
                HELD_SHAS.add(_m.group(2)[:12])


def held_bytes(f):
    """Round 33: True when f holds the bytes of a held row: the file a round-table row starts from (with the pinned sha
    when the row pins one), or a byte copy of a pinned held file elsewhere."""
    if not isinstance(f, str) or not os.path.isfile(f):
        return False
    h = file_sha(f)
    rel = f.replace(S, '')
    if rel in HELD_PIN and any(not x or h.startswith(x) for x in HELD_PIN[rel]):
        return True
    return h[:12] in HELD_SHAS


def norm(p):
    return p if p.startswith('/') else S + p


_jt = {}


def share_evidence(k, v):
    """Round 31: harvest's share audit evidence (a list of {label: the 1105 comparison archive, share1e6, share1e3, share1e2,
    maxd}) names the comparison file, not an ancestor (harvest r31 cert31 sidecars were refused for the archive path)."""
    return isinstance(v, list) and bool(v) and all(isinstance(e, dict) and 'share1e3' in e for e in v)


def jtext(p, n):
    key = (p, n, os.path.getmtime(p))
    if key not in _jt:
        _jt[key] = _jtext(p, n)
    return _jt[key]


def _jtext(p, n):
    if '/admission-probes32/' in p and p.endswith('/admission-check32.json'):
        return '{}'  # Diagnostic receipt, no ancestry edges.
    raw = open(p, errors='replace').read()
    try:
        q = json.loads(raw)
    except ValueError:
        return raw
    if os.path.basename(p)=='held-roots.json' and isinstance(q,list):
        q=[z for z in q if isinstance(z,dict) and str(z.get('n'))==str(n)]
    if isinstance(q, dict) and q and all(str(k).isdigit() for k in q):
        q = q.get(str(n), {})

    def f(x):
        if isinstance(x, dict):
            return {k: f(v) for k, v in x.items() if k not in DROPK and not share_evidence(k, v)}
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


_st = {}


def state_lines(f):
    k = (f, os.path.getmtime(f))
    if k not in _st:
        _st[k] = open(f, errors='replace').read().split('\n')
    return _st[k]


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
    for l in state_lines(S + m.group(1) + '/STATE.txt'):
        if (base in l or (len(stem) > 8 and stem in l)) and REFUSE.search(l) and not re.search(r'\b(?:QUEUE|START|FINISH|CLAIM|WORKER|RUN|PREP|SEND|COPY|COLLECT|CERT)\b', l):  # round 30: CERT lines are certify notes (twoshort r29: backlog's 'unwalked' and 'out at 0.4' words)
            k = l.find(base) if base in l else l.find(stem)
            if re.search(r'(?:parent|from|of|input|donor)\s+\S*$', l[max(0, k - 40):k]):
                continue  # the line is about a child of the start, not the start
            if re.search(r'walk it and publish it yourselves|near-only find', l):
                continue  # round 29: soft hands a find over ('our walk stops at "refused parent", so walk it and publish it yourselves'): a handover, not a refusal; the walk still checks the whole tree
            out.append(l.strip()[:300])
    return out


def snapshot_covers(rec, p):
    """True when rec is an ancestry record whose own "path" is p and that holds the node tree of p
    (root hash and nodes with their sources): the gone file's ancestry was captured when it existed."""
    if not isinstance(rec, str) or not rec.endswith('.json') or '/ancestry/' not in rec or not os.path.isfile(rec):
        return False
    try:
        o = json.load(open(rec))
    except Exception:
        return False
    return isinstance(o, dict) and norm(str(o.get('path') or '')) == p and bool(o.get('nodes')) and bool(o.get('root'))


_tree = {}
# round 28: 'exclud' left this list. Lanes parked Samanyu-only files in work/excluded-near (harvest r24, twoshort r25);
# a copy there is walked like any other, and the withdrawal lines, the names and the share test of every csv ancestor decide.
FOLLOW_MAP = re.compile(r'/take-[a-z0-9-]+-r\d+/work/(?:[\w.-]+/)?follow(?:-seen)?[\w.-]*\.json$')  # round 31: readers r22 work/follow.json and its snapshots (harvest r29 ancestry-inputs/follow-c755e428.json)
MOVED_BAD = re.compile(r'withdr|refus|quarantin|prvsiyan|bysa|by-sa|penguin|joegun|[\w-]*-out/|/out/|/gone/|/dropped/|/purge', re.I)


def moved_copy(p):
    """Round 27: lanes moved files they held back for the Samanyu-dev rule into other folders of the same
    take dir (invent r25 work/near-held-v6). A gone file with a distinctive name is walked through its
    moved copy there; a per-n name (866.csv) is not distinctive, and a copy in a withdrawn or refused
    folder is not used."""
    m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', p)
    base = os.path.basename(p)
    if not m or re.fullmatch(r'\d+\.csv', base) or len(base) < 12:
        return None
    d = S + m.group(1)
    if d not in _tree:
        idx = {}
        if d == str(__import__('pathlib').Path(__file__).resolve().parent.parent):
            for root, _, fs in os.walk(d):
                for f in fs:idx.setdefault(f, []).append(os.path.join(root, f))
        else:
            for pattern33 in ['/*.csv','/near/*.csv','/work/*.csv','/work/*/*.csv','/work/*/*/*.csv']:
                for q33 in glob.glob(d+pattern33):idx.setdefault(os.path.basename(q33),[]).append(q33)
        _tree[d] = idx
    for q in sorted(_tree[d].get(base, [])):
        rel = q.replace(d, '')
        # round 28: a folder a lane named for a share-only withdrawal (k123 work/withdrawn-near-ancestor-share,
        # work/withdrawn-seed503) holds copies the main 00:19:03Z rule reopened
        share_park = re.search(r'/withdrawn[\w-]*(?:share|seed\d+)[\w-]*/', rel, re.I) and not re.search(r'quarantin|prvsiyan|bysa|by-sa|penguin|joegun|/purge', rel, re.I)
        if q != p and os.path.isfile(q) and (share_park or not MOVED_BAD.search(rel)):
            return q
    return None


def _tree_idx(d):
    if d not in _tree:
        idx = {}
        if d == str(__import__('pathlib').Path(__file__).resolve().parent.parent):
            for root, _, fs in os.walk(d):
                for f in fs:idx.setdefault(f, []).append(os.path.join(root, f))
        else:
            for pattern33 in ['/*.csv','/near/*.csv','/work/*.csv','/work/*/*.csv','/work/*/*/*.csv']:
                for q33 in glob.glob(d+pattern33):idx.setdefault(os.path.basename(q33),[]).append(q33)
        _tree[d] = idx
    return _tree[d]


def byte_copy(path, want):
    """Round 31: a file that keeps the pinned version (sha256 prefix want) of path, or None. Places looked at: the same
    file name anywhere in the take dir of path, every csv of the same n there when path is a per-n take file (a lane moves
    a superseded per-n file to near/ under another name: twoshort r30 594), our follow's byte copies
    (take-quench-rNN/work/starts/<sha16>/), harvest's input snapshots (<stem>-<sha16>.csv) and the assembler snapshots.
    Round 30 refused 9 to 25 valid rows per pass for 'changed since pinned' while such a copy existed (rebuild's 968)."""
    want = want.lower()
    base = os.path.basename(path)
    stem = base[:-4]
    cands = []
    m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', path)
    if m and os.path.isdir(S + m.group(1)):
        idx = _tree_idx(S + m.group(1))
        cands += idx.get(base, [])
        if re.fullmatch(r'\d+\.csv', base):
            cands += [q for k, v in idx.items() if k.endswith('.csv') and re.match(re.escape(stem) + r'\b', k) for q in v]
    cands += glob.glob(S + 'take-quench-r*/work/starts/%s/%s' % (want[:16], base))
    cands += glob.glob(S + 'take-harvest-r*/work/*inputs*/%s-%s*.csv' % (stem, want[:16]))
    if m:
        cands += glob.glob(S + 'take-assemble-r*/snap/' + path.replace(S, ''))
    for q in cands:
        if q != path and os.path.isfile(q) and file_sha(q).startswith(want):
            return q
    return None


HELD_MARK = re.compile(r'start source:|resolves to:', re.I)


def held_cut(t):
    """(position, held tuple) when t names a held reference and then a 'start source:' or 'resolves to:' marker."""
    m = HELD_MARK.search(t)
    if not m:
        return None
    pre = t[:m.start()]
    for rx, flip in HELD:
        gs = rx.findall(pre)
        if gs:
            g = gs[-1]
            a, b = (g[1], g[0]) if flip else (g[0], g[1])
            if 1 <= int(a) <= 1000:
                return m.end(), ('held', int(a), int(b) if b else None)
    return None


_hf = {}


def is_held_file(f):
    """Round 31: a per-n take file take-<lane>-rK/<n>.csv that a results table (round K or later) holds as its n row is a
    held row (override 2: every row of a file we submitted is ours), so what lies below it is held ancestry. midm r30 412
    reached the harvest r29 412 row, held in round 29 b, by its path and not through a held reference."""
    if f in _hf:
        return _hf[f]
    m = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r(\d+))/(\d+)\.csv$', f) if isinstance(f, str) else None
    ok = False
    if m:
        take, k, nn = m.group(1), int(m.group(2)), int(m.group(3))
        rel = take + '/%d.csv' % nn
        for r in sorted(TABLES):
            row = TABLES[r].get(nn)
            if r < k or not row:
                continue
            txt = (row.get('source') or '') + ' ' + (row.get('take') or '')
            first = re.search(r'take-[a-z0-9-]+-r\d+/[^\s,;()]+?\.csv', row.get('source') or '')
            # the row's own file: the take column names its take dir, or the source cell starts from that file
            if (first and first.group(0) == rel) or re.search(r'\b' + re.escape(take) + r'\b', row.get('take') or ''):
                pm = re.search(re.escape(rel) + r'\s*\(sha256 ([0-9a-f]{12,64})', txt)
                ok = not pm or not os.path.isfile(f) or file_sha(f).startswith(pm.group(1))
                if ok:
                    break
    _hf[f] = ok
    return ok


def _through_held(x, via):
    if isinstance(x, str) and is_held_file(x):
        return True
    for _ in range(200):
        x = via.get(x)
        if x is None:
            return False
        if (isinstance(x, tuple) and x[0] == 'held') or (isinstance(x, str) and is_held_file(x)):
            return True
    return False


def walk(start, n, cap=100000):
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
    if re.search(r'refus|withdr|withh[eo]ld|quarantin|exclud|unclean', os.path.basename(start), re.I):
        refused.append('the producing lane named the file ' + os.path.basename(start))
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
            if not os.path.isfile(p) and not t and snapshot_covers(via.get(p), p):
                texts.append((p, 'gone, covered by the ancestry snapshot ' + str(via.get(p))))
                continue  # the record that names it is an immutable node tree of this very file (invent strict25v4)
            if not os.path.isfile(p) and not t and p.endswith('.csv') and not re.fullmatch(r'\d+\.csv', os.path.basename(p)):
                gl = ledger_lines(p)
                if gl:  # a gone file its lane's ledger still records: walk the record (family r22 near.tsv, sources.tsv)
                    t = 'gone, recorded in its lane ledger: ' + '\n'.join(gl)
            if not os.path.isfile(p) and not t:
                mv = moved_copy(p)
                if mv:
                    queue.append(mv); via.setdefault(mv, p)
                    texts.append((p, 'moved copy: ' + mv))
                    continue
            if not os.path.isfile(p):
                if not t and '...' in p:
                    continue  # round 31: an elided name in a note ('ancestry/554a2d38....json'), not a file; the full name is walked
                if not t:
                    held_chain = _through_held(p, via)
                    tag = 'held-chain ' if held_chain else ''
                    missing.append(tag + p.replace(S, '') + ' (named by ' + str(via.get(p, '?')).replace(S, '')[:120] + ')')
                    continue
                # a per-n take file that is gone, with its take.tsv row still there: walk the row
            elif p.endswith('.json') and FOLLOW_MAP.search(p):
                t += ''  # round 31: a follow lane's seen map (start path -> outcome) records no ancestry; its names are not parents
            elif p.endswith('.json'):
                if os.path.getsize(p) < 20_000_000:
                    mm = re.match(r'(\d+)[-.]', os.path.basename(p))
                    scoped33=int(mm.group(1)) if mm else n
                    if not mm:
                        up33=p
                        for _ in range(20):
                            up33=via.get(up33)
                            if not isinstance(up33,str):break
                            root33=re.match(r'(\d+)[-.]',os.path.basename(up33))
                            if root33 and 1<=int(root33[1])<=1000:
                                scoped33=int(root33[1]);break
                    t += jtext(p, scoped33)
            elif p.endswith('.csv') and (is_held_file(p) or p in {S+'seeds/samanyu_bestfit.csv', S+'seeds/merged0.csv'}):
                t += ' own submitted or original seed table root; '+p
            elif p.endswith('.csv'):
                for c in sidecars(p):
                    queue.append(c); via.setdefault(c, p)
                t += '\n'.join(ledger_lines(p))
            texts.append((p, t))
        # Legacy walk summaries list diagnostic missing paths, not input edges.
        edge_text32 = re.sub(r'\[deep25 walk[^\]]*\]', '', t)
        hc = held_cut(edge_text32) if not isinstance(p, tuple) else None
        for mq in PATH.finditer(edge_text32):
            q = mq.group(1)
            if norm(q) not in seen:
                # round 31: a path written after 'start source:' (or 'resolves to:') that follows a held reference is the
                # held row's own ancestry, copied into the record of a kick of that held row (midm r30 854, the r31 held
                # starts): it is reached through the held row
                queue.append(q); via.setdefault(norm(q), hc[1] if hc and mq.start() >= hc[0] else parent)
        for h in set(ANC.findall(edge_text32)):
            for ancestor_path in ancestor_paths31(h):
                queue.append(ancestor_path); via.setdefault(ancestor_path,parent)
        if not isinstance(p, tuple):
            here = os.path.dirname(p)
            mt = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/', p)
            dirs = [here] + ([S + mt.group(1) + '/near', S + mt.group(1) + '/work'] if mt else [])
            for b in set(BARE.findall(edge_text32)):
                for d in dirs:
                    if os.path.isfile(d + '/' + b) and d + '/' + b not in seen:
                        queue.append(d + '/' + b); via.setdefault(d + '/' + b, parent); break
        for rx, flip in HELD:
            for g in rx.findall(edge_text32):
                a, b = (g[1], g[0]) if flip else (g[0], g[1])
                nn, k = int(a), (int(b) if b else None)
                if k is None:
                    context_round = p[2] if isinstance(p,tuple) else None
                    if not isinstance(p,tuple):
                        mr = re.search(r'/take-[a-z0-9-]+-r(\d+)/', p)
                        if mr:context_round=int(mr[1])
                    if context_round is not None:k=context_round
                if 1 <= nn <= 1000 and (nn, k) not in helds:
                    helds.add((nn, k)); queue.append(('held', nn, k)); via.setdefault(('held', nn, k), parent)
    if queue:missing.append('source walk cap reached before all recorded edges resolved')
    LAST_VIA.clear(); LAST_VIA.update(via)
    return texts, missing, seen, helds, refused


LAST_VIA = {}

PUBDIR = re.compile(r'/take-harvest-r\d+/work/(?:public|collector)\w*/|/harvest[\w.-]*/(?:nb|ds|data|public)/')
PUBFIRST = re.compile(r'\s*(?:[\w ,()-]{0,60}?\bof\s+)?[\w.-]+/[\w.-]+\s*::')


_pol_c = {}


def pol_fail(path, n):
    """Round 31 override 3: (True, text) when the n rows of path share 0.4 or more at 1e-3 or at 1e-2 with a harvested version
    of the prvsiyan 1105 row that is not our own Samanyu seed (harvest31 policy.audit, read only: bounding box and ICP, eight
    symmetries, every harvested version; a version equal to our own seed is skipped, every version at 228 and 588)."""
    from publicshare31 import policy as current_policy31
    _pol=current_policy31()
    key = (path, n, os.path.getmtime(path), _pol._k123_reference_stamp)
    if key not in _pol_c:
        ok, ev = _pol.audit([r for r in csv.DictReader(open(path)) if r.get('n') == str(n)])
        if ok:
            _pol_c[key] = (False, '')
        else:
            w = max(ev, key=lambda e: max(e['share1e3'], e['share1e2']))
            _pol_c[key] = (True, '1105 share %.3f at 1e-3, %.3f at 1e-2 (ICP, version %s)' % (w['share1e3'], w['share1e2'], w['label'][-16:]))
    return _pol_c[key]


PRE = 0.2  # a single-version bounding-box share at or above this sends a file to the full policy test


def harvest_type(start, n):
    """True when the start's first recorded source is a public notebook or dataset (owner/slug :: file), or the
    start is a harvest lane file."""
    if re.search(r'/take-harvest-r\d+/|/harvest[\w.-]*/', start):
        return True
    srcs = []
    for c in sidecars(start):
        try:
            d = json.load(open(c))
        except Exception:
            continue
        if isinstance(d, dict):
            srcs.append(str(d.get('source') or ''))
    m0 = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', start)
    if m0:
        srcs.append((take_row(m0.group(1), int(m0.group(2))) or '').split(' || ')[0])
    return any(PUBFIRST.match(x) for x in srcs if x)


def check(start):
    load_withdrawn()
    if not getattr(check, '_own', False):
        for k in range(1, 1001):
            if held(k).startswith('original seed') and 'Samanyu' in held(k):
                OWN_N.add(k)
        check._own = True
    try:
        n = int(next(csv.DictReader(open(start)))['n'])
    except Exception:
        return {'start': start, 'clean': False, 'hits': ['unreadable start'], 'files': 0}
    texts, missing, seen, helds, refused = walk(start, n)
    own_root32 = any(re.search(r'original seed:\s*n\s*=\s*\d+\s+of\s+(?:Samanyu-dev/|franciscouzo/)|own independently discovered packing|own original root', t, re.I) for _,t in texts)
    public_first32 = harvest_type(start,n) or (not helds and not own_root32)
    hits = []
    via0 = dict(LAST_VIA)
    for label, t in texts:
        # a record that pins a parent by its sha256: the file on disk must still be that version, or the
        # parent's own record is no longer the one the producer traced (midm withdrew 684 for this at 15:48 UTC)
        # round 31: a record reached through a held row is the held row's business too, and a pin whose version a byte
        # copy still keeps (byte_copy) is not a change of the traced record
        held_lab = label.startswith('held ') or _through_held(label if label in via0 else S + str(label), via0)
        for m in (PIN.finditer(t) if not held_lab else ()):  # a held row's pins are the held row's business
            path, want = m.group(1), m.group(2).lower()
            if not path.startswith('/'):
                path = S + path
            have = file_sha(path)
            if have and not have.startswith(want) and not byte_copy(path, want):
                hits.append('%s: changed since pinned: %s (sha256 %s, now %s)' % (label.replace(S, '')[:80], path.replace(S, ''), want[:16], have[:16]))
        c = CMP.sub(_cmp, NEG.sub(' ', t))
        if label.startswith('held 801 '):
            continue  # main 00:19:03Z: the held 801 is ours and a start from it is allowed (its round 20 table row names the prvsiyan file)
        for m in NAMES.finditer(c):
            hits.append('%s: %s' % (label.replace(S, '')[:80], c[max(0, m.start() - 60):m.end() + 30].replace('\n', ' ')))
    alltext = '\n'.join(t for lb, t in texts if not str(lb).startswith('held 801 '))  # main 00:19:03Z: the held 801 is ours
    for name, rx in quench_audit.RULES:
        m = re.search(rx, alltext, flags=re.I)
        if m:
            hits.append('%s: %s' % (name, alltext[max(0, m.start() - 60):m.end() + 20].replace('\n', ' ')))
    hits += ['refused by its lane: ' + r for r in refused if not samanyu_only(r) and not share_only(r)]
    # round 27 rule b: the share test on the layout itself (0.4 or more of its squares within 1e-3 of the prvsiyan 1105 row)
    try:
        sh = prv_share(start, n) if public_first32 else (0.0,0.0,float('inf'),0.0)
    except Exception as e:  # an unreadable start is refused above; a failed measure must not pass silently
        sh = (1.0, 1.0, 0.0); hits.append('prvsiyan share not measured: %r' % (e,))
    # round 28 (main 00:19:03Z): the share test stays only for a row whose first source is a public notebook or
    # dataset we fetched (a harvest-type row); a share match never refuses our own layouts or their descendants
    # A start whose tree reaches no held reference has only public roots (a kick of a harvest row: twoshort r26 416 at
    # 0.745, backlog r26 646 at 0.641), so its first source is public and the test applies too.
    if public_first32:
        # round 31 override 3: a public-first row is out at a share of 0.4 or more at 1e-3 or at 1e-2 against any harvested
        # version of the 1105 row that is not our own Samanyu seed (pol_fail; the single-version rule b of rounds 27 to 30
        # had no own-seed exemption and no 1e-2 test)
        try:
            bad, why = pol_fail(start, n)
            if bad:
                hits.append('public-first row: %s: rule b' % why)
        except Exception as e:
            hits.append('public-first ICP share not measured: %r' % (e,))
    # round 29: a public-first ancestor (a fetched public file in a harvest public, collector or data folder) at a share
    # of 0.4 or more is out, and so is what is built from it (classfill 07:52:11Z withdrew its 503 for the harvest r22
    # public start 703.csv at 0.474; border r28 kept a 503 out for the harvest r22 collector file at 0.492)
    # round 30 override 3: our own layouts (the 801 row, every Samanyu-seed layout, seeds 503 and 983 among them) and
    # everything built from them get no share or ancestor-share gate. A start whose tree reaches a held reference is
    # built from our held layouts; the ancestor test stays only for a public-first start (harvest-type, or no held root),
    # the same condition as rule b above.
    # main 12:40:55Z ruling (round 30): a row built on a held row is built on our own layout, and the share test applies
    # only to a row whose own first source is a public file we fetched and that reaches no held row. So the ancestor test
    # runs only for a public-first start (harvest-type, or no held root), never for our own layouts' counts. (12:31Z I ran
    # it on every start, after the r28 skeptic's 814 drop; the ruling at 12:40Z voids that gate.)
    # main 13:32:00Z clarification: the void covers only a public file that reached us through a held row. A tree that
    # takes a public-first file directly (never held: harvest-r26 695, harvest-r26 814 5a4c0cdb) stays out even when it
    # also reaches held rows. So every start of a count that is not one of our own layouts is tested, and a public
    # ancestor is skipped only when its first-found path from the start passes through a held reference.
    pubfirst = public_first32
    via = dict(LAST_VIA)

    def through_held(x):
        if isinstance(x, str) and is_held_file(x):
            return True
        for _ in range(200):
            x = via.get(x)
            if x is None:
                return False
            if (isinstance(x, tuple) and x[0] == 'held') or (isinstance(x, str) and is_held_file(x)):
                return True
        return False
    for f in sorted(x for x in seen if isinstance(x, str)):
        if not pubfirst and through_held(f):
            continue
        if f != start and f.endswith('.csv') and re.search(r'/take-harvest-r\d+/%d(?:\.csv|-[0-9a-f]{8,}[\w.-]*\.csv)$' % n, f) and os.path.isfile(f):
            # a harvest per-n take file of the same n (a public-first row) in the tree, measured itself; round 31: also its
            # byte snapshots in other lanes' feed folders (forensics work/feed/take-harvest-r26/972-1cc8b04d.csv, the
            # alexchilton fault-line 972 at 0.402 within 1e-2 by ICP), measured with the round 31 policy (1e-3 and 1e-2, ICP)
            try:
                s3 = prv_share(f, n)
            except Exception:
                s3 = (0.0, 0.0, 0.0, 0.0)
            if max(s3[1], s3[3]) >= PRE:
                try:
                    bad, why = pol_fail(f, n)
                    if bad:
                        hits.append('public-first ancestor %s (n=%d) %s' % (f.replace(S, ''), n, why))
                except Exception as e:
                    hits.append('public-first ancestor %s: ICP share not measured: %r' % (f.replace(S, ''), e))
        if f == start or not f.endswith('.csv') or not PUBDIR.search(f) or not os.path.isfile(f):
            continue
        try:
            # the walk reaches whole collector tables; only the rows of the start's own n are taken as a parent here
            # (a public submission.csv holds every n, so its first row does not tell the n)
            from csv_rule27 import one as complete_single_count32
            complete32 = complete_single_count32(f)
            nf = complete32['n'] if complete32 else n
            s2 = prv_share(f, nf)
        except Exception:
            continue
        if max(s2[1], s2[3]) >= PRE:
            try:
                bad, why = pol_fail(f, nf)
                if bad:
                    hits.append('public-first ancestor %s (n=%d) %s' % (f.replace(S, ''), nf, why))
            except Exception as e:
                hits.append('public-first ancestor %s: ICP share not measured: %r' % (f.replace(S, ''), e))
    # a file the record names that no longer exists: the round 25 skeptic dropped
    # 860, 911, 921 and 975 for this (a start gone or replaced); rows it kept had none
    # Gone files under a held row (an accepted results-table row) are the held row's
    # business; every other gone file breaks the walk (927 of round 24 hid seed 811
    # behind a gone take-harvest-r23/866.csv).
    # A per-n take file of the live round that is gone was superseded by its lane (harvest dropped 972
    # and 910 at 14:11 UTC when midm beat them); the records that name it keep their own snapshots.
    # It refuses only when a WITHDRAW or WITHHOLD line names it.
    def superseded(x):
        # Round 27: a gone per-n take file of any round 22 to 27 counts as superseded (its lane removes the file
        # when another take beats it: harvest r23 866, family r25 860) unless a WITHDRAW or WITHHOLD line names it,
        # or its own lane's STATE.txt refuses it for a reason other than the lifted Samanyu-dev rule.
        m = re.match(r'(take-[a-z0-9-]+-r(?:2[2-9]|3[0-9])/\d+\.csv) ', x)  # round 30: rounds 22 to 39 (r29 per-n files are superseded copies now)
        if not m or any(m.group(1) == w for w, _ in WITHDRAWN_LINES):
            return False
        return not [r for r in refusals(S + m.group(1)) if not samanyu_only(r) and not share_only(r)]
    alltexts = '\n'.join(t for _, t in texts)

    def gone_copy(x):
        # round 31: a gone file that a record pins by sha256 is kept when a byte copy of that version exists (twoshort r30
        # moved its superseded 594.csv to near/ under another name; backlog's 594 names it with its sha256)
        rel = x.split(' (named by ')[0]
        for mm in re.finditer(re.escape(rel) + r'[^\n]{0,120}?sha256[\"\':=\s]*([0-9a-fA-F]{12,64})', alltexts):
            if byte_copy(S + rel, mm.group(1)):
                return True
        # a byte snapshot pinned just before the gone name ('the byte copy X (sha256 Y), taken at queue time from ... rel')
        for mr in re.finditer(re.escape(rel), alltexts):
            for mp in PIN.finditer(alltexts[max(0, mr.start() - 300):mr.start()]):
                q = mp.group(1) if mp.group(1).startswith('/') else S + mp.group(1)
                if 'copy' in alltexts[max(0, mr.start() - 300):mr.start()] and file_sha(q).startswith(mp.group(2).lower()):
                    return True
        return False
    hits += ['gone: ' + x for x in missing if not x.startswith(('held ', 'held-chain ')) and not superseded(x) and not gone_copy(x)]
    for w, line in WITHDRAWN_LINES:
        wb = os.path.basename(w)
        # round 31: a line that withdraws X and in the same breath retains n ('WITHDRAW own take n=416,850 ...; retained
        # 328,501,909,910,971,972', forensics r26 16:40Z) does not withdraw a tree of n: its lane audited that tree after
        # the purge (rebuild r31 910 reaches the forensics r26 850 snapshot that its rectangle took parts from)
        mret = re.search(r'\bretained\s*((?:\d{1,4}(?:\s*,\s*|\s+and\s+|\s+)?)+)', line, re.I)
        if mret and str(n) in re.findall(r'\d{1,4}', mret.group(1)):
            continue
        for f in seen:
            if not isinstance(f, str):
                continue
            if held_bytes(f):continue
            if through_held(f):
                continue  # round 30: reached through a held row (main 12:40:55Z, 13:32:00Z): held ancestry, the held file's business (main put our withdrawn r29 503 into round 29 b)
            mex = re.search(r'exact sha256 ([0-9a-f]{64}),?\s+(\S+?\.csv)', line)
            if mex and mex.group(2).endswith(w) and os.path.isfile(f) and not file_sha(f).startswith(mex.group(1)):
                continue  # round 31: a withdrawal names its pinned bytes; another version at the path is not withdrawn
            if f.endswith('/' + w):
                # a path a lane reuses: only the version written before the line is withdrawn; a gone one is withdrawn
                if not os.path.isfile(f) or os.path.getmtime(f) <= withdraw_time(line):
                    hits.append('withdrawn in a handoff line: ' + line[:200])
            elif os.path.basename(f) == wb and (not re.fullmatch(r'\d+(?:-[a-z]+)?\.csv', wb)
                                                 or f.startswith(S + w.split('/')[0] + '/')):
                # round 28: a reused per-round name (799-rect.csv) matches only inside the withdrawn file's own take dir;
                # forensics withdrew take-forensics-r24/near/799-rect.csv and the old read refused r23's 799-rect.csv
                # the same distinctive file moved to another folder (harvest work/near-out) is still withdrawn
                hits.append('withdrawn in a handoff line (moved copy %s): %s' % (f.replace(S, ''), line[:160]))
    if not helds and not ROOT.search(alltext):
        hits.append('no root: no held reference and no public file reached')
    return {'start': start, 'n': n, 'clean': not hits, 'capped': len(seen)>=100000, 'hits': sorted(set(hits))[:40], 'files': len(seen),
            'prv_share': [round(sh[0], 4), round(sh[1], 4), sh[2]],
            'helds': sorted('%d@%s' % h for h in helds)[:60], 'missing': sorted(set(missing))[:40]}


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    for p in sys.argv[1:]:
        print(json.dumps(check(p)), flush=True)
