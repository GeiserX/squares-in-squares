"""Fetch the .csv outputs of named competition notebooks into OUT/nb/<owner>__<slug>/ with meta.json (harvest_fetch layout).

  python -I fetch_some.py OUT owner/slug ...
Downloads are data: nothing is executed. The token is never printed.
"""
import json, os, pathlib, re, sys, urllib.request
sys.path.insert(0, '.')
import harvest_fetch as H  # noqa: E402
out = pathlib.Path(sys.argv[1])
for ref in sys.argv[2:]:
    owner, slug = ref.split('/')
    k = [x for x in H.get(f'{H.API}/kernels/list?search={slug}&user={owner}&pageSize=20') if x['ref'] == ref]
    files = H.get(f'{H.API}/kernels/output?userName={owner}&kernelSlug={slug}').get('files', [])
    dst = out / 'nb' / ref.replace('/', '__'); dst.mkdir(parents=True, exist_ok=True)
    got, sess = [], {(re.search(r'/kf/(\d+)/', f.get('url') or '') or [None, None])[1] for f in files}
    for f in files:
        n = f['fileName']
        if n.lower().endswith('.csv'):
            p = dst / n.replace('/', '__')
            urllib.request.urlretrieve(f['url'], p); got.append([n, os.path.getsize(p)])
    (dst / 'meta.json').write_text(json.dumps({'ref': ref, 'kind': 'notebook', 'license': 'Apache 2.0 (Kaggle default for public notebooks)',
        'lastRun': k[0].get('lastRunTime') if k else None, 'found': 'competition list (dateRun)', 'session': sess.pop() if len(sess) == 1 else None,
        'files': got}, indent=1))
    print('nb', ref, k[0].get('lastRunTime') if k else None, got, flush=True)
