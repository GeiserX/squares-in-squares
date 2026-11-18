#!/usr/bin/env python3
"""quench: follow the live takes of a round and queue one fq quench per new start.

Usage: quench_follow.py TAKEDIR ROUND DEADLINE_EPOCH BASE_DETAILS.csv [--once]

Every 5 minutes, until 25 minutes before the deadline:
  - rebuild TAKEDIR/work/bar.tsv: the base details lowered by every other
    take-*-ROUND/take.tsv row (quench_bar.py)
  - read the start files: take-*-ROUND/near/*.csv, the per-n take files of the
    other lanes, the csv paths of the handoff-ROUND.log lines to quench or all,
    and (first pass) the near files of the round before that its quench follow
    never saw
  - keep the files whose bounding side sits within WINDOW of the bar side,
    best two per n per pass, most negative margin first
  - walk each one (quench_walk.py, then quench_audit.py on its sidecar); a start
    that is not clean is logged and never queued
  - copy the start, its sidecars and its ledger lines to work/starts/<sha16>/,
    so the record survives the producing lane replacing the file (975 of
    round 25), prep the job from that copy and queue it on the shortest queue
"""
import csv, glob, hashlib, json, os, re, shutil, subprocess, sys, time

csv.field_size_limit(1 << 30)
LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import quench_audit as qa  # noqa: E402
import quench_near as qn  # noqa: E402
import quench_walk as qw  # noqa: E402

S = '$SCRATCH/bounties-squares/'
PY = S + 'venv/bin/python'
WINDOW = 2e-6
# Forensics quenches its compositions with the polish flags only ("flags": "p"). One fq pass with the
# default flags took its round 26 910 from side 30.666008793 to 30.663520679 and its 850 from 29.655095563
# to 29.651030809, so its files of the round get a wide window and go first. Its frozen files of rounds 23
# to 25 sit at the held side and moved by 1e-13 or less (measured 14:05 UTC): they are not read.
# Round 28: 2e-4 (was 1.2e-2). Round 27 measured 68 forensics starts more than 2e-6 of side above the bar and none
# crossed it; of 128 starts above the bar at queue time none crossed, and all 45 crossings started below it.
WIDE = ('/take-forensics-r', 2e-6)  # round 29: 2e-6 like the others (r27: 0 of 68 forensics starts above 2e-6 crossed; the first r29 pass queued 103)
# round 30: QUENCH_WINDOW (default 1e-9 of side) replaces both windows. By 14:50Z of round 30, 68 plain jobs that started
# above the bar gave 0 rows and all 13 that counted started at or below it (r27: 0 of 128 above, all 45 crossings below).
if os.environ.get('QUENCH_WINDOW'):
    WINDOW = float(os.environ['QUENCH_WINDOW'])
    WIDE = ('/take-forensics-r', WINDOW)


def window(p):
    # round 30: QUENCH_NEAR_WINDOW (when set) is the window of near files; per-n take files keep WINDOW. At 16:00Z the first
    # pass after a restart had walked near files at the bar side (margin about -7e-10) for 70 minutes, and a fresh near
    # file below the bar waited behind them.
    if os.environ.get('QUENCH_NEAR_WINDOW') and not re.search(r'/take-[a-z0-9-]+-r\d+/\d+\.csv$', p):
        return float(os.environ['QUENCH_NEAR_WINDOW'])
    return WIDE[1] if WIDE[0] in p else WINDOW
PREV = {'r26': 'r25', 'r27': 'r26', 'r28': 'r27', 'r29': 'r28', 'r30': 'r29', 'r31': 'r30', 'r32': 'r31', 'r33': 'r32', 'r34': 'r33'}


def take_row_dict(d, n):
    p = S + d + '/take.tsv'
    if os.path.isfile(p):
        for r in csv.DictReader(open(p, errors='replace'), delimiter='\t'):
            if (r.get('n') or '').strip() == str(n):
                return r
    return None


def clean_cell(t):
    return ' '.join(str(t).replace('\t', ' ').split())


def composition_cells(sc):
    """Source and licence cells for a composition start (a sidecar with "parts", as forensics writes):
    each donor, then each ancestry root of its immutable origin record with that root's own source and
    licence. A held root (gather/roundNN, n) gets its round table row. Returns ('', '') for other sidecars."""
    try:
        d = json.load(open(sc))
    except Exception:
        return '', ''
    parts = d.get('parts') if isinstance(d, dict) else None
    if not isinstance(parts, dict):
        return '', ''
    donors, roots, lics = [], {}, []
    for k in sorted(parts):
        v = parts[k]
        if not isinstance(v, dict):
            continue
        src = v.get('source') or ['', '']
        donors.append('%s = n=%s of %s' % (k, src[1] if len(src) > 1 else '?', str(v.get('original_file') or src[0]).replace(S, '')))
        rec = re.sub(r'^immutable ancestry in ', '', str(v.get('source_record') or ''))
        try:
            o = json.load(open(rec))
        except Exception:
            continue
        a = o.get('ancestry', {})
        while isinstance(a, dict) and 'roots' not in a and isinstance(a.get('ancestry'), dict):
            a = a['ancestry']
        rl = (a.get('roots') if isinstance(a, dict) else None) or [{'path': o.get('path'), 'n': o.get('n')}]
        for r in rl:
            path, rn = str(r.get('path') or ''), r.get('n')
            if not path.endswith('.csv') or rn is None:
                continue
            m = re.search(r'gather/round(\d+)-', path)
            if m and not r.get('source'):
                h = qw.held(int(rn), int(m.group(1)))
                txt, lic = (h.split(' || ', 1) + [''])[:2]
            else:
                txt, lic = str(r.get('source') or ''), str(r.get('licence') or '')
            roots[(path, str(rn))] = '%s n=%s: %s' % (path.replace(S, ''), rn, clean_cell(txt)[:420])
            if lic and clean_cell(lic)[:160] not in lics:
                lics.append(clean_cell(lic)[:160])
    if not donors:
        return '', ''
    src = '%s composition by the forensics lane (flags %s): %s; ancestry roots: %s' % (
        d.get('kind', 'rectangle'), d.get('flags', '?'), ', '.join(donors), ' | '.join(roots[k] for k in sorted(roots)))
    return src, ' + '.join(lics)


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def main():
    T, rnd, DL, base = sys.argv[1].rstrip('/'), sys.argv[2], int(sys.argv[3]), sys.argv[4]
    once = '--once' in sys.argv
    # --starts FILE: queue the listed start files once, with no window (a probe of a new kind of start)
    starts_f = sys.argv[sys.argv.index('--starts') + 1] if '--starts' in sys.argv else None
    once = once or bool(starts_f)
    W = T + '/work'
    stop = DL - 15 * 60  # round 29: 15 min (was 25); a fq job takes 20 s to 5 min
    # one seen file per starts list, so several probe lists can run side by side (round 27)
    seen_f = W + ('/follow-seen-%s.json' % os.path.basename(starts_f) if starts_f else '/follow-seen.json')
    seen = json.load(open(seen_f)) if os.path.exists(seen_f) else {}
    # a restart walks the refused starts again (the walk may have changed), after every new start
    rewalk = {k for k, v in seen.items() if str(v).startswith('out ')}
    seen = {k: v for k, v in seen.items() if k not in rewalk}
    # round 29: q-boxA is the kick slot (kicks measured far above plain fq of near-bar files); plain jobs go to boxB and boxD
    queues = [W + '/q-boxB.txt', W + '/q-boxD.txt'] if os.environ.get('QUENCH_KICK_SLOT') else [W + '/q-boxB.txt', W + '/q-boxA.txt', W + '/q-boxD.txt']
    if os.path.exists(W + '/q-boxDb.txt'):  # round 33 override 8: a second boxD slot
        queues.append(W + '/q-boxDb.txt')

    def log(s):
        open(T + '/STATE.txt', 'a').write(now() + ' boxA FOLLOW ' + s + '\n')

    def pending(q):
        # jobs not finished yet, the running one included, so an idle box gets the next job
        return sum(1 for j in open(q).read().split() if not os.path.exists(j + '/done'))

    first = True
    while True:
        takes = [t for t in glob.glob(S + 'take-*-%s/take.tsv' % rnd) if not t.startswith(T + '/')]
        barf = W + ('/bar-%s.tsv' % os.path.basename(starts_f) if starts_f else '/bar.tsv')  # the running follow owns bar.tsv
        subprocess.run([PY, '-I', LANE + '/quench_bar.py', base, barf] + takes, capture_output=True)
        bar = {int(r['n']): float(r['side']) for r in csv.DictReader(open(barf), delimiter='\t')}
        files = open(starts_f).read().split() if starts_f else [p for p in glob.glob(S + 'take-*-%s/near/*.csv' % rnd) + glob.glob(S + 'take-*-%s/near/*/*.csv' % rnd)
                 + glob.glob(S + 'take-*-%s/[0-9]*.csv' % rnd) if not p.startswith(T + '/')]
        if os.path.exists(S + 'handoff-%s.log' % rnd) and not starts_f:
            for line in open(S + 'handoff-%s.log' % rnd, errors='replace'):
                if re.search(r'-> [^:]*(?:quench|all)', line):
                    files += [p for p in re.findall(r'($SCRATCH/bounties-squares/take-[^\s,;]+?\.csv)', line)
                              if not p.startswith(T + '/')]
        if first and rnd in PREV and not starts_f:
            prev = S + 'take-quench-%s/work/follow-seen.json' % PREV[rnd]
            pseen = json.load(open(prev)) if os.path.exists(prev) else {}
            files += [p for p in glob.glob(S + 'take-*-%s/near/*.csv' % PREV[rnd]) if p not in pseen
                      and '/take-quench-' not in p]
        cand = []
        # round 30: our own take rows; a start that cannot go below our own row of n by 1e-9 of side is not queued
        # (eight raw 694 files of one twoshort kick went to eight jobs after our first one counted)
        ours = {}
        try:
            for r in csv.DictReader(open(T + '/take.tsv'), delimiter='\t'):
                ours[int(r['n'])] = (float(r['new']) + 1) * int(r['n']) ** 0.5
        except (OSError, ValueError, KeyError):
            pass
        for p in sorted(set(files)):
            if not os.path.isfile(p):
                continue
            key = '%s@%d' % (p, os.path.getmtime(p))  # lanes rewrite a near file under the same name
            if key in seen:
                continue
            try:
                n, m, s = qn.side(p)
            except Exception:
                continue  # half written: read it again next pass
            if m != n or n not in bar:
                seen[key] = 'bad'; continue
            if not starts_f and n in ours and s > ours[n] - 1e-9:
                seen[key] = 'ours lower %.2e' % (s - ours[n])
            elif starts_f or s - bar[n] < window(p):
                cand.append((s - bar[n], n, p, key))
            else:
                seen[key] = 'far %.2e' % (s - bar[n])
        per, queued, out = {}, 0, 0
        k_done = 0
        # forensics files and harvest's public rows first: both lanes quench with polish flags only
        first_rx = re.compile(r'/take-forensics-r|/take-harvest-r\d+/\d+\.csv$')
        # round 28: starts below the bar first, by margin; the forensics and harvest preference only breaks ties above it
        for mg, n, p, key in sorted(cand, key=lambda c: (c[3] in rewalk, c[0] >= 0, c[0] if c[0] < 0 else not first_rx.search(c[2]), c[0])):
            try:
                k_done += 1
                if k_done % 10 == 0:
                    json.dump(seen, open(seen_f + '.tmp', 'w')); os.replace(seen_f + '.tmp', seen_f)
                if per.get(n, 0) >= 2 or time.time() > stop:
                    continue
                data = open(p, 'rb').read()  # a lane may remove its file between the listing and here
                sha = hashlib.sha256(data).hexdigest()
                J = W + '/jobs/fo-%d-%s' % (n, sha[:10])
                if os.path.exists(J):
                    seen[key] = J; continue
                try:
                    w = qw.check(p)
                except Exception as e:  # one bad record must not stop the follow
                    import traceback
                    traceback.print_exc(); sys.stdout.flush()
                    seen[key] = 'error %r' % (e,); continue
                sc = qw.sidecars(p)
                a = qa.audit(sc[0]) if sc else {'clean': True, 'hits': []}
                if not w['clean'] or not a['clean']:
                    seen[key] = 'out ' + '; '.join(h[:100] for h in (w['hits'] + a['hits'])[:3])
                    out += 1
                    open(W + '/walk-out.jsonl', 'a').write(json.dumps({'t': now(), 'margin': mg, 'walk': w, 'audit': a}) + '\n')
                    continue
                # a byte copy of the start and its record
                D = W + '/starts/' + sha[:16]
                os.makedirs(D, exist_ok=True)
                base_name = os.path.basename(p)
                open(D + '/' + base_name, 'wb').write(data)  # the bytes that were hashed and walked
                for c in sc:
                    shutil.copyfile(c, D + '/' + os.path.basename(c))
                # a per-n take file has its record in the take.tsv row: copy the row as the sidecar of the copy
                mt = re.match(re.escape(S) + r'(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$', p)
                own_src, own_lic = '', ''
                if mt:
                    row = take_row_dict(mt.group(1), int(mt.group(2)))
                    if row:
                        own_src, own_lic = row.get('source') or '', row.get('licence') or ''
                        json.dump({'n': n, 'source': own_src, 'licence': own_lic,
                                   'record': 'the n = %d row of %s/take.tsv at %s, copied byte for byte' % (n, mt.group(1), now())},
                                  open(D + '/' + base_name + '.json', 'w'), indent=1)
                for c in sc:
                    csrc, clic = composition_cells(c)
                    own_src, own_lic = own_src or csrc, own_lic or clic
                for c in sc:
                    try:
                        sj = json.load(open(c))
                    except Exception:
                        continue
                    if isinstance(sj, dict):
                        own_src = own_src or str(sj.get('source') or '')
                        own_lic = own_lic or str(sj.get('licence') or sj.get('licence_override') or '')
                led = qw.ledger_lines(p)
                if led:
                    open(D + '/ledger.tsv', 'w').write('file\tline\n' + ''.join('%s\t%s\n' % (base_name, l.replace('\t', ' ')) for l in led))
                r = subprocess.run([PY, '-I', LANE + '/quench_once.py', 'prep', D + '/' + base_name, J, '--no-cert'],
                                   capture_output=True, text=True)
                if r.returncode:
                    seen[key] = 'prep failed ' + r.stderr[-200:]; continue
                lic = own_lic
                lane = re.match(re.escape(S) + r'take-([a-z0-9-]+)-r\d+/', p)
                rel = D.replace(S, '') + '/' + base_name
                open(J + '/source.txt', 'w').write(
                    'quench lane: one fq quench (quench_once.py, quench_box.sh, the midm_fqonce.py loop) of %s (a byte copy, sha256 %s, '
                    'of the file %s that the %s lane wrote at or before %s; %.3e of side from the bar at queue time); its sidecars and ledger '
                    'lines are copied beside it; quench_walk.py walked %d files and found no source that is out, and quench_audit.py agrees; '
                    'held references reached: %s | recorded source of the start: %s' % (
                        rel, sha[:16], base_name, lane.group(1) if lane else 'another', now(), mg, w['files'],
                        ', '.join(w.get('helds', [])[:12]) or 'none', clean_cell(own_src) or 'see the sidecars of the copy'))
                open(J + '/licence.txt', 'w').write(clean_cell(lic) if lic else 'as recorded in the sidecars of ' + rel)
                open(J + '/walk.json', 'w').write(json.dumps(w))
                q = min(queues, key=pending)
                open(q, 'a').write(J + '\n')
                seen[key] = J; per[n] = per.get(n, 0) + 1; queued += 1
                log('QUEUE n=%d margin %.3e %s -> %s' % (n, mg, p.replace(S, ''), os.path.basename(q)))
            except OSError as e:  # the start or a sidecar went away under us: read it again next pass
                log('SKIP %s: %r' % (p.replace(S, ''), e))
                continue
            except Exception as e:  # one bad start must not stop the follow
                import traceback
                traceback.print_exc(); sys.stdout.flush()
                seen[key] = 'error %r' % (e,)
        json.dump(seen, open(seen_f + '.tmp', 'w')); os.replace(seen_f + '.tmp', seen_f)
        log('pass: %d candidates within %.0e side (forensics %.0e), %d queued, %d out by the walk, %d files seen' % (len(cand), WINDOW, WIDE[1], queued, out, len(seen)))
        first = False
        if once or time.time() > stop:
            break
        time.sleep(60)  # round 29: one minute (was five); border measured rows lost to a lower peer within minutes


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    main()
