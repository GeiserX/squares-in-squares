"""table28.py OUT DONE_MM DONE_ST: one row per measured job of the rebuild workers (done.jsonl of each box), in the
column layout of results/rebuild-r26-2026-11-14.tsv. bar_side is the bar the job ran against (the round's bar);
room is bar_side minus end_side. kind: quench (q- keys), kick (a kick: mode), turn (turn + fq loop)."""
import json, os, sys
out = open(sys.argv[1], 'w')
out.write('\t'.join(['n', 'key', 'kind', 'box', 'start_side', 'turn_side', 'end_side', 'bar_side', 'room', 't0', 't1',
                     'error', 'start_file']) + '\n')
f = lambda v: '' if v is None else '%.12f' % v
rows = []
for path, box in ((sys.argv[2], 'boxB'), (sys.argv[3], 'boxE')):
    for l in open(path):
        try:
            r = json.loads(l)
        except Exception:
            continue
        kind = 'quench' if 'quench_ok' in r else ('kick' if 'kick_code' in r else 'turn')
        err = r.get('error') or ''
        if not err and r.get('side') is None:
            err = 'no lower layout' if kind == 'kick' else ('turn code %s' % r.get('turn_code') if kind == 'turn' else 'no result')
        st = r.get('start') or ''
        st = '/'.join(st.split('/')[-2:]) if st else ''
        rows.append((r.get('t0') or '', [str(r['n']), r['key'], kind, box, f(r.get('start_side')), f(r.get('turn_side')),
                     f(r.get('side')), f(r.get('bar')), f(r.get('room')), r.get('t0') or '', r.get('t1') or '', err, st]))
for _, c in sorted(rows, key=lambda x: x[0]):
    out.write('\t'.join(c) + '\n')
print(len(rows), 'jobs')
