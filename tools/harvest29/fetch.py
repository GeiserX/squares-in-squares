"""Fetch changed notebook data and their credit files as immutable passes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
import socket
import time
import signal
socket.setdefaulttimeout(25)
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L))
import harvest_fetch as H
import rpc
FIRST = ['nilanjansaha123/its-a-secret', 'amirhezekiahespanto/debut-top-145-22-17478894-v34',
         'alexchilton/squares-101-the-starter-kit-12-100-downloads',
         'malyshevdanil/squares-in-squares-living-atlas-of-tight-packings']


def output_timeout(*args):
    raise TimeoutError('notebook output read exceeded90s')


def fetch(out, cache, wide_limit=20):
    started=time.monotonic()
    kernels = []
    for page in (1, 2):
        try:
            kernels += rpc.get(f'{H.API}/kernels/list?competition={H.COMP}&sortBy=dateRun&pageSize=100&page={page}')
        except Exception as e:
            print('LIST ERROR page',page,type(e).__name__,str(e)[:80],flush=True)
    refs = {k['ref']: k for k in kernels}
    screened=set(cache.get('_older_screened',[]))
    older=list(dict.fromkeys(k['ref'] for k in kernels if k['ref'] not in cache and k['ref'] not in screened and str(k.get('lastRunTime',''))[:19]<'2026-11-14T23:00:00'))[:wide_limit]
    selected = list(dict.fromkeys(FIRST + [ref for ref,value in cache.items() if not ref.startswith('_') and isinstance(value,str) and '/' in ref] + [k['ref'] for k in kernels if str(k.get('lastRunTime', ''))[:19] >= '2026-11-14T23:00:00'] + older))
    print('COVERAGE older batch',len(older),'previously screened',len(screened),flush=True)
    changed = []
    for ref in selected:
        if time.monotonic()-started>300:
            print('FETCH pass budget300s reached; remaining refs wait for next pass',flush=True)
            break
        dst=None
        previous_handler=signal.signal(signal.SIGALRM,output_timeout)
        previous_timer=signal.setitimer(signal.ITIMER_REAL,90)
        try:
            owner, slug = ref.split('/')
            k = refs.get(ref, {})
            files = rpc.get(f'{H.API}/kernels/output?userName={owner}&kernelSlug={slug}').get('files', [])
            signature = json.dumps([(f['fileName'], (re.search(r'/kf/(\d+)/', f.get('url') or '') or [None, None])[1], f.get('size')) for f in files], sort_keys=True)
            if not files or cache.get(ref) == signature:
                print('unchanged/no output', ref, k.get('lastRunTime'), flush=True)
                if ref in older:screened.add(ref)
                continue
            dst = Path(out)/'nb'/ref.replace('/', '__')
            dst.mkdir(parents=True, exist_ok=True)
            got = []
            for f in files:
                name = f['fileName']
                if not name.lower().endswith(('.csv', '.json', '.txt', '.zip', '.gz', '.md', '.tsv')):
                    continue
                p = dst/name.replace('/', '__')
                rpc.download(f['url'],p)
                got.append({'file': name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
            (dst/'meta.json').write_text(json.dumps(dict(ref=ref, kind='notebook', license='Apache 2.0 (Kaggle default for public notebooks)',
                lastRun=k.get('lastRunTime'), signature=signature, files=got), indent=2)+'\n')
            cache[ref] = signature
            if ref in older:screened.add(ref)
            changed.append(ref)
            print('FETCH', ref, k.get('lastRunTime'), 'files',len(got),'bytes',sum(x['bytes'] for x in got),'first8',[(x['file'],x['bytes']) for x in got[:8]],flush=True)
        except Exception as e:
            if dst is not None and dst.exists():
                failed=Path(out).parent/'fetch-failed'/dst.name;failed.parent.mkdir(exist_ok=True)
                if not failed.exists():dst.rename(failed)
            print('FETCH ERROR', ref, type(e).__name__, getattr(getattr(e,'response',None),'status_code','transport failure'), flush=True)
        finally:
            signal.setitimer(signal.ITIMER_REAL,*previous_timer)
            signal.signal(signal.SIGALRM,previous_handler)
    cache['_older_screened']=sorted(screened)
    return changed


if __name__ == '__main__':
    out = Path(sys.argv[1]); cp = Path(sys.argv[2])
    cache = json.loads(cp.read_text()) if cp.exists() else {}
    changed = fetch(out, cache)
    cp.write_text(json.dumps(cache, indent=1)+'\n')
    print('CHANGED', changed, flush=True)
