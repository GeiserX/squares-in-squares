"""Round 30 source policy, bar and publisher of the modules controller.

Made from modules_policy29.py by take-modules-r30/work/setup30.py: bar30.tsv, take-*-r30, handoff-r30.log,
modules_publish30.py, held details gate/cand-round28-1115b, and trace30 (take rows of round 29 and 30 lanes).
Round 29 text follows.

Made from modules_policy28.py by take-modules-r29/work/setup29.py: bar29.tsv, take-*-r29, handoff-r29.log,
modules_publish29.py (finesafe certification). Round 28 text follows.

Made from modules_policy27.py. The Samanyu-dev rule stays lifted. Still refused: penguin069 and its n 639 691 745
858 918, every row of prvsiyan/squares-verified-best-of-1105 (CC BY-SA 4.0), unlicensed public
sources and the withdrawals made for other reasons.

Round 28 first added an ancestor share test and an original-seed share test to the publish walk. The main
session's rule change of 00:19Z on 2026-11-15 drops both: our own layouts are ours (the held 801 and every
Samanyu-seed layout, seeds 503 and 983 included, and everything built from them), and a share match with prvsiyan
1105 is never a reason to refuse our own layouts or their descendants. The functions stay (ancestor_share,
seed_share) for measurement only; walk_refusal calls neither unless MODULES_ANCESTOR_SHARE=1.

What the walk keeps: the round 27 checks (CC BY-SA and penguin069 text, the static withdrawals, missing files)
and the WITHDRAW lines of handoff-r26, -r27 and -r28. A walked file whose path, file name or sha256 prefix such a
line names is refused, except that a line resting on a share measurement only is void under the 00:19Z rule, and
a later REINSTATE, REOPEN or "withdrawal lifted" line naming the same file cancels it. The share of the published
layout is recorded in its licence cell, not used to refuse (MODULES_OWN_SHARE=1 restores the round 27 refusal).

The bar of n is round28-briefs/bar28.tsv, lowered by every other live take-*-r28 dir.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

csv.field_size_limit(2**30)
LANE = Path(__file__).resolve().parent
ROOT = Path('$SCRATCH/bounties-squares')
BAR28 = ROOT / 'round30-briefs/bar30.tsv'  # round 30 bar (name kept)
sys.path.insert(0, str(LANE))
import modules_policy27 as p27  # noqa: E402  (lifts the Samanyu rule in modules_policy24 and the soft trace)

piece, ancestry = p27.piece, p27.ancestry
SHARE_MAX = 0.4
ANCESTOR_MAX_BYTES = 12_000_000


def notice(a):
    return 'Samanyu-dev rule lifted (round 28 to 30 briefs, no Samanyu check); the round 30 exclusions checked'


# ---- the share test, with one read of each excluded source -------------------------------------------------------
_EXCL = {}
_PRV = None
_SEEDS = None
_SHARE_CACHE = {}


def _prvsiyan():
    global _PRV
    if _PRV is None:
        sys.path.insert(0, str(LANE / 'tools/harvest26'))
        import audit_ac
        z = ROOT / 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
        _PRV = audit_ac.read(str(z), list(range(1, 1001))) if z.exists() else {}
    return _PRV


def excluded(n):
    """The excluded layouts of n: audit_ac.excluded without its per-call read of the prvsiyan zip."""
    if n not in _EXCL:
        sys.path.insert(0, str(LANE / 'tools/harvest26'))
        import audit_ac
        out = []
        if n in (639, 691, 745, 858, 918) or n == 980:
            out = [(l, r) for l, r in audit_ac.excluded(n) if not l.startswith('prvsiyan')]
        rows = _prvsiyan().get(n, [])
        if len(rows) == n:
            out.append(('prvsiyan 1105 (CC BY-SA)', rows))
        _EXCL[n] = [(label, audit_ac.centres(r)) for label, r in out if len(r) == n]
    return _EXCL[n]


def share_of(rows, n):
    """(worst share within 1e-3, label) of these rows against the excluded layouts of n."""
    sys.path.insert(0, str(LANE / 'tools/harvest26'))
    import audit_ac
    import share_ac
    ex = excluded(n)
    if not ex or len(rows) != n:
        return 0.0, ''
    c = audit_ac.centres(rows)
    worst, where = 0.0, ''
    for label, e in ex:
        s = share_ac.share(c, e)[1]
        if s > worst:
            worst, where = s, label
    return worst, where


def share_refusal(path, n):
    """Under the 00:19Z rule our own module builds are never refused for a share match; the share is recorded in the
    licence cell (share_record). MODULES_OWN_SHARE=1 restores the round 27 refusal at 0.4."""
    if os.environ.get('MODULES_OWN_SHARE') != '1':
        return ''
    rows = list(csv.DictReader(open(path)))
    s, where = share_of(rows, n)
    return f'share {s:.3f} within 1e-3 of {where}' if s >= SHARE_MAX else ''


def share_record(path, n):
    rows = list(csv.DictReader(open(path)))
    if not excluded(n):
        return 'round 30 share test: no excluded layout of this n'
    s, _ = share_of(rows, n)
    return (f'round 30 share record: {s:.3f} of the squares within 1e-3 of an excluded layout of this n '
            '(own module build; the 00:19Z rule makes a share match no reason to refuse)')


def _rows_by_n(path):
    """Rows of a packing csv grouped by n; {} if the file is not a packing."""
    sys.path.insert(0, str(LANE / 'tools/harvest26'))
    import audit_ac
    out = {}
    try:
        with open(path) as f:
            for r in csv.DictReader(f):
                if 'id' in r and 'n' not in r:
                    try:
                        n = int(str(r['id']).split('_')[0])
                    except ValueError:
                        return {}
                    r = audit_ac.norm({'n': n, 'x': r.get('x'), 'y': r.get('y'), 'angle': r.get('deg', r.get('angle'))})
                else:
                    r = audit_ac.norm(r)
                if not r.get('n', '').isdigit():
                    return {}
                out.setdefault(int(r['n']), []).append(r)
    except (OSError, UnicodeDecodeError, csv.Error, KeyError, TypeError):
        return {}
    return {n: rows for n, rows in out.items() if len(rows) == n}


def ancestor_share(path, want=None):
    """Worst (share, n, label) over the complete per-n layouts of one ancestor csv, cached by content.

    A file with one complete n is tested at that n. A pool file with several n is tested only at the n in `want`
    (the n the walk texts that name it give), because a pool holds many layouts and only some are the ancestors:
    round 28 measured the k123 r24 pool defer00017.csv at share 1.0 for its n = 370 layout and 0.133 for the n = 812
    donor the 871 chain used."""
    p = Path(path)
    try:
        data = p.read_bytes()
    except OSError:
        return 0.0, 0, ''
    key = hashlib.sha256(data).hexdigest()
    if key not in _SHARE_CACHE:
        _SHARE_CACHE[key] = {}
        for n, rows in _rows_by_n(p).items():
            try:
                for r in rows:
                    float(r['x']), float(r['y']), float(r['angle'])
            except (ValueError, TypeError, KeyError):
                continue
            s, label = share_of(rows, n)
            _SHARE_CACHE[key][n] = (s, n, label)
    per = _SHARE_CACHE[key]
    if len(per) > 1:
        per = {n: v for n, v in per.items() if want and n in want}
    return max(per.values(), default=(0.0, 0, ''))


def seed_share(n):
    """Share of the original seed merged0 row of n (seeds/merged0.csv) against the excluded layouts of n."""
    global _SEEDS
    if _SEEDS is None:
        _SEEDS = _rows_by_n(ROOT / 'seeds/merged0.csv')
    rows = _SEEDS.get(n)
    if not rows:
        return 0.0, ''
    return share_of(rows, n)


# ---- withdrawal lines --------------------------------------------------------------------------------------------
_WD = None
WPATH = re.compile(r'(?:$SCRATCH/bounties-squares/)?((?:take-[a-z0-9-]+-r\d+|harvest[\w.-]*|gather)/[^\s"\'<>;,()\[\]{}|\\]*?\.csv)')
WHEX = re.compile(r'(?<![0-9a-f])([0-9a-f]{16,64})(?![0-9a-f])')


STILL_VALID = re.compile(r'unresolved|penguin|names? (?:the )?(?:prvsiyan|squares-verified-best-of-1105|CC BY-SA)'
                         r'|source notice|no per-n|trace|licen[cs]e|not reproducible|bad geometry|overlap', re.I)


def withdrawals():
    """[(line, rel paths, hex tokens)] of the WITHDRAW lines of the round 26 to 28 handoff logs that still hold.

    Void under the 00:19Z rule of 2026-11-15: a line whose reason is a share measurement and nothing else. Cancelled:
    a path or hex token that a later REINSTATE, REOPEN or "withdrawal lifted" line names."""
    global _WD
    if _WD is None:
        lines = []
        for log in ('handoff-r26.log', 'handoff-r27.log', 'handoff-r28.log', 'handoff-r29.log', 'handoff-r30.log'):
            p = ROOT / log
            if p.exists():
                lines += p.read_text(errors='replace').splitlines()
        lifted_paths, lifted_hex = set(), set()
        for line in lines:
            if re.search(r'REINSTATE|REOPEN|withdrawal lifted', line):
                lifted_paths |= {m.rstrip('.') for m in WPATH.findall(line)}
                lifted_hex |= set(WHEX.findall(line))
        _WD = []
        for line in lines:
            if 'WITHDRAW' not in line or re.search(r'REINSTATE|REOPEN|withdrawal lifted', line):
                continue
            if re.search(r'share', line, re.I) and not STILL_VALID.search(line):
                continue
            paths = {m.rstrip('.') for m in WPATH.findall(line)} - lifted_paths
            hexes = set(WHEX.findall(line)) - lifted_hex
            if paths or hexes:
                _WD.append((line[:240], paths, hexes))
    return _WD


def withdrawn_hit(files):
    """The first WITHDRAW line that names one of these walked files, by path, file name or sha256 prefix."""
    rels = {}
    for f in files:
        p = Path(f)
        if p.suffix != '.csv' or not p.exists():
            continue
        try:
            rel = str(p.relative_to(ROOT))
        except ValueError:
            rel = str(p)
        rels[rel] = p
    for line, paths, hexes in withdrawals():
        for rel, p in rels.items():
            if rel in paths:
                return f'{rel} named by: {line}'
            for h in hexes:
                if len(h) >= 16 and (h in p.name):
                    return f'{rel} (file name holds {h}) named by: {line}'
    digests = {}
    for rel, p in rels.items():
        try:
            if p.stat().st_size < ANCESTOR_MAX_BYTES:
                digests[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
    for line, paths, hexes in withdrawals():
        for rel, d in digests.items():
            for h in hexes:
                if len(h) >= 16 and d.startswith(h):
                    return f'{rel} (sha256 {h}) named by: {line}'
    return ''


# ---- the walk ----------------------------------------------------------------------------------------------------
NAMED_N = re.compile(r'"n"\s*:\s*(\d{1,4})\b')  # the n of a pinned donor record, as in {"n": 812, ...}
MERGED0_ID = re.compile(r'(?<![\w.])(\d{3,4})h[\w.~]*\s*<held: seed merged0>')
SEEDNUM = re.compile(r'(?:Samanyu(?:-dev)?(?: GitHub)? seed|original[- ]seed|seed)\s*(?:n\s*=\s*)?(\d{3})\b', re.I)


_MOVED = {}


def _moved_index(take):
    """name -> [rel paths] of the csv files with a sidecar under take/work/{withdraw,quarantine,reinstat,withheld}*,
    one and two levels down; built once per take dir."""
    if take not in _MOVED:
        index = {}
        base = ROOT / take / 'work'
        if base.is_dir():
            for d in base.iterdir():
                if not d.is_dir() or not d.name.startswith(('withdraw', 'quarantine', 'reinstat', 'withheld')):
                    continue
                for q in list(d.glob('*.csv')) + list(d.glob('*/*.csv')):
                    if any(Path(str(q) + x).exists() for x in ('.json', '.origin.json', '.source.json')):
                        key = q.name[5:] if q.name.startswith('near-') else q.name
                        index.setdefault(key, []).append(str(q.relative_to(ROOT)))
        _MOVED[take] = index
    return _MOVED[take]


def moved_copy(m):
    """Where a lane moved a withdrawn file inside its own take dir (work/withdrawn*, quarantine*, reinstated*).

    Round 28: the 00:19Z rule voids withdrawals that rested on a share measurement, but the frozen round 27 dirs keep
    the files where their lanes moved them (take-k123-r27/932.csv is now take-k123-r27/work/withdrawn-seed503/932.csv,
    with its sidecar). A copy is used only when it is a file of the same name with a sidecar record, and the walk
    then refuses the row anyway if a WITHDRAW line that still holds names the original path."""
    if ' ' in m:
        return None  # 'no record ...', 'queue file skipped ...': the file exists or is not a layout
    rel = m
    parts = rel.split('/')
    if len(parts) < 2 or not parts[0].startswith('take-') or not rel.endswith('.csv'):
        return None
    name = parts[-1]
    found = [rel2 for rel2 in _moved_index(parts[0]).get(name, ())]
    return sorted(set(found))[:2] or None


def walk_refusal(n, source, licence, take='take-modules-r30'):
    """The round 27 walk, then the WITHDRAW lines that still hold (ancestor and seed shares only on request)."""
    sys.path.insert(0, str(ROOT / 'take-assemble-r25'))
    import deep25
    texts, missing, files, helds = deep25.walk(dict(dir=take, n=n, source=source, licence=licence))
    seen = set()
    for _round in range(4):
        moved = []
        for m in missing:
            q = None if m in seen else (p27._samanyu_moved(m) or moved_copy(m))
            if q:
                seen.add(m)
                moved += q
        if not moved:
            break
        t2, m2, f2, _ = deep25.walk(dict(dir=take, n=n, source='; '.join(dict.fromkeys(moved)), licence=''))
        texts += t2
        files |= f2
        missing = [m for m in missing + m2 if m not in seen]
    sig = deep25.signals(texts)
    bad = [k for k in ('bysa', 'penguin') if sig[k]]
    still = [w for w in sig['withdrawn'] if w[1] not in p27.SAMANYU_WITHDRAWALS]
    if still:
        bad.append('withdrawn ' + ', '.join(sorted({w[1] for w in still})))
    # Round 28: a missing .tsv is a table a record names (forensics feed records name take.tsv files that their feed
    # dirs never held); deep25 reads tables through the files they describe, so only missing layouts and records
    # block. Measured on the 805 kick of 01:32Z: its two missing names were take-forensics-r26/work/feed/*/take.tsv.
    gone = [m for m in missing if not m.startswith(('no record', 'queue file')) and not m.endswith('.tsv')]
    # A file a held record names is held-chain, as in rebuild_walk27.py, which the assembler runs: it does not block.
    # Measured on the 748 of 02:57Z: its one missing name, take-forensics-r26/501.csv, came from a stair-c proof
    # that lists it as "held-chain take-forensics-r26/501.csv (named by ('held', 986, None))".
    alltext = '\n'.join(t[2] for t in texts)
    gone = [m for m in gone if not re.search(r'held(?:-chain)? ' + re.escape(m) + r' \(named by', alltext)]
    if gone:
        bad.append('missing ' + ', '.join(sorted(set(gone))[:3]))
    # 1. and 2. measurement only since the 00:19Z rule of 2026-11-15 (MODULES_ANCESTOR_SHARE=1 turns them on)
    if os.environ.get('MODULES_ANCESTOR_SHARE') == '1':
        bad += ancestor_checks(n, texts, files)
    # 3. the WITHDRAW lines, on the walked files and on the original paths of moved copies
    hit = withdrawn_hit(files)
    if not hit:
        for m in seen:
            rel = m.split(' ', 1)[-1] if m.startswith(('no record ', 'missing ')) else m
            line = next((w[0] for w in withdrawals() if rel in w[1]), '')
            if line:
                hit = f'{rel} (moved) named by: {line}'
                break
    if hit:
        bad.append('withdrawal line: ' + hit)
    return '; '.join(bad)


def ancestor_checks(n, texts, files):
    import deep25
    bad = []
    # 1. every complete per-n CSV ancestor (pool files at the n the texts that name them give)
    named = {}
    for _, nn, t, _ in texts:
        for rel in deep25.PATH.findall(t):
            if rel.endswith('.csv'):
                ns = named.setdefault(str(deep25.S / rel), {n, nn})
                ns.update(int(x) for x in NAMED_N.findall(t) if 1 <= int(x) <= 1000)
    for f in sorted(files):
        p = Path(f)
        if p.suffix != '.csv' or not p.exists() or '/gather/' in f:
            continue
        try:
            if p.stat().st_size > ANCESTOR_MAX_BYTES:
                continue
        except OSError:
            continue
        s, an, label = ancestor_share(p, named.get(f, {n}))
        if s >= SHARE_MAX:
            bad.append(f'ancestor {p} n={an} share {s:.3f} within 1e-3 of {label}')
            break
    # 2. every original seed the walk names: a module id of a held row marked seed merged0 (504h.F2 <held: seed
    # merged0> is seed 504), a held row whose own record is seed merged0, and explicit seed numbers.
    seeds = set()
    for label, nn, t, _ in texts:
        ids = [int(x) for x in MERGED0_ID.findall(t)]
        seeds.update(ids)
        if label.startswith('held ') and 'seed merged0' in t and not ids:
            seeds.add(nn)
        for m in SEEDNUM.finditer(deep25.NEG.sub(' ', t)):
            v = int(m.group(1))
            if 300 <= v <= 1000:
                seeds.add(v)
    for sn in sorted(seeds):
        s, label = seed_share(sn)
        if s >= SHARE_MAX:
            bad.append(f'original seed {sn} share {s:.3f} within 1e-3 of {label}')
            break
    return bad


def write_details(out):
    """ship/details.csv in the gate format, scores from bar28.tsv."""
    held = {int(r['n']): r for r in csv.DictReader(open(ROOT / 'gate/cand-round28-1115b/details.csv'))}
    rows = []
    for r in csv.DictReader(open(BAR28), delimiter='\t'):
        n = int(r['n'])
        s = float(r['bar'])
        rows.append(dict(n=n, L=repr((1 + s) * math.sqrt(n)), score=repr(s), min_gap=held[n].get('min_gap', '')))
    with open(str(out) + '.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, ['n', 'L', 'score', 'min_gap'])
        w.writeheader()
        w.writerows(rows)
    os.replace(str(out) + '.tmp', out)


def bind(c):
    def effective():
        return list(csv.DictReader(open('ship/details.csv')))

    def comparisons(rows):
        best = {int(r['n']): float(r['score']) for r in rows}
        for d in sorted(c['ROOT'].glob('take-*-r30')):
            if d == c['TAKE'] or not (d / 'take.tsv').exists():
                continue
            try:
                for r in csv.DictReader((d / 'take.tsv').open(), delimiter='\t'):
                    if r.get('n', '').isdigit() and r.get('new'):
                        n = int(r['n'])
                        best[n] = min(best[n], float(r['new']))
            except (OSError, ValueError, csv.Error):
                continue
        return best, []

    def refresh_bar():
        rows = effective()
        best, _ = comparisons(rows)
        with open('bar.csv.tmp', 'w', newline='') as h:
            w = csv.DictWriter(h, rows[0].keys())
            w.writeheader()
            for r in rows:
                n = int(r['n'])
                r.update(score=repr(best[n]), L=repr((1 + best[n]) * math.sqrt(n)))
                w.writerow(r)
        os.replace('bar.csv.tmp', 'bar.csv')
        c['rsync']('bar.csv', c['REMOTE'] + 'bar.csv')

    def publish_completed():
        sys.path.insert(0, str(c['LANE']))
        from modules_sources24 import normalize_record, clean_record
        import modules_publish30
        best, _ = comparisons(effective())
        ledger = Path('published30.json')
        seen = json.loads(ledger.read_text()) if ledger.exists() else {}
        for p in sorted(Path('boxD-qd').glob('*.done')):
            cp, jp = p.with_suffix('.csv'), p.with_suffix('.json')
            if not cp.exists() or not jp.exists():
                continue
            digest = hashlib.sha256(cp.read_bytes()).hexdigest()
            key = p.stem + ':' + digest[:16]
            if key in seen:
                continue
            j = normalize_record(json.loads(jp.read_text()))
            n = j['n']
            if not clean_record(j) or ancestry(j)['status'] != 'none':
                seen[key] = 'refused: source group'
                continue
            if not c['bounding_score'](cp, n) < best[n] - 5e-11:
                seen[key] = 'not below the bar'
                continue
            op = ''
            if j.get('kick_source'):
                op = ('invent_rest.py lkick, family squeeze and fq, 420 s' if j.get('kick_engine') == 'family'
                      else 'midm_scan lkick,kick sigma 0.02, 450 s') + ' on ' + j['kick_source'] + '; '
            note = (j['note'] + '; ') if j.get('note') else ''
            source = ('modules lane round 30: ' + note + op + 'certified as ' + str(j.get('precert_source', '')) +
                      ', then one certified-file fq quench on boxD (zone_corner.py quench); module sources: ' +
                      j.get('source', '') + '; held source register results/round26-best-2026-11-14.tsv and '
                      'results/round25-best-2026-11-14.tsv; results/round27-best-2026-11-15.tsv; results/round28-best-2026-11-15.tsv')
            licence = '; '.join(sorted({q['licence'] for q in j['modules']}))
            why = walk_refusal(n, source, licence)
            if not why:
                why = share_refusal(cp, n)
            if why:
                seen[key] = 'refused by walk: ' + why
                c['state'](f'refuse quenched {p.stem}: {why[:600]}')
                continue
            licence += '; ' + notice(ancestry(j)) + ' (full walk with take-assemble-r25/deep25.walk; ' + \
                share_record(cp, n) + ')'
            side = Path('publish30') / (p.stem + '.json')
            side.parent.mkdir(exist_ok=True)
            side.write_text(json.dumps(dict(source=source + f'; quenched file sha256 {digest}', licence=licence)))
            argv = [str(cp), str(side), str(n)]
            from contextlib import redirect_stdout
            with open('logs/publish30.out', 'a') as h:
                with redirect_stdout(h):
                    rc = modules_publish30.main(argv)
            seen[key] = f'publish returncode {rc}'
            if rc == 0:
                row = {r['n']: r for r in csv.DictReader((c['TAKE'] / 'take.tsv').open(), delimiter='\t')}[str(n)]
                c['state'](f'take.tsv: certified n={n} score={row["new"]} gain={row["gain"]} from {p.stem}')
                with (c['ROOT'] / 'handoff-r30.log').open('a') as h:
                    h.write(f'{c["stamp"]()} modules -> all: certified n={n}, score={row["new"]}, gain={row["gain"]} '
                            f'on bar30; finesafe certified, box quench complete, ancestry walked (deep25 walk, handoff-log checks, held-chain '
                            f'names as in rebuild_walk27), '
                            f'{c["TAKE"]}/{n}.csv\n')
        ledger.write_text(json.dumps(seen))
    return refresh_bar, publish_completed


# ---- round 29: take rows of other live and round 28 lanes as cut inputs ---------------------------------------------
# Measured at 07:55Z: the soft lane's provenance trace refused every r29 take row of harvest (public notebooks under
# Apache 2.0, harvest 848 gains 4.9e-4) and invent's 907 (its pinned source format), so modules_near29 staged none of
# them and no corner of these fresh deep layouts reached the generator. The round 29 rule: a public-first row is out
# only when its licence is not Apache 2.0, CC BY 4.0 or CC0, or when 0.4 or more of its squares lie within 1e-3 of
# the prvsiyan 1105 row of its n; our own layouts are ours. So a take row that the trace refuses is accepted here
# when its source and licence text carry no excluded marker, and, if its first source is public, when its licence
# is one of the three and its share is under 0.4. Everything else the trace refused stays refused.
import modules_sources24 as _s24  # noqa: E402

_TRACE0 = _s24.trace_file
EXCL_TEXT = re.compile(r'prvsiyan|verified-best-of-1105|penguin069|joegun|CC BY-SA|ShareAlike|withdr', re.I)
OK_LICENCE = re.compile(r'Apache[ -]2\.0|CC BY 4\.0|CC0', re.I)


def take_row_text(path, n):
    p = Path(path)
    t = p.parent / 'take.tsv'
    if not t.exists():
        return None
    for r in csv.DictReader(t.open(), delimiter='\t'):
        if r.get('n', '').strip() == str(n):
            return r.get('source', '') or '', r.get('licence', '') or '', str(t)
    return None


def trace29(path, n):
    out = _TRACE0(path, n)
    if out.get('ok'):
        return out
    p = Path(path)
    m = re.fullmatch(r'take-([a-z0-9-]+)-r(29|30)', p.parent.name)
    if not m or p.parent.name == 'take-modules-r30' or p.stem != str(n):
        return out
    row = take_row_text(p, n)
    if not row:
        return out
    source, licence, record = row
    text = source + ' ' + licence
    if not _s24.clean_text(text) or EXCL_TEXT.search(text):
        return out
    public = bool(re.match(r'\s*"?public\b', source, re.I))
    if public:
        if not OK_LICENCE.search(licence):
            return out
        rows = list(csv.DictReader(p.open()))
        s, _ = share_of(rows, n)
        if s >= SHARE_MAX:
            return out
        why = f'round 30 public-first take row, licence {OK_LICENCE.search(licence)[0]}, share {s:.3f} under {SHARE_MAX}'
    else:
        why = 'round 30 take row of a lane chain of our own (the trace could not read its records)'
    return dict(ok=True, reason=why, source=source, licence=licence, record=record, path=str(p), n=n,
                evidence=dict(trace_refusal=out.get('reason', ''), accepted=why))


_s24.trace_file = trace29
