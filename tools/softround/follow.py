#!/usr/bin/env python3
"""Follow fresh design files and handoffs with one worker per box until the round deadline."""
import csv
import glob
import functools
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctl

KICK = ('midm', 'twoshort', 'k123')
# Round 31: most lanes now kick held rows (rebuild, border, classfill, twoshort, k123, forensics, backlog, quench, midm);
# their fresh take rows are fresh geometry below bar31 and get our island 10 minutes after they are written (after
# backlog's follow), ahead of the pool (round 25: soft-box follows of fresh rows gave 534 and 597, 5.6e-4).
KICK = ('midm', 'twoshort', 'k123', 'rebuild', 'border', 'classfill', 'forensics', 'backlog', 'quench', 'invent', 'stair-c')
# Round 32: no islands on other lanes' take rows. Round 31 measured 58 such starts on backlog, twoshort, classfill, border,
# k123, invent and rebuild rows with 0 finds, while backlog's 180 s lkicks of the same rows gave about 21 take rows.
KICK = ()
FRESH_MAX = 3600   # round 32: a forensics rect file gets its island only in the hour after it was written (r31: islands
                   # on fresh r31 rect files found on 6 of 127, on the round 30 pool 0 of 117)
LOOSE_MAX = 1e-3       # round 28: score above the all-lane bar beyond which a near file is not started
LOOSE_MIN = 1e-7       # round 28: a near file between LOOSE_MIN and LOOSE_MAX above the bar gets an 1800 s island
# Round 28, 01:05Z: 17 islands on quenched forensics rect files and stair-c builds made 0 finds, and the fq quench of 16
# soft-free members 1e-4 to 4e-4 below the side went back to the start side within 1.1e-9 every time (sfq on 591, 986).
# 01:25Z: the 593 island (start 2.7e-4 over the bar) made 15 finds and fq after it, 2.0e-4 of score in all, ending 7e-5 over.
# Rounds 27 and 28 together: every find on these kinds started 1.9e-4 to 5.1e-4 over the bar, none started closer. So a
# quenched kind starts only in the loose window (QUENCHED_TIGHT, LOOSE_MAX] (island, its legal result goes back to the
# lanes as a near file). 01:55Z: the probes at the bar are dropped too (round 27: none of them found).
QUENCHED = ('forensics', 'stair-c')
QUENCHED_TIGHT = 1.5e-4
# Round 27: near files only from the kinds whose starts found in round 26 (k123 7 of 23, forensics 5 of 48, the midm and
# twoshort islands); stair-c (1 of 88), modules (0 of 24), invent (0 of 14), harvest, classfill, border, rebuild and quench
# probes (0 of 25) cost a trace each, and a trace takes minutes on boxA at load 60-100. Take files of every lane still
# reach idle_fill.
DESIGNS = ctl.FIRST + ('forensics', 'twoshort', 'midm', 'stair-c')
# Round 31: forensics rectangle files only. Round 30 measured every find on them (8 n); k123 36 starts, twoshort 35,
# midm 9, modules 6 and stair-c 1 gave 0 finds, and the all-lane lesson 6e stops kicks of k123 three-way near files.
DESIGNS = ('forensics',)
# Round 28: stair-c fresh builds come back (an island when within LOOSE_MAX of the bar, one per composition family): they
# are new constructions close to the bar (round 27: builds at 812, 871 and 995 beat bar27), and the soft search finds on
# new constructions (rounds 11 to 16), while round 26's 1 find in 88 came from 20 s probes.


def state(message):
    with open(ctl.T + '/STATE.txt', 'a') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime()) + ' boxA ' + message + '\n')
    print(message, flush=True)


def bars():
    out = ctl.held_scores()
    for _, _, d in ctl.live_dirs():
        p = ctl.S + '/' + d + '/take.tsv'
        if not os.path.exists(p):
            continue
        try:
            for r in csv.DictReader(open(p), delimiter='\t'):
                n = int(r['n']); score = float(r.get('new') or r.get('score'))
                out[n] = min(out.get(n, math.inf), score)
        except (OSError, ValueError, TypeError):
            continue
    return out


def stop_old(bar):
    pl = ctl.load_plan()
    changed = False
    for j in pl['jobs']:
        if os.path.exists(ctl.W + '/STOPWATCH'):
            break
        log = '%s/%s/run/%d-%s/chain.log' % (ctl.W, j['box'], j['n'], j['tag'])
        if os.path.exists(log) and re.search(r'CHAINEND|^DRY|^STOPPED', open(log).read(), re.M):
            continue
        target_bar=bar[j['n']]
        if False:
            source_policy=ctl.policy.classify(j.get('source',''),j.get('licence',''),j.get('ancestry'))
            target_bar=ctl.policy.floor(j['n'],source_policy,ctl.held_scores()[j['n']],bar)
        if j.get('skipped') or min(j.get('monitor_bar', j['start']), j['start']) <= target_bar + ctl.SAME:
            continue
        removed = ctl.unqueue(j['box'], j['n'], j['tag'])
        stopped = False if removed else ctl.stop_run(j['box'], j['n'], j['tag'])
        if removed or stopped:
            j['skipped'] = 'superseded by the all-lane bar %.12f' % bar[j['n']]
            changed = True
            state('STOP %d %s on %s (%s); deadline 00:15Z; log work/%s/run/%d-%s/chain.log' % (
                j['n'], j['tag'], j['box'], j['skipped'], j['box'], j['n'], j['tag']))
    # Round 32: an island start on a forensics rect file that still waits in a box queue an hour after the file was written
    # leaves the queue (brief item 8: islands only in the hour the file appears; forensics wrote 14 files in the first 13
    # minutes, against about 30 dry 360 s islands an hour on 3 slots).
    for j in pl['jobs']:
        if j.get('skipped') or j.get('stale_checked') or j.get('mode') != 'island' or not j['tag'].startswith('x'):
            continue
        try:
            age = time.time() - os.stat(j['path']).st_mtime
        except OSError:
            age = FRESH_MAX + 1
        if age <= FRESH_MAX:
            continue
        j['stale_checked'] = True; changed = True
        if ctl.unqueue(j['box'], j['n'], j['tag']):
            j['skipped'] = 'waited past the hour after its file was written'
            state('UNQUEUE %d %s on %s (its rect file was written %.0f min ago and it never started; brief item 8); deadline 00:15Z' % (
                j['n'], j['tag'], j['box'], age / 60))
    if changed:
        ctl.save_plan(pl)


def geometry_id(rows):
    """Ignore translation, square order and float-safe rounding when comparing starts."""
    coords = [(float(r['x']), float(r['y']), math.remainder(float(r['angle']), math.pi / 2)) for r in rows]
    variants = []
    for turn in range(4):
        for mirror in (False, True):
            points = []
            for x, y, angle in coords:
                for _ in range(turn):
                    x, y = -y, x
                if mirror:
                    x = -x
                    angle = -angle
                angle = math.remainder(angle, math.pi / 2)
                if abs(abs(angle) - math.pi / 4) < 1e-6:
                    angle = math.pi / 4
                points.append((x, y, angle))
            x0 = min(p[0] for p in points); y0 = min(p[1] for p in points)
            variants.append(tuple(sorted((round(x-x0, 4), round(y-y0, 4), (round(a, 6) or 0.0)) for x,y,a in points)))
    return hashlib.sha256(repr(min(variants)).encode()).hexdigest()


@functools.lru_cache(maxsize=1)
def previous_geometry():
    """Completed searches of frozen round 31 must not repeat under a fresh export name."""
    path = ctl.PREV_W + '/plan.json'
    out = set()
    if not os.path.exists(path):
        return out
    for j in json.load(open(path))['jobs']:
        p = '%s/starts/%d-%s.csv' % (ctl.PREV_W, j['n'], j['tag'])
        if os.path.exists(p) and any(os.path.exists('%s/%s/run/%d-%s/chain.log' % (
                ctl.PREV_W, b, j['n'], j['tag'])) for b in ctl.REMOTE):
            out.add((j['n'], geometry_id(ctl.rows_of(p))))
    return out


@functools.lru_cache(maxsize=1)
def previous_find_geometry():
    """Only old starts with a measured find can qualify for a licensed replay."""
    out=set()
    for j in json.load(open(ctl.PREV_W+'/plan.json'))['jobs']:
        start='%s/starts/%d-%s.csv' % (ctl.PREV_W,j['n'],j['tag'])
        logs=glob.glob('%s/*/run/%d-%s/soft-*.log' % (ctl.PREV_W,j['n'],j['tag']))
        if os.path.exists(start) and any(re.search(r'^FIND ',open(p).read(),re.M) for p in logs):
            out.add((j['n'],geometry_id(ctl.rows_of(start))))
    return out


def can_replay(n, geometry, source_policy):
    return (False and
            source_policy.get('status')=='none' and
            (n,geometry) in previous_find_geometry())


def near_files(bar, seen, priority_only=False):
    pl = ctl.load_plan()
    t0 = pl['t0']
    previous = previous_geometry()
    candidates = set()
    designs = ctl.FIRST + ('readers', 'corners') if priority_only else DESIGNS
    last_urgent = time.time()
    feed_end = float(open(ctl.W + '/deadline').read()) - 900   # round 26: no new start in the last 15 minutes of search
    # Near files of this lane's slice. Frozen round 23 files were already measured there.
    for kind in designs:
        candidates.update((kind, p) for p in glob.glob('%s/take-%s-r33/[0-9]*.csv' % (ctl.S, kind)))
        candidates.update((kind, p) for p in glob.glob('%s/take-%s-r33/near/**/*.csv' % (ctl.S, kind), recursive=True))
    for p in glob.glob(ctl.T + '/near/*-carry-*.csv'):
        try:
            meta = json.load(open(os.path.splitext(p)[0] + '.json'))
            kind = meta['kind']
            if kind in designs:
                candidates.add((kind, p))
        except (OSError, ValueError, KeyError):
            continue
    hp = ctl.HANDOFF
    lines = open(hp).read().splitlines() if os.path.exists(hp) else []
    for line in lines:
        match = re.search(r'\b(' + '|'.join(designs) + r')\s*->', line)
        if not match:
            continue
        for p in re.findall(r'$DATA/[^\s,;<>]+\.csv', line):
            if os.path.exists(p):
                candidates.add((match[1], p))
    existing = []
    for kind, p in candidates:
        try:
            existing.append((kind, p, os.stat(p)))
        except OSError:
            continue
    for kind, p, st in sorted(existing, key=lambda x: (0 if '847' in x[1] else 1 if x[0] in ('k123','readers') else 2 if x[0] == 'corners' else 4 if '/near/' in x[1] else 3, -x[2].st_mtime)):
        if time.time() >= feed_end or os.path.exists(ctl.W + '/STOPWATCH'):
            break
        if not priority_only and time.time() - last_urgent > 60:
            watch_once()
            inbox()
            near_files(bars(), seen, priority_only=True)
            # Round 25 measured: its first full pass over the near files ran from 23:51 to 02:15, so the idle_fill call
            # at the end of the cycle never came before its 02:05 cutoff and both boxes sat idle for an hour.
            idle_fill()
            lk_fill()
            ctl.collect()
            # Round 26: keep what this pass inspected, so a restart does not trace every file again (15:06Z restart:
            # 10 minutes of traces at 10% of a core on boxA while both boxes sat idle).
            sp = ctl.W + '/follow-seen.json'
            json.dump(seen, open(sp + '.tmp', 'w')); os.rename(sp + '.tmp', sp)
            last_urgent = time.time()
        try:
            st = os.stat(p)
        except OSError:
            continue
        if st.st_mtime < t0 or time.time() - st.st_mtime < 15:
            continue
        if time.time() - st.st_mtime > FRESH_MAX:
            continue
        sig = '%s:%s:%s' % (p, st.st_mtime_ns, st.st_size)
        if sig in seen:
            if not isinstance(seen[sig], (float, int)) or time.time() < seen[sig]:
                continue
        seen[sig] = 'inspected'
        try:
            rows = ctl.rows_of(p)
        except (OSError, ValueError, KeyError):
            continue
        if not rows:
            continue
        n = int(rows[0]['n'])
        if len(rows) != n or any(int(r['n']) != n for r in rows):
            state('REFUSE incomplete handoff ' + p)
            continue
        # Hash and score filter before the expensive metric. Near packings can overlap.
        import methods_lp as mlp
        try:
            X = mlp.load(p, {n})[n]
        except (OSError, ValueError, KeyError):
            continue
        side = mlp.side(X)
        if side > math.sqrt(n) * (1 + bar[n]) + .015:
            seen[sig] = 'more than .015 side over the all-lane bar'
            continue
        score = side / math.sqrt(n) - 1
        jobs = ctl.load_plan()['jobs']
        fam = re.search(r'/(\d+)-r\d+-([0-9a-f]{12})', p) if kind == 'stair-c' else None
        if fam and any(j['n'] == n and fam[2] in j.get('path', '') for j in jobs):
            seen[sig] = 'stair-c composition family already probed'
            continue
        geo = geometry_id(rows)
        licensed_replay=False
        if (n, geo) in previous:
            import provenance
            proof=provenance.trace(p,n)
            source_policy=ctl.policy.classify(proof.get('source',''),proof.get('licence',''),proof) if proof.get('ok') else {}
            licensed_replay=can_replay(n,geo,source_policy)
            if not licensed_replay:
                seen[sig] = time.time()+900 if not proof.get('ok') else 'same geometry already searched in frozen round 31'
                continue
        if any(j['n'] == n and abs((j.get('file_score') if j.get('file_score') is not None else j['start']) - score) <= ctl.SAME
               and geometry_id(ctl.rows_of('%s/starts/%d-%s.csv' % (ctl.W, j['n'], j['tag']))) == geo
               for j in jobs if not j.get('skipped')):
            seen[sig] = 'same layout already queued'
            continue
        # Round 28: a lane that rewrites one near path (forensics 746-rect.csv four times in 2 minutes) gets one start per
        # path: a newer version replaces a start that still waits in a queue, and waits 15 minutes while one runs.
        # Round 28 (00:45Z, stair-c 812 had five islands waiting): one waiting near-file start per n. A file that is not
        # lower than the start waiting for its n by more than SAME waits 15 minutes; a lower one replaces it.
        busy = False
        for jj in jobs:
            if jj['n'] != n or jj.get('skipped') or jj.get('mode') in ('certified', 'sfq'):
                continue
            lg = '%s/%s/run/%d-%s/chain.log' % (ctl.W, jj['box'], jj['n'], jj['tag'])
            if os.path.exists(lg) and re.search(r'CHAINEND|^DRY|^STOPPED', open(lg).read(), re.M):
                continue
            if jj.get('path') != p:
                jstart = jj.get('file_score') if jj.get('file_score') is not None else jj['start']
                if os.path.exists(lg):
                    continue                      # running: another file of n may still wait behind it
                if not score < jstart - ctl.SAME:
                    busy = True
                    continue
            if ctl.unqueue(jj['box'], jj['n'], jj['tag']):
                cur = ctl.load_plan()
                for q in cur['jobs']:
                    if (q['n'], q['tag']) == (jj['n'], jj['tag']):
                        q['skipped'] = 'replaced by a newer version of the same file'
                ctl.save_plan(cur); jobs = cur['jobs']
                state('UNQUEUE %d %s on %s (a newer version of %s); deadline 00:15Z' % (jj['n'], jj['tag'], jj['box'], p))
            else:
                busy = True
        if busy:
            seen[sig] = time.time() + 900
            continue
        box = ctl.WATCH_SLOTS[len(jobs) % len(ctl.WATCH_SLOTS)]
        mode = ('short' if n==847 else 'corner') if licensed_replay else 'short' if kind in ctl.FIRST else 'corner' if kind == 'corners' else 'probe'
        # Round 28: round 27 ran 111 forensics probes; the 6 with a find all started 1.9e-4 to 5.1e-4 of score above the bar
        # and ended 6.4e-5 to 3.6e-4 above it. A loose file close to the bar gets one 1800 s island, a far one is skipped.
        margin = score - bar[n]
        if kind in QUENCHED and margin <= QUENCHED_TIGHT:
            seen[sig] = 'tight %s file %.1e of score over the bar (rounds 27 and 28: 0 finds on starts under 1.9e-4)' % (kind, margin)
            continue
        if margin > LOOSE_MAX:
            seen[sig] = 'more than %.0e of score over the all-lane bar (round 27: 0 finds in 105 such probes)' % LOOSE_MAX
            continue
        if margin > LOOSE_MIN:
            mode = 'island'
        if not ctl.add(n, p, kind, box, mode=mode):
            reason = getattr(ctl, 'LAST_ADMISSION_REASON', '')
            # Round 26: a refused file was traced again every 120 s; with dozens refused, the re-traces starved the feed
            # on boxA (both boxes idle 15:21Z to 15:30Z). A source policy refusal is final, others wait 15 minutes.
            seen[sig] = ("refused: " + reason) if reason.startswith("source policy") else time.time() + 2400   # round 27: 40 minutes (traces at load 100 take minutes each)
            continue
        current = ctl.load_plan()
        current['jobs'][-1]['monitor_bar'] = bar[n]
        if licensed_replay:
            current['jobs'][-1]['licensed_replay']=True
            state('ADOPT licensed replay n=%d: prior start had a measured find; new actual input traces without Samanyu seed ancestry; deadline00:15Z' % n)
        ctl.save_plan(current)
        state('START handoff %s n=%d side=%.12f bar=%.12f on %s; log work/%s/run/; deadline 00:15Z; input %s' % (
            kind, n, side, math.sqrt(n) * (1 + bar[n]), box, box, p))
        seen[sig] = 'queued'


def order_queues():
    for box in ctl.REMOTE:
        cmd = ('cd ~/' + ctl.RDIR + ' && until mkdir qlock 2>/dev/null; do sleep 1; done; '
               './py qorder.py queue.txt; rc=$?; rmdir qlock; exit $rc')
        subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box], cmd], check=True)


def watch_once():
    # Geometry intake also handles complete designs and validates their ancestry.
    order_queues()


def _take_score(d, n):
    try:
        for r in csv.DictReader(open('%s/%s/take.tsv' % (ctl.S, d)), delimiter='\t'):
            if int(r['n']) == n:
                return float(r.get('new') or r.get('score'))
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return None


def idle_fill():
    """Round 25: a box whose queue is empty and whose worker is idle gets one long island (seed 14, 1800 s, --dry 360)
    from the certified round 25 layout of another lane with the largest step below the base, once per layout."""
    if time.time() >= float(open(ctl.W + '/deadline').read()) - 600:
        return
    held = ctl.held_scores()
    allbar = bars()   # round 26: a start above the all-lane bar is stopped by stop_old at once (15:58Z harvest 791)
    pl = ctl.load_plan()
    # Round 26: one running island per n (13:58Z two went to 328). A file a lane rewrites (midm 972) may get a new island.
    done = {(j['n'], j.get('path'), j.get('file_mtime')) for j in pl['jobs'] if j['mode'] == 'island'}
    island_n = set()
    for j in pl['jobs']:
        if j['mode'] == 'island' and not j.get('skipped'):
            log = '%s/%s/run/%d-%s/chain.log' % (ctl.W, j['box'], j['n'], j['tag'])
            if not (os.path.exists(log) and re.search(r'CHAINEND|^DRY|^STOPPED', open(log).read(), re.M)):
                island_n.add(j['n'])
    cands = []
    for kind, tag, d in ctl.live_dirs():
        for p in glob.glob('%s/%s/[0-9]*.csv' % (ctl.S, d)):
            if not re.match(r'^\d+\.csv$', os.path.basename(p)) or time.time() - os.stat(p).st_mtime < 60:
                continue
            n = int(os.path.basename(p)[:-4])
            if (n, p, os.stat(p).st_mtime) in done or n in island_n:
                continue
            # Round 26: the lane's own take.tsv score, not a floatsafe run per file each minute (at load 48 on
            # boxA that loop took over 10 minutes while the boxes sat idle). collect certifies every result anyway.
            score = _take_score(d, n)
            if score is not None and score < held[n] - ctl.BAR and score <= allbar.get(n, score) + ctl.SAME:
                cands.append((score - held[n], n, kind, p))
    # Round 26 measured: islands on midm kick files found (791: 8 finds and fq, 972: 8 finds), islands on harvest and
    # backlog bar files went dry (850, 971, 910). midm files go first, then the largest step below the base.
    cands.sort(key=lambda c: (0 if c[2] in KICK else 1, c[0]))
    for c in list(cands):
        gain, n, kind, p = c
        try:
            mtime = os.stat(p).st_mtime
        except OSError:
            continue
        if kind not in KICK or time.time() - mtime > 2400 or time.time() - mtime < 600:
            continue
        cands.remove(c)
        box = ctl.WATCH_SLOTS[len(ctl.load_plan()['jobs']) % len(ctl.WATCH_SLOTS)]
        if ctl.add(n, p, kind, box, mode='island', prefix='f', near_only=True):
            cur = ctl.load_plan(); cur['jobs'][-1]['monitor_bar'] = held[n]; cur['jobs'][-1]['file_mtime'] = mtime; ctl.save_plan(cur)
            island_n.add(n)
            state('START fresh island n=%d from %s (%.3e below base, written %s) on %s ahead of the probes; log work/%s/run/; deadline 00:05Z' % (
                n, p, -gain, time.strftime('%H:%M:%SZ', time.gmtime(mtime)), box, box))
    cands = [c for c in cands if c[1] not in island_n]
    cands = []         # round 32: no idle islands on other lanes' take rows either (round 31: 0 finds); lk_fill fills idle slots
    pool = ctl.W + '/island-pool.json'
    if os.path.exists(pool):
        for n, p, kind in json.load(open(pool)):
            if os.path.exists(p) and (n, p, os.stat(p).st_mtime) not in done and n not in island_n and held[n] <= allbar.get(n, held[n]) + ctl.SAME:
                cands.append((0.0, n, kind, p))
    # Round 26: a kept row gets another island from its own legal best once its chain ended (round 7: a new start from
    # the legal best finds again), at most twice per job, on the box that holds its run dir.
    again = []
    kept = json.load(open(ctl.W + '/kept.json')) if os.path.exists(ctl.W + '/kept.json') else {}
    # Round 28: a legal near result handed to the lanes (export_near) also gets its again islands, and they go to the head
    # of their box queue at once instead of waiting for an idle box (01:30Z: the 593 near result waited behind 12 starts).
    if os.path.exists(ctl.W + '/near-exported.json'):
        kept = dict(json.load(open(ctl.W + '/near-exported.json')), **kept)
    for j in pl['jobs']:
        if str(j['n']) not in kept or j.get('skipped') or j.get('agains', 0) >= 4:   # round 28: up to 4 (593: legs 2 and 3 still found)
            continue
        d = '%s/%s/run/%d-%s' % (ctl.W, j['box'], j['n'], j['tag'])
        if not os.path.exists(d + '/chain.log') or not any(re.search(r'^FIND ', open(q).read(), re.M) for q in glob.glob(d + '/soft-*.log')):
            continue
        ctext = open(d + '/chain.log').read()
        if j.get('agains', 0) and re.search(r'^DRY-AGAIN[^\n]*\n*$', ctext, re.M) and ctext.rstrip().splitlines()[-1].startswith('DRY-AGAIN'):
            continue                      # round 28: the last again leg found nothing, so no more
        ends = len(re.findall(r'^(?:CHAINEND|DRY|STOPPED)', ctext, re.M))
        if ends >= 1 + j.get('agains', 0):
            again.append(j)
    seen_n = set(); uniq = []
    for c in cands:
        if c[1] not in seen_n:
            seen_n.add(c[1]); uniq.append(c)
    cands = uniq
    for j in list(again):
        if j.get('mode') in ('certified', 'sfq'):
            continue
        again.remove(j)
        if ctl.push(j['box'], '%s/starts/%d-%s.csv' % (ctl.W, j['n'], j['tag']), '%d %s again' % (j['n'], j['tag'])):
            cur = ctl.load_plan()
            for jj in cur['jobs']:
                if (jj['n'], jj['tag']) == (j['n'], j['tag']):
                    jj['agains'] = jj.get('agains', 0) + 1
            ctl.save_plan(cur)
            state('START island again n=%d %s from its own legal best on %s, head of the queue (a find of this round; round 7: a restart from the legal best finds again); log work/%s/run/%d-%s; deadline 00:05Z' % (j['n'], j['tag'], j['box'], j['box'], j['n'], j['tag']))
    for box in ctl.REMOTE:
        if not cands and not again:
            return
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box],
                            'cd ~/%s && wc -l < queue.txt && pgrep -f "[c]hain[.]sh" | wc -l' % ctl.RDIR],
                           capture_output=True, text=True)
        out = r.stdout.split()
        if len(out) != 2 or out[0] != '0' or int(out[1]) >= ctl.WORKERS.get(box, 1):
            continue
        mine = [j for j in again if j['box'] == box]
        if mine:
            j = mine[0]; again.remove(j)
            if ctl.push(box, '%s/starts/%d-%s.csv' % (ctl.W, j['n'], j['tag']), '%d %s again' % (j['n'], j['tag'])):
                cur = ctl.load_plan()
                for jj in cur['jobs']:
                    if (jj['n'], jj['tag']) == (j['n'], j['tag']):
                        jj['agains'] = jj.get('agains', 0) + 1
                ctl.save_plan(cur)
                state('START island again n=%d %s from its own legal best on %s (kept row; round 7: a restart from the legal best finds again); log work/%s/run/%d-%s; deadline 00:05Z' % (j['n'], j['tag'], box, box, j['n'], j['tag']))
                continue
        while cands:
            gain, n, kind, p = cands.pop(0)
            mtime = os.stat(p).st_mtime
            if ctl.add(n, p, kind, box, mode='island', prefix='i'):
                cur = ctl.load_plan(); cur['jobs'][-1]['monitor_bar'] = held[n]; cur['jobs'][-1]['file_mtime'] = mtime; ctl.save_plan(cur)
                state('START idle island n=%d from %s (%.3e below base) on %s; log work/%s/run/; deadline 00:05Z' % (n, p, -gain, box, box))
                break


LK_LINE = re.compile(r'kick|claim', re.I)


def kick_named():
    """n named by a kick or claim line of another lane in handoff-r33.log (round 32: a held row no lane kicked in rounds 29
    to 32; the pool already leaves out the n of rounds 29 to 31). A line names n by n=N or by a per-n csv path."""
    out = set()
    try:
        lines = open(ctl.HANDOFF, errors='replace').read().splitlines()
    except OSError:
        return out
    for line in lines:
        if not LK_LINE.search(line) or re.match(r'\S+\s+(?:\S+\s+)?soft\s*->', line):
            continue
        out.update(int(m) for m in re.findall(r'\bn ?= ?(\d{1,4})\b', line))
        out.update(int(m) for m in re.findall(r'/(\d{1,4})(?:-[^/\s,;]*)?\.csv', line))
    return out


def held_start(n):
    """the held round 32 a row of n as W/held33/N.csv (a byte copy of no other file: provenance reads it as the held row)"""
    d = ctl.W + '/held33'; os.makedirs(d, exist_ok=True)
    p = '%s/%d.csv' % (d, n)
    if not os.path.exists(p):
        rows = [{k: r[k] for k in ctl.KEYS} for r in csv.DictReader(open(ctl.HELD_FILE, newline='')) if int(r['n']) == n]
        ctl.write_rows(p, sorted(rows, key=lambda r: int(r['square_id'])))
    return p


def lk_fill():
    """Round 32: a box with no waiting line and fewer running chains than workers gets a 150 s lkick chain (mode lk) of the
    next held row of W/lk-pool.json (sel32.py: held rows no kick line of rounds 29 to 31 names) that no other lane named in
    a kick or claim line this round and no live take holds lower; ctl.add posts our claim with the sha256 first.
    Decision (STATE.txt 11:5xZ): lk fills idle slots from the start of the round, behind fresh forensics rect islands
    (qorder priority 5.5 against 3.0 to 4.5), instead of waiting for 14:30Z with idle slots."""
    if time.time() >= float(open(ctl.W + '/deadline').read()) - 420 or os.path.exists(ctl.W + '/STOPLK'):
        return
    pp = ctl.W + '/lk-pool.json'
    if not os.path.exists(pp):
        return
    pool = [int(x) for x in json.load(open(pp))]
    tp = ctl.W + '/lk-tried.json'
    tried = set(json.load(open(tp))) if os.path.exists(tp) else set()
    held = ctl.held_scores(); allbar = bars(); named = kick_named()
    left = [n for n in pool if n not in tried and n not in named and allbar.get(n, held[n]) >= held[n] - ctl.BAR]
    if not left:
        # round 32 (14:2xZ): when the first pool is spent, a second pass over W/lk-pool2.json with its own tried file. The new
        # job of an n gets the tag hhel1, and lkleg.py gives that tag the seed 3401, so it does not replay the first leg
        # (the 11:35Z control replayed a seed-3201 lkick try for try). Why a second seed: midm measured 2 of 11 second kicks
        # of rows with no first find certifying, and border's round 31 second seeds gave 494 and 864.
        pp2 = ctl.W + '/lk-pool2.json'
        if not os.path.exists(pp2):
            return
        tp = ctl.W + '/lk-tried2.json'
        tried = set(json.load(open(tp))) if os.path.exists(tp) else set()
        left = [int(n) for n in json.load(open(pp2))]
        left = [n for n in left if n not in tried and n not in named and allbar.get(n, held[n]) >= held[n] - ctl.BAR]
        if not left:
            return
    for box in ctl.REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box],
                            'cd ~/%s && wc -l < queue.txt && pgrep -f "[c]hain[.]sh" | wc -l' % ctl.RDIR],
                           capture_output=True, text=True)
        out = r.stdout.split()
        if len(out) != 2:
            continue
        # round 32 (13:3xZ): one lk line may wait in the box queue beyond the workers. With none waiting, a slot sat idle
        # 2.5 min after each 150 s chain until the next cycle (boxC 906 ended 13:25:46, its worker took the next at 13:28:16).
        # qorder.py ranks lk at 5.5, so a fresh rect island still goes ahead of the waiting lk line.
        free = ctl.WORKERS.get(box, 1) + 1 - int(out[0]) - int(out[1])
        while free > 0 and left:
            n = left.pop(0)
            tried.add(n); json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
            p = held_start(n)
            if ctl.add(n, p, 'held', box, mode='lk', prefix='h'):
                src, lic = ctl.source_of(n)
                cur = ctl.load_plan(); j = cur['jobs'][-1]
                j['monitor_bar'] = held[n]; j['where'] = 'held'
                j['source'] = 'the held round32-2026-11-16a.csv row of n=%d (%s)' % (n, src); j['licence'] = lic
                ctl.save_plan(cur)
                # the assembler-style walk (quench_walk.check) has no record of a held copy and reads a public held row
                # as public-first ("no root: no held reference"); round 32 rule 2: a held row and its descendants are our
                # own layout, with no share gate. Our trace reads the copy as the held row (provenance.held_copy).
                ap = ctl.W + '/walk-allow.json'
                allow = json.load(open(ap)) if os.path.exists(ap) else {}
                allow[j['input_sha256']] = 'held round32-2026-11-16a.csv row of n=%d (byte copy held33/%d.csv; rule 2)' % (n, n)
                json.dump(allow, open(ap + '.tmp', 'w'), indent=0); os.rename(ap + '.tmp', ap)
                free -= 1
                state('START lk n=%d held round 32 a row (%s, claimed) on %s, 150 s invent_rest lkick legs then fq; log work/%s/run/%d-%s/chain.log; deadline 00:05Z' % (
                    n, p, box, box, n, j['tag']))
            else:
                state('REFUSE lk n=%d: %s' % (n, getattr(ctl, 'LAST_ADMISSION_REASON', '')))


SELF_CHAIN = ('backlog', 'border', 'harvest', 'classfill', 'soft')
UNCLAIMED = 600


def named_since(n, t0, owner=None):
    """another lane's kick or claim line in handoff-r33.log that names n and was written at or after t0 - 60 s. A line of
    the lane that wrote the file (owner) counts only when it claims: its own certify line names its recipe ('900 s kick')
    and is not a claim (19:2xZ: rebuild's certify line of 812 read as a claim)."""
    import calendar
    try:
        lines = open(ctl.HANDOFF, errors='replace').read().splitlines()
    except OSError:
        return None
    for line in lines:
        if not LK_LINE.search(line) or re.match(r'\S+\s+(?:\S+\s+)?soft\s*->', line):
            continue
        m = re.match(r'(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)', line)
        if not m:
            continue
        if calendar.timegm(time.strptime(m[1] + ' ' + m[2], '%Y-%m-%d %H:%M:%S')) < t0 - 60:
            continue
        ns = {int(x) for x in re.findall(r'\bn ?= ?(\d{1,4})\b', line)} | \
             {int(x) for x in re.findall(r'/(\d{1,4})(?:-[^/\s,;]*)?\.csv', line)}
        if n in ns:
            lane = re.match(r'\S+\s+(?:\S+\s+)?([a-z0-9-]+)\s*->', line)
            if owner and lane and lane[1] == owner and 'claim' not in line.lower():
                continue
            return line[:160]
    return None


def fresh_lk():
    """Round 33: 150 s lkick legs (mode lk, tag u...) of another lane's fresh certified take row that no lane claimed for
    10 minutes (brief lesson 6d: fresh takes of the self-chaining lanes backlog, border, harvest, classfill and soft are
    theirs; other lanes' rows are open after 10 unclaimed minutes). Only the lowest live row of an n (lesson 6d), once per
    file version (n and sha256). Why: round 32 backlog's lkick follows of fresh rows gave 17 of its 31 certified steps and
    its three largest rows, and the held-row lkick pool of n 400 to 699 is empty in round 33 (sel33.py: every row with a
    gap was lkicked or is a closed-form, shared or lattice side)."""
    if time.time() >= float(open(ctl.W + '/deadline').read()) - 420 or os.path.exists(ctl.W + '/STOPFRESH'):
        return
    held = ctl.held_scores(); allbar = bars()
    tp = ctl.W + '/fresh-tried.json'
    tried = set(json.load(open(tp))) if os.path.exists(tp) else set()
    cands = []
    for kind, tag, d in ctl.live_dirs():
        m = re.match(r'take-(.+)-r\d+$', d)
        lane = m[1] if m else kind
        if lane in SELF_CHAIN:
            continue
        for p in glob.glob('%s/%s/[0-9]*.csv' % (ctl.S, d)):
            if not re.match(r'^\d+\.csv$', os.path.basename(p)):
                continue
            try:
                mtime = os.stat(p).st_mtime
            except OSError:
                continue
            if time.time() - mtime < UNCLAIMED:
                continue
            n = int(os.path.basename(p)[:-4])
            score = _take_score(d, n)
            if score is None or n not in held or score >= held[n] - ctl.BAR or score > allbar.get(n, score) + 1e-12:
                continue
            try:
                sha = hashlib.sha256(open(p, 'rb').read()).hexdigest()
            except OSError:
                continue
            key = '%d:%s' % (n, sha)
            if key in tried:
                continue
            who = named_since(n, mtime, lane)
            if who:
                tried.add(key)
                state('SKIP fresh lk n=%d %s (claimed after it was written: %s)' % (n, p, who))
                continue
            cands.append((score - held[n], n, lane, p, key, mtime))
    json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
    if not cands:
        return
    cands.sort()
    for box in ctl.REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box],
                            'cd ~/%s && { grep -c " lk$" queue.txt || :; } && pgrep -f "[c]hain[.]sh" | wc -l' % ctl.RDIR],
                           capture_output=True, text=True)
        out = r.stdout.split()
        if len(out) != 2:
            continue
        # waiting lk lines only: a fresh row goes ahead of rect islands in the queue (qorder 2.0 against 3.0 to 4.5)
        free = ctl.WORKERS.get(box, 1) + 1 - int(out[0]) - int(out[1])
        while free > 0 and cands:
            gain, n, lane, p, key, mtime = cands.pop(0)
            tried.add(key); json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
            if ctl.add(n, p, lane, box, mode='lk', prefix='u'):
                cur = ctl.load_plan(); j = cur['jobs'][-1]
                j['monitor_bar'] = held[n]; j['file_mtime'] = mtime; ctl.save_plan(cur)
                free -= 1
                state('START fresh lk n=%d %s row %s (%.3e below bar33, written %s, unclaimed 10 min, lowest live) on %s, 150 s lkick legs then fq; log work/%s/run/%d-%s/chain.log; deadline 00:05Z' % (
                    n, lane, p, -gain, time.strftime('%H:%M:%SZ', time.gmtime(mtime)), box, box, n, j['tag']))
            else:
                state('REFUSE fresh lk n=%d %s: %s' % (n, p, getattr(ctl, 'LAST_ADMISSION_REASON', '')))


def rect_lk_fill():
    """Round 33 (main session 19:0xZ: keep the boxes busy; sel33.py finds no held row of n 400 to 699 whose current
    geometry no lane lkicked in rounds 29 to 33): a free slot gets one 150 s lkick chain (mode lk, tag r...) of a fresh
    forensics rectangle near file that near_files left as tight (1.5e-4 of score or less over the bar, where islands found
    nothing in rounds 27 and 28), 10 to 60 minutes after it was written, when no other lane named its n since then. This is
    a first lkick of fresh geometry (lesson 6a); fresh islands and fresh-row follows go first (qorder 5.5 against 2.0 to 4.5)."""
    if time.time() >= float(open(ctl.W + '/deadline').read()) - 420 or os.path.exists(ctl.W + '/STOPLK'):
        return
    sp = ctl.W + '/follow-seen.json'
    seen = json.load(open(sp)) if os.path.exists(sp) else {}
    tp = ctl.W + '/rect-tried.json'
    tried = set(json.load(open(tp))) if os.path.exists(tp) else set()
    held = ctl.held_scores(); allbar = bars()
    cands = []
    for sig, why in seen.items():
        # 19:4xZ: rect files that got an island (seen 'queued') come too, behind the tight ones: the four tight lkicks
        # (456 582 790 806) were dry and the boxes sat idle (main session: keep them busy)
        if not (str(why).startswith('tight forensics') or (why == 'queued' and '/take-forensics-r' in sig)) or sig in tried:
            continue
        path, mns, size = sig.rsplit(':', 2)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if '%s:%s:%s' % (path, st.st_mtime_ns, st.st_size) != sig or not 600 <= time.time() - st.st_mtime <= FRESH_MAX:
            continue
        m = re.match(r'(\d+)-rect\.csv$', os.path.basename(path))
        if not m:
            continue
        n = int(m[1])
        if n not in held or named_since(n, st.st_mtime, 'forensics'):
            continue
        mm = re.search(r'tight forensics file ([-0-9.e+]+)', str(why))
        cands.append((float(mm[1]) if mm else 1.0, n, path, sig, st.st_mtime))
    # 21:3xZ: fresh near files of invent and classfill (their own fresh geometry, 10 to 60 minutes old) within 2e-4 of
    # score over the all-lane bar come after the forensics files, when no lane named their n since they were written:
    # forensics wrote few rect files after 21:00Z and two of three slots sat idle (main session: keep the boxes busy).
    for lane in ('invent', 'classfill'):
        for path in glob.glob('%s/take-%s-r%d/near/**/*.csv' % (ctl.S, lane, ctl.RN), recursive=True):
            try:
                st = os.stat(path)
            except OSError:
                continue
            sig = '%s:%s:%s' % (path, st.st_mtime_ns, st.st_size)
            if sig in tried or not 600 <= time.time() - st.st_mtime <= FRESH_MAX:
                continue
            try:
                rows = ctl.rows_of(path)
                n = int(rows[0]['n'])
                if len(rows) != n or n not in held:
                    continue
                X = [(float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s')), float(str(r['angle']).lstrip('s'))) for r in rows]
                h = [(abs(math.cos(a)) + abs(math.sin(a))) / 2 for _, _, a in X]
                side = max(max(x + q for (x, _, _), q in zip(X, h)) - min(x - q for (x, _, _), q in zip(X, h)),
                           max(y + q for (_, y, _), q in zip(X, h)) - min(y - q for (_, y, _), q in zip(X, h)))
            except Exception:
                continue
            margin = side / math.sqrt(n) - 1 - allbar.get(n, held[n])
            if not 0 < margin <= 2e-4 or named_since(n, st.st_mtime, lane):
                continue
            cands.append((10 + margin, n, path, sig, st.st_mtime))
    if not cands:
        return
    cands.sort()
    seen_n = set(); uniq = []
    for c in cands:
        if c[1] not in seen_n:
            seen_n.add(c[1]); uniq.append(c)
    cands = uniq
    for box in ctl.REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box],
                            'cd ~/%s && wc -l < queue.txt && pgrep -f "[c]hain[.]sh" | wc -l' % ctl.RDIR],
                           capture_output=True, text=True)
        out = r.stdout.split()
        if len(out) != 2:
            continue
        free = ctl.WORKERS.get(box, 1) - int(out[0]) - int(out[1])
        while free > 0 and cands:
            margin, n, path, sig, mtime = cands.pop(0)
            tried.add(sig); json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
            kind = re.search(r'/take-([a-z0-9-]+)-r\d+/', path)[1]
            if ctl.add(n, path, kind, box, mode='lk', prefix='r'):
                cur = ctl.load_plan(); j = cur['jobs'][-1]
                j['monitor_bar'] = held[n]; j['file_mtime'] = mtime; ctl.save_plan(cur)
                free -= 1
                state('START rect lk n=%d %s (%.1e over the bar, written %s, tight for an island) on %s, 150 s lkick legs then fq; log work/%s/run/%d-%s/chain.log; deadline 00:05Z' % (
                    n, path, margin, time.strftime('%H:%M:%SZ', time.gmtime(mtime)), box, box, n, j['tag']))
            else:
                state('REFUSE rect lk n=%d %s: %s' % (n, path, getattr(ctl, 'LAST_ADMISSION_REASON', '')))


DEEP_LAST = 1794870900    # 23:15Z: the last deep start (main session 21:46Z)
BORDER_W = ctl.S + '/take-border-r33/work'
BORDER_REACH = 8          # border queued about 4 deep rows an hour from 20:12Z; its feeder stops 25 min before 00:05Z


def deep_order():
    """The held rows of the shared deep-kick queue (main session 21:46Z) in border's deep order (border deepfeed33.py: held33
    info.json, board gap at least 1e-5, not rigid, bad, lattice or spent, no unprobed 900 s kick in rounds 31 and 32,
    largest board gap first), and the index in it past which border's workers cannot reach before their feeder stops."""
    info = {int(k): v for k, v in json.load(open(BORDER_W + '/held33/info.json')).items()}
    skip = {639, 691, 745, 858, 918, 980, 494, 626, 677, 678, 730, 731, 842, 843, 901, 902, 962, 963, 964, 785, 786}
    order = [n for _, n in sorted((-v['gap'], n) for n, v in info.items() if v['gap'] and v['gap'] >= 1e-5 and
                                  not (v['rigid'] or v['bad'] or v['lattice'] or v['spent'] or v['unprobed3132']) and n not in skip)]
    # then the rows above the board side by less than 1e-5 of score that border's order leaves out (gap 1e-7 to 1e-5, same
    # flags; their round 31 and 32 kicks were probed and stopped early, so none had a 900 s kick of this geometry)
    order += [n for _, n in sorted((-v['gap'], n) for n, v in info.items() if v['gap'] and 1e-7 <= v['gap'] < 1e-5 and
                                   not (v['rigid'] or v['bad'] or v['lattice'] or v['spent'] or v['unprobed3132']) and n not in skip)]
    queued = {int(os.path.basename(q).split('-')[0]) for q in glob.glob(BORDER_W + '/kq/manual/*-deep.*')}
    last = max([order.index(n) for n in queued if n in order] or [-1])
    return order, queued, last + BORDER_REACH


def lost_race(n, box, tag, wait=5):
    """Round 33 (main session 22:0xZ, after the 757 race with twoshort): wait a few seconds after our claim line, read the
    log again, and give the start up when another lane's claim line names n at or before ours. Returns that line or None."""
    import calendar
    time.sleep(wait)
    try:
        lines = open(ctl.HANDOFF, errors='replace').read().splitlines()
    except OSError:
        return None
    def ts(line):
        m = re.match(r'(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d:\d\d)', line)
        return calendar.timegm(time.strptime(m[1] + ' ' + m[2], '%Y-%m-%d %H:%M:%S')) if m else None
    mine = [ts(l) for l in lines if re.match(r'\S+\s+soft\s*->', l) and 'claims kick n=%d ' % n in l]
    if not mine or mine[-1] is None:
        return None
    t = mine[-1]
    for line in lines:
        if 'claim' not in line.lower() or re.match(r'\S+\s+(?:\S+\s+)?soft\s*->', line):
            continue
        ns = {int(x) for x in re.findall(r'\bn ?= ?(\d{1,4})\b', line)} | \
             {int(x) for x in re.findall(r'/(\d{1,4})(?:-[^/\s,;]*)?\.csv', line)}
        lt = ts(line)
        if n in ns and lt is not None and t - 600 <= lt <= t:
            ctl.unqueue(box, n, tag); ctl.stop_run(box, n, tag)
            with open(ctl.HANDOFF, 'a') as f:
                f.write('%s soft -> all: releases n=%d (our claim %s): an earlier claim of another lane wins; our start never ran or was stopped at once\n' % (
                    time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, time.strftime('%H:%M:%SZ', time.gmtime(t))))
            return line[:160]
    return None


def deep_fill():
    """Round 33 (main session 21:46Z): a slot with nothing waiting and nothing running gets one unprobed 900 s kick seed
    (mode deep) of the next held row of the shared deep-kick queue that border's workers cannot reach, that no lane named
    on a kick or claim line of this round, and that no live take holds lower; the claim line is posted by ctl.add right
    after the claims are read again. Last start 23:15Z."""
    if time.time() >= DEEP_LAST or os.path.exists(ctl.W + '/STOPDEEP'):
        return
    try:
        order, queued, reach = deep_order()
    except (OSError, ValueError, KeyError):
        return
    tp = ctl.W + '/deep-tried.json'
    tried = set(json.load(open(tp))) if os.path.exists(tp) else set()
    held = ctl.held_scores()
    for box in ctl.REMOTE:
        r = subprocess.run(['ssh', '-o', 'ConnectTimeout=10', ctl.REMOTE[box],
                            'cd ~/%s && wc -l < queue.txt && pgrep -f "[c]hain[.]sh" | wc -l' % ctl.RDIR],
                           capture_output=True, text=True)
        out = r.stdout.split()
        if len(out) != 2:
            continue
        free = ctl.WORKERS.get(box, 1) - int(out[0]) - int(out[1])
        while free > 0:
            allbar = bars()
            left = [n for i, n in enumerate(order) if i > reach and n not in tried and n not in queued and n in held
                    and allbar.get(n, held[n]) >= held[n] - ctl.BAR]
            n = None
            for m in left:
                who = named_since(m, ctl.load_plan().get('t0', 0) - 3600)
                if who:
                    tried.add(m); state('SKIP deep n=%d (named this round: %s)' % (m, who))
                    continue
                n = m; break
            json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
            if n is None:
                return
            tried.add(n); json.dump(sorted(tried), open(tp + '.tmp', 'w')); os.rename(tp + '.tmp', tp)
            p = held_start(n)
            if ctl.add(n, p, 'held', box, mode='deep', prefix='d'):
                src, lic = ctl.source_of(n)
                cur = ctl.load_plan(); j = cur['jobs'][-1]
                j['monitor_bar'] = held[n]; j['where'] = 'held'
                j['source'] = 'the held round32-2026-11-16a.csv row of n=%d (%s)' % (n, src); j['licence'] = lic
                ctl.save_plan(cur)
                ap = ctl.W + '/walk-allow.json'
                allow = json.load(open(ap)) if os.path.exists(ap) else {}
                allow[j['input_sha256']] = 'held round32-2026-11-16a.csv row of n=%d (byte copy held33/%d.csv; rule 2)' % (n, n)
                json.dump(allow, open(ap + '.tmp', 'w'), indent=0); os.rename(ap + '.tmp', ap)
                who = lost_race(n, box, j['tag'])
                if who:
                    cur = ctl.load_plan(); cur['jobs'][-1]['skipped'] = 'lost claim race'; ctl.save_plan(cur)
                    state('RELEASE deep n=%d on %s: an earlier claim wins (%s)' % (n, box, who))
                    continue
                free -= 1
                state('START deep n=%d held round 32 a row (%s, claimed; border order index %d, border reach %d) on %s, one unprobed 900 s kick seed then fq; log work/%s/run/%d-%s/chain.log; deadline 00:05Z' % (
                    n, p, order.index(n), reach, box, box, n, j['tag']))
            else:
                state('REFUSE deep n=%d: %s' % (n, getattr(ctl, 'LAST_ADMISSION_REASON', '')))


def inbox():
    """Round 27: hand starts reach the plan only through this process (a second writer of plan.json can lose a job).
    W/inbox.json holds [n, path, kind, mode, prefix, box or null]; each entry is added once."""
    ip = ctl.W + '/inbox.json'; dp = ctl.W + '/inbox-done.json'
    if not os.path.exists(ip):
        return
    try:
        items = json.load(open(ip))
    except ValueError:
        return
    done = json.load(open(dp)) if os.path.exists(dp) else []
    held = ctl.held_scores()
    took = 0
    for it in items:
        key = json.dumps(it)
        if key in done:
            continue
        # round 31: at most 6 inbox starts per call (each add certifies the start on boxA, 10 to 30 s at load), so a
        # pool of 118 islands does not hold the follow of fresh files for an hour
        took += 1
        if took > 6:
            break
        done.append(key)
        json.dump(done, open(dp + '.tmp', 'w')); os.rename(dp + '.tmp', dp)
        if isinstance(it, dict):
            # a pinned start: the proof was written by hand over immutable snapshots (ctl.add_pinned)
            box = it.get('box') or ctl.WATCH_SLOTS[len(ctl.load_plan()['jobs']) % len(ctl.WATCH_SLOTS)]
            ok = ctl.add_pinned(it['n'], it['path'], it['kind'], box, it['mode'], it['prefix'], json.load(open(it['proof'])),
                                it['source'], it['licence'], it.get('reopen', False))
            state('%s pinned n=%d %s %s reopen=%s from %s on %s; proof %s; deadline 00:05Z' % (
                'START' if ok else 'REFUSE', it['n'], it['kind'], it['mode'], it.get('reopen', False), it['path'], box, it['proof']))
            continue
        n, p, kind, mode, prefix = it[:5]
        box = it[5] if len(it) > 5 and it[5] else ctl.WATCH_SLOTS[len(ctl.load_plan()['jobs']) % len(ctl.WATCH_SLOTS)]
        if not os.path.exists(p):
            state('REFUSE inbox n=%d missing %s' % (n, p)); continue
        if ctl.add(n, p, kind, box, mode=mode, prefix=prefix):
            cur = ctl.load_plan(); cur['jobs'][-1]['monitor_bar'] = held[n]
            cur['jobs'][-1]['file_mtime'] = os.stat(p).st_mtime; ctl.save_plan(cur)
            state('START inbox n=%d %s %s from %s on %s; log work/%s/run/; deadline 00:05Z' % (n, kind, mode, p, box, box))
        else:
            state('REFUSE inbox n=%d %s: %s' % (n, p, getattr(ctl, 'LAST_ADMISSION_REASON', '')))


def cycle():
    import importlib
    import provenance
    importlib.reload(provenance.forensics_sources)
    importlib.reload(ctl.policy)
    sp = ctl.W + '/follow-seen.json'
    seen = json.load(open(sp)) if os.path.exists(sp) else {}
    watch_once()
    inbox()
    bar = bars()
    stop_old(bar)
    near_files(bar, seen)
    json.dump(seen, open(sp + '.tmp', 'w')); os.rename(sp + '.tmp', sp)
    order_queues()
    idle_fill()
    fresh_lk()
    lk_fill()
    deep_fill()
    rect_lk_fill()
    ctl.collect()
    state('FINISH follow cycle: %d jobs; %s; next fresh k123 short starts, design probes, then idle islands; deadline 00:15Z' % (
        len(ctl.load_plan()['jobs']), open(ctl.W + '/totals.json').read()))


def main():
    deadline = float(open(ctl.W + '/deadline').read())
    state('START follow.py every 120 s, log work/follow.log, feed until 00:05Z, workers end 00:15Z')
    while time.time() < deadline - 300 and not os.path.exists(ctl.W + '/STOPWATCH'):
        try:
            cycle()
        except Exception:
            import traceback
            traceback.print_exc()
        for _ in range(12):
            if os.path.exists(ctl.W + '/STOPWATCH'):
                break
            time.sleep(10)
    state('FINISH handoff watch; next final collect after workers end; deadline 00:22Z')


if __name__ == '__main__':
    main()
