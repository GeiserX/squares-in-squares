"""Classfill round 34 controller (light, boxA).

Work, best measured yield first (brief round 34, items 6a, 6c, 6e, 8):
 1. own-family follows: every own certified find gets a 180 s invent lkick family run, plus one extra 180 s seed
    while it moves (round 32: 8 of 16 short follows moved).
 2. deep kicks of FRESH round 34 rows of other lanes: the lowest live row of an n, after its producer and backlog had
    their first 180 s follow (8 minutes, and no claim of another lane on that n in the last 1000 s): unprobed 900 s
    midm lkick,kick, two seeds (round 33: probes killed deep kicks; finds came on the second seed and at 872 s of 900).
    Held rows are never kicked here (6d: held deep-kick lists belong to border, twoshort, rebuild, quench).
Every start passes quench_walk.check (round-generic walker, regress controls passed at 01:31Z).
A running kick stops when another lane posts a row more than 1e-6 lower at its n (6e).
"""
import sys, time, shutil, math, subprocess, json, os, re
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common34 import *
sys.path.insert(0, str(S / 'take-classfill-r33/work'))
from light29 import load, side

ADMIT_DEEP = END - 20 * 60      # last 900 s admission 07:05Z
ADMIT_SHORT = END - 7 * 60      # last 180 s admission 07:18Z
STOP_AT = END + 8 * 60          # collect until 07:33Z
FRESH_AGE = 480
CLAIM_WINDOW = 1000
VENV = str(S / 'venv/bin/python')
state = read(W / 'cf-state.json', {}) or {}
state.setdefault('jobs', {})       # tag -> job
state.setdefault('collected', [])
state.setdefault('done_keys', [])  # "n:sha" already deep kicked (or refused)
state.setdefault('walk', {})       # sha -> walker summary
state.setdefault('chain', [])


def save():
    atom(W / 'cf-state.json', state)


def walk(path, mode='check', n=None):
    a = [VENV, '-I', str(W / 'walk34.py'), mode, str(path)] + ([str(n)] if n is not None else [])
    try:
        out = subprocess.run(['nice', '-n', '15'] + a, capture_output=True, text=True, timeout=600,
                             env=dict(os.environ, QUENCH_LIVE_ROUND='34')).stdout
        for line in out.splitlines():
            if line.startswith('WALK ') or line.startswith('POL '):
                return json.loads(line.split(' ', 1)[1])
    except Exception as e:
        return dict(clean=False, hits=['walker error ' + repr(e)], bad=True, why='walker error')
    return dict(clean=False, hits=['walker printed nothing'], bad=True, why='walker printed nothing')


def slots():
    """(waiting, active) per slot."""
    out = {}
    for host in dict(HOSTS):
        ls = cmd(['ssh', host, 'cd ' + ROOT + ' && ls queue/A queue/B queue/C 2>/dev/null; true'])
        cur = None
        res = {}
        for l in ls.splitlines():
            if l.startswith('queue/'):
                cur = l.split('/')[1].rstrip(':')
                res[cur] = [0, 0]
            elif cur and l.endswith('.json'):
                res[cur][0] += 1
            elif cur and l.endswith('.active'):
                res[cur][1] += 1
        for h, s in HOSTS:
            if h == host:
                out[(h, s)] = tuple(res.get(s, [0, 0]))
    return out


def lattice(P):
    import numpy as np
    aa = np.remainder(np.asarray(P)[:, 2] + math.pi / 4, math.pi / 2) - math.pi / 4
    tilted = np.abs(aa) > 1e-7
    return bool(tilted.any() and np.all(np.abs(np.abs(aa[tilted]) - math.pi / 4) < 1e-7))


def send(job, host, slot):
    job.setdefault('live_at_dispatch', bars()[1][job['n']])
    if job['search_method'] == 'module':
        job['wall'] = 900
    local = Path(job['input_snapshot'])
    cmd(['scp', '-q', str(local), host + ':' + ROOT + '/data/' + local.name])
    atom(W / 'jobs' / (job['tag'] + '.json'), job)
    cmd(['scp', '-q', str(W / 'jobs' / (job['tag'] + '.json')), host + ':' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.tmp'])
    cmd(['ssh', host, 'mv ' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.tmp ' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.json'])
    state['jobs'][job['tag']] = job
    save()
    note(f"START_QUEUE {host} {slot} {job['kind']} n{job['n']} {job['search_method']} {job['seconds']}s seed{job['seed']} "
         f"probe{'none' if job.get('probe_seconds') else '120'} {job['tag']}; log {ROOT}/logs/{job['tag']}.log; deadline 07:25Z")


def make_job(n, start, kind, seed, seconds, method, source, licence, start_score, parent=None):
    digest = sha(start)
    tag = 'y' + digest[:12] + 's' + str(seed)
    local = W / 'inputs' / f'{n}-{tag}.csv'
    shutil.copy2(start, local)
    assert sha(local) == digest
    j = dict(tag=tag, n=n, kind=kind, input='data/' + local.name, input_path=str(start), input_sha256=digest,
             input_snapshot=str(local), source=source, licence=licence, seed=seed, seconds=seconds,
             wall=seconds + 400, slack=0.0005, search_method=method, bar_input=True, kicks='0.02,0.04',
             priority=(-6 if kind.startswith('own') else 2), start_score=start_score, parent=parent, created_utc=now())
    if method == 'midm':
        j['probe_seconds'] = 100000  # unprobed: the run is never cut at 120 s
    return j


def claim_and_check(n, text):
    """Brief 6f: post the claim, wait 5 s, re-read, start only if no earlier claim of another lane for that n."""
    t0 = time.time()
    hand('all', 'claims n=%d %s' % (n, text))
    time.sleep(5)
    rivals = [l for t, l in claim_lines(n, t0 - CLAIM_WINDOW) if t <= t0 + 1]
    if rivals:
        hand('all', 'releases n=%d (an earlier claim of another lane: %s)' % (n, rivals[-1][:120]))
        note('CLAIM_RACE_RELEASE n%d %s' % (n, rivals[-1][:200]))
        return False
    return True


def collect():
    base, live, src = bars()
    take = own()
    for host in dict(HOSTS):
        local = W / host
        (local / 'out').mkdir(parents=True, exist_ok=True)
        try:
            cmd(['rsync', '-az', '--exclude', 'tmp/', '--exclude', 'fq-tmp/', host + ':' + ROOT + '/out/', str(local / 'out') + '/'], timeout=120)
            cmd(['rsync', '-az', host + ':' + ROOT + '/logs/', str(local / 'logs') + '/'], timeout=90)
        except Exception as e:
            note('RSYNC_DEFER ' + host + ' ' + repr(e)[:200])
            continue
        for d in list((local / 'out').glob('near-*')) + list((local / 'out').glob('final-*')):
            if not (d / 'DONE').exists() or d.name in state['collected']:
                continue
            tag = d.name.split('-', 1)[1]
            job = state['jobs'].get(tag)
            if not job:
                continue
            state['collected'].append(d.name)
            n = job['n']
            p = d / f'{n}.csv'
            meta = read(p.with_suffix('.json'), {}) or {}
            score = meta.get('finish_score')
            if score is None or job['kind'] == 'control':
                note(f'FINISH {host} {tag} n{n} kind {job["kind"]} no certified output' if score is None else f'FINISH_CONTROL {tag} score {score}')
                continue
            receipt = read(local / 'out' / ('finish-' + tag) / 'quench-receipt.json', {}) or {}
            near = T / 'near' / f'{n}-{tag}.csv'
            shutil.copy2(p, near)
            digest = sha(near)
            start_score = job.get('start_score')
            margin = live[n] - score
            note(f'FINISH {host} {tag} n{n} {job["kind"]} score {score!r} start {start_score!r} moved {(start_score or score) - score:.3e} '
                 f'live_margin {margin:.3e} quenched {meta.get("finish_quenched")} loop_complete {receipt.get("loop_complete")}')
            rec = dict(source='classfill r34 ' + job['kind'] + ' output of ' + job['search_method'] + ' ' + str(job['seconds']) + ' s seed ' + str(job['seed']) +
                       ('' if job['search_method'] == 'invent' else ' (unprobed)') + '; start ' + job['start_rec'] + '; ' + job['source'],
                       licence=job['licence'], output_sha256=digest, job=str(W / 'jobs' / (tag + '.json')),
                       receipt=str(local / 'out' / ('finish-' + tag) / 'quench-receipt.json'))
            atom(Path(str(near) + '.json'), rec)
            audit = meta.get('original_byte_audit') or {}
            if isinstance(audit, str):
                audit = {}
            ok = (score < live[n] - 1e-10 and score < base[n] - 1e-10 and meta.get('finish_quenched') and receipt.get('completed', 0) > 0
                  and receipt.get('loop_complete') and audit.get('passed') and audit.get('input_sha256') == sha(p))
            if ok and job.get('pubfirst'):
                pol = walk(near, 'pol', n)
                if pol.get('bad'):
                    note(f'PUBLIC_OUTPUT_REFUSED n{n} {pol.get("why")}')
                    ok = False
            if ok and (n not in take or score < float(take[n]['new']) - 1e-10):
                shutil.copy2(near, T / f'{n}.csv')
                source = rec['source'] + '; certified own output take-classfill-r34/near/' + near.name + ' (sha256 ' + digest + ')'
                take[n] = dict(zip(COL, [n, repr(base[n]), repr(score), repr(base[n] - score), source, job['licence']]))
                table(take)
                hand('all', f'certified n={n} score={score!r} gain={base[n]-score!r} (beyond live before: {live[n]-score:.3e}), {T}/{n}.csv; finesafe 2.2e-11, full fq loop done; start {job["input_path"]}')
                note(f'TAKE n{n} score {score!r} gain {base[n]-score:.3e}')
            # brief 8: a new geometry gain gets a 180 s family run, then one extra 180 s seed while it moves
            if score < live[n] - 1e-10 and meta.get('finish_quenched') and start_score is not None and start_score - score > 1e-10:
                state['chain'].append(dict(n=n, near=str(near), sha=digest, score=score, parent=tag, seed=job['seed'], licence=job['licence'], pubfirst=job.get('pubfirst', False)))
    # drop own rows passed by a peer
    for n, r in list(take.items()):
        if float(r['new']) >= live[n] - 1e-10:
            note(f'SUPERSEDED n{n} own {r["new"]} live {live[n]!r}')
            del take[n]
            (T / f'{n}.csv').unlink(missing_ok=True)
            table(take)
    save()


def stop_superseded():
    """6e: stop a running or queued kick when another lane posts a row more than 1e-6 lower at that n."""
    base, live, src = bars()
    for tag, j in state['jobs'].items():
        if j.get('stopped') or ('near-' + tag) in state['collected'] or j['kind'] == 'control':
            continue
        n = j['n']
        if live[n] < min(j['start_score'], j.get('live_at_dispatch', j['start_score'])) - 1e-6 and n in src:
            try:
                out = cmd(['ssh', j['host'], 'cd ' + ROOT + ' && ' + PY[j['host']] + ' killtag.py ' + j['slot'] + ' ' + tag])
            except Exception as e:
                out = repr(e)
            j['stopped'] = now()
            save()
            note(f'STOP_KICK n{n} {tag}: {src[n][0].name} posted {live[n]!r} < start {j["start_score"]!r} - 1e-6; {out.strip()[:200]}')


def health():
    for host, slot in HOSTS:
        rec = read(W / f'owned-{host}-{slot}.json', {})
        try:
            alive = cmd(['ssh', host, 'ps -p %d -o command= || true' % rec['pid']]).strip()
        except Exception as e:
            note('HEALTH_DEFER ' + host + ' ' + repr(e)[:120])
            continue
        if 'worker34.py' in alive or time.time() > END - 600:
            continue
        # re-queue an interrupted job, then restart the slot
        cmd(['ssh', host, "cd " + ROOT + " && find queue/" + slot + " -name '*.active' | while read f; do mv \"$f\" \"${f%.active}.json\"; done; rm -f active-" + slot + ".json; true"])
        out = cmd(['ssh', host, 'cd ' + ROOT + ' && nohup nice -n 5 ' + PY[host] + ' -u worker34.py ' + slot + ' >> logs/worker-' + slot + '.log 2>&1 < /dev/null & echo $!'])
        pid = int(out.strip().splitlines()[-1])
        atom(W / f'owned-{host}-{slot}.json', dict(pid=pid, host=host, slot=slot))
        note(f'RESTART_WORKER {host} {slot} old pid {rec.get("pid")} dead; new pid {pid}; interrupted job re-queued')


def free_slots():
    s = slots()
    return [k for k, (w, a) in sorted(s.items(), key=lambda kv: kv[1]) if w + a == 0], s


def admit_chain():
    if time.time() > ADMIT_SHORT:
        return
    base, live, src = bars()
    keep = []
    for c in state['chain']:
        n = c['n']
        if live[n] < c['score'] - 1e-10:
            note(f'CHAIN_DROP n{n}: a peer is lower ({live[n]!r})')
            continue
        free, sl = free_slots()
        if not free:
            # own follows jump the queue (priority -6 runs before queued deep-kick seeds)
            free = [k for k, (w, a) in sorted(sl.items(), key=lambda kv: kv[1][0] + kv[1][1])][:1]
        if claim_lines(n, time.time() - CLAIM_WINDOW):
            note(f'CHAIN_YIELD n{n}: another lane claimed n in the last {CLAIM_WINDOW} s')
            continue
        start = Path(c['near'])
        rec = 'take-classfill-r34/near/' + start.name + ' (sha256 ' + c['sha'] + ')'
        seeds = [c['seed'] + 11] + ([c['seed'] + 97] if len(free) > 1 else [])
        if not claim_and_check(n, 'sha256 %s, own-family-follow invent_rest lkick 180 s seeds %s; %s' % (c['sha'][:16], seeds, start)):
            continue
        for k, seed in enumerate(seeds):
            j = make_job(n, start, 'own-family-follow' if k == 0 else 'own-extra-family-seed', seed, 180, 'invent',
                         'classfill r34 own find ' + c['parent'], c['licence'], c['score'], parent=c['parent'])
            j['start_rec'] = rec
            j['pubfirst'] = c.get('pubfirst', False)
            h, s = free[k] if k < len(free) else free[0]
            j['host'], j['slot'] = h, s
            send(j, h, s)
    state['chain'] = keep
    save()


def fresh_files():
    """Main 01:39Z items (3) and (4): fresh r34 rows of other lanes (take.tsv) and fresh near endpoints of the
    fresh-geometry lanes, at the lowest live side."""
    base, live, src = bars()
    out = []
    for n, (lanedir, v) in src.items():
        p = lanedir / f'{n}.csv'
        if n > 40 and v < base[n] - 1e-10 and p.is_file():
            out.append((n, p, lanedir, 'fresh-row-family'))
    nc = state.setdefault('nearcache', {})
    for d in S.glob('take-*-r34'):
        if d == T or not d.name.startswith(('take-forensics-', 'take-invent-', 'take-k123-', 'take-backlog-', 'take-rebuild-')):
            continue
        for p in (d / 'near').glob('*.csv'):
            m = re.match(r'(\d+)', p.name)
            if not m:
                continue
            n = int(m.group(1))
            if n <= 40 or n > 1000:
                continue
            k = str(p) + ':' + str(p.stat().st_mtime_ns)
            if k not in nc:
                try:
                    P = load(p, {n}).get(n)
                    nc[k] = side(P) if P is not None else 1e9
                except Exception:
                    nc[k] = 1e9
            if nc[k] <= (1 + live[n]) * math.sqrt(n) + 1e-10 and live[n] < base[n] - 1e-10:
                out.append((n, p, d, 'fresh-endpoint-family'))  # 04:40Z: ties of the held side are held copies (0 of 10 moved)
    return out, base, live, src


def admit_fresh():
    """180 s invent lkick family run (one seed; the chain adds a family run and one extra seed while it moves).
    Backlog keeps the first follow of fresh rows: we start only when no other lane claimed n in the last 1000 s and
    the file is FRESH_AGE old, so a row backlog took is never run twice."""
    if time.time() > ADMIT_SHORT:
        return
    free, _ = free_slots()
    if not free:
        return
    files, base, live, src = fresh_files()
    mine = own()
    for n, p, lanedir, kind in sorted(files, key=lambda x: -(base[x[0]] - live[x[0]])):
        free, _ = free_slots()
        if not free:
            return
        if n in mine and float(mine[n]['new']) <= live[n]:
            continue
        if time.time() - p.stat().st_mtime < FRESH_AGE:
            continue
        digest = sha(p)
        key = '%d:%s' % (n, digest)
        if key in state['done_keys']:
            continue
        fam = 'fam:%d:%r' % (n, live[n])
        if fam in state['done_keys']:
            continue  # one family run per n and live value: near copies of the same row repeat it
        if claim_lines(n, time.time() - CLAIM_WINDOW):
            continue
        P = load(p, {n}).get(n)
        if P is None:
            continue
        v = live[n]
        if side(P) > (1 + v) * math.sqrt(n) + 1e-10:
            continue
        state['done_keys'].append(key)
        if lattice(P):
            note(f'LATTICE_SKIP n{n} {p}')
            continue
        hit = withdrawn_hit(digest)
        if hit:
            note(f'WITHDRAW_SKIP n{n} {hit[:160]}')
            continue
        snap = W / 'starts' / f'{n}-{lanedir.name}-{digest[:16]}.csv'
        shutil.copy2(p, snap)
        if sha(snap) != digest:
            continue
        row = next((r for r in rows(lanedir / 'take.tsv') if r.get('n') == str(n)), {}) if kind == 'fresh-row-family' else {}
        side_recs = [read(q, {}) for q in (Path(str(p) + '.json'), p.with_suffix('.json'), Path(str(p) + '.source.json'))]
        side_recs = [x for x in side_recs if x]
        srctext = row.get('source', '') if row else json.dumps(side_recs)[:3000]
        lic = row.get('licence', '') if row else next((str(x.get('licence')) for x in side_recs if isinstance(x, dict) and x.get('licence')), 'inherited terms in the producer record of ' + str(p))
        atom(Path(str(snap) + '.json'), dict(source='byte copy of ' + str(p) + ' taken ' + now() + '; producer record: ' + srctext,
                                             licence=lic, copy_of=str(p), sha256=digest))
        w = state['walk'].get(digest) or walk(snap)
        state['walk'][digest] = dict(clean=w.get('clean'), hits=w.get('hits', [])[:5], pubfirst=w.get('pubfirst'))
        save()
        if not w.get('clean'):
            note(f'ANCESTRY_REFUSED n{n} {p} {w.get("hits", [])[:3]}')
            continue
        if sha(p) != digest or claim_lines(n, time.time() - CLAIM_WINDOW):
            note(f'FRESH_YIELD n{n} {p}: changed bytes or another lane claimed n during the walk')
            continue
        free, _ = free_slots()
        if not free:
            state['done_keys'].remove(key)
            return
        seed = 3401 + n % 97
        if not claim_and_check(n, 'sha256 %s, %s invent_rest lkick 180 s seed %d (one extra seed only while it moves) of %s (lowest live side)' % (digest[:16], kind, seed, p)):
            continue
        state['done_keys'].append(fam)
        rec = 'take-classfill-r34/work/starts/' + snap.name + ' (sha256 ' + digest + '), a byte copy of ' + str(p).replace(str(S) + '/', '')
        j = make_job(n, snap, kind, seed, 180, 'invent', 'fresh r34 geometry of ' + lanedir.name + ': ' + srctext[:3000], lic, v)
        j['start_rec'] = rec
        j['pubfirst'] = bool(w.get('pubfirst'))
        h, s2 = free[0]
        j['host'], j['slot'] = h, s2
        send(j, h, s2)
        save()


HELD = S / 'gather/round33-2026-11-17a.csv'

MODQ = None


def cutcheck(paths):
    out = subprocess.run([VENV, '-I', str(W / 'modcheck34.py'), 'cut'] + [str(x) for x in paths], capture_output=True, text=True, timeout=300).stdout
    res = {}
    for line in out.splitlines():
        if line.startswith('CUT '):
            d = json.loads(line[4:])
            res[d['path']] = d
    return res


def admit_module():
    """Main 01:39Z item (2): native far-zone cuts (module33 kind sweep, 90 s per far zone, then the full fq loop)
    on changed inputs with two flush arms: the rows round 33 a changed, then fresh r34 rows and near files
    within 3e-3 of the live side. One job per input bytes."""
    if time.time() > ADMIT_DEEP:
        return
    free, _ = free_slots()
    if not free:
        return
    base, live, src = bars()
    cc = state.setdefault('cutcache', {})
    pool = []
    for n in (805, 812, 995, 998):
        pool.append((n, W / 'held34' / f'{n}.csv', 'held'))
    files, _, _, _ = fresh_files()
    for n, p, lanedir, kind in files:
        pool.append((n, p, lanedir.name))
    for d in S.glob('take-*-r34'):
        if d == T or not d.name.startswith(('take-forensics-', 'take-invent-', 'take-k123-', 'take-backlog-', 'take-rebuild-', 'take-twoshort-', 'take-border-', 'take-quench-')):
            continue
        for p in (d / 'near').glob('*.csv'):
            m = re.match(r'(\d+)', p.name)
            if not m or not (40 < int(m.group(1)) <= 1000):
                continue
            n = int(m.group(1))
            k = str(p) + ':' + str(p.stat().st_mtime_ns)
            nc = state.setdefault('nearcache', {})
            if k not in nc:
                try:
                    P = load(p, {n}).get(n); nc[k] = side(P) if P is not None else 1e9
                except Exception:
                    nc[k] = 1e9
            if nc[k] <= (1 + live[n]) * math.sqrt(n) + 3e-3:
                pool.append((n, p, d.name))
    need = [str(p) for n, p, _ in pool if str(p) + ':' + str(p.stat().st_mtime_ns) not in cc]
    if need:
        res = cutcheck(need[:200])
        for q in need[:200]:
            cc[str(q) + ':' + str(Path(q).stat().st_mtime_ns)] = bool(res.get(q, {}).get('ok'))
        save()
    for n, p, origin in pool:
        if not cc.get(str(p) + ':' + str(p.stat().st_mtime_ns)):
            continue
        digest = sha(p)
        key = 'module:%d:%s' % (n, digest)
        if key in state['done_keys']:
            continue
        free, _ = free_slots()
        if not free:
            return
        if claim_lines(n, time.time() - CLAIM_WINDOW):
            continue
        state['done_keys'].append(key)
        if origin == 'held':
            hs, hl = held_source(n)
            heldsha = 'bee523139df8fe0ec1e3fba83cb46d8cffac2a47995842ff4a97a1b4b7d45369'
            srctext = f'held n = {n} of round 33 a; submitted gather/round33-2026-11-17a.csv sha256 {heldsha}; {hs}'
            lic = 'our own submitted packing; inherited terms: ' + hl
            snap = W / 'starts' / f'{n}-held33a.csv'
            if not snap.exists():
                shutil.copy2(p, snap)
            atom(Path(str(snap) + '.json'), dict(source=srctext, licence=lic, held=str(HELD), n=n, sha256=digest))
            pub = False
        else:
            snap = W / 'starts' / f'{n}-{origin}-{digest[:16]}.csv'
            shutil.copy2(p, snap)
            sides = [read(q, {}) for q in (Path(str(p) + '.json'), p.with_suffix('.json'), Path(str(p) + '.source.json'))]
            row = next((r for r in rows(p.parent / 'take.tsv') if r.get('n') == str(n)), {}) if p.parent.name.startswith('take-') and re.fullmatch(r'\d+\.csv', p.name) else {}
            srctext = row.get('source') or json.dumps([x for x in sides if x])[:3000]
            lic = row.get('licence') or next((str(x.get('licence')) for x in sides if isinstance(x, dict) and x.get('licence')), 'inherited terms in the producer record of ' + str(p))
            atom(Path(str(snap) + '.json'), dict(source='byte copy of ' + str(p) + ' taken ' + now() + '; producer record: ' + srctext, licence=lic, copy_of=str(p), sha256=digest))
            w = state['walk'].get(digest) or walk(snap)
            state['walk'][digest] = dict(clean=w.get('clean'), hits=w.get('hits', [])[:5], pubfirst=w.get('pubfirst'))
            save()
            if not w.get('clean'):
                note(f'ANCESTRY_REFUSED module n{n} {p} {w.get("hits", [])[:3]}')
                continue
            pub = bool(w.get('pubfirst'))
        if not claim_and_check(n, 'sha256 %s, native far-zone cut (module33 kind sweep of each far zone, then the full fq loop; no kick) of %s' % (digest[:16], p)):
            continue
        rec = 'take-classfill-r34/work/starts/' + snap.name + ' (sha256 ' + digest + ')' + ('' if origin == 'held' else ', a byte copy of ' + str(p).replace(str(S) + '/', ''))
        try:
            P = load(p, {n}).get(n); sv = side(P) / math.sqrt(n) - 1
        except Exception:
            sv = live[n]
        j = make_job(n, snap, 'native-far-zone-cut', 4401, 180, 'module', srctext[:3000], lic, sv)
        j['start_rec'] = rec
        j['pubfirst'] = pub
        h, s2 = free[0]
        j['host'], j['slot'] = h, s2
        send(j, h, s2)
        save()


HAND_RX = re.compile(r'->\s*[\w,]*classfill[\w,]*:.*?\bhands?\b.*?\bdeep kick', re.I)


def held_source(n):
    import glob
    best = None
    for p in glob.glob(str(R / 'results/round*-best-*.tsv')):
        m = re.search(r'round(\d+)-best', p)
        if not m or int(m.group(1)) > 33:
            continue
        for r in rows(p):
            if r.get('n') == str(n) and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), p, r)
    if best is None:
        return 'held baseline', 'held baseline'
    return ('results/' + Path(best[1]).name + ' n=' + str(n) + ': ' + best[2].get('source', ''), best[2].get('licence', ''))


def admit_handed():
    """Rows a deep-kick owner hands to classfill by a handoff line ('<lane> -> classfill: hands ... deep kick n=N ...').
    One owner per row (6d) stays true: the owner gives the row away explicitly."""
    if time.time() > ADMIT_DEEP:
        return
    base, live, src = bars()
    done_n = {int(k.split(':')[1]) for k in state['done_keys'] if k.startswith('hand:') or k.startswith('handn:')}
    pend = {}
    for l in HANDOFF.read_text(errors='replace').splitlines():
        if ' classfill -> ' in l or not HAND_RX.search(l):
            continue
        tail = l[l.lower().find('deep kick'):]
        ns = [int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', tail)]
        m0 = re.search(r'\bn\s*=\s*((?:\d+\s+)+\d+)', tail)
        if m0:
            ns += [int(x) for x in m0.group(1).split()]
        for n in ns:
            if n <= 40 or n in done_n:
                continue
            one = bool(re.search(r'one seed is its second', l))
            if n not in pend or (pend[n][0] == 2 and one):
                pend[n] = (1 if one else 2, l)
    gap = {}
    for r in rows(S / 'main-r17/gap-by-n.tsv'):
        try:
            gap[int(r['n'])] = base[int(r['n'])] - (float(r['board_L']) / math.sqrt(int(r['n'])) - 1)
        except (ValueError, KeyError):
            pass
    for n in sorted(pend, key=lambda k: -gap.get(k, 0.0)):
        nseeds, l = pend[n]
        if True:
            hk = 'handn:%d' % n
            free, _ = free_slots()
            if not free:
                return
            if n in src:
                state['done_keys'].append(hk)
                note(f'HANDED_SKIP n{n}: a fresh r34 row is now the lowest live ({src[n][0].name}); the fresh path takes it')
                continue
            import csv as _csv
            rs = [r for r in _csv.DictReader(open(HELD)) if r['n'] == str(n)]
            snap = W / 'starts' / f'{n}-held33a.csv'
            with snap.open('w', newline='') as f:
                w = _csv.DictWriter(f, fieldnames=list(rs[0].keys()))
                w.writeheader()
                w.writerows(rs)
            digest = sha(snap)
            hs, hl = held_source(n)
            heldsha = 'bee523139df8fe0ec1e3fba83cb46d8cffac2a47995842ff4a97a1b4b7d45369'
            src_text = f'held n = {n} of round 33 a; submitted gather/round33-2026-11-17a.csv sha256 {heldsha}; {hs}'
            atom(Path(str(snap) + '.json'), dict(source=src_text, licence='our own submitted packing; inherited terms: ' + hl, held=str(HELD), n=n, sha256=digest))
            seeds = [3611 + n % 83, 3739 + n % 79][:nseeds]
            state['done_keys'].append(hk)
            if not claim_and_check(n, 'sha256 %s, deep kick 900 s midm_scan lkick,kick UNPROBED (probe 0 s), seeds %s, of the held round 33 a row, handed to classfill by: %s' % (digest[:16], seeds, l[:90])):
                continue
            rec = 'take-classfill-r34/work/starts/' + snap.name + ' (sha256 ' + digest + '), the exact rows of n=' + str(n) + ' of gather/round33-2026-11-17a.csv'
            for k, seed in enumerate(seeds):
                j = make_job(n, snap, 'handed-held-deep-kick', seed, 900, 'midm', src_text, 'our own submitted packing; inherited terms: ' + hl, base[n])
                j['start_rec'] = rec
                j['pubfirst'] = False
                h, s = free[k] if k < len(free) else free[0]
                j['host'], j['slot'] = h, s
                send(j, h, s)
            save()


if __name__ == '__main__':
    (W / 'controller-pid').write_text(str(os.getpid()))
    note('START controller cf34.py pid %d log work/cf34.log; deep admissions to 07:05Z, short to 07:18Z, collect to 07:33Z' % os.getpid())
    last_bar = 0
    while time.time() < STOP_AT and not (W / 'STOP').exists():
        try:
            collect()
            if time.time() - last_bar > 120:
                writebar()
                last_bar = time.time()
            stop_superseded()
            health()
            admit_chain()
            admit_fresh()
            admit_module()
            admit_handed()
            atom(W / 'heartbeat.json', dict(time=now(), jobs=len(state['jobs']), collected=len(state['collected']), take=len(own())))
        except Exception as e:
            import traceback
            note('CONTROLLER_ERROR ' + repr(e)[:300])
            traceback.print_exc()
            sys.stdout.flush()
        time.sleep(40)
    collect()
    note('CONTROLLER_STOP')
