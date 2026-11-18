#!/usr/bin/env python3
"""midm round 29 driver on boxA: queue fresh designs, ship kick jobs to the boxes, certify, quench, publish.

Round 29 changes to round28.py (round 29 brief overrides 1 to 7):
  - take dir take-midm-r29, bar round29-briefs/bar29.tsv, held file gather/round27-2026-11-15b.csv (round 26 b and
    25 b stay known held roots), live takes take-*-r29, handoff-r29.log, deadline 11:45Z (no new scan after 11:25Z,
    worker29.py ends every scan by 11:35Z);
  - our own layouts carry no share gate (override 3): the share test runs only on public-first starts, as in round 28;
  - rect files and fresh takes get 900 s scans (round 28: 300 s rect scans gained about their margin and were still
    finding at the cap; rebuild's 900 s kick of the 684 rect gained 9.0e-5);
  - carry jobs: the lowest raw find of each round 28 midm scan that ends within 1e-4 of bar29 is kicked again from that
    find, traced through the round 28 job's origin or its record snapshot (round 28 862 rect: 8e-5 gained in three
    legs, 643 500 234 457 ended within 2e-6 of their margins);
  - certification on boxA is border's finesafe.work (bisected dilation), as on the boxes (worker29.py);
  - a certified-file quench that gains 1e-9 of side or more is quenched again from its own certified file.

Round 28 changes to round27.py (round 28 brief overrides 1 to 7):
  - take dir take-midm-r28, bar round28-briefs/bar28.tsv, held file gather/round26-2026-11-14b.csv, live takes
    take-*-r28, handoff-r28.log, deadline 05:45Z (no new scan after 05:15Z);
  - main 00:19:03Z rule change: a prvsiyan share match never refuses our own layouts or their descendants (the
    held 801 and the Samanyu seeds included). The share test (0.4 of the centres within 1e-3, best of 8 symmetries)
    runs only on starts whose first source is a public notebook or dataset we fetched (public_first(): the
    backlog_gate27 pattern on the path and the first 3000 characters of the record), and on their final rows. A
    recorded ancestry that names the prvsiyan 1105 file stays out (BANNED). The 00:10Z ancestor share test of this
    driver (anc_pairs, ancestor_share) is kept as code but refuses nothing;
  - BANNED adds harvest r27 639 916 918 (union ancestry unresolved, prvsiyan notice); the share-based withdrawals of
    round 27 are void;
  - seed28(): the bar28 rows that are round 27 takes of other lanes and our 743 978, and the round 27 forensics rect
    files the round 27 driver queued but never ran, re-scored against bar28.

Round 27 text:

Round 27 changes to round26.py (brief overrides 2 to 6):
  - the Samanyu-dev rule is lifted: the tracer is tools/midm/sources27.py (forensics_sources.py without its Samanyu
    withdrawals), the seed classifier is off, and BANNED keeps only the prvsiyan, CC BY-SA, penguin069 and
    joegun-boxed notices and the withdrawals made for prvsiyan share or a missing parent;
  - prvsiyan is a SHARE test: a start or a final row with 0.4 or more of its centres within 1e-3 of the prvsiyan
    best-of-1105 row of its n (best of the 8 symmetries, as classfill prvsim26.py and harvest share_ac.py) is out;
  - the bar is round27-briefs/bar27.tsv; live takes are take-*-r27;
  - starts refused or withdrawn only for the Samanyu seed are seeded first (seed27(); work/extra-starts.txt adds more
    while the driver runs: one "path n priority note" per line);
  - a start that already sits below the bar is certified as it is (its own row) besides its kick, so a re-opened row
    counts even when the kick finds nothing;
  - forensics rect files and k123 near joins of round 27 rank as rect files.

One process, light work only on boxA (no search here). Every STEP seconds until the deadline:
  discover  new per-n files of the live take-*-r27 dirs (first class), their near/ files within a score margin of the
            base bar (second class), csv paths named in handoff-r27.log, and the extra starts of seed();
  assign    keep each box's open queue at its slot count plus one, best priority first (worker26.py picks
            priority first, newest first);
  pull      rsync the box's done/, jobs/, claims/, run/*/raw, run/*/scan-*.tsv, fqout/ back to work/box/<name>;
  certify   the lowest raw find of each scan through floatsafe.work (2.2e-11), kept below the base by >1e-10;
  quench    stage each certified file into one box's fqin/ (midm_fqonce.py, any free slot runs it once);
  publish   the lower of the certified file and its certified quench, when the start's ancestry walks clean and
            the row is below the base bar and every other live take-*-r27 dir by more than 1e-10.
Usage: round26.py loop | once | status
"""
import csv, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path

csv.field_size_limit(1 << 26)
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L)); sys.path.insert(0, str(L / 'tools'))
import floatsafe  # noqa: E402
sys.path.insert(0, str(L / 'tools/border/r28'))
import finesafe  # noqa: E402  (border r28: floatsafe with a bisected dilation, same rule)
sys.path.insert(0, str(L / 'tools/midm'))
import sources27 as forensics_sources  # noqa: E402
import forensics_policy  # noqa: E402
import readers_sources  # noqa: E402
import numpy as np  # noqa: E402
import zipfile, io  # noqa: E402

# Round 27 item 2: the Samanyu seed classifier refuses nothing. readers_sources keeps its other out patterns.
forensics_policy.classify_text = lambda text: dict(status='none', seeds=[])
readers_sources.classify_seed_text = lambda text: dict(status='none', seeds=[])
readers_sources.OUT_PATTERNS = [p for p in readers_sources.OUT_PATTERNS
                                if not any(t in p for t in ('take-border-r24', 'take-k123-r25', '172r'))]

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r29'; W = T / 'work'
T28 = B / 'take-midm-r28'
BASE = B / 'round29-briefs/bar29.tsv'
HELD = B / 'gather/round27-2026-11-15b.csv'
HELD26 = B / 'gather/round26-2026-11-14b.csv'
HELD25 = B / 'gather/round25-2026-11-14b.csv'
R23A = B / 'gather/round23-2026-11-13a.csv'
R23A_SRC = Path(__file__).resolve().parents[2] / 'results/forensics-round23a-sources-r24-2026-11-13.tsv'
RES = L / 'results'
HANDOFF = B / 'handoff-r29.log'
DEADLINE = 1794743100.0          # 2026-11-15T11:45:00Z, search and quench
SEARCH_END = 1794741900.0        # 2026-11-15T11:25:00Z, no new scan starts after this
STEP = 60
BOXES = {
    'boxE': dict(host='boxE', dir='scratch/squares-midm', slots=2, base='$SCRATCH/squares-base'),
    # 09:15Z: boxD runs rect files only (fresh takes held both boxes 07:00-09:15Z and the 1e-5 to 3e-5 rect
    # band, which crossed 3 of 8 in round 28, got one scan: 747)
    'boxD': dict(host='boxD', dir='scratch/squares-midm', slots=1, base='$SCRATCH/squares-midm/base', kinds=('rect',)),
}
SSH = ['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes']
# 'squares-joegun-boxed' is the upstream of source out (a), penguin069/squares-joegun-boxed-certified-union. A bare
# 'joegun' also matched jonathan1506/joegun-squares-packings (Apache 2.0, the source of held rows such as 684 in
# results/round13-best), and refused clean starts (forensics 910 and 850, the quench 910 start); narrowed 13:50Z.
# Round 27: the Samanyu-dev tokens (samanyu-dev, squares_in_squares, 29e12ff3, 921r25c921, 921mo16.F1d,
# 985-r25-ba842328a07b, the 863-0f92c19d-n alias, border-r24 735, k123-r24 735 790 968 489, "Samanyu ancestry: yes")
# are gone; they refused only for that seed.
BANNED = [r'squares-joegun-boxed', r'prvsiyan/squares-verified-best-of-1105', r'cc[ -]?by[ -]?sa']
OUT_N = {639, 691, 745, 858, 918}     # out as they stand in take-harvest-r22 and the areebbb file (brief, sources out a)
# 15:45Z withdrawals of round 26 (handoff-r26.log): harvest 15:18:34Z (416 499 646 654 695 814, share 0.42 to 0.76 of
# squares within 1e-3 of the prvsiyan 1105 row), k123 15:37:47Z (546 695 932), backlog 15:13:36Z (706), quench
# 15:24:45Z (held 415 and 501 are round 21 rect pairs on the round 19 501, a Samanyu-dev seed: rule d).
# Kept for round 27: harvest withdrew these at a prvsiyan share of 0.42 to 0.76 (the share rule), and k123 546 695 are
# built on the harvest 695. Re-opened: k123 932 and forensics 415 501 (Samanyu only), backlog 706 (distance cut only,
# share 0.001).
BANNED += [r'take-harvest-r26/(?:near/|work/[^"]*/)?(?:416|499|646|654|695|814)(?:[-.]|/)',
           r'take-k123-r26/(?:near/)?(?:546|695)(?:[-.]|/)']
# Round 28: withdrawals of round 27 that name files (handoff-r27.log). invent 23:50:47Z: the 684 donor of the n910
# tree (share 1.0) and both 910 near files; k123 23:07:53Z and 23:35:43Z: the 798 tree (complete ancestor 742, share
# 0.454, sha256 b890df05302fbe14), border 23:26:55Z: its 798; classfill 22:15:52Z: k123-r25 982 descendants (747
# donor share 1.0); forensics 21:41Z and 23:06Z: near rect 796 853 971 599 647 699 860; harvest 22:05Z to 22:31Z: 639
# 916 918.
# 00:45Z: the main 00:19:03Z rule change voids every withdrawal above that rested on a share only (684 donor, n910
# tree, 798 tree, 742 donors, k123-r25 982, forensics r27 rect 796 853 971 599 647 699 860). Kept: harvest r27 639 918
# (union ancestry of out source a unresolved) and 916 (its public notice names the prvsiyan file, no per-n trace).
BANNED += [r'take-harvest-r27/(?:near/)?(?:639|916|918)(?:[-.]|/)']
PUBLIC_FIRST = re.compile(r'take-harvest-r\d+|/data/nb/|/public\d*/|^\s*public |harvested|kaggle\.com|kaggle notebook', re.I)
HELD_OUT = set()
ANC_EPOCH = '2026-11-15T06:55Z'   # 06:55Z: bar29 rows and live r29 take rows accepted by their take.tsv row


def held_out(o):
    """A walked node that uses the held, gathered or tabled row of n = 415 or 501."""
    if isinstance(o, dict):
        p = str(o.get('path', ''))
        if o.get('n') in HELD_OUT and ('/gather/' in p or '/results/round' in p):
            return '%s n=%s' % (p, o.get('n'))
        src = o.get('source')
        if isinstance(src, list) and len(src) == 2 and src[1] in HELD_OUT and ('/gather/' in str(src[0]) or '/results/round' in str(src[0])):
            return '%s n=%s' % (src[0], src[1])
        for v in o.values():
            h = held_out(v)
            if h:
                return h
    elif isinstance(o, list):
        for v in o:
            h = held_out(v)
            if h:
                return h
    return None


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def state_line(s):
    with open(T / 'STATE.txt', 'a') as f:
        f.write('%s boxA %s\n' % (now(), s))


def log(s):
    with open(W / 'driver.log', 'a') as f:
        f.write('%s %s\n' % (now(), s))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


_HELD_ROWS = {}


def load_rows(p, n=None):
    if Path(p).parent.name == 'gather' and n is not None:
        # 20:50Z: per-n cache files (work/gcache/<file>/<n>.csv), written once from the whole gather file: at 2% of
        # a core a restart spent minutes parsing the whole file again
        cd = W / 'gcache' / Path(p).stem
        cf = cd / ('%d.csv' % n)
        if cf.exists():
            return list(csv.DictReader(open(cf)))
        g = _HELD_ROWS.setdefault(str(p), {})
        if not g:
            for r in csv.DictReader(open(p)):
                g.setdefault(int(r['n']), []).append(r)
            cd.mkdir(parents=True, exist_ok=True)
            for k, rows in g.items():
                with open(cd / ('.%d.tmp' % k), 'w', newline='') as h:
                    w = csv.DictWriter(h, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
                (cd / ('.%d.tmp' % k)).replace(cd / ('%d.csv' % k))
        return list(g.get(n, []))
    rows = [r for r in csv.DictReader(open(p)) if n is None or int(r['n']) == n]
    return rows


def side_rows(rows):
    lo = [math.inf] * 2; hi = [-math.inf] * 2
    for r in rows:
        a = float(r['angle']); x = float(r['x']); y = float(r['y'])
        h = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        lo[0] = min(lo[0], x - h); hi[0] = max(hi[0], x + h); lo[1] = min(lo[1], y - h); hi[1] = max(hi[1], y + h)
    return max(hi[0] - lo[0], hi[1] - lo[1])


def score_file(p, n):
    rows = load_rows(p, n)
    if len(rows) != n:
        return None
    return side_rows(rows) / math.sqrt(n) - 1


def bar():
    return {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BASE), delimiter='\t')}


# ---------------------------------------------------------------- prvsiyan share (round 27 item 3)

PRV_ZIP = B / 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
_PRV = {}


def _prv_rows():
    pc = W / 'prv-cache.json'
    if not _PRV and pc.exists():
        _PRV.update({int(k): v for k, v in json.loads(pc.read_text()).items()})
    if not _PRV:
        with zipfile.ZipFile(PRV_ZIP) as z:
            for name in ['submission.csv']:      # the one layout file of the dataset (the other csvs are tables)
                for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
                    k = {str(a).strip().lower(): v for a, v in r.items()}
                    if 'x' not in k or 'y' not in k:
                        continue
                    m = str(k['n']).lstrip('s') if 'n' in k else str(k.get('id', '')).split('_')[0]
                    if m.isdigit():
                        _PRV.setdefault(int(m), []).append((float(str(k['x']).lstrip('s')), float(str(k['y']).lstrip('s'))))
        pc.write_text(json.dumps(_PRV))
    return _PRV


def prv_share(rows, n):
    """Share of centres within 1e-3 of the prvsiyan 1105 row of n, best of the 8 symmetries; None if no such row."""
    p = _prv_rows().get(n)
    if not p or len(p) != n or len(rows) != n:
        return None
    a = np.array([[float(r['x']), float(r['y'])] for r in rows]); a -= (a.min(0) + a.max(0)) / 2
    b = np.array(p); b -= (b.min(0) + b.max(0)) / 2
    from scipy.spatial import cKDTree
    tree = cKDTree(b); best = 0.0
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = (a[:, ::-1] if sw else a) * np.array([sx, sy])
                d, _ = tree.query(c)
                best = max(best, float((d < 1e-3).mean()))
    return best


PRV_OUT = 0.4
_SHARE = {}


def share_of(p, n):
    """prv_share of file p at n, cached by sha256 of its bytes (gather files by path and n)."""
    p = Path(p)
    try:
        key = ('%s|%d' % (p, n)) if p.parent.name == 'gather' else sha(p) + '|%d' % n
    except OSError:
        return None
    if key not in _SHARE:
        try:
            _SHARE[key] = prv_share(load_rows(p, n), n)
        except (OSError, ValueError, KeyError):
            _SHARE[key] = None
    return _SHARE[key]


def load_state():
    p = W / 'state29.json'
    if p.exists():
        return json.loads(p.read_text())
    return dict(next_k=50000, jobs={}, seen={}, cert={}, fq={}, published={}, handoff_off=0, boxes={})


def save_state(st):
    p = W / 'state29.json'; tmp = p.with_suffix('.tmp'); tmp.write_text(json.dumps(st)); tmp.replace(p)


# ---------------------------------------------------------------- sources

def banned_text(text):
    norm = text.replace('samanyu1808/sis-final-packings', 'licensed-public/final-packings').replace(
        'samanyu1808/sis-submit', 'licensed-public/sis-submit')
    # negative declarations ("Samanyu-dev seed ancestry: no", "no Samanyu-dev seed layout") are not a reference
    norm = re.sub(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry:\s*(?:none|no)\b(?:\s*\([^)]*\))?', '', norm, flags=re.I)
    norm = re.sub(r'no\s+(?:known\s+)?Samanyu(?:-dev)?(?:\s+seed)?(?:\s+(?:ancestry|layout))?|Samanyu[- ]free', '', norm, flags=re.I)
    for pat in BANNED:
        if re.search(pat, norm, re.I):
            return pat
    for n in OUT_N:
        if re.search(r'take-harvest-r22/(?:near/)?%d(?:[-.]|/)' % n, text) or re.search(r'areebbb[^"]{0,200}\b%d\b' % n, text):
            return 'out source n=%d' % n
    return None


def held_source(n, upto=27):
    """Source and licence cells of the held row of n: the newest round table up to round `upto` that names it (round 27
    for the held round 27 b file, 26 for round 26 b, 25 for round 25 b)."""
    tabs = sorted(RES.glob('round*-best-*.tsv'), key=lambda p: (int(re.search(r'round(\d+)', p.name)[1]), p.name), reverse=True)
    tabs = [t for t in tabs if int(re.search(r'round(\d+)', t.name)[1]) <= upto]
    for t in tabs:
        for r in csv.DictReader(open(t), delimiter='\t'):
            if int(r['n']) == n:
                return r.get('source', ''), r.get('licence', ''), 'results/' + t.name
    return 'seed merged0, see README', 'see README, Files', 'README'


def record_text(p, n):
    rec, ledger = forensics_sources.record(p, n)
    if rec is None:
        return None, ledger
    return json.dumps(rec), ledger


def parts_source(rec, led):
    """Source and licence cells of a forensics composition (14:30Z): each part's original file and the ledger that
    gives its source, and the licence cell of that ledger's row when the part is a per-n take file."""
    cells, lics = [], []
    parts = rec['parts']
    for key in sorted(k for k, v in parts.items() if isinstance(v, dict)):
        p = parts[key]
        of = p.get('original_file') or (p.get('source') or [''])[0]
        ledger = p.get('ledger', '')
        cells.append('part %s %s (ledger %s)' % (key, of, ledger))
        lic = p.get('licence', '')
        m = re.match(r'(\d+)\.csv$', Path(of).name)
        if m and ledger.endswith('take.tsv') and Path(ledger).exists():
            try:
                for r in csv.DictReader(open(ledger), delimiter='\t'):
                    if r.get('n') == m[1] and (r.get('licence') or r.get('license')):
                        lic = r.get('licence') or r.get('license')
            except (OSError, csv.Error):
                pass
        lics.append('part %s: %s' % (key, lic))
    return ('forensics %s, record %s: %s' % (rec.get('kind', 'composition'), led, '; '.join(cells)), '; '.join(lics))


def anc_pairs(o, out=None):
    """(path, n) of every per-n CSV the walked evidence names: nodes with path and n, and [path, n] source pairs."""
    out = set() if out is None else out
    if isinstance(o, dict):
        if 'path' in o and isinstance(o.get('n'), int) and str(o['path']).endswith('.csv'):
            out.add((str(o['path']), o['n']))
        for v in o.values():
            anc_pairs(v, out)
    elif isinstance(o, list):
        if len(o) == 2 and isinstance(o[0], str) and isinstance(o[1], int) and o[0].endswith('.csv'):
            out.add((o[0], o[1]))
        for v in o:
            anc_pairs(v, out)
    return out


def ancestor_share(ev, rec=None):
    """Round 28: the highest prvsiyan share over every complete CSV ancestor the walk names (its own n each).
    Returns (max share, path, n, count measured)."""
    pairs = anc_pairs(ev)
    if rec is not None:
        anc_pairs(rec, pairs)
    # paths named only inside text cells (source strings, pinned donor ancestry): the k123 798 tree reached its 742
    # ancestor (share 0.454) only through such a string; n is the leading number of the file name
    txt = json.dumps(ev) + (json.dumps(rec) if rec is not None else '')
    for q in set(re.findall(r'((?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/[^\s"\\,;|()\[\]]+?\.csv)', txt)):
        m = re.match(r'(\d+)(?:[-.]|$)', Path(q).name)
        if m:
            pairs.add((q if q.startswith('/') else str(B / q), int(m[1])))
    best = (0.0, '', 0, 0); cnt = 0
    for path, k in sorted(pairs):
        if not (1 <= k <= 1000) or not Path(path).is_file():
            continue
        sh = share_of(path, k)
        if sh is None:
            continue
        cnt += 1
        if sh > best[0]:
            best = (sh, path, k, 0)
    return best[0], best[1], best[2], cnt


def public_first(origin, n):
    """Main 00:19:03Z: the share test runs only on rows whose first source is a public notebook or dataset we
    fetched. Held and round 23 a gather rows are ours. Else the path or the first 3000 characters of its record."""
    if Path(origin) in (HELD, HELD26, HELD25, R23A):
        return False
    if PUBLIC_FIRST.search(str(origin)):
        return True
    try:
        text, _ = record_text(origin, n)
    except Exception:  # noqa: BLE001
        text = None
    return bool(text and PUBLIC_FIRST.search(text[:3000]))


def ancestry(origin, n):
    return ancestry27(origin, n)


def ancestry_with_ancestor_share(origin, n):
    """00:10Z to 00:50Z: refused at an ancestor share of 0.4; void under the main 00:19:03Z rule change."""
    r = ancestry27(origin, n)
    if not r[0]:
        return r
    try:
        if Path(origin) in (HELD, R23A):
            ev = {'path': str(origin), 'n': n}
            rec = None
        else:
            ok, ev = forensics_sources.trace(origin, n, B)
            rec, _ = forensics_sources.record(origin, n)
        mx, mp, mk, cnt = ancestor_share(ev, rec)
    except Exception as ex:  # noqa: BLE001
        return False, 'ancestor share check error %r' % ex, r[2], r[3]
    if mx >= PRV_OUT:
        return False, 'complete ancestor %s n=%d has prvsiyan 1105 share %.3f >= %.1f' % (mp, mk, mx, PRV_OUT), r[2], r[3]
    return True, r[1] + '; %d complete CSV ancestors share-tested, max %.3f' % (cnt, mx), r[2], r[3]


def ancestry27(origin, n):
    """(ok, why, source, licence) for a start file. Held rows of round 25 b pass the skeptic's audit; other files
    need forensics_sources.trace ok and no banned token anywhere in the walked evidence."""
    origin = Path(origin)
    sh = share_of(origin, n) if public_first(origin, n) else None
    if sh is not None and sh >= PRV_OUT:
        return False, 'public-first start, prvsiyan 1105 share %.3f >= %.1f (share test, main 00:19:03Z)' % (sh, PRV_OUT), '', ''
    if origin in (HELD, HELD26):
        src, lic, tab = held_source(n, 27 if origin == HELD else 26)
        bad = banned_text(src + ' ' + lic)
        if bad:
            return False, 'held source names ' + bad, src, lic
        return True, 'held round%s b row, source as %s' % ('27' if origin == HELD else '26', tab), src, lic
    if origin == R23A:
        # the round 23 candidate: the skeptic held 20 of its n for the Samanyu-dev seed only (handoff-r23 20:05:12Z);
        # round 27 item 2 re-opens them. Source cells: results/forensics-round23a-sources-r24-2026-11-13.tsv.
        row = next((r for r in csv.DictReader(open(R23A_SRC), delimiter='\t') if r['n'].isdigit() and int(r['n']) == n), None)
        if row is None:
            return False, 'no round23a source row', '', ''
        src = 'round 23 candidate gather/round23-2026-11-13a.csv, held out of round 23 b for the Samanyu-dev seed only; source as results/forensics-round23a-sources-r24-2026-11-13.tsv: ' + row['source']
        lic = row['licence']
        bad = banned_text(row['source'] + ' ' + lic)
        if bad:
            return False, 'round23a source names ' + bad, src, lic
        ok, ev = forensics_sources.trace(origin, n, B)
        if not ok:
            return False, 'trace refused round23a n=%d: %s' % (n, json.dumps(ev)[:300]), src, lic
        return True, 'round23a row, tracer: %s; prvsiyan share %s' % (ev.get('reason'), sh), src, lic
    br = bar_row_source(origin, n)
    if br is not None:
        return br
    text, ledger = record_text(origin, n)
    if text is None:
        return False, 'no source record (%s)' % ledger, '', ''
    rec, led = forensics_sources.record(origin, n)
    src = rec.get('source', '') if isinstance(rec, dict) else text
    lic = rec.get('licence', rec.get('license', '')) if isinstance(rec, dict) else ''
    if isinstance(rec, dict) and not src and isinstance(rec.get('parts'), dict):
        src, lic = parts_source(rec, led)
    bad = banned_text(text)
    if bad:
        return False, 'record names ' + bad, src, lic
    try:
        ok, ev = forensics_sources.trace(origin, n, B)
    except Exception as ex:  # noqa: BLE001
        return False, 'trace error %r' % ex, src, lic
    evt = json.dumps(ev)
    bad = banned_text(evt)
    if bad:
        return False, 'walked evidence names ' + bad, src, lic
    h = held_out(ev) or held_out(rec)
    if h and n not in HELD_OUT:
        return False, 'walked evidence uses the withdrawn held row ' + h, src, lic
    if not ok:
        # The tracer of round 24 knows round23 b and round24 a as clean gather roots, not the held round 25 b file.
        # A leaf "missing source record" on a row of round25 b is that row: it passed the skeptic, and its source
        # cell (results/round25-best and older tables) is checked for banned tokens here. Any other leaf refuses.
        leaves = []

        def walk(o):
            if isinstance(o, dict):
                why = o.get('reason')
                if why and why not in ('refused parent', 'recorded ancestry', 'pinned immutable ancestry',
                                       'unique immutable ancestry roots', 'verified immutable donor group') and (
                        'missing' in why or 'refused' in why or 'prohibited' in why or 'excluded' in why or
                        'unresolved' in why or 'incomplete' in why or 'unsupported' in why or 'outside' in why or
                        'withdraw' in why or 'cycle' in why or 'differs' in why or 'changed' in why or 'unreadable' in why):
                    leaves.append((why, str(o.get('path')), o.get('n')))
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(ev)
        rest = []
        for why, path, k in leaves:
            if why == 'missing source record' and Path(path) in (HELD, HELD26, HELD25) and isinstance(k, int):
                hs, hl, _ = held_source(k, 27 if Path(path) == HELD else 26 if Path(path) == HELD26 else 25)
                if banned_text(hs + ' ' + hl) is None:
                    continue
            rest.append((why, path, k))
        if rest and leaves and live_take_row(origin, n) and all(w in ('missing source record', 'ancestry cycle') for w, _, _ in rest):
            # 06:50Z: a per-n file of a live round 29 take dir is that lane's take row: its source is the lane's take.tsv
            # row (output contract). A gap in the records below it (a work/starts snapshot with no record, k123's cycle
            # through its own 756) is not a banned source; banned tokens in the walked evidence still refuse (above).
            return True, ('live round 29 take row of %s, source as its take.tsv; the walk below it stops at %s' % (
                origin.parent.name, '; '.join('%s %s n=%s' % x for x in sorted(set(rest)))[:400])), src, lic
        if rest or not leaves:
            return False, 'trace refused: ' + '; '.join('%s %s n=%s' % x for x in sorted(set(rest)))[:600], src, lic
        return True, 'forensics_sources.trace ok to held round25/26/27 b roots %s (their source cells clean), %d chars, no banned token' % (
            sorted(set(k for _, _, k in leaves)), len(evt)), src, lic
    return True, 'forensics_sources.trace ok, %d chars of evidence, no banned token' % len(evt), src, lic


def live_take_row(origin, n):
    origin = Path(origin)
    return (origin.parent.parent == B and re.fullmatch(r'take-[a-z0-9-]+-r29', origin.parent.name) is not None and
            origin.name == '%d.csv' % n and origin.parent.name != T.name)


_BARSRC = {}


def bar_row_source(origin, n):
    """06:50Z: a round 28 take file that is the bar29 row of n (bar29.tsv source cell names it) passed the round 28
    assembly: it is a held row of this round. Source and licence cells are its round 28 take.tsv row (output contract);
    banned tokens in them still refuse. None when origin is not such a row."""
    origin = Path(origin)
    if not _BARSRC:
        _BARSRC.update({int(r['n']): r['source'] for r in csv.DictReader(open(BASE), delimiter='\t')})
    rel = _BARSRC.get(n, '')
    if not re.fullmatch(r'take-[a-z0-9-]+-r28/\d+\.csv', rel) or origin != B / rel:
        return None
    row = None
    try:
        for r in csv.DictReader(open(origin.parent / 'take.tsv'), delimiter='\t'):
            if r.get('n') == str(n):
                row = r
    except (OSError, csv.Error):
        row = None
    if row is None:
        return False, 'bar29 row %s has no take.tsv row' % rel, '', ''
    src = row.get('source', ''); lic = row.get('licence', row.get('license', ''))
    bad = banned_text(src + ' ' + lic)
    if bad:
        return False, 'bar29 row %s source names %s' % (rel, bad), src, lic
    return True, 'bar29 row %s (round 28 take, in the round 28 assembly), source as its take.tsv' % rel, src, lic


# ---------------------------------------------------------------- discovery

def live_takes():
    for d in sorted(B.glob('take-*-r29')):
        if d.name == 'take-midm-r29':
            continue
        yield d


def live_bar():
    """n -> (score, path) lowest certified per-n file over the other live r27 take dirs."""
    out = {}
    for d in live_takes():
        tab = d / 'take.tsv'
        rows = {}
        if tab.exists():
            try:
                for r in csv.DictReader(open(tab), delimiter='\t'):
                    try:
                        rows[int(r['n'])] = float(r.get('new') or r.get('score'))
                    except (TypeError, ValueError, KeyError):
                        pass
            except OSError:
                pass
        for p in d.glob('*.csv'):
            if not p.stem.isdigit():
                continue
            n = int(p.stem)
            s = rows.get(n)
            if s is None:
                try:
                    s = score_file(p, n)
                except (OSError, ValueError, KeyError):
                    s = None
            if s is not None and (n not in out or s < out[n][0]):
                out[n] = (s, str(p))
    return out


def add_job(st, n, origin, kind, prio, seconds, note=''):
    k = st['next_k']; st['next_k'] += 1
    start = W / 'starts' / ('%d-%d.csv' % (k, n)); start.parent.mkdir(parents=True, exist_ok=True)
    rows = load_rows(origin, n)
    with open(start, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, r in enumerate(rows):
            w.writerow([n, i, r['x'], r['y'], r['angle']])
    st['jobs'][str(k)] = dict(k=k, n=n, origin=str(origin), origin_sha=sha(origin) if Path(origin) != HELD else 'held-b',
                              start=str(start), kind=kind, priority=prio, seconds=seconds, created=time.time(), box=None,
                              note=note)
    if Path(origin) != HELD:
        # 14:40Z: keep the source record as it stood at queue time (other lanes rewrite near/<n>-rect.csv, its .json
        # sidecar and their take.tsv rows); publish() traces this snapshot when the origin changed since.
        try:
            rec, led = forensics_sources.record(origin, n)
            if rec is not None:
                Path(str(start) + '.json').write_text(json.dumps(rec))
                st['jobs'][str(k)]['rec_ledger'] = led
        except (OSError, ValueError, KeyError):
            pass
    state_line('QUEUE k=%d n=%d kind=%s prio=%.3f seconds=%d origin=%s %s' % (k, n, kind, prio, seconds, origin, note))
    return k


# 14:05Z: forensics rectangle compositions (near/<n>-rect.csv) are the inputs our kicks open. Measured this round on
# the r25b bar: 971-rect, 972-rect (twice) and the quench 910 take built on a rect gained 4.2e-5, 6.2e-5, 1.67e-4 and
# 1.93e-4 in their first scan, and legs added 7e-6 to 2.2e-5. The 13 other first scans on already quenched takes and
# near files gained 0 (or the 5e-11 floatsafe step) except twoshort 328 (8.0e-5). So a rect file up to 2.5e-4 above the
# bar runs before every plain near file, and one below the bar runs before the fresh takes. Order: legs of a parent
# that gained 1e-4 (0.05), rect below the bar (0.07), rect up to 1e-4 above (0.08-0.10), fresh takes (0.10), legs of
# a parent that gained 1e-5 (0.18), rect 1e-4 to 2e-4 above (0.19-0.20), plain near files (0.20-0.24), held (0.30).
RECT_MARGIN = 2e-4


def is_rect(p):
    # round 27 item 6: k123 join near files rank with the forensics rect compositions
    return ((str(p).endswith('-rect.csv') and re.search(r'/take-forensics-r2[789]/near/', str(p)) is not None) or
            re.search(r'/take-k123-r2[89]/near/', str(p)) is not None)


def rect_prio(m):
    # 14:12Z: before the fresh takes too. First scans on fresh takes paid 2 of 8 (910 on a rect, twoshort 328), on rect
    # files 3 of 3.
    # Round 28, 01:35Z: rect files within 1e-6 above the lowest row of n are re-cuts of that row. Round 27 and 28 ran
    # 16 such scans (415 591 641 686 740 799 861 459 535 547 986): none went below the held basin. Rect files 1e-5 to
    # 3e-5 above crossed 3 of 8 (743 +1.16e-5, 978 +1.33e-5 and +1.42e-5 with legs); 4e-5 to 1.7e-4 above gained up to
    # 7.8e-5 but crossed 0 of 14. So: below the bar first, then 1e-6 to 3e-5, then up to 1e-4, re-cuts last.
    if m <= -1e-9:
        return 0.07
    if m <= 1e-6:
        return 0.60
    # 01:45Z: 1e-6 to 1e-5 above crossed 0 of 4 (986 989 995 591), 1e-5 to 3e-5 above 3 of 8: that band first
    if 1e-5 < m <= 3e-5:
        return 0.075 + (m - 1e-5) * 100
    if m <= 1e-5:
        # 02:05Z: 8 scans in this band (986 989 995 591 547 697 632 789): all ended in the held basin or found nothing,
        # so after the 3e-5 to 1e-4 band
        return 0.115 + m * 100
    return 0.09 + m * 200 if m <= 1e-4 else 0.19 + (m - 1e-4) * 100


def reopen_prio(m):
    """Round 27 item 2: starts refused only for the Samanyu seed run first, the ones furthest below the bar first."""
    if m <= -1e-6:
        return 0.01
    if m <= 1e-9:
        return 0.03
    if m <= 2e-5:
        return 0.06 + m * 2000
    if m <= 1e-4:
        return 0.12 + m * 500
    return 0.25 + m * 300


def consider(st, p, base, kind_hint):
    p = Path(p)
    m = re.match(r'(\d+)', p.name)
    if not m or not p.is_file():
        return
    n = int(m[1])
    if not 1 <= n <= 1000:
        return
    try:
        st_ = p.stat(); key = '%s|%d|%d' % (p, st_.st_size, st_.st_mtime_ns)
    except OSError:
        return
    if key in st['seen']:
        return
    try:
        h = sha(p)
    except OSError:
        return
    if h in st['seen'].values():
        st['seen'][key] = h; return
    st['seen'][key] = h
    try:
        s = score_file(p, n)
    except (OSError, ValueError, KeyError):
        s = None
    if s is None:
        log('skip %s: unreadable or wrong count' % p); return
    margin = s - base[n]
    text, _ = record_text(p, n)
    if text is None:
        log('skip %s: no source record' % p); return
    bad = banned_text(text)
    if bad:
        state_line('SKIP start %s n=%d: its record names %s' % (p, n, bad)); return
    sh = share_of(p, n) if public_first(p, n) else None
    if sh is not None and sh >= PRV_OUT:
        state_line('SKIP start %s n=%d: public-first start, prvsiyan 1105 share %.3f >= %.1f' % (p, n, sh, PRV_OUT)); return
    if kind_hint == 'reopen':
        if margin > 2e-4:
            log('skip reopen %s: margin %+.3g above the bar' % (p, margin)); return
        k = add_job(st, n, p, 'reopen', reopen_prio(margin), 300, 'score %.12g margin %+.3g (re-opened: Samanyu-only refusal)' % (s, margin))
        if margin < -1e-10:
            st['jobs'][str(k)]['self_cert'] = True
    elif kind_hint == 'take':
        add_job(st, n, p, 'fresh-take', 0.10 + max(0.0, min(margin, 1e-4)) * 500, 900, 'score %.12g margin %+.3g' % (s, margin))
    elif is_rect(p) and margin <= RECT_MARGIN:
        add_job(st, n, p, 'rect', rect_prio(margin), 900, 'score %.12g margin %+.3g' % (s, margin))
    elif margin <= 2e-5:
        add_job(st, n, p, 'fresh-near', 0.20 + max(0.0, margin) * 2000, 300, 'score %.12g margin %+.3g' % (s, margin))
    elif margin <= 1e-4:
        add_job(st, n, p, 'fresh-near-far', 0.36 + margin * 500, 150, 'score %.12g margin %+.3g' % (s, margin))
    else:
        log('skip %s: margin %+.3g above the base bar' % (p, margin))


def discover(st, base):
    for d in live_takes():
        for p in sorted(d.glob('*.csv')):
            if p.stem.isdigit():
                consider(st, p, base, 'take')
        nd = d / 'near'
        if nd.is_dir():
            for p in sorted(nd.glob('*.csv')):
                consider(st, p, base, 'near')
    if HANDOFF.exists():
        data = HANDOFF.read_bytes()
        new = data[st['handoff_off']:].decode(errors='replace'); st['handoff_off'] = len(data)
        for line in new.splitlines():
            if ' midm ' in line[:30]:
                continue
            for q in re.findall(r'($SCRATCH/bounties-squares/[^\s,;"()]+\.csv)', line):
                if '/take-midm-' in q or '/take-' not in q:
                    continue
                if re.search(r'/take-[a-z0-9-]+-r(?:1\d|2[0-8])/', q):
                    continue                       # frozen dirs: no new designs there
                consider(st, q, base, 'take' if Path(q).parent.name.startswith('take-') and Path(q).stem.isdigit() else 'near')


R23A_REOPEN = (597, 599, 648, 698, 753, 809, 866, 868, 927, 935, 990)
SAMANYU_SKIP = re.compile(r'samanyu|squares_in|29e12ff3|863-0f92c19d|921r25c921|921mo16|985-r25-ba842328a07b|'
                          r'take-border-r24|take-k123-r24|take-forensics-r26/\(\?:near/\)\?\(\?:415|classifier', re.I)


def seed(st, base):
    """Round 29, queued once at the start: (1) the bar29 rows that are round 28 takes (other lanes' certified rows and
    our own 540 743), kicked as fresh takes for 900 s; (2) carry jobs from the round 28 finds (seed_carry); (3) the round
    28 forensics rect and k123 near files that the round 28 driver queued but never ran (401 rect jobs unassigned at its
    deadline), re-scored against bar29."""
    if st.get('seeded29'):
        return
    st['seeded29'] = True
    for r in csv.DictReader(open(BASE), delimiter='\t'):
        src = r.get('source', '')
        m = re.match(r'(take-[a-z0-9-]+-r28)/(\d+)\.csv$', src)
        if not m:
            continue
        consider(st, B / src, base, 'take')
    seed_carry(st, base)
    old = T28 / 'work/state28.json'
    if old.exists():
        o = json.loads(old.read_text())
        for j in sorted(o['jobs'].values(), key=lambda j: j['k']):
            if j['box'] is None and j['kind'] == 'rect':
                consider(st, j['origin'], base, 'near')
    extra_starts(st, base)


CARRY_MARGIN = 1e-4


def seed_carry(st, base):
    """Round 29: the lowest raw find of every round 28 midm scan (take-midm-r28/work/box and the box tail pulled into
    work/r28tail) whose score is within CARRY_MARGIN of the lower of bar29 and the live takes becomes a 900 s start. Its
    ancestry is the round 28 job's: the origin while its sha256 is the one pinned at round 28 queue time, else the
    record snapshot of the round 28 start (copied beside the carry start as <start>.json)."""
    o = json.loads((T28 / 'work/state28.json').read_text())
    live = live_bar()
    best = {}
    roots = [T28 / 'work/box' / b / 'back/run' for b in BOXES] + [W / 'r28tail' / b / 'run' for b in BOXES]
    for root in roots:
        if not root.is_dir():
            continue
        for sd in root.glob('s*'):
            j = o['jobs'].get(sd.name[1:])
            if j is None or not (sd / 'raw').is_dir():
                continue
            n = j['n']
            for p in (sd / 'raw').glob('%d-*.csv' % n):
                try:
                    sc = score_file(p, n)
                except (OSError, ValueError, KeyError):
                    continue
                if sc is not None and (n not in best or sc < best[n][0]):
                    best[n] = (sc, p, j)
    for n, (sc, p, j) in sorted(best.items()):
        ref = min(base[n], live.get(n, (math.inf,))[0])
        m = sc - ref
        if m > CARRY_MARGIN:
            continue
        if banned_text(j['origin']):
            continue
        k = st['next_k']; st['next_k'] += 1
        start = W / 'starts' / ('%d-%d.csv' % (k, n)); start.parent.mkdir(parents=True, exist_ok=True)
        rows = load_rows(p, n)
        with open(start, 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for i, r in enumerate(rows):
                w.writerow([n, i, r['x'], r['y'], r['angle']])
        snap = Path(j['start'] + '.json')
        if snap.exists():
            Path(str(start) + '.json').write_bytes(snap.read_bytes())
        origin = j['origin']
        if origin == str(HELD26) or j.get('origin_sha') == 'held-b':
            origin = str(HELD26)
        st['jobs'][str(k)] = dict(k=k, n=n, origin=origin, origin_sha=j['origin_sha'], start=str(start), kind='carry',
                                  priority=0.06 + max(0.0, m) * 300, seconds=900, created=time.time(), box=None,
                                  carry=dict(raw=str(p), raw_sha=sha(p), k28=j['k'], start28=j['start']),
                                  note='round 28 find score %.12g margin %+.3g' % (sc, m))
        state_line('QUEUE k=%d n=%d kind=carry prio=%.3f seconds=900 from round 28 find %s (sha256 %s) of k=%d, origin %s; margin %+.3g' % (
            k, n, st['jobs'][str(k)]['priority'], p, sha(p)[:16], j['k'], origin, m))


def extra_starts(st, base):
    """work/extra-starts.txt: "path [n] [note]" per line, considered once as re-opened starts (lines read so far kept)."""
    p = W / 'extra-starts.txt'
    if not p.exists():
        return
    lines = p.read_text().splitlines()
    done = st.setdefault('extra_done', 0)
    for line in lines[done:]:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == 'held' and parts[1].isdigit():
            n = int(parts[1])
            add_job(st, n, HELD, 'reopen-held', 0.05, 300, 'held round25 b row of n = %d, re-opened (%s)' % (n, ' '.join(parts[2:])))
        elif parts and parts[0].startswith('/'):
            consider(st, parts[0], base, 'reopen')
    st['extra_done'] = len(lines)


def seed2(st, base):
    return


def certify_starts(st, base):
    """A re-opened start that already sits below the bar is certified as it is: its own row can publish after its
    certified-file quench even when the kick finds nothing."""
    for j in st['jobs'].values():
        if not j.get('self_cert') or j.get('self_done') or j['box'] in (None, 'refused', 'cancelled'):
            continue
        n = j['n']
        if j.get('boxcert'):
            bj = box_dir(j['box']) / 'back/run' / ('s%d' % j['k']) / 'cert/start.json'
            if not bj.exists():
                continue                           # worker27.py certifies the start after its first scan
            rec = json.loads(bj.read_text())
            score = rec.get('score') if rec.get('ok') else None
            fr = list(csv.DictReader(open(bj.with_suffix('.csv')))) if rec.get('ok') else None
            j['self_done'] = True
        else:
            j['self_done'] = True
            score, fr = certify_file(j['start'], n)
        if score is None or not score < base[n] - 1e-10:
            state_line('SELFCERT k=%d n=%d: certified %s, not below the bar %.15g' % (j['k'], n, score, base[n])); continue
        cdir = W / 'cert'; cdir.mkdir(exist_ok=True)
        cp = cdir / ('%d-k%d-start-%s.csv' % (n, j['k'], sha(j['start'])[:12]))
        write_rows(cp, fr)
        st['cert'][j['start']] = dict(raw=score, n=n, k=j['k'], score=score, cert=str(cp), self=True)
        state_line('SELFCERT k=%d n=%d start as it is: score=%.15g bar=%.15g gain=%.4g' % (j['k'], n, score, base[n], base[n] - score))


_RAN28 = {}


def ran28():
    """sha256 of every start origin that a round 28 midm scan ran (06:30Z: the seed re-queued round 28 rect files whose
    same bytes round 28 had already scanned, e.g. 234-rect three times, 457 980 910; a repeat of a 300 s first scan is
    the carry job's work, and the carry starts from the find)."""
    if not _RAN28:
        o = json.loads((T28 / 'work/state28.json').read_text())
        _RAN28['s'] = {j.get('origin_sha') for j in o['jobs'].values() if j['box'] in BOXES}
    return _RAN28['s']


def reprioritize(st, base, live):
    """Unassigned fresh jobs rank by their start score against the lowest of the base and every live take of n:
    a result must beat both, so a near file far above another lane's new row of n has nothing to win. Starts within
    1e-9 of a start already run or queued for n are the same design re-quenched: parked. At most 3 runnable jobs per n."""
    jobs = sorted(st['jobs'].values(), key=lambda j: j['k'])
    for j in jobs:
        if 'score' not in j:
            try:
                j['score'] = score_file(j['start'], j['n'])
            except (OSError, ValueError, KeyError):
                j['score'] = None
    taken = {}
    for j in jobs:
        if j['box'] is not None and j['score'] is not None:
            taken.setdefault(j['n'], []).append(j['score'])
    # 13:58Z: our own certified finds count too. A start above our own row of n has to beat that row to publish, and a
    # start within 1e-9 of one of our finds (another lane's copy of our take) repeats a chain our legs already run.
    own = {}
    cn = {}
    for c in st['cert'].values():
        if c.get('score') is not None:
            own.setdefault(c['n'], []).append(c['score'])
            if c.get('cert'):
                cn[c['cert']] = c['n']
    # 14:10Z: the quenched copies count as our finds too (forensics near 972-rect became a copy of our quenched 972)
    for cpath, r in st['fq'].get('done', {}).items():
        if r.get('fq_score') is not None and cpath in cn:
            own.setdefault(cn[cpath], []).append(r['fq_score'])
    pins = {}
    pf = W / 'pin-k.txt'
    if pf.exists():
        for line in pf.read_text().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 2 and parts[0].isdigit():
                pins[int(parts[0])] = float(parts[1])
    cands = [j for j in jobs if j['box'] is None and j['kind'] != 'r25-leg']
    cands.sort(key=lambda j: (j['score'] is None, j['score'] if j['score'] is not None else 0.0))
    for j in cands:
        s = j['score']; n = j['n']
        if s is None:
            j['priority'] = 9.0; continue
        ref = min(base[n], live.get(n, (math.inf,))[0], min(own.get(n, [math.inf])))
        m = s - ref
        if j['k'] in pins:
            p = pins[j['k']]                        # work/pin-k.txt: a handoff line addressed to midm
        elif any(abs(s - t) < 1e-9 for t in taken.get(n, []) + own.get(n, [])):
            p = 5.0                                 # same design as a start already run or queued, or one of our finds
        elif j['kind'] != 'carry' and j.get('origin_sha') in ran28():
            p = 4.0                                 # these bytes had a round 28 scan; its find is a carry job
        elif j['kind'].startswith('reopen'):
            p = reopen_prio(m) if m <= 2e-4 else 0.85
        elif j['kind'] == 'carry':
            # a round 28 find continued: within 3e-5 before the rect band (0.06-0.069), then with the 3e-5 to 1e-4 rects
            # 06:20Z: within 1e-5 first (round 28 legs gained 2e-6 to 2.5e-5, typically 1e-5), 1e-5 to 3e-5 after the
            # fresh rect files of that band (0.078-0.084), then with the 3e-5 to 1e-4 rects
            p = (0.06 + max(0.0, m) * 300) if m <= 1e-5 else (0.078 + (m - 1e-5) * 300) if m <= 3e-5 else (
                0.09 + m * 200 if m <= CARRY_MARGIN else 0.90)
            if abs(s - base[n]) < 1e-6 or abs(m) < 1e-6:     # 06:15Z: 1e-6, as rect_prio (re-cuts within 1e-6 gained 0 of 16 in round 28)
                # 06:12Z: a round 28 find within 2e-8 of the bar or of a live row is that row re-found (11 of the first
                # carry jobs: 980 743 799 861 540 547 871 500 415 232 272 at -4.9e-11): held class, after the designs
                p = 0.55
        elif j['kind'].startswith('held'):
            p = (0.30 if j['kind'] == 'held-unkicked' else 0.55) if m <= 1e-9 else 0.75
        elif j['kind'] == 'rect' or is_rect(j['origin']):
            # a rect file within 1e-9 of the base bar is the held row re-certified (488, 685): held class, not a design
            p = 0.30 if abs(s - base[n]) < 1e-9 else (rect_prio(m) if m <= RECT_MARGIN else 0.90)
        elif m <= 1e-9:
            # 06:20Z: a fresh round 29 take of another lane is the live row itself, so any gain of its kick counts (rebuild
            # r28: first kicks of fresh rows moved 748 by 3.1e-5 and 910 by 8.4e-6): before everything else
            p = 0.04 if (j['kind'] == 'fresh-take' and '-r29/' in j['origin']) else 0.10
            # 07:50Z: fresh takes of the polishing lanes are converged: quench 503, backlog 421 and our earlier kicks of
            # them gave 0 of 4 (stop6 ends them in 24 to 900 s); they go after the rect files below the bar (0.074)
            if p == 0.04 and re.search(r'/take-(?:quench|border|backlog|harvest|classfill|soft)-r29/', j['origin']):
                p = 0.074
        elif m <= 2e-5:
            p = 0.20 + m * 2000
        elif m <= 1e-4:
            p = 0.36 + m * 500
        else:
            p = 0.90
        if p < 1 and len(taken.get(n, [])) >= 3 and not j['kind'].startswith('reopen'):
            p = max(p, 0.80)
        j['priority'] = p; j['margin_ref'] = m
        if p < 1:
            taken.setdefault(n, []).append(s)


def controls(st):
    """work/cancel-k.txt: one job number per line (with a reason after it). The job leaves the queue; a job that a
    box already holds gets cancel/<k>-<n> there, which worker26.py reads before a claim and while the scan runs."""
    p = W / 'cancel-k.txt'
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        parts = line.split(None, 1)
        if not parts or not parts[0].isdigit():
            continue
        j = st['jobs'].get(parts[0])
        if j is None or j.get('cancelled'):
            continue
        j['cancelled'] = True; j['priority'] = 9.0
        if j['box'] is None:
            j['box'] = 'cancelled'
        else:
            b = BOXES[j['box']]; out = box_dir(j['box']) / 'out'; (out / 'cancel').mkdir(parents=True, exist_ok=True)
            (out / 'cancel' / ('%d-%d' % (j['k'], j['n']))).write_text(parts[1] if len(parts) > 1 else 'cancel')
            run(['rsync', '-a', str(out) + '/', '%s:%s/' % (b['host'], b['dir'])])
        state_line('CANCEL k=%s n=%d: %s' % (parts[0], j['n'], parts[1] if len(parts) > 1 else ''))


# ---------------------------------------------------------------- boxes

def run(cmd, timeout=120, inp=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, input=inp)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 124, 'timeout'


def box_dir(name):
    return W / 'box' / name


def box_open(st, name):
    """Jobs on the box with no done record (leg jobs the worker wrote included)."""
    bd = box_dir(name)
    done = {p.stem for p in (bd / 'back/done').glob('*.json')} if (bd / 'back/done').is_dir() else set()
    remote = {p.stem for p in (bd / 'back/jobs').glob('*.json')} if (bd / 'back/jobs').is_dir() else set()
    mine = {'%d-%d' % (j['k'], j['n']) for j in st['jobs'].values() if j['box'] == name}
    gone = {'%d-%d' % (j['k'], j['n']) for j in st['jobs'].values() if j.get('cancelled')}
    return {x for x in (remote | mine) - done if '-'.join(x.split('-')[:2]) not in gone}


def assign(st):
    if time.time() >= SEARCH_END - 60:
        return
    todo = sorted((j for j in st['jobs'].values() if j['box'] is None), key=lambda j: (j['priority'], -j['created']))

    def room(kind):
        return any(not st['boxes'].get(nm, {}).get('down') and (not bb.get('kinds') or kind in bb['kinds']) and
                   bb['slots'] + 2 - len(box_open(st, nm)) > 0 for nm, bb in BOXES.items())
    for j in todo:
        if not any(room(kd) for kd in ('rect', 'fresh-take')):
            return
        if not room(j['kind']):
            continue
        if j['priority'] < 1 and j['origin'] != str(HELD) and not j.get('anc_checked'):
            # 14:57Z: trace the start before it takes a slot. The kicks of round 26 on starts the tracer refused (k123
            # 365 and 580, modules 911) beat nothing, and a refused start can never publish.
            j['anc_checked'] = True
            ok, why = job_ancestry(st, j)
            if not ok:
                j['box'] = 'refused'
                state_line('REFUSE k=%d n=%d before assign: %s' % (j['k'], j['n'], why[:300]))
                continue
        best = None
        for name, b in BOXES.items():
            if st['boxes'].get(name, {}).get('down'):
                continue
            if b.get('kinds') and j['kind'] not in b['kinds']:
                continue
            # 20:35Z: boxA at load 75-100 gives the driver about 3% of a core, so a step takes minutes; three
            # queued jobs per box keep the slots busy between steps (the worker picks the best priority first)
            free = b['slots'] + 2 - len(box_open(st, name))   # 06:30Z: +2 (boxA load 3-4, steps of 10-20 s)
            if free > 0 and (best is None or free > best[0]):
                best = (free, name)
        if best is None:
            continue                               # 09:15Z: another box may take the next kind
        name = best[1]; b = BOXES[name]
        out = box_dir(name) / 'out'; (out / 'jobs').mkdir(parents=True, exist_ok=True); (out / 'in').mkdir(exist_ok=True)
        stem = '%d-%d' % (j['k'], j['n'])
        Path(out / 'in' / (stem + '.csv')).write_bytes(Path(j['start']).read_bytes())
        job = dict(k=j['k'], n=j['n'], sub='in/%s.csv' % stem, seed=j['k'] % 10000 + 1, seconds=j['seconds'], sigma=0.04,
                   priority=j['priority'], created=j['created'], leg=0, kind=j['kind'], self_cert=bool(j.get('self_cert')))
        tmp = out / 'jobs' / (stem + '.tmp'); tmp.write_text(json.dumps(job)); tmp.replace(out / 'jobs' / (stem + '.json'))
        rc, msg = run(['rsync', '-a', str(out) + '/', '%s:%s/' % (b['host'], b['dir'])])
        if rc != 0:
            log('push %s failed rc=%d %s' % (name, rc, msg[-300:])); (out / 'jobs' / (stem + '.json')).unlink(); return
        j['box'] = name; j['pushed'] = time.time(); j['boxcert'] = True
        state_line('ASSIGN k=%d n=%d kind=%s -> %s' % (j['k'], j['n'], j['kind'], name))


def pull(st):
    for name, b in BOXES.items():
        bd = box_dir(name) / 'back'; bd.mkdir(parents=True, exist_ok=True)
        rc, msg = run(['rsync', '-a', '--include=done/***', '--include=jobs/***', '--include=claims/***',
                       '--include=logs/***', '--include=fqout/***', '--include=run/', '--include=run/s*/',
                       '--include=run/s*/raw/', '--include=run/s*/raw/*.csv', '--include=run/s*/scan-*.tsv',
                       '--include=run/s*/cert/', '--include=run/s*/cert/*.csv', '--include=run/s*/cert/*.json',
                       '--exclude=*', '%s:%s/' % (b['host'], b['dir']), str(bd) + '/'], timeout=300)
        if rc != 0:
            log('pull %s failed rc=%d %s' % (name, rc, msg[-300:]))


def boost_legs(st, base=None):
    """worker26.py gives every raw-find leg priority 0.45, after the held starts. A leg whose parent scan gained
    1e-5 of score or more goes to 0.25 (round 25: raw legs 0.000158 in 14 scans), still after fresh first scans."""
    boosted = st.setdefault('boosted', [])
    for name, b in BOXES.items():
        bd = box_dir(name) / 'back'
        if not (bd / 'jobs').is_dir():
            continue
        push = False
        for p in (bd / 'jobs').glob('*-L*.json'):
            stem = p.stem
            if stem in boosted or (bd / 'claims' / stem).exists() or (bd / 'done' / p.name).exists():
                continue
            k, n, leg = stem.split('-'); i = int(leg[1:])
            parent = bd / 'done' / (('%s-%s' % (k, n)) + ('' if i == 1 else '-L%d' % (i - 1)) + '.json')
            if not parent.exists():
                continue
            try:
                g = json.loads(parent.read_text()).get('gain') or 0.0
                j = json.loads(p.read_text())
            except ValueError:
                continue
            # a parent that gained 1e-4 or more (910 k26195: 3.4e-4 in 300 s, 6 finds, still descending at the end)
            # runs its leg before every first scan (13:40Z)
            want = 0.05 if g >= 1e-4 else 0.18     # 0.25 until 14:10Z; 0.18 puts it before the far rect files
            # round 29, 07:05Z: a leg whose start (the parent's find) sits 1e-6 to 1.2e-5 above the lower of the bar and
            # the live rows of n runs with the carry jobs of that band (642 carry: 8.9e-6 margin, gained 6.5e-6 in
            # 900 s, 2.4e-6 short; its leg waited at 0.45)
            m_leg = None
            if base is not None:
                try:
                    sc = score_file(bd / j['sub'], int(n))
                    if sc is not None:
                        m_leg = sc - min(base[int(n)], live_now().get(int(n), (math.inf,))[0])
                except (OSError, ValueError, KeyError):
                    m_leg = None
            if m_leg is not None and 1e-6 < m_leg <= 1.2e-5 and g < 1e-4:
                want = 0.065; g = max(g, 1e-5)
            # 08:10Z: a leg whose start is below the bar and every live row is a follow of our own row (907: kick of the
            # invent take gained 5.4e-6 in 900 s; its leg waited at 0.45): with the fresh takes of the building lanes
            if m_leg is not None and m_leg <= -1e-10 and g >= 1e-6:
                want = 0.05; g = max(g, 1e-5)
            if g >= 1e-5 and j.get('priority', 1) > want:
                j['priority'] = want
                out = box_dir(name) / 'out' / 'jobs'; out.mkdir(parents=True, exist_ok=True)
                tmp = out / (stem + '.tmp'); tmp.write_text(json.dumps(j)); tmp.replace(out / (stem + '.json'))
                boosted.append(stem); push = True
                state_line('BOOST leg %s on %s to priority %.3f (parent gained %.3g, leg start margin %s)' % (
                    stem, name, want, g, ('%+.3g' % m_leg) if m_leg is not None else '-'))
        if push:
            run(['rsync', '-a', str(box_dir(name) / 'out') + '/', '%s:%s/' % (b['host'], b['dir'])])


# ---------------------------------------------------------------- certify, quench, publish

def certify_file(p, n):
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
    if len(rows) != n:
        return None, None
    _, fr, score, e = finesafe.work((n, rows))
    if fr is None:
        return None, None
    return score, fr


def write_rows(path, fr):
    path = Path(path); tmp = path.with_name('.' + path.name + '.tmp')
    with open(tmp, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    tmp.replace(path)


_LIVE = {}


def live_now():
    """live_bar() at most once a step (certify asks for it per scan dir)."""
    if _LIVE.get('t', 0) < time.time() - 300:
        _LIVE['bar'] = live_bar(); _LIVE['t'] = time.time()
    return _LIVE['bar']


def scan_done(k, n):
    """Every scan of job k (first scan and legs) has a done record back on boxA."""
    return not scan_running(k, n)


def certify(st, base):
    """The lowest raw find of every scan dir (first scan and legs) goes through floatsafe."""
    for name in BOXES:
        run_d = box_dir(name) / 'back/run'
        if not run_d.is_dir():
            continue
        for sd in run_d.glob('s*'):
            k = sd.name[1:]
            j = st['jobs'].get(k)
            if j is None:
                continue
            n = j['n']
            raws = sorted((sd / 'raw').glob('%d-*.csv' % n)) if (sd / 'raw').is_dir() else []
            if not raws:
                continue
            best = None
            for p in raws:
                key = str(p)
                c = st['cert'].get(key)
                if c is None:
                    try:
                        s = score_file(p, n)
                    except (OSError, ValueError, KeyError):
                        continue
                    if s is None:
                        continue
                    c = st['cert'][key] = dict(raw=s, n=n, k=int(k))
                if best is None or c['raw'] < best[1]['raw']:
                    best = (key, c)
            key, c = best
            if 'score' in c or c['raw'] > base[n] - 5e-11:
                continue
            bj = sd / 'cert' / (Path(key).stem + '.json')
            box_rec = None
            if bj.exists():
                try:
                    box_rec = json.loads(bj.read_text())
                except ValueError:
                    box_rec = None
            if box_rec and box_rec.get('sha') == sha(key):
                # 21:25Z: certified on the box by worker27.py (floatsafe.work, 2.2e-11): no floatsafe here
                score = box_rec.get('score') if box_rec.get('ok') else None
                fr = list(csv.DictReader(open(sd / 'cert' / (Path(key).stem + '.csv')))) if box_rec.get('ok') else None
            elif j.get('boxcert') and not scan_done(int(k), n):
                continue                           # the box certifies it when the scan ends
            elif c['raw'] > min(base[n], live_now().get(n, (math.inf,))[0]) - 5e-11:
                c['score'] = None; c['skipped'] = 'not below a live take'; continue
            else:
                score, fr = certify_file(key, n)
            c['score'] = score
            if score is None:
                log('floatsafe failed %s' % key); continue
            if not score < base[n] - 1e-10:
                log('certified %s at %.15g, not below the base %.15g' % (key, score, base[n])); continue
            cdir = W / 'cert'; cdir.mkdir(exist_ok=True)
            cp = cdir / ('%d-k%s-%s.csv' % (n, k, hashlib.sha256(Path(key).read_bytes()).hexdigest()[:12]))
            write_rows(cp, fr); c['cert'] = str(cp)
            state_line('CERT n=%d k=%s raw=%s score=%.15g base=%.15g gain=%.4g (before quench)' % (
                n, k, Path(key).name, score, base[n], base[n] - score))


def best_cert(st, base):
    """n -> the lowest certified file that is below the base."""
    out = {}
    for key, c in st['cert'].items():
        if c.get('cert') and c.get('score') is not None and c['score'] < base[c['n']] - 1e-10:
            if c['n'] not in out or c['score'] < out[c['n']]['score']:
                out[c['n']] = dict(c, raw_path=key)
    return out


def quench_step(st, base):
    """One batch per box at a time: stage certified files that have no quench, read back finished batches."""
    for name, b in BOXES.items():
        q = st['fq'].get(name)
        if q and q['state'] == 'running':
            od = box_dir(name) / 'back/fqout'
            if (od / 'DONE').exists() or (od / 'FAILED').exists():
                failed = (od / 'FAILED').exists()
                for n_s, cpath in q['files'].items():
                    n = int(n_s)
                    rec = st['fq'].setdefault('done', {}).setdefault(cpath, {})
                    done_mark = od / ('%d.done' % n)
                    if not done_mark.exists() or done_mark.read_text().strip() != sha(cpath):
                        rec['state'] = 'failed'; continue
                    rec['state'] = 'quenched'; rec['box'] = name
                    outs = list(od.glob('%d-fq+*.csv' % n))
                    if outs:
                        s2, fr2 = certify_file(outs[0], n)
                        if s2 is not None and s2 < st_score(st, cpath) - 0:
                            qp = W / 'cert' / (Path(cpath).stem + '-fq.csv'); write_rows(qp, fr2)
                            rec['fq'] = str(qp); rec['fq_score'] = s2
                            # round 29 (border r28: self follow until a step gains under 1e-9 of side): a quench that
                            # gained 1e-9 of side or more is quenched again from its own certified file
                            src_kc = next(((kk, c) for kk, c in st['cert'].items() if c.get('cert') == cpath), None)
                            if src_kc is not None and (st_score(st, cpath) - s2) * math.sqrt(n) >= 1e-9:
                                st['cert']['follow:' + str(qp)] = dict(raw=s2, n=n, k=src_kc[1]['k'], score=s2, cert=str(qp),
                                                                       follow_of=cpath,
                                                                       raw_key=src_kc[1].get('raw_key', src_kc[0]))
                    state_line('QUENCHED n=%d on %s: certified %.15g -> %s' % (
                        n, name, st_score(st, cpath), ('%.15g' % rec['fq_score']) if 'fq_score' in rec else 'no lower side'))
                q['state'] = 'idle'
                if failed:
                    log('quench batch on %s FAILED' % name)
                run(SSH + [b['host'], 'cd %s && rm -rf fqin fqout' % b['dir']])
                import shutil
                shutil.rmtree(od, ignore_errors=True)
        if st['fq'].get(name, {}).get('state') == 'running' or time.time() > DEADLINE - 120:
            continue
        done = st['fq'].get('done', {})
        cands = best_cert(st, base)
        live = live_bar()
        files = {}
        for n, c in sorted(cands.items()):
            if n in live and not c['score'] < live[n][0] + 3e-6:
                # 09:45Z: up to 3e-6 above another lane's live row the quench may still cross (our 504: the certified-file
                # quench gained 1.3e-6 of score; the 504 leg find sat 3.1e-8 above twoshort's 504 and was never quenched)
                continue                      # not near another lane's live row of n: nothing to publish
            if scan_running(c['k'], n):
                continue                      # 14:45Z: quench the last find of a scan, not each find while it runs
            r = done.get(c['cert'])
            if r and r.get('state') in ('quenched', 'staged'):
                continue
            if r and r.get('state') == 'failed' and r.get('tries', 0) >= 2:
                continue
            files[str(n)] = c['cert']
        if not files:
            continue
        stage = box_dir(name) / 'fqstage'
        import shutil
        shutil.rmtree(stage, ignore_errors=True); (stage / 'fqin').mkdir(parents=True)
        for n_s, cpath in files.items():
            (stage / 'fqin' / ('%s.csv' % n_s)).write_bytes(Path(cpath).read_bytes())
        rc, msg = run(SSH + [b['host'], 'cd %s && rm -rf fqin fqout' % b['dir']])
        rc2, msg2 = run(['rsync', '-a', str(stage) + '/', '%s:%s/' % (b['host'], b['dir'])])
        rc3, msg3 = run(SSH + [b['host'], 'cd %s && touch fqin/GO' % b['dir']])
        if rc or rc2 or rc3:
            log('stage quench on %s failed %s %s %s' % (name, msg[-200:], msg2[-200:], msg3[-200:])); continue
        st['fq'][name] = dict(state='running', files=files, started=time.time())
        for cpath in files.values():
            r = done.setdefault(cpath, {}); r['state'] = 'staged'; r['tries'] = r.get('tries', 0) + 1
        st['fq']['done'] = done
        state_line('QUENCH STAGE %s n=%s (midm_fqonce.py from the certified files, one free slot runs it)' % (
            name, ','.join(sorted(files))))
        break        # one box per step: the other box keeps its slots for search


def scan_running(k, n):
    """A scan of job k (first scan or leg, all in run/s<k>) is claimed on a box and has no done record. Measured
    13:18-15:02Z: certified-file quenches held a boxE slot 3098 s in 14 batches and the boxD slot 2577 s in 6, about a
    third and a half of their time, mostly on finds that a later find of the same running scan replaced."""
    for name in BOXES:
        bd = box_dir(name) / 'back'
        cl = bd / 'claims'
        if not cl.is_dir():
            continue
        for c in cl.glob('%d-%d*' % (k, n)):
            if not (bd / 'done' / (c.name + '.json')).exists():
                return True
    return False


def st_score(st, cpath):
    for c in st['cert'].values():
        if c.get('cert') == cpath:
            return c['score']
    return math.inf


_WD = {}


def withdrawn():
    """09:00Z: sha256 -> handoff line of every exact-bytes withdrawal in handoff-r29.log (a line with the word WITHDRAW in
    capitals that names a full 64-hex sha256), minus bytes a later REINSTATE line names (full sha or a 16-hex prefix).
    Forensics withdrew its r29 376 take (sha256 baeff87d) at 08:32Z for public-first held ancestors with prvsiyan shares
    0.755 and 1.0; our 376 was a kick of those bytes. Withdrawals apply to the bytes they name (override 3)."""
    try:
        size = HANDOFF.stat().st_size
    except OSError:
        return {}
    if _WD.get('size') != size:
        wd = {}; re_in = []
        for line in HANDOFF.read_text(errors='replace').splitlines():
            if 'REINSTATE' in line:
                re_in += re.findall(r'\b[0-9a-f]{16,64}\b', line)
            elif 'WITHDRAW' in line:
                for h in re.findall(r'\b[0-9a-f]{64}\b', line):
                    wd[h] = line[:300]
        for p in re_in:
            for h in [h for h in wd if h.startswith(p)]:
                del wd[h]
        _WD['size'] = size; _WD['wd'] = wd
    return _WD['wd']


def job_ancestry(st, j):
    """Trace a job's start once per origin version (cached in st['anc']): the origin while its sha256 equals the sha
    at queue time, else the record snapshot of the start, else refuse."""
    n = j['n']
    wl = withdrawn().get(j.get('origin_sha', ''))
    if wl:
        key = j['origin'] + '|' + j['origin_sha']
        if not st.setdefault('anc', {}).get(key, {}).get('withdrawn'):
            st['anc'][key] = dict(ok=False, why='start bytes withdrawn: ' + wl, src='', lic='', withdrawn=True)
            state_line('ANCESTRY n=%d start %s: REFUSED (start bytes sha256 %s withdrawn in the handoff log: %s)' % (
                n, j['origin'], j['origin_sha'][:16], wl[:200]))
        return False, st['anc'][key]['why']
    anc = st.setdefault('anc', {}).get(j['origin'] + '|' + j['origin_sha'])
    if anc is None or (anc['ok'] and not anc.get('src')):     # a refusal is final (no STATE line every step)
        try:
            now_sha = sha(j['origin']) if j['origin'] not in (str(HELD), str(HELD26)) else 'held-b'
        except OSError:
            now_sha = None
        if now_sha == j['origin_sha']:
            ok, why, src, lic = ancestry(j['origin'], n)
        elif Path(j['start'] + '.json').exists():
            ok, why, src, lic = ancestry(j['start'], n)
            why = 'origin changed since queue; traced the record snapshot %s.json: %s' % (j['start'], why)
        else:
            ok, why, src, lic = False, 'origin changed since queue and no record snapshot', '', ''
        anc = st['anc'][j['origin'] + '|' + j['origin_sha']] = dict(ok=ok, why=why, src=src, lic=lic)
        state_line('ANCESTRY n=%d start %s: %s (%s)' % (n, j['origin'], 'clean' if ok else 'REFUSED', why))
    return anc['ok'], anc['why']


def publish(st, base):
    live = live_bar()
    done = st['fq'].get('done', {})
    rows = {}
    for key, c in st['cert'].items():
        cp = c.get('cert')
        if not cp or c.get('score') is None:
            continue
        r = done.get(cp)
        if not r or r.get('state') != 'quenched':
            continue
        n = c['n']; s = c['score']; final = cp
        if r.get('fq_score') is not None and r['fq_score'] < s:
            s = r['fq_score']; final = r['fq']
        if not s < base[n] - 1e-10:
            continue
        if n in live and not s < live[n][0] - 1e-10:
            continue
        if n not in rows or s < rows[n]['score']:
            rows[n] = dict(score=s, file=final, cert=cp, k=c['k'], raw=c.get('raw_key', key), quench_gain=c['score'] - s,
                           follows=key.startswith('follow:'))
    table = []
    for n, row in sorted(rows.items()):
        j = st['jobs'][str(row['k'])]
        job_ancestry(st, j)
        anc = st['anc'][j['origin'] + '|' + j['origin_sha']]
        if not anc['ok']:
            continue
        fsh = prv_share(load_rows(row['file'], n), n)
        if fsh is not None and fsh >= PRV_OUT and public_first(j['origin'], n):
            state_line('REFUSE publish n=%d: final row prvsiyan 1105 share %.3f' % (n, fsh)); continue
        m_seed = re.search(r'-(\d+)-\d+\.csv$', row['raw'])
        leg = (int(m_seed[1]) - (j['k'] % 10000 + 1)) // 100 if m_seed else 0
        mode = re.search(r'/%d-([a-z]+)-' % n, row['raw'])
        start_txt = ('the held round 27 b row of n = %d (gather/round27-2026-11-15b.csv)' % n if j['origin'] == str(HELD)
                     else 'the held round 26 b row of n = %d (gather/round26-2026-11-14b.csv)' % n if j['origin'] == str(HELD26)
                     else 'the round 23 candidate row of n = %d (gather/round23-2026-11-13a.csv, sha256 %s)' % (n, j['origin_sha'][:16])
                     if j['origin'] == str(R23A)
                     else 'the file %s (sha256 %s, byte copy %s)' % (j['origin'], j['origin_sha'][:16], j['start']))
        if j.get('carry'):
            start_txt = ('our round 28 find %s (sha256 %s) of the midm round 28 scan k=%d, whose start was %s' % (
                j['carry']['raw'], j['carry']['raw_sha'][:16], j['carry']['k28'], start_txt))
        if row['raw'] == j['start']:
            src = ('fq quench (midm_fqonce.py) of the certified start as it is, re-opened (round 29)'
                   ': %s; start source: %s' % (start_txt, anc['src']))
        else:
            src = ('fq quench of fq kick and quench (midm_scan.py %s, leg %d, kick sigma 0.04 and local kick) from %s; '
                   'start source: %s' % (mode[1] if mode else 'kick', leg, start_txt, anc['src']))
        if row.get('follows'):
            src = src.replace('fq quench of fq kick', 'fq quench of an fq quench of fq kick', 1)
        src += '; prvsiyan 1105 share of the final row within 1e-3: %s' % ('%.3f' % fsh if fsh is not None else 'no prvsiyan row of n')
        table.append((n, base[n], row['score'], base[n] - row['score'], src, anc['lic'] or 'see start source',
                      j['origin'], row['quench_gain'], row['file'], live.get(n, (None, ''))[0]))
    # write the per-n files first, then take.tsv by rename
    keep = set()
    for t in table:
        n = t[0]; dst = T / ('%d.csv' % n); keep.add(dst.name)
        src_bytes = Path(t[8]).read_bytes()
        if not dst.exists() or dst.read_bytes() != src_bytes:
            tmp = T / ('.%d.csv.tmp' % n); tmp.write_bytes(src_bytes); tmp.replace(dst)
    tmp = T / '.take.tsv.tmp'
    with open(tmp, 'w', newline='') as h:
        w = csv.writer(h, delimiter='\t', lineterminator='\n')
        w.writerow(['n', 'held', 'new', 'gain', 'source', 'licence', 'start', 'polish_gain', 'live_peer'])
        for t in table:
            w.writerow([t[0], repr(t[1]), repr(t[2]), repr(t[3]), t[4], t[5], t[6], repr(t[7]), repr(t[9]) if t[9] is not None else ''])
    tmp.replace(T / 'take.tsv')
    for p in T.glob('*.csv'):
        if p.stem.isdigit() and p.name not in keep:
            p.unlink(); state_line('DROP n=%s from take: no longer below the base and every live take by 1e-10, or refused' % p.stem)
    pub = st.setdefault('published', {})
    for t in table:
        n = t[0]
        if pub.get(str(n)) != t[2]:
            pub[str(n)] = t[2]
            state_line('TAKE n=%d score=%.15g gain=%.4g start=%s' % (n, t[2], t[3], t[6]))
            with open(HANDOFF, 'a') as f:
                f.write('%s midm -> all: certified n=%d, score=%r, gain=%.4g on bar29 (from %s, quenched from the certified file), %s\n' % (
                    now(), n, t[2], t[3], t[6], T / ('%d.csv' % n)))


def status(st):
    base = bar()
    print('jobs', len(st['jobs']), 'assigned', sum(1 for j in st['jobs'].values() if j['box']))
    for name in BOXES:
        print(name, 'open', sorted(box_open(st, name)))
    for n, c in sorted(best_cert(st, base).items()):
        print('cert', n, c['score'], base[n] - c['score'], c['cert'])
    print('fq', json.dumps({k: v for k, v in st['fq'].items() if k != 'done'}))
    print('take', (T / 'take.tsv').read_text()[:3000] if (T / 'take.tsv').exists() else '-')


def step(st):
    t0 = time.time(); marks = []
    base = bar()
    if st.get('anc_epoch') != ANC_EPOCH:
        # a new withdrawal list: every start is traced again before it is assigned or published
        st['anc'] = {}
        for j in st['jobs'].values():
            j.pop('anc_checked', None)
            if j['box'] == 'refused' and not j.get('cancelled'):
                j['box'] = None                 # traced again under the new tracer before it can take a slot
        st['anc_epoch'] = ANC_EPOCH
        state_line('ANCESTRY epoch %s: cache cleared, every start traced again' % ANC_EPOCH)
    for name, fn in (('seed', lambda: seed(st, base)), ('extra', lambda: extra_starts(st, base)),
                     ('discover', lambda: discover(st, base)), ('controls', lambda: controls(st)),
                     ('reprioritize', lambda: reprioritize(st, base, live_bar())), ('assign', lambda: assign(st)),
                     ('save', lambda: save_state(st)), ('pull', lambda: pull(st)), ('legs', lambda: boost_legs(st, base)),
                     ('selfcert', lambda: certify_starts(st, base)), ('certify', lambda: certify(st, base)),
                     ('save', lambda: save_state(st)), ('quench', lambda: quench_step(st, base)),
                     ('save', lambda: save_state(st)), ('publish', lambda: publish(st, base)), ('save', lambda: save_state(st))):
        t = time.time(); fn(); marks.append('%s %.0f' % (name, time.time() - t))
    log('step %.0f s: %s' % (time.time() - t0, ', '.join(marks)))


def main():
    W.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'once'
    st = load_state()
    if cmd == 'status':
        status(st); return
    if cmd == 'once':
        step(st); return
    if cmd == 'unsee-skips':
        # 00:50Z, run with the driver stopped: forget the starts that discovery skipped (STATE.txt "SKIP start" lines)
        # so they are considered again under the main 00:19:03Z rule; the seed runs again for the frozen round 27 rows
        paths = set(re.findall(r' SKIP start (\S+) n=\d+', (T / 'STATE.txt').read_text()))
        drop = [k for k in st['seen'] if k.split('|')[0] in paths]
        for k in drop:
            del st['seen'][k]
        st['seeded29'] = False
        save_state(st)
        print('dropped %d seen keys of %d skipped starts' % (len(drop), len(paths))); return
    if cmd == 'unsee-rect':
        # run with the driver stopped: forget forensics rect near files so discover() weighs them by the rect rule
        drop = [k for k in st['seen'] if is_rect(k.split('|')[0])]
        for k in drop:
            del st['seen'][k]
        save_state(st)
        print('dropped %d seen keys of forensics rect near files' % len(drop)); return
    if cmd == 'dry-rect':
        base = bar(); live = live_bar()
        for p in sorted((B / 'take-forensics-r29/near').glob('*-rect.csv')):
            n = int(re.match(r'(\d+)', p.name)[1]); s = score_file(p, n)
            if s is None:
                continue
            ref = min(base[n], live.get(n, (math.inf,))[0]); m = s - ref
            print(n, '%.12g' % s, 'margin %+.3g' % m, 'prio %.3f' % rect_prio(m) if m <= RECT_MARGIN else 'out')
        return
    (W / 'driver.pid').write_text(str(os.getpid()))
    state_line('START driver loop pid=%d deadline 11:45Z (search starts until 11:25Z), log work/driver.log' % os.getpid())
    while time.time() < DEADLINE + 8 * 60 and not (W / 'STOP').exists():
        t0 = time.time()
        try:
            step(st)
        except Exception as ex:  # noqa: BLE001
            import traceback
            log('step error %r\n%s' % (ex, traceback.format_exc()))
        time.sleep(max(5, STEP - (time.time() - t0)))
    state_line('FINISH driver loop pid=%d' % os.getpid())


if __name__ == '__main__':
    main()
