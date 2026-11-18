"""Check recorded public origins without comparing owned descendants."""
import csv
from functools import lru_cache
import hashlib
import io
import json
from pathlib import Path
import re
import sys

TOOLS = Path(__file__).resolve().parent/'tools/harvest29'


@lru_cache(maxsize=1)
def reader():
    sys.path.insert(0, str(TOOLS))
    import walk
    import public_sources
    return public_sources


@lru_cache(maxsize=256)
def document(path, modified, size):
    return json.loads(Path(path).read_text())


def load(path):
    p = Path(path)
    st = p.stat()
    return document(str(p), st.st_mtime_ns, st.st_size)


@lru_cache(maxsize=128)
def selected_rows(path, modified, size, n):
    with open(path) as stream:
        return [r for r in csv.DictReader(stream) if int(r['n']) == n]


def audit(proof, references, work, notices, gather=None, matrix=None):
    public = reader()
    nodes, texts, files, counts, terms = {}, {}, {}, {}, {}
    def visit(value):
        if isinstance(value, dict):
            path, n = value.get('path'), value.get('n')
            if path and isinstance(n, int) and str(path).endswith('.csv'):
                path = str(path)
                counts[(path, n)] = path
                files.setdefault(path, path)
                record = value.get('record')
                if isinstance(record, dict):
                    texts[path+'.json'] = json.dumps(record)
                    texts[path] = str(record.get('source', ''))
                actual = Path(path)
                origin = Path(path+'.origin.json')
                if actual.is_file() and origin.is_file():
                    data = load(origin)
                    expected = data.get('snapshot_sha256')
                    if data.get('path') and expected and hashlib.sha256(actual.read_bytes()).hexdigest() == expected:
                        original = str(data['path'])
                        files[original] = path
                        counts[(original, n)] = path
            for key, child in value.items():
                if key != 'record':
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(proof)
    for text in references:
        visit(json.loads(text))
    folder = Path(work)/'public-root-snapshots'
    for (original, n), actual in counts.items():
        logical = original
        if '/gather/' in original and gather is not None:
            held = gather({'root':dict(source=[original,n])})
            if not held or not public.direct_public(held[0].get('source','')):
                continue
            logical = original[:-4]+'.n%d.csv'%n
            texts[logical] = held[0]['source']
            terms[logical] = held[0].get('licence','')+' '+held[0]['source']
            texts[logical+'.json'] = json.dumps(dict(n=n,source=held[0]['source'],licence=held[0].get('licence','')))
            actual = original
        if not public.public_node(logical, n, texts, files):
            continue
        if logical not in terms:
            for name in (original+'.json',original+'.origin.json',original[:-4]+'.json'):
                try:
                    data = json.loads(texts[name]) if name in texts else load(files.get(name,name))
                except (OSError,ValueError,KeyError):
                    continue
                if isinstance(data,dict):
                    terms[logical] = ' '.join(str(data.get(k,'')) for k in ('licence','licence_text','source'))
                    if any(token in terms[logical] for token in ('Apache','CC0','CC BY 4.0')):
                        break
        path = Path(actual)
        if not path.is_file():
            raise ValueError('missing recorded public-first packing: '+original)
        parsed = public.packing(path)
        if parsed is None:
            st = path.stat()
            coords = matrix(str(path)) if matrix is not None else None
            if coords is not None:
                part = coords[coords[:,0] == n]
                rows = [dict(n=str(n),x=repr(float(q[1])),y=repr(float(q[2]))) for q in part]
            else:
                rows = selected_rows(str(path), st.st_mtime_ns, st.st_size, n)
            if len(rows) != n:
                raise ValueError('public-first ancestor count missing: '+original)
            stream = io.StringIO(newline='')
            writer = csv.DictWriter(stream, fieldnames=['n','x','y'], extrasaction='ignore')
            writer.writeheader(); writer.writerows(rows)
            payload = stream.getvalue().encode()
            folder.mkdir(exist_ok=True)
            key = hashlib.sha256(payload).hexdigest()
            selected = folder/(key+'.csv')
            if not selected.exists():
                selected.write_bytes(payload)
            path = selected
        key = hashlib.sha256(path.read_bytes()).hexdigest()
        nodes[(logical, key)] = (logical, str(path), key)
    results = public.audit_nodes(list(nodes.values()), texts, files)
    for row in results:
        row['licence_notice'] = terms.get(row['original'],'')
        row['licence_allowed'] = any(token in row['licence_notice'] for token in ('Apache','CC0','CC BY 4.0'))
        row['allowed'] = row['allowed'] and row['licence_allowed']
    return results
