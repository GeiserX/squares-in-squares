"""Round 26 base bar and publisher of the modules controller.

The bar is the round 25 b gate (gate/cand-round25-1114b/details.csv) lowered by every other live round 26 take.
A completed box quench enters the take only after a full ancestry walk: the round 25 assembler's deep25.walk
(imported unchanged) follows every file and held donor the record names, and the row is refused on any positive
Samanyu-dev signal, unresolved seed merged0 label, withdrawn file, CC BY-SA or penguin069 upstream, or a bare name
of the excluded trees (921-29e12ff3, the 747r joins, seeds 365, 804 and 983). The take row is written by
modules_publish26.py, which certifies again and never overwrites a lower row.
Module choices also refuse the bare names before a build.
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
import modules_policy24 as p24  # noqa: E402

BARE = re.compile(r'29e12ff3|take-stair-c-r17/near/921|747r|seeds? (?:n\s*=\s*)?(?:365|804|983)\b'
                  r'|Samanyu-dev/squares_in_squares|samanyu_bestfit|penguin069|verified-best-of-1105|CC BY-SA', re.I)
_origin24 = p24._origin


def _origin(source, licence, root):
    out = _origin24(source, licence, root)
    if out['status'] == 'none' and BARE.search(source + ' ' + licence):
        out = dict(out, status='unknown', unresolved=sorted(set(out['unresolved']) | {root or 0}))
    return out


# Every later `from modules_policy24 import piece/ancestry` sees the stricter rule.
p24._origin = _origin
piece, ancestry, notice = p24.piece, p24.ancestry, p24.notice


def walk_refusal(n, source, licence):
    """Walk the recorded ancestry to its first public files; return a reason to refuse, or ''."""
    sys.path.insert(0, '$SCRATCH/bounties-squares/take-assemble-r25')
    import deep25
    texts, missing, files, helds = deep25.walk(dict(dir='take-modules-r26', n=n, source=source, licence=licence))
    sig = deep25.signals(texts)
    bad = [k for k in ('pos', 'merged0', 'withdrawn', 'bysa', 'penguin') if sig[k]]
    for label, _, t, _ in texts:
        clean = deep25.NEG.sub(' ', t).replace('samanyu_ancestry', ' ')
        m = BARE.search(clean)
        if m:
            bad.append(f'bare name {m.group(0)} in {label[:80]}')
            break
    gone = [m for m in missing if not m.startswith(('no record', 'queue file'))]
    if gone:
        bad.append('missing ' + ', '.join(sorted(set(gone))[:3]))
    return '; '.join(bad)


def bind(c):
    def effective():
        return list(csv.DictReader(open('ship/details.csv')))

    def comparisons(rows):
        best = {int(r['n']): float(r['score']) for r in rows}
        for d in sorted(c['ROOT'].glob('take-*-r26')):
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
        import modules_publish26
        best, _ = comparisons(effective())
        ledger = Path('published26.json')
        seen = json.loads(ledger.read_text()) if ledger.exists() else {}
        for p in sorted(Path('boxD-qd').glob('*.done')):
            cp, jp = p.with_suffix('.csv'), p.with_suffix('.json')
            if not cp.exists() or not jp.exists():
                continue
            key = p.stem + ':' + hashlib.sha256(cp.read_bytes()).hexdigest()[:16]
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
            source = ('modules lane round 26: ' + note + op + 'certified as ' + str(j.get('precert_source', '')) +
                      ', then one certified-file fq quench on boxD (zone_corner.py quench); module sources: ' +
                      j.get('source', '') + '; held source register results/round25-best-2026-11-14.tsv')
            licence = '; '.join(sorted({q['licence'] for q in j['modules']}))
            why = walk_refusal(n, source, licence)
            if why:
                seen[key] = 'refused by walk: ' + why
                c['state'](f'refuse quenched {p.stem}: {why}')
                continue
            licence += '; ' + notice(ancestry(j)) + ' (full walk with take-assemble-r25/deep25.walk)'
            side = Path('publish26') / (p.stem + '.json')
            side.parent.mkdir(exist_ok=True)
            side.write_text(json.dumps(dict(source=source, licence=licence)))
            argv = [str(cp), str(side), str(n)]
            from contextlib import redirect_stdout
            with open('logs/publish26.out', 'a') as h:
                with redirect_stdout(h):
                    rc = modules_publish26.main(argv)
            seen[key] = f'publish returncode {rc}'
            if rc == 0:
                row = {r['n']: r for r in csv.DictReader((c['TAKE'] / 'take.tsv').open(), delimiter='\t')}[str(n)]
                c['state'](f'take.tsv: certified n={n} score={row["new"]} gain={row["gain"]} from {p.stem}')
                with (c['ROOT'] / 'handoff-r26.log').open('a') as h:
                    h.write(f'{c["stamp"]()} modules -> all: certified n={n}, score={row["new"]}, gain={row["gain"]} '
                            f'on round25b; box quench complete, ancestry walked, {c["TAKE"]}/{n}.csv\n')
        ledger.write_text(json.dumps(seen))
    return refresh_bar, publish_completed
