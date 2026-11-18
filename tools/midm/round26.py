#!/usr/bin/env python3
"""midm round 26 driver on boxA: queue fresh designs, ship kick jobs to the boxes, certify, quench, publish.

One process, light work only on boxA (no search here). Every STEP seconds until the deadline:
  discover  new per-n files of the live take-*-r26 dirs (first class), their near/ files within a score margin of the
            base bar (second class), csv paths named in handoff-r26.log, and the extra starts of seed();
  assign    keep each box's open queue at its slot count plus one, best priority first (worker26.py picks
            priority first, newest first);
  pull      rsync the box's done/, jobs/, claims/, run/*/raw, run/*/scan-*.tsv, fqout/ back to work/box/<name>;
  certify   the lowest raw find of each scan through floatsafe.work (2.2e-11), kept below the base by >1e-10;
  quench    stage each certified file into one box's fqin/ (midm_fqonce.py, any free slot runs it once);
  publish   the lower of the certified file and its certified quench, when the start's ancestry walks clean and
            the row is below the base bar and every other live take-*-r26 dir by more than 1e-10.
Usage: round26.py loop | once | status
"""
import csv, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path

csv.field_size_limit(1 << 26)
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L)); sys.path.insert(0, str(L / 'tools'))
import floatsafe  # noqa: E402
import forensics_sources  # noqa: E402
import forensics_policy  # noqa: E402

B = Path('$SCRATCH/bounties-squares')
T = B / 'take-midm-r26'; W = T / 'work'
BASE = B / 'gate/cand-round25-1114b/details.csv'
HELD = B / 'gather/round25-2026-11-14b.csv'
RES = L / 'results'
HANDOFF = B / 'handoff-r26.log'
DEADLINE = 1794676500.0          # 2026-11-14T17:15:00Z, search and quench
SEARCH_END = 1794675000.0        # 2026-11-14T16:50:00Z, no new scan starts after this
STEP = 60
BOXES = {
    'boxE': dict(host='boxE', dir='scratch/squares-midm', slots=2, base='$SCRATCH/squares-base'),
    'boxD': dict(host='boxD', dir='scratch/squares-midm', slots=1, base='$SCRATCH/squares-midm/base'),
}
SSH = ['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes']
# 'squares-joegun-boxed' is the upstream of source out (a), penguin069/squares-joegun-boxed-certified-union. A bare
# 'joegun' also matched jonathan1506/joegun-squares-packings (Apache 2.0, the source of held rows such as 684 in
# results/round13-best), and refused clean starts (forensics 910 and 850, the quench 910 start); narrowed 13:50Z.
BANNED = [r'samanyu[-_]dev', r'github\.com/samanyu', r'squares_in_squares', r'29e12ff3', r'penguin069', r'squares-joegun-boxed',
          r'prvsiyan/squares-verified-best-of-1105', r'cc[ -]?by[ -]?sa', r'921r25c921\.', r'921mo16\.F1d', r'985-r25-ba842328a07b',
          r'take-stair-c-r22(?:/|\s+)near/863-0f92c19d-n', r'take-border-r24/(?:near/)?735(?:[-.]|/)',
          r'take-k123-r24/(?:near/)?(?:735|790|968|489)(?:[-.]|/)',
          r'Samanyu(?:-dev)?(?: seed)? ancestry[:=]\s*(?:yes|seeds|unknown|unresolved)']
OUT_N = {639, 691, 745, 858, 918}     # out as they stand in take-harvest-r22 and the areebbb file (brief, sources out a)
# 15:45Z withdrawals of round 26 (handoff-r26.log): harvest 15:18:34Z (416 499 646 654 695 814, share 0.42 to 0.76 of
# squares within 1e-3 of the prvsiyan 1105 row), k123 15:37:47Z (546 695 932), backlog 15:13:36Z (706), quench
# 15:24:45Z (held 415 and 501 are round 21 rect pairs on the round 19 501, a Samanyu-dev seed: rule d).
BANNED += [r'take-harvest-r26/(?:near/|work/[^"]*/)?(?:416|499|646|654|695|814)(?:[-.]|/)',
           r'take-k123-r26/(?:near/)?(?:546|695|932)(?:[-.]|/)', r'take-backlog-r26/(?:near/)?706(?:[-.]|/)',
           r'take-forensics-r26/(?:near/)?(?:415|501)(?:[-.]|/)']
HELD_OUT = {415, 501}
ANC_EPOCH = '2026-11-14T15:45Z'


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
    if Path(p) == HELD and n is not None:
        if not _HELD_ROWS:
            for r in csv.DictReader(open(HELD)):
                _HELD_ROWS.setdefault(int(r['n']), []).append(r)
        return list(_HELD_ROWS.get(n, []))
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
    return {int(r['n']): float(r['score']) for r in csv.DictReader(open(BASE))}


def load_state():
    p = W / 'state26.json'
    if p.exists():
        return json.loads(p.read_text())
    return dict(next_k=26000, jobs={}, seen={}, cert={}, fq={}, published={}, handoff_off=0, boxes={})


def save_state(st):
    p = W / 'state26.json'; tmp = p.with_suffix('.tmp'); tmp.write_text(json.dumps(st)); tmp.replace(p)


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
    if forensics_policy.classify_text(norm)['status'] != 'none':
        return 'samanyu seed classifier'
    for n in OUT_N:
        if re.search(r'take-harvest-r22/(?:near/)?%d(?:[-.]|/)' % n, text) or re.search(r'areebbb[^"]{0,200}\b%d\b' % n, text):
            return 'out source n=%d' % n
    return None


def held_source(n):
    """Source and licence cells of the held row of n: the newest round table that names it."""
    tabs = sorted(RES.glob('round*-best-*.tsv'), key=lambda p: (int(re.search(r'round(\d+)', p.name)[1]), p.name), reverse=True)
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


def ancestry(origin, n):
    """(ok, why, source, licence) for a start file. Held rows of round 25 b pass the skeptic's audit; other files
    need forensics_sources.trace ok and no banned token anywhere in the walked evidence."""
    origin = Path(origin)
    if origin == HELD:
        src, lic, tab = held_source(n)
        bad = banned_text(src + ' ' + lic)
        if bad:
            return False, 'held source names ' + bad, src, lic
        return True, 'held round25 b row, source as %s' % tab, src, lic
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
            if why == 'missing source record' and Path(path) == HELD and isinstance(k, int):
                hs, hl, _ = held_source(k)
                if banned_text(hs + ' ' + hl) is None:
                    continue
            rest.append((why, path, k))
        if rest or not leaves:
            return False, 'trace refused: ' + '; '.join('%s %s n=%s' % x for x in sorted(set(rest)))[:600], src, lic
        return True, 'forensics_sources.trace ok to held round25 b roots %s (their source cells clean), %d chars, no banned token' % (
            sorted(set(k for _, _, k in leaves)), len(evt)), src, lic
    return True, 'forensics_sources.trace ok, %d chars of evidence, no banned token' % len(evt), src, lic


# ---------------------------------------------------------------- discovery

def live_takes():
    for d in sorted(B.glob('take-*-r26')):
        if d.name == 'take-midm-r26':
            continue
        yield d


def live_bar():
    """n -> (score, path) lowest certified per-n file over the other live r26 take dirs."""
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
    return str(p).endswith('-rect.csv') and '/take-forensics-r26/near/' in str(p)


def rect_prio(m):
    # 14:12Z: before the fresh takes too. First scans on fresh takes paid 2 of 8 (910 on a rect, twoshort 328), on rect
    # files 3 of 3.
    if m <= 1e-9:
        return 0.07
    return 0.08 + m * 200 if m <= 1e-4 else 0.19 + (m - 1e-4) * 100


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
    if kind_hint == 'take':
        add_job(st, n, p, 'fresh-take', 0.10 + max(0.0, min(margin, 1e-4)) * 500, 300, 'score %.12g margin %+.3g' % (s, margin))
    elif is_rect(p) and margin <= RECT_MARGIN:
        add_job(st, n, p, 'rect', rect_prio(margin), 300, 'score %.12g margin %+.3g' % (s, margin))
    elif margin <= 2e-5:
        add_job(st, n, p, 'fresh-near', 0.20 + max(0.0, margin) * 2000, 200, 'score %.12g margin %+.3g' % (s, margin))
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
                if re.search(r'/take-[a-z0-9-]+-r(?:1\d|2[0-5])/', q):
                    continue                       # frozen dirs: no new designs there
                consider(st, q, base, 'take' if Path(q).parent.name.startswith('take-') and Path(q).stem.isdigit() else 'near')


def seed(st, base):
    """Starts that no midm kick touched, queued once at the start of the round (STATE.txt says why)."""
    if st.get('seeded'):
        return
    st['seeded'] = True
    for n in (973, 535, 646, 791, 922, 595, 699):       # held round 25 b rows never kicked by midm, constructions first
        add_job(st, n, HELD, 'held-unkicked', 0.30, 200, 'held round25 b row, no midm kick of this layout r19-r25')
    for n in (802, 907, 800, 968, 985, 503, 550, 750, 548, 978, 542, 551, 599, 645, 926):
        add_job(st, n, HELD, 'held-other', 0.55, 150, 'held round25 b row; midm kicked another layout of n only')
    seed2(st, base)


def seed2(st, base):
    """The two n = 934 raw legs of round 25 (next items 2 and 3): 1.8e-7 and 3.4e-7 above the r25b bar, and their
    last legs gained 2.6e-6 and 2.8e-6. Ancestry traced clean (tools/midm/round26.py ancestry) at queue time."""
    if st.get('seeded2'):
        return
    st['seeded2'] = True
    for f in ('934-raw-kick-r25627-7d10b52df496.csv', '934-raw-kick-r25626-bf1cebc80203.csv'):
        p = B / 'take-midm-r25/near' / f
        ok, why, _, _ = ancestry(p, 934)
        if ok:
            add_job(st, 934, p, 'r25-leg', 0.40, 300, 'r25 raw leg, score %.12g, ancestry %s' % (score_file(p, 934), why))
        else:
            state_line('SKIP r25 leg %s: %s' % (p, why))


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
        elif j['kind'].startswith('held'):
            p = (0.30 if j['kind'] == 'held-unkicked' else 0.55) if m <= 1e-9 else 0.75
        elif j['kind'] == 'rect' or is_rect(j['origin']):
            # a rect file within 1e-9 of the base bar is the held row re-certified (488, 685): held class, not a design
            p = 0.30 if abs(s - base[n]) < 1e-9 else (rect_prio(m) if m <= RECT_MARGIN else 0.90)
        elif m <= 1e-9:
            p = 0.10
        elif m <= 2e-5:
            p = 0.20 + m * 2000
        elif m <= 1e-4:
            p = 0.36 + m * 500
        else:
            p = 0.90
        if p < 1 and len(taken.get(n, [])) >= 3:
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
    for j in todo:
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
            free = b['slots'] + 1 - len(box_open(st, name))
            if free > 0 and (best is None or free > best[0]):
                best = (free, name)
        if best is None:
            return
        name = best[1]; b = BOXES[name]
        out = box_dir(name) / 'out'; (out / 'jobs').mkdir(parents=True, exist_ok=True); (out / 'in').mkdir(exist_ok=True)
        stem = '%d-%d' % (j['k'], j['n'])
        Path(out / 'in' / (stem + '.csv')).write_bytes(Path(j['start']).read_bytes())
        job = dict(k=j['k'], n=j['n'], sub='in/%s.csv' % stem, seed=j['k'] % 10000 + 1, seconds=j['seconds'], sigma=0.04,
                   priority=j['priority'], created=j['created'], leg=0, kind=j['kind'])
        tmp = out / 'jobs' / (stem + '.tmp'); tmp.write_text(json.dumps(job)); tmp.replace(out / 'jobs' / (stem + '.json'))
        rc, msg = run(['rsync', '-a', str(out) + '/', '%s:%s/' % (b['host'], b['dir'])])
        if rc != 0:
            log('push %s failed rc=%d %s' % (name, rc, msg[-300:])); (out / 'jobs' / (stem + '.json')).unlink(); return
        j['box'] = name; j['pushed'] = time.time()
        state_line('ASSIGN k=%d n=%d kind=%s -> %s' % (j['k'], j['n'], j['kind'], name))


def pull(st):
    for name, b in BOXES.items():
        bd = box_dir(name) / 'back'; bd.mkdir(parents=True, exist_ok=True)
        rc, msg = run(['rsync', '-a', '--include=done/***', '--include=jobs/***', '--include=claims/***',
                       '--include=logs/***', '--include=fqout/***', '--include=run/', '--include=run/s*/',
                       '--include=run/s*/raw/', '--include=run/s*/raw/*.csv', '--include=run/s*/scan-*.tsv',
                       '--exclude=*', '%s:%s/' % (b['host'], b['dir']), str(bd) + '/'], timeout=300)
        if rc != 0:
            log('pull %s failed rc=%d %s' % (name, rc, msg[-300:]))


def boost_legs(st):
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
            if g >= 1e-5 and j.get('priority', 1) > want:
                j['priority'] = want
                out = box_dir(name) / 'out' / 'jobs'; out.mkdir(parents=True, exist_ok=True)
                tmp = out / (stem + '.tmp'); tmp.write_text(json.dumps(j)); tmp.replace(out / (stem + '.json'))
                boosted.append(stem); push = True
                state_line('BOOST leg %s on %s to priority %.2f (parent gained %.3g)' % (stem, name, want, g))
        if push:
            run(['rsync', '-a', str(box_dir(name) / 'out') + '/', '%s:%s/' % (b['host'], b['dir'])])


# ---------------------------------------------------------------- certify, quench, publish

def certify_file(p, n):
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
    if len(rows) != n:
        return None, None
    _, fr, score, e = floatsafe.work((n, rows))
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
            if n in live and not c['score'] < live[n][0] - 1e-10:
                continue                      # not below another lane's live row of n: nothing to publish
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


def job_ancestry(st, j):
    """Trace a job's start once per origin version (cached in st['anc']): the origin while its sha256 equals the sha
    at queue time, else the record snapshot of the start, else refuse."""
    n = j['n']
    anc = st.setdefault('anc', {}).get(j['origin'] + '|' + j['origin_sha'])
    if anc is None or (anc['ok'] and not anc.get('src')):     # a refusal is final (no STATE line every step)
        try:
            now_sha = sha(j['origin']) if j['origin'] != str(HELD) else 'held-b'
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
            rows[n] = dict(score=s, file=final, cert=cp, k=c['k'], raw=key, quench_gain=c['score'] - s)
    table = []
    for n, row in sorted(rows.items()):
        j = st['jobs'][str(row['k'])]
        job_ancestry(st, j)
        anc = st['anc'][j['origin'] + '|' + j['origin_sha']]
        if not anc['ok']:
            continue
        m_seed = re.search(r'-(\d+)-\d+\.csv$', row['raw'])
        leg = (int(m_seed[1]) - (j['k'] % 10000 + 1)) // 100 if m_seed else 0
        mode = re.search(r'/%d-([a-z]+)-' % n, row['raw'])
        start_txt = ('the held round 25 b row of n = %d (gather/round25-2026-11-14b.csv)' % n if j['origin'] == str(HELD)
                     else 'the round 26 file %s (sha256 %s)' % (j['origin'], j['origin_sha'][:16]))
        src = ('fq quench of fq kick and quench (midm_scan.py %s, leg %d, kick sigma 0.04 and local kick) from %s; '
               'start source: %s' % (mode[1] if mode else 'kick', leg, start_txt, anc['src']))
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
                f.write('%s midm -> all: certified n=%d, score=%r, gain=%.4g on the r25b bar (kick of %s, quenched from the certified file), %s\n' % (
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
    base = bar()
    if st.get('anc_epoch') != ANC_EPOCH:
        # a new withdrawal list: every start is traced again before it is assigned or published
        st['anc'] = {}
        for j in st['jobs'].values():
            j.pop('anc_checked', None)
        st['anc_epoch'] = ANC_EPOCH
        state_line('ANCESTRY epoch %s: cache cleared, every start traced again' % ANC_EPOCH)
    seed(st, base)
    seed2(st, base)
    discover(st, base)
    controls(st)
    reprioritize(st, base, live_bar())
    assign(st)
    save_state(st)
    pull(st)
    boost_legs(st)
    certify(st, base)
    save_state(st)
    quench_step(st, base)
    save_state(st)
    publish(st, base)
    save_state(st)


def main():
    W.mkdir(parents=True, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'once'
    st = load_state()
    if cmd == 'status':
        status(st); return
    if cmd == 'once':
        step(st); return
    if cmd == 'unsee-rect':
        # run with the driver stopped: forget forensics rect near files so discover() weighs them by the rect rule
        drop = [k for k in st['seen'] if is_rect(k.split('|')[0])]
        for k in drop:
            del st['seen'][k]
        save_state(st)
        print('dropped %d seen keys of forensics rect near files' % len(drop)); return
    if cmd == 'dry-rect':
        base = bar(); live = live_bar()
        for p in sorted((B / 'take-forensics-r26/near').glob('*-rect.csv')):
            n = int(re.match(r'(\d+)', p.name)[1]); s = score_file(p, n)
            if s is None:
                continue
            ref = min(base[n], live.get(n, (math.inf,))[0]); m = s - ref
            print(n, '%.12g' % s, 'margin %+.3g' % m, 'prio %.3f' % rect_prio(m) if m <= RECT_MARGIN else 'out')
        return
    (W / 'driver.pid').write_text(str(os.getpid()))
    state_line('START driver loop pid=%d deadline 17:15Z (search starts until 16:50Z), log work/driver.log' % os.getpid())
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
