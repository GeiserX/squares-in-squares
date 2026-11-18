#!/usr/bin/env python3
"""Close round 32 of the midm lane: verify the take, write the results table, measure the queues, clean the boxes.

Usage: final32.py dry      verify without writing take.tsv, results/ or STATE (output under work/)
       final32.py verify   re-certify every take row (finesafe 2.2e-11), keep it only below bar32 and every
                           other live take-*-r32 row of n by more than 1e-10, rewrite take.tsv by rename, write
                           results/midm-r32-2026-11-16.tsv and work/final32.json (sums and queue measurements)
       final32.py clean    after the last pull: check that every take row's raw find and certified file are on
                           boxA, then remove $SCRATCH/squares-midm on boxE and on boxD
"""
import csv, glob, json, math, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import round32 as r  # noqa: E402

RESULTS = r.RES / 'midm-r32-2026-11-16.tsv'


def bar29b():
    """Round 32 bar: round32-briefs/bar32.tsv (the held round 31 b gate details); name kept from final30.py."""
    return r.bar()


def done_records():
    out = []
    for name in r.BOXES:
        for p in glob.glob(str(r.box_dir(name) / 'back/done/*.json')):
            try:
                d = json.loads(Path(p).read_text())
            except ValueError:
                continue
            d['box'] = name; d['stem'] = Path(p).stem
            out.append(d)
    return out


def measure(st):
    rows = {}
    for d in done_records():
        j = st['jobs'].get(str(d['k']), {})
        kind = j.get('kind', d.get('kind', '?'))
        if str(d['k']) in st['jobs'] and j.get('kind') == 'fresh-near' and r.is_rect(j.get('origin', '')):
            kind = 'rect'
        if 'take-harvest-r32/' in j.get('origin', '') and kind == 'fresh-take':
            kind = 'fresh-take harvest'
        key = 'raw legs' if d.get('leg', 0) else kind
        m = rows.setdefault(key, dict(scans=0, seconds=0.0, gain=0.0, paid=0))
        m['scans'] += 1; m['seconds'] += d.get('elapsed') or 0.0
        g = d.get('gain') or 0.0
        m['gain'] += g
        m['paid'] += g >= 1e-6
        m['probe_stops'] = m.get('probe_stops', 0) + bool(d.get('probe_stop'))
        m['finds'] = m.get('finds', 0) + bool(d.get('side_gain', 0) > 1e-8)
    return rows


def verify(dry=False):
    st = r.load_state(); base = bar29b()
    res = (r.W / 'results-dry.tsv') if dry else RESULTS
    tab = r.T / 'take.tsv'
    rows = list(csv.DictReader(open(tab), delimiter='\t')) if tab.exists() else []
    keep, dropped = [], []
    # a per-n file byte-identical to a file the driver certified (floatsafe.work output, or its certified quench)
    # keeps that score; any other file is certified again here (boxA at load 40 needs ~20 s a row)
    known = {}
    for c in st['cert'].values():
        if c.get('cert') and c.get('score') is not None and Path(c['cert']).exists():
            known[r.sha(c['cert'])] = c['score']
    for cpath, q in st['fq'].get('done', {}).items():
        if q.get('fq') and q.get('fq_score') is not None and Path(q['fq']).exists():
            known[r.sha(q['fq'])] = q['fq_score']
    scores = {}
    for row in rows:
        n = int(row['n']); p = r.T / ('%d.csv' % n)
        if p.exists() and r.sha(p) in known:
            score = known[r.sha(p)]
        else:
            score, _ = r.certify_file(p, n) if p.exists() else (None, None)
        scores[n] = score
    live = r.live_bar()                       # read after the certification: the latest rows of the other lanes
    for row in rows:
        n = int(row['n']); score = scores[n]
        peer = live.get(n, (math.inf, ''))
        why = None
        if score is None:
            why = 'floatsafe failed or file missing'
        elif abs(score - float(row['new'])) > 1e-15:
            why = 'certified %.17g differs from take %.17g' % (score, float(row['new']))
        elif not score < base[n] - 1e-10:
            why = 'not below the base bar'
        elif not score < peer[0] - 1e-10:
            why = 'not below %s (%.17g)' % (peer[1], peer[0])
        if why:
            dropped.append((n, why)); continue
        keep.append((row, score, peer))
    if dropped and not dry:
        tmp = r.T / '.take.tsv.tmp'
        with open(tmp, 'w', newline='') as h:
            w = csv.writer(h, delimiter='\t', lineterminator='\n')
            w.writerow(list(rows[0].keys()))
            for row, _, _ in keep:
                w.writerow([row[k] for k in rows[0].keys()])
        tmp.replace(tab)
        for n, why in dropped:
            (r.T / ('%d.csv' % n)).unlink(missing_ok=True)
            r.state_line('FINAL DROP n=%d: %s' % (n, why))
    # results table in the round 25 layout
    out = []
    for row, score, peer in keep:
        n = int(row['n'])
        job = None
        for c in st['cert'].values():
            if c['n'] == n and c.get('cert'):
                fq = st['fq'].get('done', {}).get(c['cert'], {})
                if c.get('score') == score or fq.get('fq_score') == score:
                    job = st['jobs'].get(str(c['k']))
        inp = job.get('score') if job else None
        lowest_other = min(base[n], peer[0])
        out.append(dict(n=n, held=base[n], new=score, gain_on_base=base[n] - score, lowest_other=lowest_other,
                        gain_on_all=lowest_other - score, input_score=inp,
                        gain_on_input=(inp - score) if inp is not None else None,
                        source=row['source'], licence=row['licence'], k=job['k'] if job else None,
                        kind=job['kind'] if job else None))
    with open(res, 'w', newline='') as h:
        w = csv.writer(h, delimiter='\t', lineterminator='\n')
        cols = ['n', 'held', 'new', 'gain_on_base', 'lowest_other', 'gain_on_all', 'input_score', 'gain_on_input',
                'source', 'licence']
        w.writerow(cols)
        for o in out:
            w.writerow([repr(o[c]) if isinstance(o[c], float) else ('' if o[c] is None else o[c]) for c in cols])
    summary = dict(at=r.now(), improved_n=len(out), against_base=sum(o['gain_on_base'] for o in out),
                   beyond_other_live_r32=sum(o['gain_on_all'] for o in out),
                   rows={o['n']: {k: o[k] for k in ('new', 'gain_on_base', 'gain_on_all', 'input_score',
                                                    'gain_on_input', 'k', 'kind')} for o in out},
                   dropped=dropped, queues=measure(st), jobs=len(st['jobs']),
                   assigned=sum(1 for j in st['jobs'].values() if j['box'] not in (None, 'cancelled')),
                   certified=sum(1 for c in st['cert'].values() if c.get('cert')))
    (r.W / ('final32-dry.json' if dry else 'final32.json')).write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


def clean():
    st = r.load_state()
    tab = r.T / 'take.tsv'
    rows = list(csv.DictReader(open(tab), delimiter='\t')) if tab.exists() else []
    missing = [row['n'] for row in rows if not (r.T / ('%s.csv' % row['n'])).exists()]
    certs = [c['cert'] for c in st['cert'].values() if c.get('cert')]
    missing += [c for c in certs if not Path(c).exists()]
    if missing:
        print('copies missing, not cleaning:', missing); return
    for name, b in r.BOXES.items():
        rc, msg = r.run(r.SSH + [b['host'], 'pgrep -f "[s]quares-midm/" >/dev/null && echo busy || '
                                 '(rm -rf ~/%s && echo removed)' % b['dir']], timeout=300)
        print(name, rc, msg.strip()[-200:])
        r.state_line('CLEAN %s: ~/%s %s' % (b['host'], b['dir'], msg.strip()[-80:]))


if __name__ == '__main__' and sys.argv[1] != 'doc':
    {'verify': verify, 'dry': lambda: verify(True), 'clean': clean}[sys.argv[1]]()


QLABEL = {'rect': 'forensics rect files', 'fresh-take': 'fresh takes of other lanes',
          'fresh-take harvest': 'harvest public takes', 'fresh-near': 'near files of other lanes',
          'fresh-near-far': 'near files 2e-5 to 1e-4 above', 'raw legs': 'raw legs', 'held-unkicked': 'held, never kicked',
          'held-other': 'held, other layout kicked', 'r25-leg': 'round 25 raw legs',
          'reopen': 're-opened starts (Samanyu only)', 'reopen-row': 're-opened round 23 a rows',
          'reopen-held': 're-opened held rows', 'own-held': 'our round 30 rows (held)',
          'seed-take': 'round 30 c rows from takes (held)', 'held-rekick': 'held, kicked again (last kick r28 to r30)',
          'pub-near': 'public rows 1e-6 to 2.5e-4 above the bar (changed files)', 'drop1': 'drop1 from a public n+1',
          'held-gap2': 'held rows by board gap, two unprobed seeds (filler)'}


def doc(text_file):
    """Print the Round 32 doc section: the fixed text of text_file with {keys} filled from work/final32.json."""
    f = json.loads((r.W / 'final32.json').read_text())
    q = f['queues']
    rows = ['| queue | scans | probe stops | seconds | gain before certification | scans that gained 1e-6 or more |',
            '|---|---|---|---|---|---|']
    for key in sorted(q, key=lambda k: -q[k]['gain']):
        m = q[key]
        rows.append('| %s | %d | %d | %.0f | %.4g | %d |' % (QLABEL.get(key, key), m['scans'], m.get('probe_stops', 0),
                                                           m['seconds'], m['gain'], m['paid']))
    vals = dict(improved_n=f['improved_n'], against_base='%.6g' % f['against_base'],
                beyond='%.6g' % f['beyond_other_live_r32'], table='\n'.join(rows),
                rows=', '.join('%s (%.3g)' % (n, v['gain_on_base']) for n, v in sorted(f['rows'].items(), key=lambda x: int(x[0]))))
    for key in q:
        vals['%s_scans' % key.replace(' ', '_').replace('-', '_')] = q[key]['scans']
        vals['%s_paid' % key.replace(' ', '_').replace('-', '_')] = q[key]['paid']
        vals['%s_gain' % key.replace(' ', '_').replace('-', '_')] = '%.3g' % q[key]['gain']
    print(Path(text_file).read_text().format(**vals))


if __name__ == '__main__' and sys.argv[1] == 'doc':
    doc(sys.argv[2])
