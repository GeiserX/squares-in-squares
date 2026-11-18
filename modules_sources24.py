"""Refuse excluded or unresolved ancestry before using module geometry."""
import json
import csv
csv.field_size_limit(2**30)
import re
from pathlib import Path

# Old files can contain rejected geometry under the same n as a clean candidate.
# Conservatively exclude those old module families and every named descendant.
EXCLUDED = {639, 691, 745, 801, 858, 918, 980, 981}
BAD = re.compile(r'(?<!\d)(?:639|691|745|801|858|918|980|981)(?!\d)')


def clean_text(text):
    return not (BAD.search(text) or any(s in text for s in (
        'squares-joegun-boxed-certified-union', 'squares-verified-best-of-1105',
        'CC BY-SA')) or ('sis-certified-union-micro-shrink' in text and not ('per_n.csv' in text and ('Upstream per-n records:' in text or 'malyshevdanil/squares-in-squares-living-atlas-of-tight-packings' in text))))


def clean_module(q):
    if q.get('clean_candidate'):
        return True
    return q.get('n') not in EXCLUDED and clean_text(q.get('src', '') + ' ' + q.get('licence', ''))


def clean_record(j):
    parts = j.get('modules', [])
    return bool(parts) and all(clean_text(str(q)) for q in parts)


def trace_file(path, n):
    # Import the other lane's reader without changing it.
    import importlib.util
    p = Path('tools/softround/provenance.py')
    spec = importlib.util.spec_from_file_location('soft_provenance', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.trace(path, n)
    return result


def stage_take(directory, out):
    import csv
    import shutil
    table = directory / 'take.tsv'
    if not table.exists():
        return None
    dest = out / directory.name
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in csv.DictReader(table.open(), delimiter='\t'):
        if not r.get('n', '').isdigit():
            continue
        n = int(r['n'])
        path = directory / f'{n}.csv'
        if not path.exists() or not clean_text(r.get('source', '') + ' ' + r.get('licence', '')):
            continue
        proof = trace_file(path, n)
        if not proof['ok']:
            continue
        shutil.copy2(path, dest / path.name)
        rows.append(dict(n=n, source=f'{path}: {r.get("source", "")}', licence=r.get('licence', '')))
    with (dest / 'take.tsv').open('w', newline='') as h:
        w = csv.DictWriter(h, ['n', 'source', 'licence'], delimiter='\t')
        w.writeheader()
        w.writerows(rows)
    return dest


def filter_library(path):
    import pickle
    import os
    lp = path / 'library.pkl'
    lib = pickle.load(lp.open('rb'))
    lib['mods'] = [q for q in lib['mods'] if clean_module(q)]
    ids = {q['id'] for q in lib['mods']}
    lib['layouts'] = [q for q in lib['layouts'] if all(i in ids for i in q['ids'])]
    with lp.with_suffix('.tmp').open('wb') as h:
        pickle.dump(lib, h)
    os.replace(lp.with_suffix('.tmp'), lp)


def normalize_record(j):
    """Expand the archived public donor hidden by the old 911 join label."""
    import csv
    register = Path('results/round22-best-2026-11-13.tsv')
    for q in j.get('modules', []):
        if ('911k122.' in q.get('id', '') or 'take-polish-r22/538.csv' in q.get('source', '')):
            row = next(r for r in csv.DictReader(register.open(), delimiter='\t') if r['n'] == '911')
            if 'Upstream per-n records:' not in q['source']:
                q['source'] += '; recorded 911 join ancestry in results/round22-best-2026-11-13.tsv: ' + row['source']
                q['licence'] += '; ' + row['licence']
    return j
