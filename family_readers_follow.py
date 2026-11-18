#!/usr/bin/env python3
"""Follow fresh packing files with immutable, content-keyed reader walks.

The coordinator runs on the archive host. Three serial workers run on the two
boxes. A worker quenches a floatsafe candidate before the coordinator publishes
it. Source records belong to donor versions and never change with a lane's file.
"""
import argparse
import collections
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).parent))
import readers_sources
import readers_anc

ROUND = 25
# Fresh traced designs walk first: modules and k123 paid in round 24; gap and rebuild are new builders.
FRESH = ('take-modules-r25', 'take-k123-r25', 'take-gap-r25', 'take-rebuild-r25')
DEADLINE = '02:45Z'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def job_key(content_hash, direction, pick):
    return f'{content_hash}:{direction}:{pick}'


def geometry_key(fs, packing):
    """A coarse identity for quench copies, independent of row order and box symmetry."""
    np = fs.np
    side, Q = fs.canon(packing)
    variants = []
    for ops in ('', 'T', 'X', 'Y', 'TX', 'TY', 'XY', 'TXY'):
        R = Q.copy()
        for op in ops:
            R = fs.turned(R, side, op)
        _, R = fs.canon(R)
        rounded = np.rint(R * 1e4).astype(np.int64)
        rounded = rounded[np.lexsort((rounded[:, 2], rounded[:, 1], rounded[:, 0]))]
        variants.append(hashlib.sha256(rounded.tobytes()).hexdigest())
    return side, min(variants)


def rows(p, delimiter='\t'):
    try:
        return list(csv.DictReader(open(p), delimiter=delimiter))
    except FileNotFoundError:
        return []


def atomic(p, text):
    p = Path(p)
    tmp = p.with_name(p.name + '.tmp')
    tmp.write_text(text)
    tmp.replace(p)


def tabtext(fields, records):
    out = io.StringIO()
    w = csv.DictWriter(out, fields, delimiter='\t', lineterminator='\n')
    w.writeheader()
    w.writerows(records)
    return out.getvalue()


def stamp():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def mtime(path):
    """Another lane can replace a file between discovery and sorting."""
    try:
        return Path(path).stat().st_mtime
    except OSError:
        return 0.0


def historical_unread(path):
    path = Path(path)
    return path.parent.name == 'unread' and re.search(r'-[a-z0-9]*23$', path.stem) is not None


def reachable_gap(n, m, direction, bar, board):
    """Priority estimate for the first two targets, using the stored per-puzzle board."""
    targets = (n - 2*m - 1, n - 4*m) if direction == 'down' else (n + 2*m + 3, n + 4*m + 8)
    gaps = [(bar[t] + 1) * math.sqrt(t) - board[t]
            for t in targets if 1 <= t <= 1000 and t in bar and t in board]
    return max(gaps, default=math.inf)


def specs(n, m, down_gap, near=False, unranked=False, fresh=False):
    """Both first cuts, below 790 too. New designs tolerate a +0.015 down start."""
    result = []
    if n + 2 * m + 3 <= 1000:
        result += [('up', 0), ('up', 1)]
    if n - 2 * m - 1 >= 1 and (unranked or (down_gap is not None and down_gap < 0.015)):
        result += [('down', 0), ('down', 1)]
    if fresh and not result and n - 2*m - 1 >= 1:
        result.append(('down', 0))
    return result


def fresh_design_cuts(options, path, rnd):
    if rnd == ROUND and any(x in str(path) for x in FRESH):
        if ('down', 0) in options and ('down', 1) not in options:
            return options + [('down', 1)]
    return options


def deferred_rows(jobs):
    result = []
    for job in jobs:
        prefix = job['name'].split('-', 1)[0][:-8]
        allow = 'rectangle-part-excluded' if job.get('part_only') else prefix
        if job.get('part_only') or prefix in ('y', 'b', 'a8', 'a3', 'a4', 'a5'):
            result.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix=allow))
    return result


def cut_priority(priority, pick):
    return {'a0': 'a3', 'a1': 'a4', 'a2': 'a5'}.get(priority, priority) if pick else priority


def whole_layout(path):
    return '/work/interior/' not in str(path)


def sidecar_source(path, source, licence):
    for meta in (Path(str(path) + '.json'), Path(path).with_suffix('.json')):
        if not meta.exists():
            continue
        try:
            item = json.loads(meta.read_text())
            if isinstance(item.get('source'), str) and isinstance(item.get('licence'), str):
                return f'{source}; {meta}: {item["source"]}', item['licence']
        except (OSError, ValueError, AttributeError):
            continue
    return source, licence


def pending_versions(data, completed):
    pending = collections.defaultdict(list)
    for key, job in data['jobs'].items():
        if job.get('part_only'):
            continue
        h = key.split(':')[0]
        if (h, job['direction'], job['pick']) not in completed:
            pending[h].append(job)
    return pending


class Follow:
    def __init__(self, scratch):
        self.s = Path(scratch)
        self.t = self.s / f'take-readers-r{ROUND}'
        self.w = self.t / 'work'
        self.b = self.w / 'box'
        self.statefile = self.w / 'follow.json'
        self.data = readers_anc.load(self.statefile, self.w / 'anc') if self.statefile.exists() else {
            'seen': {}, 'jobs': {}, 'sources': {}, 'archives': {}, 'quenches': {},
            'published': [], 'sequence': 0}
        self.held = {int(r['n']): float(r['score']) for r in rows(self.w / 'details.csv', ',')}
        self.board = {int(r['n']): float(r['board_L']) for r in rows(self.s / 'main-r17/gap-by-n.tsv')}
        self.py = sys.executable
        self.code = Path(__file__).parent
        sys.path.insert(0, str(self.code))
        import family_readers
        self.fr = family_readers
        self.oldwalks = set()
        self.references = collections.defaultdict(list)
        self.geometry_cache = self.data.setdefault('geometry_cache', {})
        previous = self.s / f'take-readers-r{ROUND - 1}/work'
        self.previous = previous
        # A compact copy (seen and geometry only); the full round 24 state is 175 MB.
        self.previous_data = json.loads((self.w / 'previous-compact.json').read_text())
        self.geometry_cache.update(self.previous_data.get('geometry_cache', {}))
        for p in previous.glob('out-*/rows-walk-*.tsv'):
            for r in rows(p):
                if r['shells'].split('c')[0] != '1':
                    continue
                donor = previous / 'box/donors' / (r['donor'] + '.csv')
                if donor.exists():
                    pick = int(r['shells'].split('c')[1]) if 'c' in r['shells'] else 0
                    h = digest(donor)
                    self.oldwalks.add((h, r['direction'], pick))
                    side, geom = self.geometry(donor, h)
                    self.references[(geom, r['direction'], pick)].append((side, h))
        deferred = []
        current_bar = self.bars()
        for key, job in self.data['jobs'].items():
            h = key.split(':')[0]
            path = self.b / 'donors' / (job['donor'] + '.csv')
            if not whole_layout(self.data['seen'].get(h, {}).get('path', '')):
                deferred.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix='rectangle-part-excluded'))
                job['part_only'] = True
                continue
            side, geom = self.geometry(path, h)
            n = int(job['donor'].split('-')[0])
            gap = reachable_gap(n, int(math.floor(side + 1e-9)), job['direction'], current_bar, self.board)
            job['reachable_board_gap'] = gap if math.isfinite(gap) else None
            job['low_gap'] = gap < 1e-3
            refkey = (geom, job['direction'], job['pick'])
            copy = any(abs(side - old_side) < 1e-5 for old_side, _ in self.references[refkey])
            job['quench_copy'] = copy
            if copy:
                deferred.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix='y'))
                if not job['name'].startswith('y'):
                    old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
                    if old.exists():
                        prefix, rest = job['name'].split('-', 1)
                        job['name'] = 'y' + prefix[-8:] + '-' + rest + '-copy'
                        shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
            else:
                self.references[refkey].append((side, h))
                if historical_unread(self.data['seen'].get(h, {}).get('path', '')):
                    allowed = 'y' if job['name'].startswith('y') else 'b'
                    deferred.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix=allowed))
                    if not job['name'].startswith(allowed):
                        old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
                        if old.exists():
                            prefix, rest = job['name'].split('-', 1)
                            job['name'] = 'b' + prefix[-8:] + '-' + rest + '-frozen'
                            shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
                elif job['low_gap'] and job['name'].startswith('a') and not job.get('near_promoted') and not job.get('manual_priority') and not any(x in self.data['seen'].get(h, {}).get('path', '') for x in FRESH):
                    deferred.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix='a8'))
                    if not job['name'].startswith('a8'):
                        old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
                        if old.exists():
                            prefix, rest = job['name'].split('-', 1)
                            job['name'] = 'a8' + prefix[-8:] + '-' + rest + '-smallgap'
                            shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
        for job in self.data['jobs'].values():
            prefix = job['name'].split('-', 1)[0]
            new_priority = cut_priority(prefix[:-8], job['pick'])
            if new_priority == prefix[:-8] or job.get('part_only'):
                continue
            old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
            if old.exists():
                job['name'] = new_priority + prefix[-8:] + '-' + job['name'].split('-', 1)[1] + '-cut1'
                shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
                deferred.append(dict(donor=job['donor'], direction=job['direction'], pick=job['pick'], allow_prefix=new_priority))
        atomic(self.b / 'defer.tsv', tabtext(['donor', 'direction', 'pick', 'allow_prefix'], deferred_rows(self.data['jobs'].values())))
        copies = sum(r['allow_prefix'] == 'y' for r in deferred)
        historical = sum(r['allow_prefix'] == 'b' for r in deferred)
        small = sum(r['allow_prefix'] == 'a8' for r in deferred)
        self.state(f'QUEUE RANK {copies} quench copies last, {historical} historical unread walks after r25, {small} walks with first-two-target board gap under 0.001 side after fresh designs; log work/box/defer.tsv')
        self.save()

    def geometry(self, path, h):
        if h not in self.geometry_cache:
            n = int(Path(path).name.split('-')[0].split('.')[0])
            self.geometry_cache[h] = geometry_key(self.fr.fs, self.fr.fs.load(path)[n])
        return self.geometry_cache[h]

    def state(self, message):
        with open(self.t / 'STATE.txt', 'a') as f:
            f.write(f'{stamp()} boxA {message}\n')

    def save(self):
        readers_anc.save(self.statefile, self.data, self.w / 'anc')
        atomic(self.w / 'sources-all.tsv', tabtext(['donor', 'source', 'licence'], [
            dict(donor=d, source=v[0], licence=v[1]) for d, v in self.data['sources'].items()]))

    def bars(self):
        bar = dict(self.held)
        for p in list(self.s.glob(f'take-*-r{ROUND}/take.tsv')):
            if 'assemble' in str(p):
                continue
            for r in rows(p):
                n = int(r['n'])
                bar[n] = min(bar[n], float(r['new']))
        return bar

    def discover(self):
        found = []
        for rnd in (ROUND,):
            for directory in sorted(self.s.glob(f'take-*-r{rnd}')):
                if 'assemble' in directory.name:
                    continue
                take = {int(r['n']): r for r in rows(directory / 'take.tsv')}
                for n, r in take.items():
                    p = directory / f'{n}.csv'
                    if p.exists():
                        found.append((p, n, rnd, False, f'{directory.name}/take.tsv: {r["source"]}', r.get('licence', 'see source')))
                for p in sorted((directory / 'near').glob('*.csv')):
                    returning = directory == self.t
                    if returning and not re.match(r'^\d+-down2(?:c\d+)?from\d+-r(?:24|25)h[0-9a-f]+$', p.stem):
                        continue
                    try:
                        n = int(p.stem.split('-')[0])
                    except ValueError:
                        continue
                    # Frozen near layouts already had a full round. These named
                    # late near misses are explicit next steps in the r23 reports.
                    if rnd == 23 and not ((directory.name == 'take-stair-c-r23' and n == 921)
                                          or (directory.name == 'take-border-r23' and n == 929)):
                        continue
                    r = take.get(n, {})
                    source = f'{directory.name}/near/{p.name}; {directory.name}/take.tsv; results/round23-best-2026-11-13.tsv'
                    if returning:
                        parent = p.stem.split('from', 1)[1]
                        parent_source = self.data['sources'].get(parent, [source, 'see source'])
                        source = f'two shells down from {parent_source[0]}; return walk from {p}'
                        r = {'licence': parent_source[1]}
                    source, licence = sidecar_source(p, source, r.get('licence', 'see source'))
                    found.append((p, n, rnd, True, source, licence))
        # Carry only immutable versions with an unstarted first cut. Frozen
        # public donors can disappear from a live take after a kick or retraction.
        pending = {}  # Carried cuts were audited and ranked before worker launch.
        for h, jobs in pending.items():
            donor = jobs[0]['donor']
            p = self.previous / 'box/donors' / (donor + '.csv')
            if p.exists():
                source, licence = self.previous_data['sources'][donor]
                found.append((p, int(donor.split('-')[0]), 23, False, source, licence))
        # A handoff can point to an unquenched build outside near/.
        log = self.s / f'handoff-r{ROUND}.log'
        withdrawn = set()
        if log.exists():
            for line in log.read_text().splitlines():
                if 'WITHDRAW' in line:
                    withdrawn.update(re.findall(re.escape(str(self.s)) + r'/[^\s;,()]+\.csv', line))
                # Claims of saved starts are not new designs.
                if not re.search(r'-> [^:]*\b(?:readers|all)\b[^:]*:', line) or re.search(r'\bCLAIMS?\b|claims |WITHDRAW', line):
                    continue
                for match in re.finditer(re.escape(str(self.s)) + r'/[^\s;,()]+\.csv', line):
                    p = Path(match.group())
                    if not p.exists() or p.is_relative_to(self.t) or '/take-' not in str(p) or not whole_layout(p):
                        continue
                    try:
                        rr = rows(p, ',')
                        n = int(rr[0]['n'])
                    except (ValueError, KeyError, IndexError):
                        continue
                    known = next((item for item in found if item[0] == p), None)
                    source, licence = (known[4], known[5]) if known else (f'{p}; {line[:400]}', 'see source')
                    source, licence = sidecar_source(p, source, licence) if not known else (source, licence)
                    found.append((p, n, ROUND - 1 if historical_unread(p) else ROUND, False, source, licence))
        # Certified live files and explicit handoffs must not wait behind a large
        # near/ folder. New versions are discovered before frozen seeds too.
        found.sort(key=lambda item: (item[2] != ROUND, not any(x in str(item[0]) for x in FRESH), item[0].parent != self.t / 'near', item[3], -mtime(item[0])))
        return self.strict(readers_sources.admit(found, self.s, self.w, self.data), withdrawn)

    def strict(self, allowed, withdrawn):
        """Round 25 rule: no Samanyu seed, no unresolved seed, no withdrawn lineage, full proof retained."""
        kept = []
        refused = self.data.setdefault('refused_r25', {})
        for item in allowed:
            p, n, rnd, near, source, licence = item
            h = digest(p)
            entry = self.data.get('source_evidence', {}).get(h)
            text = source + ' ' + licence + ' ' + json.dumps(entry) + ' ' + str(p)
            why = readers_sources.out_reason(n, text)
            # Whole path or file name only: a bare count such as 534 would match unrelated text.
            if not why and any(w in text or '/' + Path(w).name in text for w in withdrawn):
                why = 'withdrawn in the handoff log'
            if not why and not (entry and entry.get('ok')):
                why = 'no retained ancestry proof'
            if why:
                if h not in refused:
                    refused[h] = why
                    self.state(f'SOURCE OUT {p}: {why}')
                continue
            kept.append(item)
        return kept

    def enqueue(self, limit=32):
        bar = self.bars()
        count = 0
        for p, n, rnd, near, source, licence in self.discover():
            if not 1 <= n <= 1000:
                continue
            try:
                payload = p.read_bytes()
                h = hashlib.sha256(payload).hexdigest()
            except FileNotFoundError:
                continue
            direct = p.parent.parent == self.s and p.parent.name.startswith('take-')
            live_priority = 'a0' if direct or '/work/unread/' in str(p) else 'a1'
            if h in self.data['seen']:
                old_donor = self.data['seen'][h]['donor']
                if self.data['sources'][old_donor][1] == 'see source' and licence != 'see source':
                    self.data['sources'][old_donor] = [source, licence]
                if rnd == ROUND and not near:
                    original = self.data['seen'][h]
                    if direct and not original.get('certified_source'):
                        original['certified_source'] = str(p)
                        old_source = self.data['sources'][original['donor']][0]
                        self.data['sources'][original['donor']] = [old_source + '; certified as ' + source, licence]
                    for key, job in self.data['jobs'].items():
                        same_path = self.data['seen'].get(key.split(':')[0], {}).get('path') == str(p)
                        promoted_priority = cut_priority(live_priority, job['pick'])
                        promotable = not job.get('near_promoted') and not job.get('low_gap') and (job['name'].startswith('g') or (live_priority == 'a0' and job['name'].startswith('a') and not job['name'].startswith(promoted_priority)))
                        if (key.startswith(h + ':') or same_path) and promotable:
                            old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
                            if old.exists():
                                prefix, rest = job['name'].split('-', 1)
                                job['name'] = promoted_priority + prefix[-8:] + '-' + rest + '-handoff'
                                shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
                                self.state(f'PROMOTE explicit handoff {p} to {job["name"]}; old alias will skip the completed donor walk')
                continue
            count += 1
            if count > limit:
                break
            donor = f'{n}-r{rnd}h{h[:16]}'
            target = self.b / 'donors' / (donor + '.csv')
            target.write_bytes(payload)
            self.data['sources'][donor] = [source, licence]
            info = {'path': str(p), 'donor': donor, 'time': stamp(), 'near': near}
            if self.previous_data['seen'].get(h, {}).get('rank_timeout'):
                info['rank_timeout'] = True
            if direct:
                info['certified_source'] = str(p)
            self.data['seen'][h] = info
            try:
                signal.alarm(25)
                P = self.fr.fs.load(target)[n]
                side = self.fr.fs.canon(P)[0]
                _, geom = self.geometry(target, h)
                m = int(math.floor(side + 1e-9))
                archived_info = self.previous_data['seen'].get(h, {})
                down_gap = archived_info.get('down_gap')
                try:
                    if archived_info:
                        raise self.fr.Unreadable('reuse archived rank')
                    G, inf, _, _ = self.fr.read_build(P, n, 'down', mine_first=True)
                    down_gap = inf['side'] - (bar[len(G)] + 1) * math.sqrt(len(G))
                except self.fr.Unreadable:
                    pass
                except TimeoutError:
                    info['rank_timeout'] = True
                    self.state(f'RANK TIMEOUT {p}; queue both directions on the boxes without a local down-gap estimate')
                signal.alarm(0)
                info.update(side=side, down_gap=down_gap)
                options = specs(n, m, down_gap, near, unranked=info.get('rank_timeout', False),
                                fresh=rnd == ROUND and not archived_info)
                options = fresh_design_cuts(options, p, rnd)
                returning = p.parent == self.t / 'near'
                if returning:
                    options = [(direction, pick) for direction, pick in options if direction == 'up']
                # Refused up cuts are cheap on the worker. Keep the coordinator
                # responsive instead of finding both directions twice here.
                for direction, pick in options:
                    if (h, direction, pick) in self.oldwalks:
                        continue
                    key = job_key(h, direction, pick)
                    if key in self.data['jobs']:
                        continue
                    self.data['sequence'] += 1
                    j = self.data['sequence']
                    priority = live_priority if rnd == ROUND and not near else 'b' if rnd == ROUND - 1 and not near else 'g'
                    if returning:
                        priority = 'a2'
                    if rnd == ROUND and not near:
                        earlier = [v for v in self.data['seen'].values()
                                   if v.get('side') is not None and v.get('path') == str(p) and v is not info]
                        if earlier and min(abs(side - v['side']) for v in earlier) < 1e-5:
                            priority = 'y'
                    priority = cut_priority(priority, pick)
                    refkey = (geom, direction, pick)
                    copy = any(abs(side - old_side) < 1e-5 for old_side, _ in self.references[refkey])
                    if copy:
                        priority = 'y'
                    else:
                        self.references[refkey].append((side, h))
                    source_refresh = (rnd == ROUND and 'CC0' in licence and
                                      readers_sources.classify_seed_text(source + ' ' + licence + json.dumps(self.data.get('source_evidence', {}).get(h, {})))['status'] == 'none')
                    if rnd == ROUND and any(x in str(p) for x in FRESH) and (priority != 'y' or source_refresh):
                        priority = 'a00' if pick == 0 else 'a30'
                        if source_refresh:
                            copy = False
                    board_gap = reachable_gap(n, m, direction, bar, self.board)
                    low_gap = board_gap < 1e-3
                    if priority.startswith('a') and priority not in ('a00', 'a30') and low_gap:
                        priority = 'a8'
                    # New live versions sort ahead of old waiting live versions.
                    name = f'{priority}{99999999-j:08d}-{donor}-{direction}-c{pick}' + ('-return' if returning else '')
                    slot = (j - 1) % 3
                    atomic(self.b / f'q{slot}' / (name + '.tsv'),
                           f'donor\tdirection\tpick\n{donor}\t{direction}\t{pick}\n')
                    self.data['jobs'][key] = dict(name=name, donor=donor, slot=slot, direction=direction, pick=pick, quench_copy=copy, low_gap=low_gap,
                                                 reachable_board_gap=board_gap if math.isfinite(board_gap) else None, source_group_refresh=source_refresh)
                self.state(f'QUEUE {donor}, source {p}, down as built gap {down_gap}; immutable version, cuts 0/1, deadline {DEADLINE}; log work/out-*/walk.log')
            except Exception as ex:
                signal.alarm(0)
                info['error'] = repr(ex)
                self.state(f'REFUSED donor {p}: {ex}')
        self.save()

    def command(self, command):
        if command[0] == 'rsync':
            command = ['rsync', '-e', 'ssh -oControlMaster=auto -oControlPersist=600 -oControlPath=/tmp/readers25-%C'] + command[1:]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90)
        if result.returncode:
            self.state(f'SYNC ERROR {command[0]} {result.returncode}: {result.stdout[-300:]}')
        return result

    def drop_claims(self):
        """Remove queue files that the backlog lane claimed in the handoff log."""
        log = self.s / f'handoff-r{ROUND}.log'
        if not log.exists():
            return
        claimed = set()
        for line in log.read_text().splitlines():
            if re.search(r'backlog -> [^:]*readers[^:]*: claims', line):
                claimed.update(re.findall(r'\b([a-z]\d{8,}-\d+-r\d+h[0-9a-f]{16}-(?:up|down)-c\d[\w-]*?)(?:\.tsv|\b)', line))
        for job in self.data['jobs'].values():
            if job.get('claimed') or not any(c.startswith(job['name']) or job['name'].startswith(c) for c in claimed):
                continue
            job['claimed'] = True
            q = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
            if q.exists():
                q.unlink()
            self.state(f'CLAIMED by backlog: {job["name"]}; queue file removed, boxes drop it on the next rsync --delete')

    def sync(self):
        self.drop_claims()
        atomic(self.b / 'defer.tsv', tabtext(['donor', 'direction', 'pick', 'allow_prefix'], deferred_rows(self.data['jobs'].values())))
        for p in list(self.s.glob(f'take-*-r{ROUND}/take.tsv')):
            if 'assemble' not in str(p) and p.parent != self.t:
                shutil.copyfile(p, self.b / 'beat' / (p.parent.name + '.tsv'))
        for host, slots in [('boxD', (0, 1)), ('boxC', (2,))]:
            self.command(['rsync', '-a', str(self.b / 'defer.tsv'), f'{host}:scratch/squares-readers/'])
            self.command(['rsync', '-a', str(self.b / 'donors') + '/', f'{host}:scratch/squares-readers/donors/'])
            self.command(['rsync', '-a', str(self.b / 'beat') + '/', f'{host}:scratch/squares-readers/beat/'])
            for slot in slots:
                # --delete drops queue files of jobs that backlog claimed.
                self.command(['rsync', '-a', '--delete', str(self.b / f'q{slot}'), f'{host}:scratch/squares-readers/'])
                self.command(['rsync', '-a', f'{host}:scratch/squares-readers/out{slot}/', str(self.w / f'out-{host}-{slot}') + '/'])
            self.command(['rsync', '-a', f'{host}:scratch/squares-readers/quench/', str(self.w / f'quench-{host}') + '/'])
            for slot in slots:
                log = self.w / f'out-{host}-{slot}' / 'run.log'
                lines = log.read_text().splitlines() if log.exists() else []
                key = f'{host}:{slot}'
                previous = self.data.setdefault('worker_log_lines', {}).get(key, 0)
                for line in lines[previous:]:
                    self.state(f'WORKER {host} slot {slot}: {line}; command run25.sh, log {log}, deadline {DEADLINE}')
                self.data['worker_log_lines'][key] = len(lines)


    def take(self, out, rawdirs, logfile):
        beat = [str(p) for p in list(self.s.glob(f'take-*-r{ROUND}/take.tsv'))
                if p.parent != self.t and 'assemble' not in str(p)]
        command = [self.py, '-I', str(self.code / 'readers_policy_take.py'), str(self.w / 'details.csv'),
                   str(out)] + list(map(str, rawdirs)) + ['--sources', str(self.w / 'sources-all.tsv'), '--beat'] + beat
        with open(logfile, 'w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)

    def collect(self):
        raw = self.w / 'rawarc/raw'
        raw.mkdir(parents=True, exist_ok=True)
        fast = self.w / 'fast/raw'
        fast.mkdir(parents=True, exist_ok=True)
        for p in fast.glob('*.csv'):
            p.unlink()
        for p in self.w.glob('out-*/raw/*.csv'):
            h = digest(p)
            if h not in self.data['archives']:
                # Content-specific donors prevent a raw name collision.
                q = raw / p.name
                shutil.copyfile(p, q)
                self.data['archives'][h] = str(q)
                shutil.copyfile(q, fast / q.name)
        for p in self.w.glob('out-*/near/*.csv'):
            shutil.copyfile(p, self.t / 'near' / p.name)
            readers_sources.write_near_source(self.t / 'near' / p.name, self.data, self.w)
            h = digest(p)
            announced = self.data.setdefault('announced_near', [])
            if h not in announced:
                n = int(p.name.split('-')[0])
                side = self.fr.fs.canon(self.fr.fs.load(p)[n])[0]
                bar = (self.bars()[n] + 1) * math.sqrt(n)
                with open(self.s / f'handoff-r{ROUND}.log', 'a') as f:
                    f.write(f'{stamp()} readers -> all: unquenched layer-walk end n={n}, side={side:.12f}, margin={side-bar:+.6g}; {self.t}/near/{p.name}; donor provenance in {self.w}/sources-all.tsv\n')
                announced.append(h)
        # Include earlier winning candidates until their quench returns.
        for h, q in self.data['quenches'].items():
            if not q.get('complete') and Path(q['raw']).exists():
                shutil.copyfile(q['raw'], fast / Path(q['raw']).name)
        self.take(self.w / 'pre', [self.w / 'fast'], self.w / 'pre.log')
        for line in (self.w / 'pre.log').read_text().splitlines():
            if not line.startswith('keep '):
                continue
            _, n, held, score, gain, tag = line.split()
            p = self.w / 'pre' / (n + '.csv')
            h = digest(p)
            if h in self.data['quenches']:
                continue
            # Queue the certified file, never its original unguarded coordinates.
            qz = self.b / 'qz'
            qz.mkdir(exist_ok=True)
            shutil.copyfile(p, qz / (tag + '.csv'))
            self.data['quenches'][h] = dict(tag=tag, n=int(n), raw=str(raw / (tag + '.csv')), complete=False)
            self.state(f'QUENCH queued n={n} certified score={score}, {tag}; publish only after box quench')
        # Quench jobs belong to boxD, whose two workers share an atomic mkdir lock.
        if (self.b / 'qz').exists():
            self.command(['rsync', '-a', str(self.b / 'qz') + '/', 'boxD:scratch/squares-readers/qz/'])
        for q in self.data['quenches'].values():
            q['complete'] = any((self.w / f'quench-{host}' / 'raw' / (q['tag'] + '.csv')).exists() for host in ('boxC', 'boxD'))
        # All files here have already had fq run on their floatsafe copies.
        self.take(self.t, [self.w / 'quench-boxC', self.w / 'quench-boxD'], self.w / 'take-f.log')
        kept = {int(r['n']) for r in rows(self.t / 'take.tsv')}
        superseded = self.w / 'superseded'
        superseded.mkdir(exist_ok=True)
        for p in self.t.glob('*.csv'):
            if int(p.stem) not in kept:
                p.replace(superseded / p.name)
        # Preserve source text while recording the required final quench.
        take = rows(self.t / 'take.tsv')
        for r in take:
            r['source'] += '; one fq default quench of the floatsafe file on boxD before publication'
        atomic(self.t / 'take.tsv', tabtext(['n', 'held', 'new', 'gain', 'source', 'licence'], take))
        for r in take:
            key = f'{r["n"]}:{r["new"]}'
            if key not in self.data['published']:
                message = f'certified n={r["n"]} score={r["new"]}, gain={r["gain"]} vs the round 25 base bar and below every live r25 take; {self.t}/{r["n"]}.csv'
                with open(self.s / f'handoff-r{ROUND}.log', 'a') as f:
                    f.write(f'{stamp()} readers -> all: {message}\n')
                self.state('CERTIFIED ' + message)
                self.data['published'].append(key)
        # Ends that no longer beat the bar still supply fresh corners to others.
        for p in fast.glob('*.csv'):
            shutil.copyfile(p, self.t / 'near' / p.name)
            readers_sources.write_near_source(self.t / 'near' / p.name, self.data, self.w)
        self.save()

    def promote_near_cuts(self):
        completed = set()
        near = set()
        for path in self.w.glob('out-*/rows-walk-*.tsv'):
            for row in rows(path):
                shell = row['shells']
                pick = int(shell.split('c')[1]) if 'c' in shell else 0
                if shell.split('c')[0] == '1':
                    completed.add((row['donor'], row['direction'], pick))
                try:
                    delta = float(row['after_squeeze']) - float(row['bar'])
                except ValueError:
                    continue
                if not pick and shell in ('1', '2') and 1e-7 < delta < 1e-4:
                    near.add((row['donor'], row['direction']))
        for key, job in self.data['jobs'].items():
            original = self.data['seen'].get(key.split(':')[0], {}).get('path', '')
            if (job['pick'] != 1 or job.get('part_only') or job.get('quench_copy') or f'-r{ROUND}/' not in original or
                    (job['donor'], job['direction']) not in near or
                    (job['donor'], job['direction'], 1) in completed or
                    job.get('near_promoted')):
                continue
            old = self.b / f'q{job["slot"]}' / (job['name'] + '.tsv')
            if not old.exists():
                continue
            prefix, rest = job['name'].split('-', 1)
            job['name'] = 'a01' + prefix[-8:] + '-' + rest + '-nearcut'
            job['near_promoted'] = True
            shutil.copyfile(old, old.with_name(job['name'] + '.tsv'))
            self.state(f'PROMOTE cut1 after first-cut result within0.0001 of side: {job["donor"]} {job["direction"]}; next after fresh module/k123 first cuts, before ordinary fresh files; log work/out-*/walk.log deadline {DEADLINE}')
        self.save()

    def cycle(self):
        self.sync()
        self.collect()
        self.promote_near_cuts()
        if time.time() < float((self.b / 'deadline').read_text()) - 300:
            self.enqueue()
        else:
            self.state(f'INTAKE CLOSED 15 minutes before {DEADLINE}; collect and quench existing work through the {DEADLINE} compute deadline')
        self.sync()
        self.state(f'CYCLE jobs={len(self.data["jobs"])} raw={len(self.data["archives"])} published={len(self.data["published"])}; log work/follow.log; next fresh designs and kicks')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scratch', default='$SCRATCH/bounties-squares')
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        second = dict(donor='648-fresh', direction='up', pick=1, name='a399999999-648-fresh-up-c1')
        defer = deferred_rows([second])[0]
        assert not 'a099999999-old-alias'.startswith(defer['allow_prefix'])
        assert second['name'].startswith(defer['allow_prefix'])
        assert cut_priority('a0', 0) == 'a0'
        assert cut_priority('a0', 1) == 'a3'
        assert cut_priority('a1', 1) == 'a4'
        assert cut_priority('y', 1) == 'y'
        assert cut_priority('a1', 0) < cut_priority('a0', 1) < 'b'
        print('CONTROL PASSES: fresh first cuts precede second cuts; second cuts precede frozen donors')
        assert whole_layout('/take-forensics-r24/near/796.csv')
        assert whole_layout('/take-family-r24/work/unread/796-f24.csv')
        assert not whole_layout('/take-forensics-r24/work/interior/796/175-interior.csv')
        print('CONTROL PASSES: complete near and unread layouts retained; rectangle parts excluded')
        previous = {'jobs': {
            'old:up:0': dict(direction='up', pick=0),
            'old:up:1': dict(direction='up', pick=1),
            'fresh:down:0': dict(direction='down', pick=0),
            'part:up:0': dict(direction='up', pick=0, part_only=True)}}
        pending = pending_versions(previous, {('old', 'up', 0)})
        assert len(pending['old']) == 1 and pending['old'][0]['pick'] == 1
        assert 'fresh' in pending
        assert not pending_versions(previous, {('old', 'up', 0), ('old', 'up', 1), ('fresh', 'down', 0)})
        print('CONTROL PASSES: archive restores unstarted cuts and excludes every completed cut')
        assert ('up', 1) in specs(752, 27, 0.013)
        assert ('up', 0) in specs(234, 15, 0.013)
        assert ('down', 1) in specs(992, 31, 0.013)
        assert not specs(992, 31, 0.016)
        assert specs(992, 31, 0.016, fresh=True) == [('down', 0)]
        assert fresh_design_cuts([('down', 0)], f'/take-modules-r{ROUND}/near/992.csv', ROUND) == [('down', 0), ('down', 1)]
        assert fresh_design_cuts([('down', 0)], f'/take-mid-m-r{ROUND}/992.csv', ROUND) == [('down', 0)]
        print('CONTROL PASSES: fresh module/k123 high-n probes retain both first cuts')
        assert ('down', 0) in specs(992, 31, None, unranked=True)
        assert historical_unread('/work/unread/929-iv23.csv')
        assert not historical_unread('/work/unread/930-rdn24.csv')
        assert reachable_gap(931, 30, 'up', {994: 31.92835/math.sqrt(994)-1}, {994: 31.92834}) < 1e-3
        assert reachable_gap(997, 31, 'down', {934: 30.96414/math.sqrt(934)-1}, {934: 30.95868}) > 1e-3
        sys.path.insert(0, str(Path(__file__).parent))
        import family_step as fs
        import family_readers as fr
        miss = fr.walk_misses(0, 'below held', 3e-9, 1e-7)
        assert miss == 1
        assert fr.walk_misses(miss, 'below held', 1e-3, 1e-7) == 0
        assert fr.walk_misses(miss, 'below held', 2e-9, 1e-7) == 2
        assert fr.walk_misses(1, 'below held', 2e-9, 0) == 0
        print('CONTROL PASSES: meaningful gain resets misses; two numerical returns stop; zero restores the old rule')
        packing = fs.np.array([[0.6317, 0.7321, 0.1234], [2.1123, 0.5817, -0.0713], [1.5213, 2.2817, 0.2104]])
        side, geom = geometry_key(fs, packing)
        tiny = packing[::-1].copy() + fs.np.array([3.123456789, 2.345678901, 0.0])
        assert geometry_key(fs, tiny)[1] == geom
        assert geometry_key(fs, packing + 1e-9)[1] == geom
        assert geometry_key(fs, fs.turned(fs.canon(packing)[1], side, 'X'))[1] == geom
        tiny[0, 2] += 0.01
        assert geometry_key(fs, tiny)[1] != geom
        print('CONTROL PASSES: geometry identity keeps translated/reordered copies and distinguishes a changed tilt')
        # Exercise the same identity and duplicate check as enqueue().
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / '7.csv.json'
            meta.write_text(json.dumps(dict(source='public donor', licence='Apache 2.0')))
            source, licence = sidecar_source(meta.with_suffix(''), 'walk', 'see source')
            assert licence == 'Apache 2.0' and 'public donor' in source
            meta.write_text('{partial')
            assert sidecar_source(meta.with_suffix(''), 'walk', 'see source') == ('walk', 'see source')
            print('CONTROL PASSES: source sidecar retains licence and partial JSON leaves the original source intact')
            donor = Path(tmp) / '752.csv'
            donor.write_text('first version\n')
            first = job_key(digest(donor), 'up', 0)
            pending = {first}
            donor.write_text('kicked version\n')
            second = job_key(digest(donor), 'up', 0)
            assert second not in pending
            pending.add(second)
            assert job_key(digest(donor), 'up', 0) in pending
            assert len(pending) == 2
        print('CONTROL PASSES: low n included; +0.013 down admitted; fresh high-n +0.016 probed; two donor versions retained')
        return
    follow = Follow(args.scratch)
    def rank_timeout(signum, frame):
        raise TimeoutError('coordinator read/build exceeded 25 s')
    signal.signal(signal.SIGALRM, rank_timeout)
    deadline = float((follow.b / 'deadline').read_text())
    while True:
        try:
            follow.cycle()
        except Exception as ex:
            follow.state('LOOP ERROR ' + repr(ex))
            import traceback
            traceback.print_exc()
        if args.once or time.time() >= deadline:
            break
        time.sleep(60)


if __name__ == '__main__':
    main()
