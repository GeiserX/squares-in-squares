#!/usr/bin/env python3
"""Download every public Squares-in-Squares packing source on Kaggle.

  python3 -I harvest_fetch.py OUTDIR

- datasets: every dataset whose search for "squares in squares" / "square packing"
  returns a squares-related ref, downloaded whole (zip) into OUTDIR/ds/<owner>__<slug>/;
- notebooks: every public kernel of the competition, its output files ending in
  .csv/.zip/.txt/.json/.npz into OUTDIR/nb/<owner>__<slug>/.
Each source dir gets a meta.json with its licence (datasets: licenseName and
description; notebooks: Kaggle's default Apache 2.0 for public notebooks).
discover_extra() adds what the search strings and the competition's kernel list
miss: the squares datasets and notebooks of the teams at the top of the public
leaderboard, the datasets and notebooks a competition notebook takes as inputs or
links in its source, and the notebooks that take a known squares dataset as input.
A leaderboard user's notebook from outside the competition's list is kept only when
its ref says squares. The forum is not covered: the public
API has no discussion endpoint.
The token is read from ~/.kaggle/access_token and sent as a Bearer header; it
is never printed. Downloads are data: nothing in them is executed.
"""
import json, os, pathlib, sys, time, urllib.error, urllib.parse, urllib.request

API = 'https://www.kaggle.com/api/v1'
TOK = pathlib.Path('~/.kaggle/access_token').expanduser().read_text().strip()
COMP = 'squares-in-squares'
KEEP = ('.csv', '.zip', '.txt', '.json', '.npz', '.gz', '.parquet')


def get(url, raw=False, pause=0.0):
    """GET with the token. A 429 (rate limit) waits and retries, up to 6 times; pause sleeps first."""
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOK}'})
    for attempt in range(6):
        time.sleep(pause)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            return data if raw else json.loads(data)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(min(int(e.headers.get('Retry-After') or 0) or 30 * (attempt + 1), 180))


def fetch(url, path):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOK}'})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, 'wb') as h:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            h.write(b)


def squareish(ref):
    """Does an owner/slug ref look like this competition's work? Used only for sources found outside the lists."""
    s = ref.lower().split('/')[-1]
    return ('squares' in s or 'square-in' in s or 'packing' in s or 'boxed' in s or 'sis' in s.split('-')) \
        and not any(w in s for w in ('chess', 'foursquare', 'classif'))


def top_users(k=40):
    """User names of the first k teams of the public leaderboard."""
    import csv, io, zipfile
    z = zipfile.ZipFile(io.BytesIO(get(f'{API}/competitions/{COMP}/leaderboard/download', raw=True)))
    rows = list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8-sig')))
    return [u.strip() for r in rows[:k] for u in r.get('TeamMemberUserNames', '').split(',') if u.strip()]


def discover_extra(refs, kernels, log=print, cache=None, ttl=12 * 3600):
    """Add datasets to refs and notebooks to kernels (both ref -> list entry) from the leaderboard,
    notebook inputs, notebook source links and dataset users. Returns {ref: how it was found}.

    cache (a dict, changed in place; the caller loads and saves it) keeps the answer that makes most of the
    calls and rarely changes: what a notebook's source names (its inputs and links), or that the source is not
    readable (403, 404). An entry is used again only when it is younger than ttl seconds and, for a notebook
    of the lists, its lastRunTime is the one the entry was read at. A notebook outside the lists is asked every
    time unless it was missing or private, because its answer carries its run time; any other failure is not
    kept. The listings that find new sources (leaderboard users, dataset users) and every dataset lookup are
    always asked. Measured on 2026-11-11 on one listing: 230 of the 395 calls are these reads and 222 of them
    come from the cache (616 s without it, 252 s with it); both passes list the same sources."""
    import re
    how, pulled = {}, {}
    cache = {} if cache is None else cache
    cpull = cache.setdefault('pull', {})
    now = time.time()
    phase, calls, spent, hits = ['users'], {}, {}, {}

    def slow(url):                              # about 300 calls when nothing is cached: stay under the rate limit
        t = time.time()
        try:
            return get(url, pause=1.0)
        finally:
            calls[phase[0]] = calls.get(phase[0], 0) + 1
            spent[phase[0]] = spent.get(phase[0], 0.0) + time.time() - t

    def pull(ref):
        """What the source of a notebook names: {'ref', 'private', 'lastRun', 'ds_in', 'nb_in', 'ds_link', 'nb_link'}."""
        if ref in pulled:
            return pulled[ref]
        run = (kernels.get(ref) or {}).get('lastRunTime')
        c = cpull.get(ref)
        # a notebook outside the lists has no listed run time: only "not there" or "private" is used again
        same = c.get('run') == run if c and ref in kernels else c and (not c['d'].get('ref') or c['d'].get('private'))
        if c and now - c['t'] < ttl and same:
            hits['pull'] = hits.get('pull', 0) + 1
            pulled[ref] = c['d']
            return c['d']
        keep = True
        try:
            o, s = ref.split('/')
            d = slow(f'{API}/kernels/pull?userName={o}&kernelSlug={s}')
            md = d.get('metadata', {})
            src = (d.get('blob') or {}).get('source') or ''
            out = {'ref': md.get('ref'), 'private': bool(md.get('isPrivate')), 'lastRun': md.get('lastRunTime'),
                   'ds_in': md.get('datasetDataSources') or [], 'nb_in': md.get('kernelDataSources') or [],
                   'ds_link': re.findall(r'kaggle\.com/datasets/([\w-]+/[\w-]+)', src),
                   'nb_link': re.findall(r'kaggle\.com/code/([\w-]+/[\w-]+)', src)}
        except Exception as e:
            out = {}
            keep = isinstance(e, urllib.error.HTTPError) and e.code in (403, 404)
            log('pull fail', ref, e)
        if keep:
            cpull[ref] = {'t': now, 'run': run, 'd': out}
        else:
            cpull.pop(ref, None)
        pulled[ref] = out
        return out

    def add_ds(ref, why):
        ref = ref.strip().strip('/')
        if ref.count('/') != 1 or ref in refs or ref in how:
            return
        how[ref] = 'no'
        was, phase[0] = phase[0], 'dataset lookups'
        try:
            o, s = ref.split('/')
            for d in slow(f'{API}/datasets/list?user={o}&search={urllib.parse.quote(s)}'):
                if d['ref'] == ref:
                    refs[ref] = d; how[ref] = why
        except Exception as e:
            log('ds lookup fail', ref, e)
        phase[0] = was

    def add_nb(k, why):
        if k['ref'] not in kernels:
            kernels[k['ref']] = k; how[k['ref']] = why

    try:
        users = top_users()
    except Exception as e:
        users = []
        log('leaderboard fail', e)
    for u in users:
        try:
            for d in slow(f'{API}/datasets/list?user={u}'):
                if squareish(d['ref']) and d['ref'] not in refs:
                    refs[d['ref']] = d; how[d['ref']] = f'leaderboard user {u}'
            for k in slow(f'{API}/kernels/list?user={u}&pageSize=100&sortBy=dateRun'):
                if squareish(k['ref']):        # one tagged with the competition is in its list already
                    add_nb(k, f'leaderboard user {u}')
        except Exception as e:
            log('user fail', u, e)
    phase[0] = 'pulls'
    for ref in sorted(kernels):                 # inputs and source links of the notebooks found so far, one level
        d = pull(ref)
        for r in d.get('ds_in', []):
            add_ds(r, f'input of {ref}')
        for r in d.get('ds_link', []):
            if squareish(r):
                add_ds(r, f'linked in {ref}')
        linked = [r for r in d.get('nb_link', []) if squareish(r)]
        for r in d.get('nb_in', []) + linked:
            r = r.strip().strip('/')
            if r.count('/') == 1 and r not in kernels and r not in how:
                m2 = pull(r)
                if m2.get('ref') == r and not m2.get('private'):
                    add_nb({'ref': r, 'lastRunTime': m2.get('lastRun')}, f'input or link of {ref}')
    phase[0] = 'dataset users'
    for ref in sorted(refs):                    # notebooks that take a squares dataset as input
        try:
            for k in slow(f'{API}/kernels/list?dataset={ref}&pageSize=100'):
                if squareish(ref):
                    add_nb(k, f'uses dataset {ref}')
        except Exception as e:
            log('dataset users fail', ref, e)
    for r in [r for r in cpull if r not in pulled and now - cpull[r]['t'] >= ttl]:
        del cpull[r]                            # not looked at in this run and past the ttl
    how = {r: w for r, w in how.items() if w != 'no'}
    for r, w in sorted(how.items()):
        log('extra', r, '<-', w, flush=True)
    log('discover: ' + '; '.join('%s %d calls %.0f s' % (p, calls[p], spent[p]) for p in calls)
        + '; from the cache: %d pulls' % hits.get('pull', 0), flush=True)
    return how


def main():
    out = pathlib.Path(sys.argv[1]); (out / 'ds').mkdir(parents=True, exist_ok=True); (out / 'nb').mkdir(exist_ok=True)
    refs = {}
    for q in ('squares in squares', 'square packing', 'squares-in-squares', 'packing squares'):
        for page in (1, 2, 3):
            try:
                for d in get(f"{API}/datasets/list?search={urllib.parse.quote(q)}&page={page}"):
                    r = d['ref'].lower()
                    if 'square' in r or 'sis' in r.split('/')[1] or 'packing' in r:
                        refs[d['ref']] = d
            except Exception as e:
                print('list error', q, page, e)
    kernels = {}
    for sort in ('voteCount', 'dateRun', 'hotness', 'scoreAscending', 'dateCreated', 'viewCount'):
        for page in range(1, 6):
            try:
                ks = get(f'{API}/kernels/list?competition={COMP}&sortBy={sort}&pageSize=100&page={page}')
            except Exception as e:
                print('klist error', sort, page, e); break
            if not ks:
                break
            for k in ks:
                kernels[k['ref']] = k
    discover_extra(refs, kernels)
    for ref, d in sorted(refs.items()):
        if d.get('totalBytes', 0) > 1.5e9:
            print('skip big', ref); continue
        dst = out / 'ds' / ref.replace('/', '__')
        if (dst / 'meta.json').exists():
            continue
        dst.mkdir(exist_ok=True)
        owner, slug = ref.split('/')
        try:
            fetch(f'{API}/datasets/download/{owner}/{slug}', dst / 'data.zip')
            try:
                md = get(f'{API}/datasets/metadata/{owner}/{slug}')
            except Exception:
                md = {}
            info = md.get('info', md) if isinstance(md, dict) else {}
            (dst / 'meta.json').write_text(json.dumps({
                'ref': ref, 'kind': 'dataset', 'license': d.get('licenseName'),
                'updated': d.get('lastUpdated'), 'description': (info.get('description') or '')[:4000]}, indent=1))
            print('ds', ref, d.get('licenseName'), os.path.getsize(dst / 'data.zip'), flush=True)
        except Exception as e:
            print('ds fail', ref, e, flush=True)
    print(len(kernels), 'kernels', flush=True)
    for ref in sorted(kernels):
        dst = out / 'nb' / ref.replace('/', '__')
        if (dst / 'meta.json').exists():
            continue
        dst.mkdir(exist_ok=True)
        owner, slug = ref.split('/')
        try:
            files = get(f'{API}/kernels/output?userName={owner}&kernelSlug={slug}').get('files', [])
        except Exception as e:
            print('nb fail', ref, e); continue
        got = []
        for f in files:
            n = f['fileName']
            if n.lower().endswith(KEEP):
                p = dst / n.replace('/', '__')
                try:
                    urllib.request.urlretrieve(f['url'], p); got.append((n, os.path.getsize(p)))
                except Exception as e:
                    print('nb file fail', ref, n, e)
        (dst / 'meta.json').write_text(json.dumps({
            'ref': ref, 'kind': 'notebook', 'license': 'Apache 2.0 (Kaggle default for public notebooks)',
            'lastRun': kernels[ref].get('lastRunTime'), 'files': got}, indent=1))
        print('nb', ref, len(got), sum(s for _, s in got), flush=True)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
