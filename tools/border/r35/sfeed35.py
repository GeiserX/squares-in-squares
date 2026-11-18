"""boxA self-follow of our own take rows (border r28, light python; r32: a polish and a default-flag fq each time).
Every 60 s: each row of our take.tsv that has not been followed at its score gets one more polish fq (POLISH flags)
from its certified csv, as a final job <n>-self-<hash>-p cloned from the job that made the row. The driver certifies it
and replaces the row only when the result is lower. A row is followed again only when its last step gained more than
1e-9 of side, so a converged row stops.
Why: the 978 row came from the polish fq of the harvest 978 take, which had one fq follow behind it, and that polish
gained 2.08e-8 of side; the follow chain had not converged."""
import csv, json, math, re, sys, time, hashlib
from pathlib import Path
W = Path(__file__).parent; T = W.parent
sys.path.insert(0, '.')
import border_sweep as bs
bs.lib()
csv.field_size_limit(10**9)
END = float((W / 'deadline').read_text())
ix_file = W / 'sfeed.json'; st = json.load(open(ix_file)) if ix_file.exists() else {'done': [], 'last': {}}
done = set(tuple(x) for x in st['done'])  # (n, score) of take rows and ('near', file name)
last = {int(k): v for k, v in st['last'].items()}
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
while time.time() < END - 300:
    try:
        rows = list(csv.DictReader(open(T / 'take.tsv'), delimiter='\t')) if (T / 'take.tsv').exists() else []
        for r in rows:
            n = int(r['n']); new = float(r['new']); key = (n, repr(new))
            if key in done: continue
            done.add(key)
            prev = last.get(n); last[n] = new
            if prev is not None and (prev - new) * math.sqrt(n) <= 1e-9:
                log(f'SELF {n}: last step gained {(prev - new) * math.sqrt(n):.3e} of side; converged, no more self follow'); continue
            m = re.findall(r'certified-file fq (\S+) on boxC', r['source'])
            if not m or not (W / 'final' / f'{m[-1]}.job.json').exists(): log(f'SELF {n}: no template job in the source; skipped'); continue
            uid0 = m[-1]; tj = json.load(open(W / 'final' / f'{uid0}.job.json'))
            fr = list(csv.DictReader(open(T / f'{n}.csv')))
            if len(fr) != n: log(f'SELF {n}: {n}.csv has {len(fr)} rows; skipped'); continue
            uid = f'{n}-self-' + hashlib.sha256(repr(new).encode()).hexdigest()[:8] + '-p'
            if (W / 'final' / f'{uid}.job.json').exists(): continue
            ss, AA = bs.normalize([(float(q['x']), float(q['y']), float(q['angle'])) for q in fr])
            bs.write_txt(str(W / 'final' / f'{uid}.input.txt'), ss, AA)
            (W / 'staged' / f'{uid}.csv').write_bytes((T / f'{n}.csv').read_bytes())
            note = f'self follow: one more fq loop (default flags, then polish, up to three rounds) from our certified take row {n} (score {new!r}), made by {uid0}'
            j = dict(tj, input=f'{uid}.input.txt', output=f'{uid}.output.txt', certified_before=new, flags=list(bs.POLISH), loop=True, priority=-180,
                     manifest=dict(tj['manifest'], id=uid), flags_note=(tj.get('flags_note', '') + '; ' if tj.get('flags_note') else '') + note)
            tmp = W / 'final' / f'{uid}.job.tmp'; tmp.write_text(json.dumps(j)); tmp.replace(W / 'final' / f'{uid}.job.json')
            log(f'SELF {n}: queued {uid} (fq loop of take-border-r35/{n}.csv, score {new!r})')
            # r28 05:06Z: a row made by a default-flag fq (993: 2.4e-6 of side on the k123 take) also gets a default-flag self follow
            # r29 10:58Z: a row made by a default-flag self follow gets one more too (988: the default fq gained 3.4e-5 of score, then 7.8e-7)
            if False and not re.search(r'-ns', uid0):   # r35: the loop job runs both flags; r32: both flags on every self follow (the midm_fqonce loop: default, then polish)
                ud = uid[:-2] + '-d'
                (W / 'final' / f'{ud}.input.txt').write_bytes((W / 'final' / f'{uid}.input.txt').read_bytes())
                (W / 'staged' / f'{ud}.csv').write_bytes((T / f'{n}.csv').read_bytes())
                jd = dict(j, input=f'{ud}.input.txt', output=f'{ud}.output.txt', flags=[], manifest=dict(j['manifest'], id=ud),
                          flags_note=j['flags_note'].replace('one more polish fq', 'one more default-flag fq'))
                tmp = W / 'final' / f'{ud}.job.tmp'; tmp.write_text(json.dumps(jd)); tmp.replace(W / 'final' / f'{ud}.job.json')
                log(f'SELF {n}: queued {ud} (default-flag fq of take-border-r35/{n}.csv, score {new!r})')
        # r28 03:27Z: our near files below the live bar but short of the rule, whose last polish gained more than 1e-9 of
        # side over its certified input, get one more polish (the 978 chase: 3.0e-9 and 2.0e-9 below takes, rule 3.13e-9).
        bars = json.load(open(W / 'bars.json'))
        for mp in sorted((T / 'near').glob('*.json'), key=lambda q: q.stat().st_mtime):
            if ('near', mp.name) in done: continue
            done.add(('near', mp.name))
            try: meta = json.load(open(mp)); fr = list(csv.DictReader(open(mp.with_suffix('.csv'))))
            except (OSError, ValueError): continue
            n = meta.get('n') if isinstance(meta, dict) else None
            if not isinstance(n, int): continue
            if len(fr) != n or 'flags' not in meta: continue
            hh = [.5 * (abs(math.cos(float(q['angle']))) + abs(math.sin(float(q['angle'])))) for q in fr]
            side = max(max(float(q[k]) + h for q, h in zip(fr, hh)) - min(float(q[k]) - h for q, h in zip(fr, hh)) for k in ('x', 'y'))
            gap = side - bars.get(str(n), 0); rule = math.sqrt(n) * 1e-10
            step = (meta['certified_before'] + 1) * math.sqrt(n) - side
            depth = mp.name.count('-ns')
            if not (-rule <= gap < 0 and step > 1e-9 and depth < 6): continue
            uid = mp.stem.split('-', 1)[1] + '-ns' + hashlib.sha256(repr(side).encode()).hexdigest()[:6]
            if (W / 'final' / f'{uid}.job.json').exists(): continue
            ss, AA = bs.normalize([(float(q['x']), float(q['y']), float(q['angle'])) for q in fr])
            bs.write_txt(str(W / 'final' / f'{uid}.input.txt'), ss, AA)
            (W / 'staged' / f'{uid}.csv').write_bytes(mp.with_suffix('.csv').read_bytes())
            note = f'near follow: one more polish fq from our certified near file {mp.name[:-5]}.csv ({gap:.3e} of side vs the live bar, last step {step:.3e})'
            j = dict(meta, input=f'{uid}.input.txt', output=f'{uid}.output.txt', certified_before=(side / math.sqrt(n)) - 1,
                     flags=list(bs.POLISH), loop=True, priority=-180, manifest=dict(meta['manifest'], id=uid),
                     flags_note=(meta.get('flags_note', '') + '; ' if meta.get('flags_note') else '') + note)
            tmp = W / 'final' / f'{uid}.job.tmp'; tmp.write_text(json.dumps(j)); tmp.replace(W / 'final' / f'{uid}.job.json')
            log(f'SELF near {n}: queued {uid} ({gap:.3e} of side vs the live bar, rule {rule:.3e}, last step {step:.3e})')
        tmp = W / 'sfeed.tmp'; tmp.write_text(json.dumps({'done': sorted([list(x) for x in done], key=repr), 'last': last})); tmp.replace(ix_file)
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(60)
log('sfeed35 finished by deadline')
