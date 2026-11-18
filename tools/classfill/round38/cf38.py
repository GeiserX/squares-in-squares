"""Classfill round 38 controller (light, boxA). Built from the round 37 controller cf37.py.

Work (round 38 brief, overrides 6a to 6v and 8):
 1. k123 near donors (6d, 8): only donors within 1e-7 of score above bar38 (and not below it by 1e-10), held share
    at 1e-3 against the held round 37 a row under 0.5, an unprobed geometry (share at 1e-3 under 0.9 with every
    900 s seed of ours of r35 to r38 at that n and every donor another lane claimed by bytes), no claim by another
    lane, and an n where no donor fell back to the held geometry (rounds 36 to 38) and where two donor outputs did not
    end at one endpoint. ONE unprobed 900 s seed per geometry. No legs, no held-row seeds, no fresh-row follows.
 2. own follows BEFORE the certified line (6b, 8): a find that passes every number gate is held (no find line, no
    take row) while two 180 s invent lkick follows run from it; a follow that improves the best by 1e-8 or more gets
    one more pair, at most three rounds. Then the best of the find and its follows is walked and published.
Workers start on demand and leave after 10 idle minutes (6h: no retired work refills a slot).
Stop and skip rule (6q): stop a kick, or skip a start, when the live row of its n is more than 1e-6 below
min(own start, bar). Every record path is absolute (6e). Every published row gets a detached full walk (6m).
"""
import sys, time, shutil, math, subprocess, json, os, re
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from common38 import *
sys.path.insert(0, str(S / 'take-classfill-r33/work'))
from light29 import load, side

ADMIT_DEEP = END - 90 * 60      # last 900 s admission 12:15Z: seed, follows and walk end before the 12:45Z walk start (6m)
ADMIT_SHORT = END - 65 * 60     # last 180 s own follow admission 12:40Z; a later find publishes without follows
STOP_AT = END + 8 * 60          # collect until 13:53Z
FOLLOW_ROUNDS = 3
IDLE_EXIT = 600
CLAIM_WINDOW = 1000
VENV = str(S / 'venv/bin/python')
WALKMAX = 3
FULLMAX = 2
FULLCAP = 100000
state = read(W / 'cf-state.json', {}) or {}
state.setdefault('jobs', {})
state.setdefault('collected', [])
state.setdefault('done_keys', [])
state.setdefault('walk', {})
state.setdefault('chain', [])
state.setdefault('pending', [])    # outputs that passed every number gate and wait for their walk
state.setdefault('full', {})       # n -> {sha, started, result}
state.setdefault('hold', {})       # n -> held finds waiting for their own follows (6b)
state.setdefault('endpoints', {})  # n -> donor output scores (6d endpoint stop)
PROCS = {}


def save():
    atom(W / 'cf-state.json', state)


def should_stop(start, bar, live):
    """Rule 6i: stop (or skip) when the live row is more than 1e-6 below min(own start, bar)."""
    return live < min(start, bar) - 1e-6


def stop_rule_controls():
    bar = 0.02
    cases = [('donor above bar, live at bar', bar + 3e-5, bar, False),
             ('donor above bar, live 2e-6 below bar', bar + 3e-5, bar - 2e-6, True),
             ('held start, live 2e-6 below', bar, bar - 2e-6, True),
             ('held start alone', bar, bar, False)]
    res = [(name, should_stop(s, bar, l), want) for name, s, l, want in cases]
    ok = all(a == b for _, a, b in res)
    return ok, res


# ---------------------------------------------------------------- walks (detached, rule 6g, 6h)
def walk_async(path, cap=3000, mode='check', n=None, limit=WALKMAX):
    digest = sha(path)
    key = f'{digest[:24]}-{mode}-{cap}'
    out = W / 'walkres' / (key + '.json')
    r = read(out)
    if r is not None:
        return r
    p = PROCS.get(key)
    if p is not None:
        if p.poll() is None:
            return None
        del PROCS[key]
        r = read(out)
        return r if r is not None else dict(clean=False, bad=True, hits=['walker printed nothing'], why='walker printed nothing')
    running = sum(1 for k, q in PROCS.items() if q.poll() is None and k.endswith('-' + str(cap)) == key.endswith('-' + str(cap)))
    if running >= limit:
        return None
    if subprocess.run(['pgrep', '-f', str(out)], capture_output=True).returncode == 0:
        return None  # a walk left by an earlier controller still writes this record
    a = ['nice', '-n', '15', VENV, '-I', str(W / 'walk38.py'), mode, str(path), str(out), str(cap)] + ([str(n)] if n is not None else [])
    PROCS[key] = subprocess.Popen(a, stdout=subprocess.DEVNULL, stderr=open(W / 'walkres' / (key + '.err'), 'w'),
                                  env=dict(os.environ, QUENCH_LIVE_ROUND='38'), start_new_session=True)
    return None


def eff_clean(w, n):
    if w.get('clean'):
        return True
    hits = w.get('hits') or []
    if not hits:
        return False
    for h in hits:
        m = PIN_RX.search(h)
        if not (m and int(m.group(1)) != n):
            return False
    return True


def slots():
    out = {}
    for host in dict(HOSTS):
        ls = cmd(['ssh', host, 'cd ' + ROOT + ' && ls ' + ' '.join('queue/' + s for h, s in HOSTS if h == host) + ' 2>/dev/null; true'])
        cur = None
        res = {}
        mine = [s for h, s in HOSTS if h == host]
        if len(mine) == 1:
            cur = mine[0]
            res[cur] = [0, 0]
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


def worker_alive(host, slot):
    rec = read(W / f'owned-{host}-{slot}.json', {}) or {}
    if not rec.get('pid'):
        return False
    alive = cmd(['ssh', host, 'ps -p %d -o command= || true' % rec['pid']]).strip()
    return 'worker38.py' in alive


def start_worker(host, slot, why):
    cmd(['ssh', host, "cd " + ROOT + " && mkdir -p queue/" + slot + " && find queue/" + slot + " -name '*.active' | while read f; do mv \"$f\" \"${f%.active}.json\"; done; rm -f active-" + slot + ".json; true"])
    out = cmd(['ssh', host, 'cd ' + ROOT + ' && nohup nice -n 5 ' + PY[host] + ' -u worker38.py ' + slot + ' >> logs/worker-' + slot + '.log 2>&1 < /dev/null & echo $!'])
    pid = int(out.strip().splitlines()[-1])
    atom(W / f'owned-{host}-{slot}.json', dict(pid=pid, host=host, slot=slot, started=now()))
    note(f'START_WORKER {host} {slot} pid{pid} {ROOT}/worker38.py log {ROOT}/logs/worker-{slot}.log deadline 13:45Z ({why})')


def send(job, host, slot):
    job.setdefault('live_at_dispatch', bars()[1][job['n']])
    local = Path(job['input_snapshot'])
    cmd(['scp', '-q', str(local), host + ':' + ROOT + '/data/' + local.name])
    atom(W / 'jobs' / (job['tag'] + '.json'), job)
    cmd(['scp', '-q', str(W / 'jobs' / (job['tag'] + '.json')), host + ':' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.tmp'])
    cmd(['ssh', host, 'mv ' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.tmp ' + ROOT + '/queue/' + slot + '/' + job['tag'] + '.json'])
    if not worker_alive(host, slot):
        start_worker(host, slot, 'on demand for ' + job['tag'])
    state['jobs'][job['tag']] = job
    _SL[1] = None
    save()
    note(f"START_QUEUE {host} {slot} {job['kind']} n{job['n']} {job['search_method']} {job['seconds']}s seed{job['seed']} "
         f"probe{'none' if job.get('probe_seconds') else '120'} {job['tag']}; log {ROOT}/logs/{job['tag']}.log; deadline 13:45Z")


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
    if method in ('midm', 'nearmidm'):
        j['probe_seconds'] = 100000  # unprobed: the run is never cut at 120 s
    return j


def claim_and_check(n, text, since=None, digest=None, deep=False):
    """6s: post the claim, wait 5 s, re-read, start only if no earlier claim of another lane for that n (for a fresh
    row: for those bytes, and for a deep seed: a 900 s claim on those bytes)."""
    t0 = time.time()
    hand('all', 'claims n=%d %s' % (n, text))
    time.sleep(5)
    if digest is not None:
        l = other_claim_on_bytes(digest, t0 - CLAIM_WINDOW, deep=deep)
        rivals = [l] if l and (ltime(l) or 0) <= t0 + 1 else []
    elif since is not None:
        rivals = [l for t, l in rival_claims(n, since, t0 + 1)]
    else:
        rivals = [l for t, l in claim_lines(n, t0 - CLAIM_WINDOW) if t <= t0 + 1]
    if rivals:
        hand('all', 'releases n=%d (an earlier claim of another lane: %s)' % (n, rivals[-1][:120]))
        note('CLAIM_RACE_RELEASE n%d %s' % (n, rivals[-1][:200]))
        return False
    return True


_SL = [0.0, None]


def free_slots():
    """Slot occupancy, cached 20 s (each read is three ssh calls; per-donor reads made one loop take 4 minutes)."""
    if _SL[1] is None or time.time() - _SL[0] > 20:
        _SL[1] = slots()
        _SL[0] = time.time()
    s = _SL[1]
    return [k for k, (w, a) in sorted(s.items(), key=lambda kv: kv[1]) if w + a == 0], s


# ---------------------------------------------------------------- collect and publish
def running_jobs(n=None, kinds=None):
    out = []
    for t, j in state['jobs'].items():
        if j.get('stopped') or ('near-' + t) in state['collected'] or ('final-' + t) in state['collected'] or j.get('dead'):
            continue
        if (n is None or j['n'] == n) and (kinds is None or j['kind'] in kinds):
            out.append((t, j))
    return out


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
        # a job whose worker wrote a status file but no near/final dir finished without output
        for st in (local / 'out').glob('*-status.json'):
            tag = st.name[:-len('-status.json')]
            job = state['jobs'].get(tag)
            if not job or job.get('dead') or ('near-' + tag) in state['collected'] or ('final-' + tag) in state['collected']:
                continue
            if not (local / 'out' / ('near-' + tag) / 'DONE').exists() and not (local / 'out' / ('final-' + tag) / 'DONE').exists():
                if time.time() - st.stat().st_mtime > 120:
                    job['dead'] = now()
                    note(f'FINISH {host} {tag} n{job["n"]} kind {job["kind"]} no output dir (returncode {(read(st, {}) or {}).get("returncode")})')
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
            if score is None:
                note(f'FINISH {host} {tag} n{n} kind {job["kind"]} no certified output')
                continue
            receipt = read(local / 'out' / ('finish-' + tag) / 'quench-receipt.json', {}) or {}
            near = T / 'near' / f'{n}-{tag}.csv'
            shutil.copy2(p, near)
            digest = sha(near)
            start_score = job.get('start_score')
            margin = live[n] - score
            moved = (start_score or score) - score
            note(f'FINISH {host} {tag} n{n} {job["kind"]} score {score!r} start {start_score!r} moved {moved:.3e} '
                 f'live_margin {margin:.3e} bar_margin {base[n] - score:.3e} quenched {meta.get("finish_quenched")} loop_complete {receipt.get("loop_complete")}')
            rec = dict(source='classfill r38 ' + job['kind'] + ' output of ' + job['search_method'] + ' ' + str(job['seconds']) + ' s seed ' + str(job['seed']) +
                       ('' if job['search_method'] == 'invent' else ' (unprobed)') + '; start ' + job['start_rec'] + '; ' + job['source'],
                       licence=job['licence'], output_sha256=digest, job=str(W / 'jobs' / (tag + '.json')),
                       receipt=str(W / host / 'out' / ('finish-' + tag) / 'quench-receipt.json'))
            if not Path(rec['receipt']).exists():
                del rec['receipt']
            atom(Path(str(near) + '.json'), rec)
            audit = meta.get('original_byte_audit') or {}
            if isinstance(audit, str):
                audit = {}
            ok = (score < live[n] - 1e-10 and score < base[n] - 1e-10 and meta.get('finish_quenched') and receipt.get('completed', 0) > 0
                  and receipt.get('loop_complete') and audit.get('passed') and audit.get('input_sha256') == sha(p))
            if job['kind'] == 'donor-unprobed':
                ep = state['endpoints'].setdefault(str(n), [])
                # 6d: a donor that ends within 1e-10 of the bar fell back to the held geometry; two donors at one endpoint
                if abs(base[n] - score) < 1e-10 and ('basin:%d' % n) not in state['done_keys']:
                    state['done_keys'].append('basin:%d' % n)
                    note(f'BASIN n{n}: donor output {base[n] - score:.3e} from the bar; every further donor at n skipped (6d)')
                elif any(abs(v - score) < 1e-10 for v in ep) and ('basin:%d' % n) not in state['done_keys']:
                    state['done_keys'].append('basin:%d' % n)
                    note(f'ENDPOINT n{n}: a second donor ended at {score!r}; every further donor at n skipped (6d)')
                ep.append(score)
            if not ok:
                continue
            hold = state['hold'].setdefault(str(n), dict(cands=[], rounds=0, best=None))
            cand = dict(n=n, near=str(near), sha=digest, score=score, tag=tag, pubfirst=bool(job.get('pubfirst')), seed=job['seed'],
                        licence=job['licence'], source=rec['source'], input_path=job['input_path'], t=now())
            hold['cands'].append(cand)
            prev = hold['best']
            note(f'HELD_FIND n{n} {near.name}: {base[n] - score:.3e} below bar38, {live[n] - score:.3e} below live; passed every number gate; '
                 f'held for own follows before the certified line (6b)')
            improved = prev is None or score < prev - 1e-8
            if prev is None or score < prev:
                hold['best'] = score
            if improved and hold['rounds'] < FOLLOW_ROUNDS and time.time() < ADMIT_SHORT and moved > 1e-10:
                state['chain'].append(dict(n=n, near=str(near), sha=digest, score=score, parent=tag, seed=job['seed'], licence=job['licence'],
                                           pubfirst=job.get('pubfirst', False), source=job['source']))
                hold['rounds'] += 1
    # release held finds whose follows ended: the best candidate goes to the walk and publish queue
    for k, hold in list(state['hold'].items()):
        n = int(k)
        if any(c['n'] == n for c in state['chain']) or running_jobs(n, ('own-family-follow', 'own-extra-family-seed')):
            continue
        if not hold['cands']:
            del state['hold'][k]
            continue
        best = min(hold['cands'], key=lambda c: c['score'])
        state['pending'].append(best)
        note(f'RELEASE n{n}: best of {len(hold["cands"])} held finds after {hold["rounds"]} follow rounds: {Path(best["near"]).name} score {best["score"]!r}; walk next')
        del state['hold'][k]
    for n, r in list(take.items()):
        if float(r['new']) >= live[n] - 1e-10:
            note(f'SUPERSEDED n{n} own {r["new"]} live {live[n]!r}')
            del take[n]
            (T / f'{n}.csv').unlink(missing_ok=True)
            table(take)
    save()


def publish():
    base, live, src = bars()
    take = own()
    keep = []
    for c in state['pending']:
        n, near = c['n'], Path(c['near'])
        if c['score'] >= live[n] - 1e-10 or (n in take and c['score'] >= float(take[n]['new']) - 1e-10):
            note(f'PENDING_DROP n{n} {near.name}: no longer below live ({live[n]!r}) or own take')
            continue
        w = walk_async(near)
        if w is None:
            keep.append(c)
            continue
        if not eff_clean(w, n):
            note(f'OUTPUT_WALK_REFUSED n{n} {near.name} files {w.get("files")} capped {w.get("capped")} {str(w.get("hits", [])[:3])[:300]}')
            continue
        if c['pubfirst']:
            pol = walk_async(near, cap=0, mode='pol', n=n)
            if pol is None:
                keep.append(c)
                continue
            if pol.get('bad'):
                note(f'PUBLIC_OUTPUT_REFUSED n{n} {pol.get("why")}')
                continue
        shutil.copy2(near, T / f'{n}.csv')
        if sha(T / f'{n}.csv') != c['sha']:
            keep.append(c)
            continue
        source = c['source'] + '; certified own output ' + str(near) + ' (sha256 ' + c['sha'] + ')'
        take[n] = dict(zip(COL, [n, repr(base[n]), repr(c['score']), repr(base[n] - c['score']), source, c['licence']]))
        table(take)
        hand('all', f'certified n={n} score={c["score"]!r} gain={base[n]-c["score"]!r} (beyond live before: {live[n]-c["score"]:.3e}), {T}/{n}.csv sha256 {c["sha"]}; '
                    f'finesafe 2.2e-11, full fq loop done, own 180 s follows done (6b); walk clean files {w.get("files")} capped {w.get("capped")} (cap {w.get("cap")}), full-cap walk started; start {c["input_path"]}')
        note(f'TAKE n{n} score {c["score"]!r} gain {base[n]-c["score"]:.3e} walk files {w.get("files")} capped {w.get("capped")}')
        state['full'][str(n)] = dict(sha=c['sha'], started=now(), result=None)
    state['pending'] = keep
    save()


def full_walks():
    """6g: every take row gets a detached walk at cap 100000; a refusal takes the row out at once."""
    take = own()
    for k, f in state['full'].items():
        n = int(k)
        if n not in take or f.get('result') is not None:
            continue
        p = T / f'{n}.csv'
        if not p.exists() or sha(p) != f['sha']:
            continue
        w = walk_async(p, cap=FULLCAP, limit=FULLMAX)
        if w is None:
            continue
        f['result'] = dict(clean=eff_clean(w, n), files=w.get('files'), capped=w.get('capped'), hits=(w.get('hits') or [])[:5], t=now())
        note(f'FULL_WALK n{n} clean {f["result"]["clean"]} files {w.get("files")} capped {w.get("capped")} hits {str(w.get("hits", [])[:2])[:200]}')
        if not f['result']['clean']:
            del take[n]
            p.unlink(missing_ok=True)
            table(take)
            hand('all', f'withdraws n={n} sha256 {f["sha"]}: the full-cap walk refuses it ({str(w.get("hits", [])[:1])[:160]})')
        else:
            hand('all', f'full-cap walk of n={n} sha256 {f["sha"][:16]}: clean, files {w.get("files")}, capped {w.get("capped")} (cap {FULLCAP})')
    save()


def stop_superseded():
    """6i/6n: stop a running or queued kick when the live row is more than 1e-6 below min(its start, the bar)."""
    base, live, src = bars()
    for tag, j in state['jobs'].items():
        if j.get('stopped') or ('near-' + tag) in state['collected'] or ('final-' + tag) in state['collected']:
            continue
        n = j['n']
        if should_stop(j['start_score'], base[n], live[n]) and n in src:
            try:
                out = cmd(['ssh', j['host'], 'cd ' + ROOT + ' && ' + PY[j['host']] + ' killtag.py ' + j['slot'] + ' ' + tag])
            except Exception as e:
                out = repr(e)
            j['stopped'] = now()
            save()
            note(f'STOP_KICK n{n} {tag}: {src[n][0].name} posted {live[n]!r} < min(start {j["start_score"]!r}, bar {base[n]!r}) - 1e-6; {out.strip()[:200]}')


def health():
    """6t: a slot with a queued or active job needs a live worker; restart a dead one and re-queue its job."""
    free, sl = free_slots()
    for host, slot in HOSTS:
        w, a = sl.get((host, slot), (0, 0))
        if w + a == 0 or time.time() > END - 600:
            continue
        try:
            if worker_alive(host, slot):
                continue
            start_worker(host, slot, 'restart: worker dead with %d queued and %d active jobs' % (w, a))
        except Exception as e:
            note('HEALTH_DEFER ' + host + ' ' + repr(e)[:120])


# ---------------------------------------------------------------- admissions
def admit_chain():
    """6b, 8: two own 180 s follows of a held find, before its certified line."""
    base, live, src = bars()
    keep = []
    for c in state['chain']:
        n = c['n']
        if time.time() > ADMIT_SHORT:
            note(f'CHAIN_LATE n{n}: past 12:40Z, the held find publishes without more follows')
            continue
        if live[n] < c['score'] - 1e-10:
            note(f'CHAIN_DROP n{n}: a peer is lower ({live[n]!r})')
            continue
        free, sl = free_slots()
        if not free:
            keep.append(c)
            continue
        free = free + [k for k, (w, a) in sorted(sl.items(), key=lambda kv: kv[1][0] + kv[1][1]) if k not in free]
        start = Path(c['near'])
        rec = str(start) + ' (sha256 ' + c['sha'] + ')'
        seeds = [c['seed'] + 11, c['seed'] + 97]
        if not claim_and_check(n, 'sha256 %s, own-family-follow invent_rest lkick 180 s seeds %s of our own held find %s (rule 6b: producer follow before its certified line)' % (c['sha'][:16], seeds, start)):
            keep.append(c)
            continue
        for k, seed in enumerate(seeds):
            j = make_job(n, start, 'own-family-follow' if k == 0 else 'own-extra-family-seed', seed, 180, 'invent',
                         'classfill r38 own find ' + c['parent'] + ' (' + rec + '); ' + c['source'], c['licence'], c['score'], parent=c['parent'])
            j['start_rec'] = rec
            j['pubfirst'] = c.get('pubfirst', False)
            h, s = free[k] if k < len(free) else free[0]
            j['host'], j['slot'] = h, s
            send(j, h, s)
    state['chain'] = keep
    save()


def producer_record(p, n):
    sides = [read(q, {}) for q in (Path(str(p) + '.json'), p.with_suffix('.json'), Path(str(p) + '.source.json'))]
    sides = [x for x in sides if x]
    row = next((r for r in rows(p.parent / 'take.tsv') if r.get('n') == str(n)), {}) if re.fullmatch(r'\d+\.csv', p.name) else {}
    # 6e, 6p: name the producer's own record by absolute path and sha256, never quote its text (audit notes inside a
    # quoted record made a whole r37 tree walk unclean)
    recs = [q for q in (Path(str(p) + '.json'), p.with_suffix('.json'), Path(str(p) + '.source.json')) if q.is_file()]
    srctext = ('producer record ' + '; '.join(str(q) + ' (sha256 ' + sha(q) + ')' for q in recs)) if recs else ('producer take row ' + str(p.parent / 'take.tsv') + ' n=' + str(n))
    lic = row.get('licence') or next((str(x.get('licence')) for x in sides if isinstance(x, dict) and x.get('licence')), 'inherited terms in the producer record of ' + str(p))
    return srctext, lic


def snapshot(p, n, label):
    digest = sha(p)
    snap = W / 'starts' / f'{n}-{label}-{digest[:16]}.csv'
    if not snap.exists():
        shutil.copy2(p, snap)
    if sha(snap) != digest:
        return None, digest, '', ''
    srctext, lic = producer_record(p, n)
    if not Path(str(snap) + '.json').exists():
        atom(Path(str(snap) + '.json'), dict(source='byte copy of ' + str(p) + ' taken ' + now() + '; producer record: ' + srctext,
                                             licence=lic, copy_of=str(p), sha256=digest))
    return snap, digest, srctext, lic





HELD = S / 'gather/round37-2026-11-18a.csv'
HELDSHA = '7e0d3ddf6154e920ef943ccf3fb704413a12bfef9863932f66f5cc4b132c29b2'
assert sha(HELD) == HELDSHA


def held_source(n):
    import glob
    best = None
    for p in glob.glob(str(R / 'results/round*-best-*.tsv')):
        m = re.search(r'round(\d+)-best', p)
        if not m or int(m.group(1)) > 37:
            continue
        for r in rows(p):
            if r.get('n') == str(n) and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), p, r)
    if best is None:
        return 'held baseline', 'held baseline'
    return ('results/' + Path(best[1]).name + ' n=' + str(n) + ': ' + best[2].get('source', ''), best[2].get('licence', ''))


HAND_RX = re.compile(r'->\s*(?:all|[\w,]*classfill[\w,]*)\s*:.*?\bhand(?:s|ed|ing)?\b(?!\s+(?:off|no|nothing|any)\b)(?=\s+(?:deep|over|n\s*=|classfill|the|row|tail|held|us|you))', re.I)
BACK_RX = re.compile(r'\btakes?\s+back\b|\btaken\s+back\b|\btake-back\b|\breclaim', re.I)
OWNERS = ('border', 'rebuild', 'quench', 'backlog')


def ltime(l):
    import datetime
    try:
        return datetime.datetime.fromisoformat(l.split()[0].replace('Z', '+00:00')).timestamp()
    except (ValueError, IndexError):
        return None


def lane_of(l):
    m = re.match(r'\S+\s+(\S+)\s+->', l)
    return m.group(1) if m else ''




_HR = {}



VOID_SHARE = re.compile(r'^public-first (?:ancestor|row)\b.*\b1105 share\b', re.I)
PIN_RX = re.compile(r'changed since pinned: \S*?/(\d+)[-.]')




DONOR_DIRS = lambda: ([S / 'take-k123-r36', S / 'take-k123-r37'] + [d for d in S.glob('take-*-r38') if d.name.startswith(('take-k123-', 'take-forensics-'))])
DONOR_MAX = 1e-7   # 6d: only donors within 1e-7 of score of the bar (1e-6 or more gave 0 of about 30)
DONOR_MIN = -1e-10  # a donor more than 1e-10 below the bar is a row of its producer, not a donor
# 6d, 6g: n where a donor fell back to the held geometry or donors returned to one endpoint in rounds 36 and 37
# (classfill r36 BASIN 407 448 537 581 735 738 807 904 965; r37 367 448; backlog r37 911 367; border r37 591 642 687,
# 634 endpoint 25.68843844046 twice; r36 330; spent donor families 372 367 591 642)
CLOSED = {330, 367, 372, 407, 448, 537, 581, 591, 634, 642, 687, 735, 738, 807, 904, 911, 965}
NEAR_AGE = 60     # r37: backlog claimed a k123 donor 86 s after its line; a 600 s wait loses every donor


_LOGC = {}


def _loglines(log):
    st = log.stat()
    k = (str(log), st.st_size, st.st_mtime_ns)
    if k not in _LOGC:
        _LOGC.clear() if len(_LOGC) > 4 else None
        _LOGC[k] = log.read_text(errors='replace').splitlines()
    return _LOGC[k]


def other_claim_on_bytes(digest, since, deep=False):
    """A CLAIM line of another lane that names these bytes (a producer's donor announcement is not a claim).
    deep=True: only a 900 s claim counts (a 180 s follow of the same bytes does not take the first deep seed)."""
    for log in (S / 'handoff-r36.log', S / 'handoff-r37.log', HANDOFF):
        for l in _loglines(log):
            if ' classfill -> ' in l or digest[:12] not in l or not CLAIM.search(l) or re.search(r'probe ?120', l):
                continue  # invent's probe120 runs stop dry at 120 s: not an unprobed seed (6c)
            if deep and not re.search(r'900|deep|unprobed', l, re.I):
                continue
            t = ltime(l)
            if t is not None and t >= since:
                return l
    return None


def board_scores():
    out = {}
    for r in rows(S / 'main-r17/gap-by-n.tsv'):
        try:
            n = int(r['n'])
            out[n] = float(r['board_L']) / math.sqrt(n) - 1
        except (ValueError, KeyError):
            pass
    return out


BOARD = board_scores()
R35SEEDS = {}   # our own 900 s seeds of rounds 35 to 37, by input sha256
PRIOR_GEOM = {}  # n -> input snapshots of our r35 to r37 900 s donor and fresh-row seeds (geometry grouping, 6d)
for _r in ('35', '36', '37'):
    _st = read(S / ('take-classfill-r%s/work/cf-state.json' % _r), {}) or {}
    for _j in _st.get('jobs', {}).values():
        if _j.get('seconds', 0) < 900:
            continue
        R35SEEDS[_j['input_sha256']] = R35SEEDS.get(_j['input_sha256'], 0) + 1
        if _j.get('kind', '').startswith(('donor', 'fresh', 'own')) and Path(_j.get('input_snapshot', '')).is_file():
            PRIOR_GEOM.setdefault(_j['n'], []).append(_j['input_snapshot'])

_HC = {}


def _centres(p, n):
    import numpy as np
    P = load(p, {n}).get(n)
    if P is None:
        return None
    c = np.asarray(P)[:, :2].astype(float)
    return c - c.min(0)


def _held_centres(n):
    import numpy as np, csv as _csv
    if not _HC:
        for r in _csv.DictReader(open(HELD)):
            _HC.setdefault(int(r['n']), []).append((float(r['x'].lstrip('s')), float(r['y'].lstrip('s'))))
        for k in list(_HC):
            a = np.array(_HC[k])
            _HC[k] = a - a.min(0)
    return _HC[n]


def share_of(A, B):
    """Fraction of A's centres within 1e-3 (and 1e-2) of a centre of B, corner aligned, best of 8 symmetries
    (the measure of tools/invent/round36/heldshare.py, here against any reference layout)."""
    from scipy.spatial import cKDTree
    t = cKDTree(B)
    best = (0.0, 0.0)
    for k in range(8):
        X = A.copy()
        if k & 1:
            X[:, 0] = A[:, 0].max() - X[:, 0]
        if k & 2:
            X[:, 1] = A[:, 1].max() - X[:, 1]
        if k & 4:
            X = X[:, ::-1]
        d, _ = t.query(X)
        best = max(best, (float((d < 1e-3).mean()), float((d < 1e-2).mean())))
    return best


def heldshare(p, n):
    """Share at 1e-3 of a donor with the held round 37 a row (6d: kick only under 0.5)."""
    k = 'hs:' + sha(p)
    hc = state.setdefault('heldshare', {})
    if k not in hc:
        A = _centres(p, n)
        hc[k] = share_of(A, _held_centres(n))[0] if A is not None else 1.0
    return hc[k]


def same_geometry(p, n):
    """6d: a donor whose share at 1e-3 with a donor already seeded at n (ours, r35 to r38, or claimed by another lane) is 0.9 or more."""
    refs = list(PRIOR_GEOM.get(n, [])) + [j['input_snapshot'] for j in state['jobs'].values()
                                          if j['n'] == n and j.get('kind', '').startswith('donor')]
    # donors at n that another lane claimed by bytes in r36 or r37 count as seeded geometry too
    for d in DONOR_DIRS():
        for q in (d / 'near').glob('%d-*.csv' % n):
            if q != p and other_claim_on_bytes(sha(q), 0):
                refs.append(str(q))
    A = _centres(p, n)
    if A is None:
        return 'unreadable'
    for q in refs:
        B = _centres(q, n)
        if B is not None and len(B) == len(A) and max(share_of(A, B)) >= 0.9:
            return q  # r38: 0.9 at 1e-3 OR at 1e-2 (973 donors 21a4b3a1 and 55b96949 share 0.53 at 1e-3 but 0.95 at 1e-2)
    return None


def donor_pool():
    base, live, src = bars()
    nc = state.setdefault('nearcache', {})
    pool = []
    plist = []
    for d in DONOR_DIRS():
        plist += [(p, d) for p in (d / 'near').glob('*.csv')]
    for p, d in plist:
        m = re.match(r'(\d+)', p.name)
        if not m or not (40 < int(m.group(1)) <= 1000):
            continue
        n = int(m.group(1))
        try:
            st = p.stat()
        except OSError:
            continue
        if d != T and time.time() - st.st_mtime < NEAR_AGE:
            continue
        k = str(p) + ':' + str(st.st_mtime_ns)
        if k not in nc:
            try:
                P = load(p, {n}).get(n)
                nc[k] = side(P) if P is not None else 1e9
            except Exception:
                nc[k] = 1e9
        sc = nc[k] / math.sqrt(n) - 1
        bar = base[n]
        if n in CLOSED or not (bar + DONOR_MIN <= sc < bar + DONOR_MAX) or sc < live[n] + 1e-10:
            continue
        if should_stop(sc, bar, live[n]):
            continue  # 6e/6i: another lane holds a row more than 1e-6 below the bar: kick only the lowest live row
        if ('basin:%d' % n) in state['done_keys']:
            continue  # 6c(3): a donor at n already fell back to the bar this round
        room = (bar - BOARD.get(n, bar)) - (sc - bar)
        if room <= 0:
            continue
        pool.append((room, n, sc, p, d, k))
    # r37 next: donors at the bar first (the 793 donor sat 4e-11 above it), then by board room
    pool.sort(key=lambda x: (min(R35SEEDS.get(sha(x[3]), 0), 1), x[2] - base[x[1]] > 1e-9, x[2] - base[x[1]], -x[0]))
    return pool, base, live


def admit_donors():
    """6d, 8: k123 near donors within 1e-7 of the bar, at-the-bar first, ONE unprobed 900 s seed per geometry, no legs."""
    if time.time() > ADMIT_DEEP:
        return
    free, _ = free_slots()
    if not free:
        return
    pool, base, live = donor_pool()
    inflight = {j['n'] for t, j in state['jobs'].items() if j['kind'] == 'donor-unprobed' and ('near-' + t) not in state['collected']
                and ('final-' + t) not in state['collected'] and not j.get('stopped')}
    seen_n = set()
    for room, n, sc, p, d, k in pool:
        if n in inflight or n in seen_n:
            continue
        free, _ = free_slots()
        if not free:
            return
        digest = sha(p)
        dk = 'donor:%s' % digest
        if dk in state['done_keys']:
            continue
        used = R35SEEDS.get(digest, 0)
        sk = 'donorsc:%d:%.12e' % (n, sc)
        prev = [float(x.split(':')[2]) for x in state['done_keys'] if x.startswith('donorsc:%d:' % n)]
        if sk in state['done_keys'] or any(abs(sc - v) < 2e-7 for v in prev):
            continue  # a byte-different copy of a donor already run (same side)
        if used >= 1 and d != T:
            state['done_keys'].append(dk)
            continue  # 6c: one seed per donor geometry
        hs = heldshare(p, n)
        if hs >= 0.5:
            state['done_keys'].append(dk)
            note(f'DONOR_SHARE_SKIP n{n} {p}: held share at 1e-3 {hs:.3f} vs round 37 a (6d: kick only under 0.5)')
            continue
        g = same_geometry(p, n) if d != T else None
        if g:
            state['done_keys'].append(dk)
            note(f'DONOR_GEOM_SKIP n{n} {p.name}: same geometry (share at 1e-3 of 0.9 or more) as seeded {Path(str(g)).name}')
            continue
        if d != T:
            l = other_claim_on_bytes(digest, 0)
            if l:
                state['done_keys'].append(dk)
                note(f'DONOR_TAKEN n{n} {p.name}: claimed by another lane: {l[:160]}')
                continue
        P = load(p, {n}).get(n)
        if P is None or lattice(P):
            state['done_keys'].append(dk)
            continue
        hit = withdrawn_hit(digest)
        if hit:
            state['done_keys'].append(dk)
            note(f'WITHDRAW_SKIP n{n} {hit[:160]}')
            continue
        snap, _, srctext, lic = snapshot(p, n, d.name)
        if snap is None:
            continue
        w = walk_async(snap)
        if w is None:
            seen_n.add(n)
            continue
        state['done_keys'].append(dk)
        state['walk'][digest] = dict(clean=w.get('clean'), hits=w.get('hits', [])[:5], pubfirst=w.get('pubfirst'), files=w.get('files'), capped=w.get('capped'))
        save()
        if not eff_clean(w, n):
            note(f'ANCESTRY_REFUSED donor n{n} {p} {w.get("hits", [])[:3]}')
            continue
        free, sl = free_slots()
        if not free:
            state['done_keys'].remove(dk)
            return
        nseeds = 1
        seeds = [4801 + n % 89 + 7 * i + (211 if d == T else 0) for i in range(nseeds)]
        if not claim_and_check(n, 'sha256 %s, k123-near donor UNPROBED 900 s midm_scan lkick,kick seed %s of %s (board room %.3e, %.3e above the bar, held share at 1e-3 vs round 37 a %.3f; geometry share under 0.9 at 1e-3 and 1e-2 with every donor seeded or claimed at this n; walked clean, files %s capped %s)' % (
                digest[:16], seeds, p, room, sc - base[n], hs, w.get('files'), w.get('capped')), digest=digest, deep=True):
            continue
        g = same_geometry(p, n)  # 6s: a claim of another lane on the same geometry that landed while we walked or claimed
        if g:
            hand('all', 'releases n=%d sha256 %s unkicked: another lane claimed the same geometry (%s)' % (n, digest[:16], Path(str(g)).name))
            note(f'DONOR_GEOM_SKIP n{n} {p.name}: same geometry as {g}, claimed while we walked')
            continue
        rec = str(snap) + ' (sha256 ' + digest + '), a byte copy of ' + str(p)
        slots2 = free + [kk for kk, (ww, aa) in sorted(sl.items(), key=lambda kv: kv[1][0] + kv[1][1]) if kk not in free]
        for i, seed in enumerate(seeds):
            j = make_job(n, snap, 'donor-unprobed' if d != T else 'donor-leg', seed, 900, 'nearmidm', 'near geometry of ' + str(d) + ': ' + srctext, lic, sc)
            j['bar_input'] = False
            j['slack'] = max(0.0005, (sc - live[n]) * math.sqrt(n) + 2e-4)
            j['start_rec'] = rec
            j['pubfirst'] = bool(w.get('pubfirst'))
            j['priority'] = 1
            h, s2 = slots2[i % len(slots2)]
            j['host'], j['slot'] = h, s2
            send(j, h, s2)
        inflight.add(n)
        state['done_keys'].append(sk)
        note(f'DECIDE donor n{n}: {p.name} room {room:.3e}, {sc - base[n]:.3e} above bar, {sc - live[n]:.3e} above live, held share {hs:.3f}, seeds {seeds}')
        save()





def idle_note():
    """6h: say in STATE.txt when no job runs and no donor is eligible (workers leave after 10 idle minutes)."""
    busy = bool(running_jobs()) or bool(state['chain']) or bool(state['hold']) or bool(state['pending'])
    key = 'busy' if busy else 'idle'
    if state.get('mode') != key:
        state['mode'] = key
        if key == 'idle':
            note('IDLE no job running and no eligible donor (6d bounds: within 1e-7 of bar38, held share under 0.5, unprobed geometry, open n); '
                 'workers leave after 10 idle minutes and restart on demand when a donor appears (6h)')
        else:
            note('BUSY jobs or held finds in flight')
        save()


if __name__ == '__main__':
    ok, res = stop_rule_controls()
    note('CONTROL stop rule 6q: ' + ('PASS ' if ok else 'FAIL ') + json.dumps(res))
    if not ok:
        sys.exit(1)
    if '--dry' in sys.argv:
        pool, base, live = donor_pool()
        for room, n, sc, p, d, k in pool[:40]:
            print('%4d room %.3e above_bar %.3e above_live %.3e heldshare %.3f %s' % (n, room, sc - base[n], sc - live[n], heldshare(p, n), p))
        print(len(pool), 'donors')
        sys.exit(0)
    (W / 'controller-pid').write_text(str(os.getpid()))
    note('START controller cf38.py pid %d log %s; deep admissions to 12:15Z, own follows to 12:40Z, collect to 13:53Z' % (os.getpid(), W / 'cf38.log'))
    last_bar = 0
    while time.time() < STOP_AT and not (W / 'STOP').exists():
        try:
            collect()
            publish()
            full_walks()
            if time.time() - last_bar > 120:
                writebar()
                last_bar = time.time()
            stop_superseded()
            health()
            admit_chain()
            admit_donors()
            idle_note()
            atom(W / 'heartbeat.json', dict(time=now(), jobs=len(state['jobs']), running=len(running_jobs()), collected=len(state['collected']), take=len(own()),
                                            hold=len(state['hold']), pending=len(state['pending']), walks=sum(1 for q in PROCS.values() if q.poll() is None)))
        except Exception as e:
            import traceback
            note('CONTROLLER_ERROR ' + repr(e)[:300])
            traceback.print_exc()
            sys.stdout.flush()
        time.sleep(30)
    collect()
    publish()
    note('CONTROLLER_STOP')
