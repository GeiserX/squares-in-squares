"""Use the producer lanes' ancestry readers before admitting soft starts."""
import csv
import json
import re
import sys
from pathlib import Path

LANE = Path('.')
sys.path.insert(0, str(LANE))
sys.path.insert(0, str(LANE / 'tools'))
import forensics_sources
import readers_sources
from harvest_follow import refused_source, provenance_text

S = Path('$SCRATCH/bounties-squares')
CANDIDATE = S / 'gather/round23-2026-11-13a.csv'


CANDIDATE_B = S / 'gather/round23-2026-11-13b.csv'
_TRACE = forensics_sources._trace


CANDIDATE_R25B = S / 'gather/round25-2026-11-14b.csv'
R25_TABLE = LANE / 'results/round25-best-2026-11-14.tsv'


def _trace_b(path, n, scratch, active=None, recorded=None):
    """Round 25: the held round23b file is a clean root, except held 801 and 907.
    Round 26: a row of the held round25b file resolves to the take file its round 25 table names, else to round23b.
    The root text check in trace() then reads that row's recorded source."""
    p = Path(path)
    if not p.is_absolute() and str(p).startswith(('take-', 'gather/')):
        p = Path(scratch) / p
    if p == CANDIDATE_R25B:
        if False:
            return False, dict(path=str(p), n=n, reason='prohibited held801 in round25b')
        row = next((r for r in csv.DictReader(open(R25_TABLE), delimiter='\t') if int(r['n']) == n), None)
        if row:
            names = re.findall(r'take-[a-z-]+-r\d+', row.get('take', ''))
            if len(names) != 1:
                return False, dict(path=str(p), n=n, reason='unresolved round25b donor')
            ok, proof = _trace_b(Path(scratch) / names[0] / ('%d.csv' % n), n, scratch, active)
        else:
            ok, proof = _trace_b(CANDIDATE_B, n, scratch, active)
        return ok, dict(path=str(p), n=n, parent=proof, reason='round25b row resolved to its recorded donor')
    m = re.search(r'/take-border-r\d+/work/donors/(\d+)-[0-9a-f]{16}\.csv$', str(p))
    if m and int(m[1]) == n:
        ok, proof = _TRACE(path, n, scratch, active, recorded=recorded)
        if ok or proof.get('reason') != 'missing source record':
            return ok, proof
        # Round 26: the border lane keeps byte copies of its donors without a record (border-r26 794 and 791 at 13:45Z).
        # A copy counts as its original when one take or near file of n has the same bytes and traces clean.
        import glob, hashlib
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        names = glob.glob('%s/take-*-r2[2-6]/%d.csv' % (scratch, n)) + glob.glob('%s/take-*-r2[2-6]/near/%d-*.csv' % (scratch, n))
        for q in sorted(names):
            if 'take-border-' in q or hashlib.sha256(open(q, 'rb').read()).hexdigest() != digest:
                continue
            ok2, proof2 = _trace_b(q, n, scratch, active)
            if ok2:
                return True, dict(path=str(p), n=n, parent=proof2, reason='byte-identical copy of a traced file', original=q)
        return ok, proof
    if p == CANDIDATE_B:
        if n == 907:
            return False, dict(path=str(p), n=n, reason='prohibited held801/907 in round23b')
        return True, dict(path=str(p), n=n, reason='clean round23b held file')
    return _TRACE(path, n, scratch, active, recorded=recorded)


def _install():
    """follow.py reloads forensics_sources each cycle, so the round23b root goes back in before each trace."""
    global _TRACE
    if getattr(forensics_sources._trace, '__name__', '') != '_trace_b':
        _TRACE = forensics_sources._trace
        forensics_sources._trace = _trace_b


_install()


def metadata(path, n):
    path = Path(path)
    for side in (Path(str(path) + '.json'), path.with_suffix('.json')):
        if side.exists():
            obj = json.load(open(side))
            if isinstance(obj, dict):
                src = obj.get('source_override') or obj.get('source')
                if isinstance(src, str):
                    return src, str(obj.get('licence_override') or obj.get('licence') or ''), str(side)
                notices = set()
                def collect(value):
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if k in ('licence', 'license', 'donor_licence') and isinstance(v, str):
                                notices.add(v)
                            elif isinstance(v, (dict, list)):
                                collect(v)
                    elif isinstance(value, list):
                        for v in value:
                            collect(v)
                collect(obj)
                return provenance_text(obj), '; '.join(sorted(notices)), str(side)
    root = next((p for p in path.parents if re.fullmatch(r'take-.+-r\d+', p.name)), path.parent)
    # Reader end names pin an immutable donor version in the producer's register.
    match = re.search(r'from(.+)\.csv$', path.name)
    if match and root.name.startswith('take-readers-'):
        table = root / 'work/sources-all.tsv'
        if table.exists():
            for row in csv.DictReader(open(table), delimiter='\t'):
                if row.get('donor') == match[1]:
                    return row['source'], row.get('licence') or '', str(table)
    tables = [(path.parent / 'near.tsv', 'file', path.name)]
    if path.parent.name == 'unread':
        tables.append((root / 'work/sources.tsv', 'donor', path.stem))
    if path.stem.isdigit() and path.parent == root:
        tables.append((root / 'take.tsv', 'n', str(n)))
    for table, key, value in tables:
        if table.exists():
            for row in csv.DictReader(open(table), delimiter='\t'):
                if row.get(key) == value and row.get('source'):
                    return row['source'], row.get('licence') or '', str(table)
    return '', '', ''


def inline_record(detail, source, licence, record, rnd):
    """Read exact producer records when an exported family file has rotated away.

    A missing policy root or a forbidden parent never qualifies. The source must
    retain an explicit public origin or an original construction notice.
    """
    if rnd != 24 or not source or not record:
        return None
    def missing_only(value):
        if isinstance(value, list):
            return all(missing_only(v) for v in value)
        if not isinstance(value, dict):
            return True
        reason = value.get('reason', '')
        if reason and reason not in ('refused parent', 'missing source record', 'missing donor file'):
            # Accepted branches retain their positive reason.
            if reason not in ('clean round23 candidate', 'round23 changed-count whitelist', 'recorded ancestry'):
                return False
        return all(missing_only(v) for k, v in value.items() if k != 'record')
    if not missing_only(detail):
        return None
    text = source + ' ' + licence
    if refused_source(dict(source=source, licence=licence), str(S)):
        return None
    named_origin = re.search(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+', text)
    public_notice = re.search(r'Apache|CC0|CC BY 4\.0|MIT', text)
    own = 'our own design' in text or 'own construction' in text
    candidate = 'round23-best-2026-11-13.tsv' in text or 'round23-2026-11-13a.csv' in text
    if not (own or candidate or (named_origin and public_notice)):
        return None
    if 'sis-certified-union-micro-shrink' in text and not re.search(r'upstream per-n|per-n origin', text, re.I):
        return None
    return dict(reason='complete inline producer ancestry', source_record=record,
                source=source, licence=licence, original_trace=detail)


_STATES = {}


def reader_state(root):
    """The readers lane stores state subtrees by hash from round 25 (readers_anc.py); expand the keys audit reads."""
    state = root / 'work/follow.json'
    if not state.exists():
        return dict(seen={}, sources={})
    key = state.stat().st_mtime_ns
    if _STATES.get(str(state), (None,))[0] != key:
        raw = json.load(open(state))
        if any(isinstance(v, dict) and set(v) == {'$anc'} for v in raw.values()):
            import readers_anc
            cache = {}
            raw = {k: (readers_anc.expand(v, root / 'work/anc', cache) if k in ('seen', 'sources', 'jobs') else v) for k, v in raw.items()}
        _STATES[str(state)] = (key, raw)
    return _STATES[str(state)][1]


# Round 26 brief, sources that are out. Text markers and path patterns, checked over the whole trace and over the
# recorded source text of every held root it reaches (a bare file name such as 921-29e12ff3.csv escapes a path walk).
# Round 27 (stair-c copy): the Samanyu markers are out of this list (override 2).
FORBIDDEN_R26 = ('penguin069/squares-joegun-boxed-certified-union', 'prvsiyan/squares-verified-best-of-1105', 'CC BY-SA')
OUT_PATHS_R26 = (r'take-harvest-r22/(?:.*/)?(?:639|691|745|858|918)\b', r'take-(?:invent|midm)-r23/(?:.*/)?639\b',
                 r'take-forensics-r23/(?:.*/)?(?:980|639)\b', r'take-forensics-r(?:1\d|2[0-3])/(?:.*/)?918\b',
                 r'take-midm-r23/(?:.*/)?639')
GATHER_ROOTS = ('round23-2026-11-13a.csv', 'round23-2026-11-13b.csv', 'round24-2026-11-13a.csv', 'round25-2026-11-14b.csv')
_ROOT_TEXT = {}


def root_text(n):
    """The newest recorded source and licence of held n (round tables, newest first)."""
    if not _ROOT_TEXT:
        csv.field_size_limit(16 * 1024 * 1024)
        files = list((LANE / 'results').glob('round*-best-*.tsv'))
        files.sort(key=lambda q: int(re.search(r'round(\d+)-', q.name)[1]), reverse=True)
        files += sorted((LANE / 'results').glob('harvest-best-*.tsv'), reverse=True)
        for q in files:
            for r in csv.DictReader(open(q), delimiter='\t'):
                _ROOT_TEXT.setdefault(int(r['n']), (r.get('source') or '') + ' ' + (r.get('licence') or ''))
    return _ROOT_TEXT.get(n, '')


def r26_check(detail, source, licence):
    """None when clean, else the reason. Walks every dict of the trace."""
    roots, paths = set(), []
    def walk(v):
        if isinstance(v, dict):
            q = v.get('path')
            if isinstance(q, str):
                paths.append(q)
                if q.rsplit('/', 1)[-1] in GATHER_ROOTS and isinstance(v.get('n'), int):
                    roots.add(v['n'])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(detail)
    if False:
        return 'held 801 (prvsiyan, CC BY-SA) in ancestry'
    text = json.dumps(detail, default=str) + ' ' + source + ' ' + licence + ' ' + ' '.join(root_text(k) for k in sorted(roots))
    for m in FORBIDDEN_R26:
        if m in text:
            return 'round 26 excluded source marker ' + m
    for q in paths:
        for pat in OUT_PATHS_R26:
            if re.search(pat, q):
                return 'round 26 excluded path ' + q
    return None


def trace(path, n):
    out = _trace_r25(path, n)
    if out.get('ok'):
        why = r26_check(out.get('evidence'), out.get('source', ''), out.get('licence', ''))
        if why:
            out = dict(out, ok=False, reason=why)
    return out


def _trace_r25(path, n):
    _install()
    path = Path(path)
    try:
        if not path.is_file():
            return dict(ok=False, reason='missing input', path=str(path), n=n)
        if False:
            return dict(ok=False, reason='held n801 is excluded as a donor', path=str(path), n=n)
        source, licence, record = metadata(path, n)
        reason = refused_source(dict(source=source, licence=licence), str(S))
        if reason:
            return dict(ok=False, reason=reason, path=str(path), n=n)
        rnd = re.search(r'-r(\d+)(?:/|$)', str(path))
        rnd = int(rnd[1]) if rnd else 26
        # The version-aware reader traces through its saved parent state.
        if 'take-readers-' in str(path) and 'from' in path.name:
            root = next(p for p in path.parents if p.name.startswith('take-readers-'))
            data = reader_state(root)
            ok, detail = readers_sources.audit((path, n, rnd, True, source, licence), S, data)
        else:
            ok, detail = forensics_sources.trace(path, n, S)
        if not ok and not ('take-readers-' in str(path) and 'from' in path.name):
            inline = inline_record(detail, source, licence, record, rnd)
            if inline is not None:
                ok, detail = True, inline
        withdrawn = []
        def withdrawn_paths(value):
            # Round 25 rule (d): the border 735 tree (735, 790, 228) and the k123 735/790 join (968, its 489 child).
            if isinstance(value, dict):
                q = value.get('path')
                if isinstance(q, str) and (re.search(r'take-border-r2[34]/(?:.*/)?(?:735|790|228)\b', q) or
                                           re.search(r'take-k123-r2[34]/.*(?:735r-790|790-968|/968[-.]|/489[-.])', q)):
                    withdrawn.append(q)
                for v in value.values():
                    withdrawn_paths(v)
            elif isinstance(value, list):
                for v in value:
                    withdrawn_paths(v)
        # Round 27 (stair-c copy): the 735 tree was withdrawn for the Samanyu seed 365 only.
        withdrawn = []
        if False:
            return dict(ok=False, path=str(path), n=n, source=source, licence=licence, record=record,
                        evidence=dict(reason='withdrawn 735 tree'), reason='withdrawn 735 tree: ' + (withdrawn[0] if withdrawn else 'source text'))
        def excluded_held(value):
            if isinstance(value, dict):
                if value.get('n') == 801 and value.get('path') == str(CANDIDATE):
                    return True
                return any(excluded_held(v) for v in value.values())
            if isinstance(value, list):
                return any(excluded_held(v) for v in value)
            return False
        if False:
            ok = False
            detail['reason'] = 'excluded held n801 in ancestry'
        return dict(ok=bool(ok), path=str(path), n=n, source=source, licence=licence,
                    record=record, evidence=detail, reason=detail.get('reason', 'ancestry trace'))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as ex:
        return dict(ok=False, reason=str(ex), path=str(path), n=n)
