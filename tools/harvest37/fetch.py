"""Fetch changed notebook data and their credit files as immutable passes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request
import urllib.parse
import socket
import time
import signal
socket.setdefaulttimeout(25)
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L))
import harvest_fetch as H
import rpc
import download_parts
from common import W
FIRST = ['nilanjansaha123/its-a-secret', 'amirhezekiahespanto/debut-top-145-22-17478894-v34',
         'alexchilton/squares-101-the-starter-kit-12-100-downloads',
         'malyshevdanil/squares-in-squares-living-atlas-of-tight-packings']


def output_timeout(*args):
    raise TimeoutError('notebook output read exceeded90s')


def defer_dry(selected,kernels,notes):
    def slow(ref):
        old=notes.get(ref,{})
        return bool(old.get('run') and old['run']==kernels.get(ref,{}).get('lastRunTime'))
    return sorted(selected,key=slow)


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
    older=list(dict.fromkeys(k['ref'] for k in kernels if k['ref'] not in cache and k['ref'] not in screened and str(k.get('lastRunTime',''))[:19]<'2026-11-14T23:17:00'))[:wide_limit]
    last_runs=cache.setdefault('_last_runs',{})
    selected = list(dict.fromkeys(FIRST + [k['ref'] for k in kernels if str(k.get('lastRunTime', ''))[:19] >= '2026-11-14T23:17:00'] + older))
    defer_path=W/'diagnostic-defer.json'
    if defer_path.exists():selected=defer_dry(selected,refs,json.loads(defer_path.read_text()))
    print('COVERAGE older batch',len(older),'previously screened',len(screened),flush=True)
    changed = []
    for ref in selected:
        if time.monotonic()-started>300:
            print('FETCH pass budget300s reached; remaining refs wait for next pass',flush=True)
            break
        dst=None;got=[];reused=0
        previous_handler=signal.signal(signal.SIGALRM,output_timeout)
        previous_timer=signal.setitimer(signal.ITIMER_REAL,90)
        try:
            owner, slug = ref.split('/')
            k = refs.get(ref, {})
            current_run=k.get('lastRunTime')
            blocked=cache.setdefault('_bounded_failures',{}).get(ref,{})
            if current_run and blocked.get('run')==current_run:
                print('unchanged bounded failure',ref,current_run,flush=True)
                continue
            if ref in cache and current_run and last_runs.get(ref)==current_run:
                print('unchanged run',ref,current_run,flush=True)
                continue
            listing=f'{H.API}/kernels/output?userName={owner}&kernelSlug={slug}'
            if current_run:listing+='&harvestRun='+urllib.parse.quote(str(current_run),safe='')
            files = rpc.get(listing).get('files', [])
            signature = json.dumps([(f['fileName'], (re.search(r'/kf/(\d+)/', f.get('url') or '') or [None, None])[1], f.get('size')) for f in files], sort_keys=True)
            if files and blocked.get('signature')==signature:
                print('unchanged bounded output signature',ref,flush=True)
                continue
            if not files or cache.get(ref) == signature:
                if current_run and files:last_runs[ref]=current_run
                print('unchanged/no output', ref, k.get('lastRunTime'), flush=True)
                if ref in older:screened.add(ref)
                continue
            dst = Path(out)/'nb'/ref.replace('/', '__')
            dst.mkdir(parents=True, exist_ok=True)
            got = []
            finals={'submission.csv','submission_merged.csv','submission_ours.csv','effective_pandas_roundtrip.csv','best_current.csv','best.csv','merged.csv','c0.csv'}
            def priority(file):
                name=file['fileName'].lower()
                return (0 if Path(name).name in finals else 1 if name.endswith('.csv') else 3 if name.endswith(('.zip','.gz')) else 2,name)
            for f in sorted(files,key=priority):
                name = f['fileName']
                if not name.lower().endswith(('.csv', '.json', '.txt', '.zip', '.gz', '.md', '.tsv')):
                    continue
                p = dst/name.replace('/', '__')
                reused+=int(download_parts.fetch(f['url'],p,ref,signature,rpc.download))
                got.append({'file': name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})
            (dst/'meta.json').write_text(json.dumps(dict(ref=ref, kind='notebook', license='Apache 2.0 (Kaggle default for public notebooks)',
                lastRun=k.get('lastRunTime'), signature=signature, files=got), indent=2)+'\n')
            cache[ref] = signature
            if current_run:last_runs[ref]=current_run
            if ref in older:screened.add(ref)
            changed.append(ref)
            print('FETCH', ref, k.get('lastRunTime'), 'files',len(got),'reused',reused,'bytes',sum(x['bytes'] for x in got),'first8',[(x['file'],x['bytes']) for x in got[:8]],flush=True)
        except Exception as e:
            if str(e)=='public file exceeds bounded download' and dst is not None:
                cache.setdefault('_bounded_failures',{})[ref]=dict(run=current_run,signature=signature)
            if dst is not None and got:
                (dst/'meta.json').write_text(json.dumps(dict(ref=ref,kind='notebook',license='Apache 2.0 (Kaggle default for public notebooks)',lastRun=current_run,signature=signature,fetch_incomplete='source proof incomplete after '+type(e).__name__,files=got),indent=2)+'\n')
            if dst is not None and dst.exists():
                failed=Path(out).parent/'fetch-failed'/dst.name;failed.parent.mkdir(exist_ok=True)
                if not failed.exists():dst.rename(failed)
            status=getattr(getattr(e,'response',None),'status_code',None)
            reason=str(e) if str(e) in ('public file exceeds bounded download','kernel output pagination exceeded200 pages','kernel output pagination repeated token','unexpected metadata RPC redirect') else 'transport failure'
            print('FETCH ERROR', ref, type(e).__name__, status or reason, flush=True)
            if status==429:
                print('RATE LIMIT: stop this pass; next refresh follows the20-minute backoff',flush=True)
                break
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
