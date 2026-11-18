"""boxA feeder of kicked follows (border r28, light python, no floatsafe here).
Every 60 s: each default-flag LP final job final/<uid>.job.json whose input is a live take csv of another r28 lane
(take-<lane>-r28/<n>.csv) and whose certified start is within 5e-9 of side of the live bar (bars.json) gets three more
final jobs <uid>-k1..k3: the same certified file, one fq quench with --kick SIGMA --seed K (default flags otherwise).
The driver certifies, checks and publishes them like every other final job.
Why: in r27 our 866 and 693 rows were overtaken 7 and 13 minutes later by kicked follows of other lanes (3.75e-8 and
9.1e-7 lower), while the LP and polish fq on converged takes gain 0 to 3.3e-10 of side, a tenth of the rule."""
import json, re, time, math
from pathlib import Path
W = Path(__file__).parent; T = W.parent
END = float((W / 'deadline').read_text())
KICKS = ((1, 0.003), (2, 0.01), (3, 0.02))
ix_file = W / 'kfeed.json'; ix = set(json.load(open(ix_file))) if ix_file.exists() else set()
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
while time.time() < END - 120:
    try:
        bars = json.load(open(W / 'bars.json'))
        for p in sorted((W / 'final').glob('*.job.json'), key=lambda q: q.stat().st_mtime):
            uid = p.name[:-9]
            if uid in ix or not re.fullmatch(r'\d+-lp-[0-9a-f]{8}-[0-9a-f]{8}', uid): continue
            j = json.load(open(p)); src = j['manifest']['donor_source'].split(', ', 1)[0]
            if not re.search(r'/take-(?!border-)[a-z0-9-]+-r28/\d+\.csv$', src): ix.add(uid); continue
            n = j['n']; side = (j['certified_before'] + 1) * math.sqrt(n); bar = bars.get(str(n), 1e100)
            ix.add(uid)
            if side >= bar + 5e-9 or not Path(src).exists(): continue
            # one kicked set per layout: a take re-read under a new name certifies to the same score (793, 814, 860)
            if any(abs(json.load(open(q))['certified_before'] - j['certified_before']) < 1e-11
                   for q in (W / 'final').glob(f'{n}-lp-*-k1.job.json')): continue
            made = []
            for k, sig in KICKS:
                kid = f'{uid}-k{k}'
                if (W / 'final' / f'{kid}.job.json').exists(): continue
                (W / 'final' / f'{kid}.input.txt').write_bytes((W / 'final' / j['input']).read_bytes())
                (W / 'staged' / f'{kid}.csv').write_bytes((W / 'staged' / f'{uid}.csv').read_bytes())
                note = f'kicked follow: one fq quench of the certified LP file with --kick {sig} --seed {k} (kfeed.py)'
                jk = dict(j, input=f'{kid}.input.txt', output=f'{kid}.output.txt', flags=['--kick', repr(sig), '--seed', str(k)],
                          manifest=dict(j['manifest'], id=kid), flags_note=note)
                tmp = W / 'final' / f'{kid}.job.tmp'; tmp.write_text(json.dumps(jk)); tmp.replace(W / 'final' / f'{kid}.job.json')
                made.append(kid)
            if made: log(f'KICK {n} from {src} (certified side {side:.13f}, {side - bar:.3e} vs the live bar): queued {", ".join(made)}')
        tmp = W / 'kfeed.tmp'; tmp.write_text(json.dumps(sorted(ix))); tmp.replace(ix_file)
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(60)
log('kfeed finished by deadline')
