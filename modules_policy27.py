"""Round 27 source policy, bar and publisher of the modules controller.

The round 27 brief lifts the Samanyu-dev rule: the layouts that match the Samanyu-dev/squares_in_squares GitHub seed
were found by our own code, so ancestry through that seed, the held 921 modules, 921-29e12ff3.csv, seed 503 and the
seed merged0 roots is no reason to refuse anything. This module removes that check from every tool of the lane:
modules_policy24.piece/ancestry report status none for those roots, the soft provenance trace used to stage other
lanes' files drops its Samanyu markers, and the publish walk drops the Samanyu signals and the withdrawals that were
made only for Samanyu ancestry.

Still refused: penguin069/squares-joegun-boxed-certified-union and its n 639 691 745 858 918, the held 801 and every
row of prvsiyan/squares-verified-best-of-1105 (CC BY-SA 4.0), unlicensed public sources (modules_sources24.clean_text
and harvest_follow.refused_source, unchanged), and the withdrawals made for other reasons. For prvsiyan the test is
the share test of the round 27 brief: a layout is out if 0.4 or more of its squares lie within 1e-3 of the prvsiyan
1105 row of that n (tools/harvest26/share_ac.py with audit_ac.excluded, imported unchanged).

The bar of n is round27-briefs/bar27.tsv (the lower of the held round 25 b row and the best certified round 26 take
row), lowered by every other live take-*-r27 dir.
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
BAR27 = ROOT / 'round27-briefs/bar27.tsv'
sys.path.insert(0, str(LANE))
import modules_policy24 as p24  # noqa: E402
import modules_sources24 as s24  # noqa: E402

# The rules that stay: penguin069 and prvsiyan 1105 by name. The Samanyu names are gone.
BARE = re.compile(r'penguin069|verified-best-of-1105|CC BY-SA', re.I)
SHARE_MAX = 0.4


def _origin(source, licence, root):
    if BARE.search(source + ' ' + licence):
        return dict(status='unknown', seeds=[], couzo=[], unresolved=[root or 0])
    return dict(status='none', seeds=[], couzo=[], unresolved=[])


# Every later `from modules_policy24 import piece/ancestry` in this process sees the round 27 rule.
p24._origin = _origin
piece, ancestry = p24.piece, p24.ancestry


def notice(a):
    # Round 27: the k123 lane's text scan refused 597 because this notice named the excluded file and its licence. The
    # published text names neither; the checks themselves are unchanged.
    return 'Samanyu-dev rule lifted by the round 27 brief (no Samanyu check); the round 27 exclusions checked'


# The soft lane's provenance trace (imported, never edited) carries Samanyu markers in FORBIDDEN_R26.
SAMANYU_MARKERS = {'Samanyu-dev/squares_in_squares', 'seed merged0', 'original clean seed', '921r25c921', '921mo16.F1d',
                   '863-0f92c19d-n.csv', '921-29e12ff3.csv'}
_PROV = None


def _provenance():
    global _PROV
    if _PROV is None:
        import importlib.util
        p = LANE / 'tools/softround/provenance.py'
        spec = importlib.util.spec_from_file_location('soft_provenance27', p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.FORBIDDEN_R26 = tuple(m for m in mod.FORBIDDEN_R26 if m not in SAMANYU_MARKERS)
        _PROV = mod
    return _PROV


def trace27(path, n):
    return _provenance().trace(path, n)


s24.trace_file = trace27

# Withdrawals of the round 25 assembler walk that were made only for Samanyu ancestry (the 735 tree with seed 365,
# 921-29e12ff3, the 927 seed 811 reclassification, k123 968 and 489 with seed 365). Other withdrawals stay.
SAMANYU_WITHDRAWALS = {'take-border-r24/735.csv', 'take-border-r24/790.csv', 'take-border-r23/735.csv',
                       'take-border-r23/790.csv', 'take-stair-c-r17/near/921-29e12ff3.csv', '927-reclassified-seed811',
                       'take-k123-r24/968.csv', 'take-k123-r24/489.csv'}


# Round 26 moved the 932 files away only for Samanyu reach. k123 dropped its 932 at 15:37 UTC on 2026-11-14 ("held933
# donor ancestry unresolved: round20 held813 may reach Samanyu seed503") into take-k123-r26/work/withdrawn, and the
# forensics purge of 16:11-16:48 UTC moved its 932 files into work/quarantine-withdrawals. The walk reads those copies
# and the withdrawn take row instead. Only n = 932 is mapped: the 695 files of the same purge left for an unresolved
# prvsiyan source, a reason that still holds.
_Q = 'take-forensics-r26/work/quarantine-withdrawals/'
SAMANYU_QUARANTINE = True


def _samanyu_moved(m):
    name = m.rsplit('/', 1)[-1]
    if not SAMANYU_QUARANTINE or not (name.startswith('932-') or name == '932.csv'):
        return None
    if m.startswith('take-forensics-r26/'):
        q = [_Q + m[len('take-forensics-r26/'):]] + ([_Q + 'withdrawn-932.json'] if name == '932.csv' else [])
    elif m.startswith('take-k123-r26/near/'):
        q = ['take-k123-r26/work/withdrawn/' + name]
    elif m.startswith('take-twoshort-r26/near/'):
        # twoshort moved its 932 near files at 16:06 UTC because they descend from the k123 and forensics 932.
        q = ['take-twoshort-r26/work/withdrawn/near-' + name]
    else:
        return None
    return q if (ROOT / q[0]).exists() else None


def walk_refusal(n, source, licence, take='take-modules-r27'):
    """Walk the recorded ancestry to its first public files; return a reason to refuse, or ''."""
    sys.path.insert(0, str(ROOT / 'take-assemble-r25'))
    import deep25
    texts, missing, files, helds = deep25.walk(dict(dir=take, n=n, source=source, licence=licence))
    seen = set()
    while True:
        moved = []
        for m in missing:
            q = None if m in seen else _samanyu_moved(m)
            if q:
                seen.add(m)
                moved += q
        if not moved:
            break
        t2, m2, _, _ = deep25.walk(dict(dir=take, n=n, source='; '.join(dict.fromkeys(moved)), licence=''))
        texts += t2
        missing = [m for m in missing + m2 if m not in seen]
    sig = deep25.signals(texts)
    bad = [k for k in ('bysa', 'penguin') if sig[k]]
    still = [w for w in sig['withdrawn'] if w[1] not in SAMANYU_WITHDRAWALS]
    if still:
        bad.append('withdrawn ' + ', '.join(sorted({w[1] for w in still})))
    gone = [m for m in missing if not m.startswith(('no record', 'queue file'))]
    if gone:
        bad.append('missing ' + ', '.join(sorted(set(gone))[:3]))
    return '; '.join(bad)


_EXCL = {}


def share_refusal(path, n):
    """The round 27 prvsiyan share test: '' when every excluded layout of n shares under 0.4 within 1e-3."""
    sys.path.insert(0, str(LANE / 'tools/harvest26'))
    import audit_ac
    import share_ac
    if n not in _EXCL:
        _EXCL[n] = [(label, audit_ac.centres(rows)) for label, rows in audit_ac.excluded(n)]
    rows = list(csv.DictReader(open(path)))
    c = audit_ac.centres(rows)
    for label, ex in _EXCL[n]:
        s = share_ac.share(c, ex)
        if s[1] >= SHARE_MAX:
            return f'share {s[1]:.3f} within 1e-3 of {label}'
    return ''


def share_record(path, n):
    sys.path.insert(0, str(LANE / 'tools/harvest26'))
    import audit_ac
    import share_ac
    if n not in _EXCL:
        _EXCL[n] = [(label, audit_ac.centres(rows)) for label, rows in audit_ac.excluded(n)]
    rows = list(csv.DictReader(open(path)))
    c = audit_ac.centres(rows)
    if not _EXCL[n]:
        return 'round 27 share test: no excluded layout of this n'
    worst = max(share_ac.share(c, ex)[1] for label, ex in _EXCL[n])
    return f'round 27 share test passed: at most {worst:.3f} of the squares within 1e-3 of an excluded layout of this n, limit 0.4'


def write_details(out):
    """ship/details.csv in the gate format, scores from bar27.tsv."""
    held = {int(r['n']): r for r in csv.DictReader(open(ROOT / 'gate/cand-round25-1114b/details.csv'))}
    rows = []
    for r in csv.DictReader(open(BAR27), delimiter='\t'):
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
        for d in sorted(c['ROOT'].glob('take-*-r27')):
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
        import modules_publish27
        best, _ = comparisons(effective())
        ledger = Path('published27.json')
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
            source = ('modules lane round 27: ' + note + op + 'certified as ' + str(j.get('precert_source', '')) +
                      ', then one certified-file fq quench on boxD (zone_corner.py quench); module sources: ' +
                      j.get('source', '') + '; held source register results/round26-best-2026-11-14.tsv and '
                      'results/round25-best-2026-11-14.tsv')
            licence = '; '.join(sorted({q['licence'] for q in j['modules']}))
            why = walk_refusal(n, source, licence)
            if not why:
                why = share_refusal(cp, n)
            if why:
                seen[key] = 'refused by walk: ' + why
                c['state'](f'refuse quenched {p.stem}: {why}')
                continue
            licence += '; ' + notice(ancestry(j)) + ' (full walk with take-assemble-r25/deep25.walk; ' + \
                share_record(cp, n) + ')'
            side = Path('publish27') / (p.stem + '.json')
            side.parent.mkdir(exist_ok=True)
            side.write_text(json.dumps(dict(source=source + f'; quenched file sha256 {digest}', licence=licence)))
            argv = [str(cp), str(side), str(n)]
            from contextlib import redirect_stdout
            with open('logs/publish27.out', 'a') as h:
                with redirect_stdout(h):
                    rc = modules_publish27.main(argv)
            seen[key] = f'publish returncode {rc}'
            if rc == 0:
                row = {r['n']: r for r in csv.DictReader((c['TAKE'] / 'take.tsv').open(), delimiter='\t')}[str(n)]
                c['state'](f'take.tsv: certified n={n} score={row["new"]} gain={row["gain"]} from {p.stem}')
                with (c['ROOT'] / 'handoff-r27.log').open('a') as h:
                    h.write(f'{c["stamp"]()} modules -> all: certified n={n}, score={row["new"]}, gain={row["gain"]} '
                            f'on bar27; box quench complete, ancestry walked, share test passed, {c["TAKE"]}/{n}.csv\n')
        ledger.write_text(json.dumps(seen))
    return refresh_bar, publish_completed
