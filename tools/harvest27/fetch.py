"""Fetch changed notebook data and their credit files as immutable passes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L))
import harvest_fetch as H
FIRST = ['nilanjansaha123/its-a-secret', 'amirhezekiahespanto/debut-top-145-22-17478894-v34',
         'alexchilton/squares-101-the-starter-kit-12-100-downloads',
         'malyshevdanil/squares-in-squares-living-atlas-of-tight-packings']


def fetch(out, cache):
    kernels = []
    for page in (1, 2):
        kernels += H.get(f'{H.API}/kernels/list?competition={H.COMP}&sortBy=dateRun&pageSize=100&page={page}')
    refs = {k['ref']: k for k in kernels}
    selected = list(dict.fromkeys(FIRST + [k['ref'] for k in kernels if str(k.get('lastRunTime', ''))[:19] >= '2026-11-14T17:00:00']))
    changed = []
    for ref in selected:
        try:
            owner, slug = ref.split('/')
            k = refs.get(ref, {})
            files = H.get(f'{H.API}/kernels/output?userName={owner}&kernelSlug={slug}').get('files', [])
            signature = json.dumps([(f['fileName'], (re.search(r'/kf/(\d+)/', f.get('url') or '') or [None, None])[1], f.get('size')) for f in files], sort_keys=True)
            if not files or cache.get(ref) == signature:
                print('unchanged/no output', ref, k.get('lastRunTime'), flush=True)
                continue
            dst = Path(out)/'nb'/ref.replace('/', '__')
            dst.mkdir(parents=True, exist_ok=True)
            got = []
            for f in files:
                name = f['fileName']
                if not name.lower().endswith(('.csv', '.json', '.txt', '.zip', '.gz', '.md', '.tsv')):
                    continue
                p = dst/name.replace('/', '__')
                urllib.request.urlretrieve(f['url'], p)
                got.append({'file': name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
            (dst/'meta.json').write_text(json.dumps(dict(ref=ref, kind='notebook', license='Apache 2.0 (Kaggle default for public notebooks)',
                lastRun=k.get('lastRunTime'), signature=signature, files=got), indent=2)+'\n')
            cache[ref] = signature
            changed.append(ref)
            print('FETCH', ref, k.get('lastRunTime'), [(x['file'], x['bytes']) for x in got], flush=True)
        except Exception as e:
            print('FETCH ERROR', ref, type(e).__name__, str(e)[:120], flush=True)
    return changed


if __name__ == '__main__':
    out = Path(sys.argv[1]); cp = Path(sys.argv[2])
    cache = json.loads(cp.read_text()) if cp.exists() else {}
    changed = fetch(out, cache)
    cp.write_text(json.dumps(cache, indent=1)+'\n')
    print('CHANGED', changed, flush=True)
