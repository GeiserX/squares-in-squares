#!/usr/bin/env python3
"""Fetch only the public sources that are new or re-run since an earlier harvest.

  python3 -I harvest_delta.py OLD_HARVEST NEW_OUTDIR

A notebook is fetched when it is missing from OLD_HARVEST, its lastRunTime is newer
than the one in OLD_HARVEST's meta.json, or it had no output file then (a notebook
that is still running lists none); a dataset when it is missing or its
lastUpdated changed. Kaggle reports the run time of some old notebooks relative to
now, so it grows on every listing: such a notebook is asked for its output list
again, and its files are downloaded only when the run id in their URLs (/kf/<id>/)
differs from the "session" its meta.json recorded. The output layout is the same as harvest_fetch.py, so
harvest_merge.py reads NEW_OUTDIR unchanged. Downloads are data: nothing is executed.
A source that did not move leaves only its meta.json in NEW_OUTDIR (carry), so NEW_OUTDIR is the OLD_HARVEST of
the next run. The run prints how many notebooks it listed; 0 means Kaggle was not reached, not that nothing moved.
Besides the four search strings and the competition's kernel list, the sources come
from harvest_fetch.discover_extra (leaderboard teams, notebook inputs and links,
notebooks that use a squares dataset); each such source's meta.json says how it was
found ("found").
That step keeps what a notebook's source names in NEW_OUTDIR/discover-cache.json and
reads OLD_HARVEST's copy: an answer is used again for 12 hours while the notebook was
not run again (see discover_extra).
"""
import json, pathlib, re, sys, urllib.parse, urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # -I drops the script dir
import harvest_fetch as H  # noqa: E402


def old_meta(old, kind, ref):
    p = old / kind / ref.replace('/', '__') / 'meta.json'
    return json.loads(p.read_text()) if p.exists() else None


def session(files):
    """The run id shared by every output URL of a notebook (/kf/<id>/), or None when they do not show one."""
    ids = {(re.search(r'/kf/(\d+)/', f.get('url') or '') or [None, None])[1] for f in files}
    return ids.pop() if len(ids) == 1 else None


def carry(old, out):
    """Copy the meta.json of every source of OLD that was not fetched into OUT, so OUT knows every source seen
    so far and the next delta against OUT fetches only what moved. A carried dir holds no packing file."""
    k = 0
    for kind in ('ds', 'nb'):
        for m in sorted((old / kind).glob('*/meta.json')):
            dst = out / kind / m.parent.name
            if not (dst / 'meta.json').exists():
                dst.mkdir(parents=True, exist_ok=True)
                (dst / 'meta.json').write_text(json.dumps(dict(json.loads(m.read_text()), carried=str(old)), indent=1))
                k += 1
    print('carried', k, 'unchanged sources from', old, flush=True)


def main():
    old, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    (out / 'ds').mkdir(parents=True, exist_ok=True); (out / 'nb').mkdir(exist_ok=True)
    refs = {}
    for q in ('squares in squares', 'square packing', 'squares-in-squares', 'packing squares'):
        for page in (1, 2, 3):
            try:
                for d in H.get(f"{H.API}/datasets/list?search={urllib.parse.quote(q)}&page={page}"):
                    r = d['ref'].lower()
                    if 'square' in r or 'sis' in r.split('/')[1] or 'packing' in r:
                        refs[d['ref']] = d
            except Exception as e:
                print('list error', q, page, e)
    kernels = {}
    for sort in ('dateRun', 'scoreAscending', 'voteCount', 'hotness', 'dateCreated'):
        for page in range(1, 6):
            try:
                ks = H.get(f'{H.API}/kernels/list?competition={H.COMP}&sortBy={sort}&pageSize=100&page={page}')
            except Exception as e:
                print('klist error', sort, page, e); break
            if not ks:
                break
            for k in ks:
                kernels[k['ref']] = k
    n_ds, n_nb = len(refs), len(kernels)
    cache = {}
    try:
        cache = json.loads((old / 'discover-cache.json').read_text())
    except (OSError, ValueError):
        pass                                    # no cache yet, or an unreadable one: every source is asked
    how = H.discover_extra(refs, kernels, cache=cache)
    (out / 'discover-cache.json').write_text(json.dumps(cache))
    print(f'{n_ds} datasets by search + {len(refs) - n_ds} extra; {n_nb} competition kernels + {len(kernels) - n_nb} extra',
          flush=True)
    for ref, d in sorted(refs.items()):
        m = old_meta(old, 'ds', ref)
        if m and m.get('updated') == d.get('lastUpdated'):
            continue
        if d.get('totalBytes', 0) > 1.5e9:
            print('skip big', ref); continue
        dst = out / 'ds' / ref.replace('/', '__'); dst.mkdir(exist_ok=True)
        owner, slug = ref.split('/')
        try:
            H.fetch(f'{H.API}/datasets/download/{owner}/{slug}', dst / 'data.zip')
            (dst / 'meta.json').write_text(json.dumps({
                'ref': ref, 'kind': 'dataset', 'license': d.get('licenseName'),
                'updated': d.get('lastUpdated'), 'previous': (m or {}).get('updated'),
                'found': how.get(ref, 'search')}, indent=1))
            print('ds', ref, d.get('licenseName'), d.get('lastUpdated'), flush=True)
        except Exception as e:
            print('ds fail', ref, e, flush=True)
    print(len(kernels), 'kernels', flush=True)
    for ref, k in sorted(kernels.items()):
        m = old_meta(old, 'nb', ref)
        if m and (m.get('lastRun') or '') >= (k.get('lastRunTime') or '') and m.get('files') != []:
            continue                            # no output file last time: it may have been running, ask again
        dst = out / 'nb' / ref.replace('/', '__'); dst.mkdir(exist_ok=True)
        owner, slug = ref.split('/')
        try:
            files = H.get(f'{H.API}/kernels/output?userName={owner}&kernelSlug={slug}').get('files', [])
        except Exception as e:
            print('nb fail', ref, e); continue
        sid = session(files)
        if m and m.get('files') and sid and m.get('session') == sid:
            dst.rmdir()                         # same run as the one we hold: carry() copies its meta.json
            print('same', ref, 'run', sid, flush=True); continue
        got = []
        for f in files:
            n = f['fileName']
            if n.lower().endswith(H.KEEP):
                p = dst / n.replace('/', '__')
                for attempt in (1, 2, 3):           # a dropped connection is common on the big files
                    try:
                        H.fetch(f['url'], p) if f['url'].startswith(H.API) else urllib.request.urlretrieve(f['url'], p)
                        got.append((n, p.stat().st_size))
                        break
                    except Exception as e:
                        print('nb file fail', ref, n, e, 'attempt', attempt, flush=True)
                        p.unlink(missing_ok=True)
        (dst / 'meta.json').write_text(json.dumps({
            'ref': ref, 'kind': 'notebook', 'license': 'Apache 2.0 (Kaggle default for public notebooks)',
            'lastRun': k.get('lastRunTime'), 'previous': (m or {}).get('lastRun'),
            'found': how.get(ref, 'competition list'), 'session': sid, 'files': got}, indent=1))
        print('nb', ref, k.get('lastRunTime'), len(got), sum(s for _, s in got), flush=True)
    carry(old, out)


if __name__ == '__main__':
    main()
