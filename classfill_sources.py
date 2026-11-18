#!/usr/bin/env python3
"""Trace recorded classfill source notices without approving a layout.

Read trusted lane metadata as data. Follow both sidecar names and relative
near paths. Report excluded roots and unresolved CSV references. A publication
still needs a complete source review and the numerical gate.
"""
import csv, hashlib, json, re
from functools import lru_cache
from pathlib import Path
csv.field_size_limit(50000000)
S = Path('$SCRATCH/bounties-squares')
R = Path(__file__).resolve().parent
BAD = re.compile('no licen[cs]e|joegun-boxed|joegun excluded donor|verified-best-of-1105|CC BY-SA|CC-BY-SA|Other \\(specified', re.I)
ROOTS = {r['n']: r for r in csv.DictReader(open(R / 'results/round23-best-2026-11-13.tsv'), delimiter='\t')}


def source_text(text):
    """Keep source declarations separate from the parents they describe."""
    # Round 27 permits the independently discovered seed with identical coordinates.
    text = re.sub(r'Samanyu(?:-dev)?(?:/squares_in_squares)?(?: \(GitHub\))?[^;\n]{0,50}?(?:no licen[cs]e|unlicensed)(?: stated upstream)?',
                  'own-discovered seed (round 27)', text, flags=re.I)
    text = re.sub(r'Samanyu(?:-dev)?(?: seed)? ancestry:\s*(?:none|no)\b(?:\s*\([^)]*\))?',
                  '', text, flags=re.I)
    return re.sub(r'(?:recorded ancestry has )?no Samanyu-dev seed layout',
                  '', text, flags=re.I)


@lru_cache(maxsize=None)
def merged_seed_source(n):
    """Resolve an explicit merged0 reference from the original score ledgers."""
    merged_path = S / 'seeds/merged0.tsv'
    couzo_path = S / 'seeds/couzo.tsv'
    if not merged_path.exists() or not couzo_path.exists():
        return 'unresolved original merged0 seed ' + str(n)
    merged = {int(r['n']): r for r in csv.DictReader(merged_path.open(), delimiter='\t')}
    couzo = {int(r['n']): r for r in csv.DictReader(couzo_path.open(), delimiter='\t')}
    if n in couzo and couzo[n]['reason'] == 'ok' and abs(float(couzo[n]['score']) - float(merged[n]['score'])) < 1e-15:
        return 'franciscouzo/square-packing (GitHub), MIT, seed ' + str(n)
    return 'Samanyu-dev/squares_in_squares (GitHub), no licence, seed ' + str(n)


def archived_sidecar(path):
    """Use archived metadata only when its CSV exactly matches the near copy."""
    root = next((q for q in path.parents if re.match(r'take-.*-r\d+$', q.name)), None)
    if root is None:
        return None
    digest = hashlib.sha256(path.read_bytes()).digest()
    for sub in ['raw-a', 'raw-n', 'raw-s', 'archive/n/raw-a', 'archive/s/raw-a', 'archive/a/raw-a']:
        candidate = root / 'work' / sub / (path.stem + '.json')
        raw = candidate.with_suffix('.csv')
        if candidate.exists() and raw.exists() and hashlib.sha256(raw.read_bytes()).digest() == digest:
            return candidate
    return None


def ledger_parent(path):
    """Resolve a shell walk by its exact parent ID, preserving the donor count."""
    root = next((q for q in path.parents if re.match(r'take-.*-r\d+$', q.name)), None)
    match = re.search(r'from(.+)\.csv$', path.name)
    if root is None or match is None:
        return None
    donor = match[1]
    number = re.match(r'\d+', donor)
    if number is None:
        return None
    for name in ['work/sources-all.tsv', 'work/sources.tsv']:
        ledger = root / name
        if not ledger.exists():
            continue
        with ledger.open() as handle:
            for row in csv.DictReader(handle, delimiter='\t'):
                if row.get('donor') == donor:
                    return ledger, dict(n=int(number[0]), donor=donor,
                                        source=row.get('source', ''),
                                        licence=row.get('licence', ''))
    return None


def expand(source, licence, metadata, n):
    seen = set()
    records = []
    texts = []
    todo = [(source, n), (licence, n)]
    missing = []

    def notices(value, context):
        if isinstance(value, str):
            todo.append((value, context))
        elif isinstance(value, list):
            for child in value:
                notices(child, context)
        elif isinstance(value, dict):
            try:
                context = int(value.get('n', context))
            except (ValueError, TypeError):
                pass
            parent = value.get('source')
            if isinstance(parent, list) and len(parent) == 2:
                try:
                    context = int(parent[1])
                except (ValueError, TypeError):
                    pass
            for key, child in value.items():
                if key in ['producer_take_tsv', 'what_was_measured', 'next',
                           'final_competing_takes', 'blocked_examples', 'excluded_roots']:
                    continue
                child_context = int(key) if str(key).isdigit() and 1 <= int(key) <= 1000 else context
                notices(child, child_context)

    notices(metadata, n)
    while todo and len(records) < 300:
        text, context = todo.pop()
        if not isinstance(text, str):
            continue
        # A rectangle's two parents have their own counts. Do not search the
        # escaped aggregate text with the count of its resulting layout.
        match = re.search(r'(?:rectangle windows |rectangle windows: )(?=\{)', text)
        if match:
            try:
                obj, length = json.JSONDecoder().raw_decode(text[match.end():])
                if isinstance(obj, dict) and all(k in obj for k in ['A', 'B']):
                    notices(obj, context)
                    text = text[:match.end()] + '[structured parents]' + text[match.end() + length:]
            except (ValueError, TypeError):
                pass
        texts.append(text)
        for rel in re.findall(r'(take-[A-Za-z0-9-]+-r\d+/(?:near|work)/[^\s<>";,()]+\.csv(?:\.json)?)', text):
            text += ' ' + str(S / rel)
        relatives = re.findall(r'(take-[A-Za-z0-9-]+-r\d+)\s+(?:n=\d+:\s*)?(near/[^\s<>,;()]+\.csv(?:\.json)?)', text)
        for lane, tail in relatives:
            text += ' ' + str(S / lane / tail)
        for seed in re.findall(r'(\d+)h(?:\d+)?\.[A-Za-z0-9~]+\s*<held: seed merged0>', text):
            texts.append(merged_seed_source(int(seed)))
        if re.search(r'take-harvest-r22\s+n\s*=\s*(?:639|691|745|858|918)\b', text):
            texts.append('joegun excluded donor')
        if re.search(r'held n\s*=\s*801\b', text):
            texts.append('verified-best-of-1105 excluded donor')
        dirs = [Path(x.rstrip('.:')) for x in re.findall(r'$DATA/[^\s<>";,()]+', text)]
        for name in re.findall(r'(?<![/\w-])(\d{2,4}-[A-Za-z0-9_.-]+\.csv)', text):
            for directory in dirs:
                if directory.is_dir() and (directory / name).exists():
                    text += ' ' + str(directory / name)
        for match in re.finditer(r'$DATA/[^\s<>";,()]+', text):
            p = Path(match.group().rstrip('.:'))
            key = (str(p), context)
            if key in seen:
                continue
            seen.add(key)
            if not p.exists():
                continue
            if p.name == 'round23-2026-11-13a.csv' and str(context) in ROOTS:
                row = ROOTS[str(context)]
                notices(row, context)
                records.append(dict(path=str(p), n=context, row=row))
            elif p.suffix == '.csv':
                if re.search(r'take-harvest-r22/(?:639|691|745|858|918)\.csv', str(p)) or re.search(r'take-(?:invent|midm)-r23/639\.csv|take-forensics-r23/980\.csv|take-forensics-r22/918\.csv', str(p)):
                    texts.append('joegun excluded donor ' + str(p))
                side = next((q for q in [p.with_suffix('.json'), Path(str(p) + '.json'), Path(str(p) + '.origin.json')] if q.exists()), None)
                if side is None:
                    side = archived_sidecar(p)
                if side:
                    todo.append((str(side), context))
                    continue
                parent = ledger_parent(p)
                if parent:
                    ledger, row = parent
                    notices(row, row['n'])
                    records.append(dict(path=str(ledger), metadata=row))
                    continue
                if p.parent.name.startswith('take-') and (p.parent / 'take.tsv').exists():
                    row = next((r for r in csv.DictReader((p.parent / 'take.tsv').open(), delimiter='\t') if r['n'] == p.stem), None)
                    if row:
                        notices(row, int(row['n']))
                        records.append(dict(path=str(p.parent / 'take.tsv'), row=row))
                        continue
                missing.append(str(p))
            elif p.suffix == '.json' and p.stat().st_size < 2000000:
                try:
                    raw = p.read_text()
                    obj = json.loads(raw)
                except (OSError, ValueError):
                    continue
                selection = None
                # These files are indexes of layouts, not a list of parents.
                # Select the requested row before following any of its fields.
                if isinstance(obj, dict) and obj and all(str(k).isdigit() for k in obj):
                    if str(context) not in obj:
                        missing.append(str(p) + ' (missing row n=' + str(context) + ')')
                        continue
                    obj = obj[str(context)]
                    selection = context
                digest = hashlib.sha256(raw.encode()).hexdigest()
                records.append(dict(path=str(p), sha256=digest, selection_n=selection, metadata=obj))
                notices(obj, context)
    return dict(blocks=sorted({m.group() for t in texts for m in BAD.finditer(source_text(t))}),
                records=records, unresolved_csv=sorted(set(missing)), text='\n'.join(texts))

def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('proof', type=Path)
    ap.add_argument('--n', type=int, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    j = json.loads(a.proof.read_text())
    result = expand(j.get('source', ''), j.get('licence', ''), j.get('producer_metadata', j), a.n)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print('EXCLUDED_ROOTS', len(result['blocks']), 'RECORDS', len(result['records']), 'UNRESOLVED_CSV', len(result['unresolved_csv']))
    return 1 if result['blocks'] else 0
if __name__ == '__main__':
    raise SystemExit(main())
