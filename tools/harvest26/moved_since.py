"""List competition notebooks run and squares datasets updated after a UTC time (listing only, no download).

  python -I moved_since.py 2026-11-14T15:18:00
"""
import sys, urllib.parse
sys.path.insert(0, '.')
import harvest_fetch as H  # noqa: E402
since = sys.argv[1]
for page in (1, 2):
    for k in H.get(f'{H.API}/kernels/list?competition={H.COMP}&sortBy=dateRun&pageSize=100&page={page}'):
        t = str(k.get('lastRunTime') or '')
        if t[:19] >= since:
            print('nb', k['ref'], t, flush=True)
seen = set()
for q in ('squares in squares', 'square packing', 'squares-in-squares'):
    for d in H.get(f"{H.API}/datasets/list?search={urllib.parse.quote(q)}&sortBy=updated&page=1"):
        t = str(d.get('lastUpdated') or '')
        if d['ref'] not in seen and t[:19] >= since:
            seen.add(d['ref']); print('ds', d['ref'], t, d.get('licenseName'), flush=True)
