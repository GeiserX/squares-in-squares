"""Run one boxC fq (remote_run.py, 120 s) on each public near-miss start of a queue, best gap first.

  python -I near_fq.py QUEUE.tsv [--max-gap 6e-5]
A result that certifies below the held bar by more than 1e-10 is staged through cand26.py --no-fq
(then the collector proves and publishes it). A result above the bar that the fq moved by more than
1e-8 goes to take-harvest-r26/near/ with a json sidecar and one handoff line, for the kick lanes.
Every outcome is one line in work/near-fq.tsv. Stops at the deadline in work/deadline.
"""
import argparse, csv, datetime as dt, json, subprocess, sys, time
from pathlib import Path
L = Path('.')
sys.path.insert(0, str(L)); sys.path.insert(0, str(L / 'tools'))
from harvest_collect import Collector, rows_write  # noqa: E402
S = Path('$SCRATCH/bounties-squares')
T = S / 'take-harvest-r26'
W = T / 'work'
PY = str(S / 'venv/bin/python')

ap = argparse.ArgumentParser()
ap.add_argument('queue')
ap.add_argument('--max-gap', type=float, default=6e-5)
a = ap.parse_args()
deadline = int((W / 'deadline').read_text())
ns = argparse.Namespace(details=str(S / 'gate/cand-round25-1114b/details.csv'), own=[], live=[], out=[str(T)],
                        work=str(W / 'nearfq'), host='boxC', remote_dir='scratch/squares-harvest/r26',
                        handoff=None, exclude=[], control=False)
C = Collector(ns)
log = W / 'near-fq.tsv'
if not log.exists():
    log.write_text('utc\tn\tstart\tstart_score\tbar\tfq_score\tgap_after\tseconds\toutcome\n')
done = {l.split('\t')[2] for l in log.read_text().splitlines()[1:]}
for r in csv.DictReader(open(a.queue), delimiter='\t'):
    if time.time() > deadline - 240:
        print('deadline', flush=True); break
    if r['start'] in done or float(r['gap']) > a.max_gap:
        continue
    n = int(r['n'])
    cert = C.cert(r['start'], n)
    if cert is None:
        continue
    t0 = time.time()
    try:
        res, proof = C.remote(cert, n)
    except Exception as e:
        out = ('remote failed ' + repr(e))[:120]; res = None
    bar = C.held[n]
    if res is not None:
        s = res[0]
        if s < bar - 1e-10:
            src = (f"fq quench (boxC, remote_run.py: --no-alm --loosen 1.0 --pit 40 --flip-top 8, 120 s) of a public near miss, "
                   f"start {Path(r['start']).name} certified {float(r['score']):.12g} ({float(r['gap']):.2e} above the r25b bar) from "
                   f"{r['file'].split('/data/')[-1].replace('nb/', '', 1).replace('ds/', '', 1).replace('__', '/', 1)} "
                   f"(public file updated {r['updated']}; layout read as data, not a copy of a held or winning layout)")
            lic = r['licence']
            p = subprocess.run([PY, '-I', str(W / 'tools/cand26.py'), str(n), str(res[1]), src, lic, '--no-fq'],
                               capture_output=True, text=True)
            out = 'staged ' + (p.stdout.strip().splitlines() or [''])[-1][:100]
        elif cert[0] - s > 1e-8:
            near = T / 'near'
            near.mkdir(exist_ok=True)
            tgt = near / f'{n}-pubfq-{res[2][:12]}.csv'
            with open(res[1]) as f:
                rows_write(tgt, list(csv.DictReader(f)))
            Path(str(tgt) + '.json').write_text(json.dumps(dict(n=n, score=s, bar=bar, over_bar=s - bar, start=r['start'],
                                                                start_score=float(r['score']), source_file=r['file'],
                                                                licence=r['licence'], updated=r['updated'], proof=proof), indent=1) + '\n')
            with open(S / 'handoff-r26.log', 'a') as f:
                f.write(f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} harvest -> all: fq of a fresh public near miss n={n}, "
                        f"over bar={s - bar:.3e}, fq gain={cert[0] - s:.3e}, source and licence in sidecar, {tgt}\n")
            out = 'near'
        else:
            out = 'no move'
    with open(log, 'a') as f:
        f.write(f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\t{n}\t{r['start']}\t{cert[0]!r}\t{bar!r}\t"
                f"{(res[0] if res else None)!r}\t{((res[0] - bar) if res else None)!r}\t{time.time() - t0:.0f}\t{out}\n")
    print(n, out, flush=True)
