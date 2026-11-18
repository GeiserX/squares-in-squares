#!/usr/bin/env python3
"""Follow fresh layouts with one boxB scanner and three boxE workers.

The local process admits sources and collects certificates. Remote workers
claim one quench at a time. Every published result receives a quench from its
certified file. Search stops before the final certification period.
"""
import csv
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

csv.field_size_limit(16 * 1024 * 1024)

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
import numpy as np
import forensics_compose as fc
import forensics_rect as rect
import midm_scan as ms


def atomic_json(path, data):
    path = Path(path)
    path.with_suffix('.tmp').write_text(json.dumps(data, indent=2))
    os.replace(path.with_suffix('.tmp'), path)


def raw_allowed(work, flags):
    """Keep late polish starts while reserving the last phase for certificates."""
    return (not (work / 'STOP_NEW_RAW').exists() and
            (not (work / 'POLISH_ONLY').exists() or flags == 'p'))


def gather_notices(parts):
    """Resolve a gather donor, including rows inherited from earlier rounds."""
    notices = []
    for tag, part in parts.items():
        if not isinstance(part, dict) or 'source' not in part:
            continue
        donor = Path(part.get('original_file', part['source'][0]))
        if re.fullmatch(r'take-.+-r23', donor.parent.name) and donor.stem.isdigit():
            donor = donor.parent.parent / 'gather/round23-2026-11-13a.csv'
        if donor.parent.name != 'gather':
            continue
        match = re.match(r'(round\d+)-(\d{4}-\d{2}-\d{2})[a-z]*\.csv$', donor.name)
        if not match:
            continue
        requested = CODE / ('results/%s-best-%s.tsv' % match.groups())
        if not requested.exists():
            continue
        round_no = int(match[1][5:])
        candidates = []
        for ledger in (CODE / 'results').glob('round*-best-*.tsv'):
            lm = re.match(r'round(\d+)-best-(.+)\.tsv$', ledger.name)
            if lm and int(lm[1]) <= round_no:
                candidates.append((int(lm[1]), ledger.name, ledger))
        ledgers = [r[2] for r in sorted(candidates, reverse=True)]
        frozen_a = CODE / 'results/forensics-round23a-sources-r24-2026-11-13.tsv'
        if donor.name == 'round23-2026-11-13a.csv' and frozen_a.exists():
            ledgers.insert(0, frozen_a)
        ledgers.append(CODE / 'results/harvest-best-2026-11-09.tsv')
        dn = int(part['source'][1])
        for ledger in ledgers:
            if not ledger.exists():
                continue
            records = [r for r in csv.DictReader(open(ledger), delimiter='\t') if int(r['n']) == dn]
            if records:
                row = records[0]
                notices.append(dict(part=tag, n=dn, requested_ledger=str(requested),
                                    ledger=str(ledger), source=row.get('source', ''),
                                    licence=row.get('licence', '')))
                break
    return notices


def ancestry_notices(parts, scratch):
    """Credit clean roots from the exact snapshot's retained ancestry."""
    import forensics_sources
    roots = {}
    public = {}
    def visit(value):
        if isinstance(value, dict):
            if value.get('reason') == 'declared root retained by reference':
                import forensics_policy
                source = value.get('source', '') + '; immutable derivation: ' + value['source_proof']
                source += '; ' + forensics_policy.label(value['seed_policy'])
                public[(value['source_proof'], value['n'])] = dict(
                    part='declared-' + str(value['n']), n=value['n'], ledger=value['source_proof'],
                    source=source, licence=value.get('licence', '') + '; ' + forensics_policy.label(value['seed_policy']))
            if value.get('reason') == 'retained polished public input and verified upstream row':
                row = value['per_n_row']
                public[(value['per_n_csv'], int(row['n']))] = dict(
                    part='public-' + row['n'], n=int(row['n']), ledger=value['per_n_csv'],
                    source=value['source'] + ' :: per_n.csv, donor n=' + row['n'] + ', src=' + row['src'],
                    licence=value['licence'])
            path, n = value.get('path'), value.get('n')
            if path and isinstance(n, int):
                donor = Path(path)
                if (donor.parent.name == 'gather' or
                        (re.fullmatch(r'take-.+-r23', donor.parent.name) and donor.stem.isdigit())):
                    roots[(path, n)] = dict(source=[path, n])
            for key, child in value.items():
                if key != 'record':
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    for tag in ('A', 'B', 'C'):
        if tag in parts:
            part = parts[tag]
            ok, proof = forensics_sources.trace_part(part, scratch)
            if ok:
                visit(proof)
    return gather_notices({str(i): part for i, part in enumerate(roots.values())}) + list(public.values())


def ready_raw(path):
    """Return a complete packing and sidecar, or retry it on the next pass."""
    try:
        parts = json.loads(Path(str(path) + '.json').read_text())
        if not isinstance(parts, dict):
            return None
        data = next(iter(rect.layouts(path).values()))
        return parts, data
    except (OSError, ValueError, StopIteration, TypeError, AttributeError, csv.Error):
        return None


def priority_time(now, gap):
    """Five-minute freshness groups, with larger board gaps first within each."""
    return math.floor(now / 300) * 300 + min(299., max(0., gap) * 100000.)


def stamp():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def worker(root, wk, deadline, fq):
    root = Path(root)
    for name in ('claims', 'results', 'tmp'):
        (root / name).mkdir(exist_ok=True)
    while time.time() < deadline and not (root / 'STOP').exists():
        tasks = sorted((root / 'tasks').glob('*.json'),
                       key=lambda p: (not p.name.startswith('final-'), -p.stat().st_mtime))
        job = None
        for p in tasks:
            if root.name.endswith('-r25') and time.time() >= deadline - 1800 and not p.name.startswith('final-'):
                continue
            if time.time() >= deadline - 300 and not p.name.startswith('final-'):
                continue
            if time.time() >= deadline - 900 and not p.name.startswith('final-') and json.loads(p.read_text())['flags'] != 'p':
                continue
            try:
                (root / 'claims' / p.stem).mkdir()
                job = p
                break
            except FileExistsError:
                continue
        if job is None:
            time.sleep(3)
            continue
        meta = json.loads(job.read_text())
        t = time.time()
        try:
            sq = next(iter(rect.layouts(root / 'inputs' / (job.stem + '.csv')).values()))
            side, q = fc.frame(sq)
            x = np.column_stack([q[:, 0], q[:, 1], np.degrees(q[:, 2])])
            flags = () if meta['flags'] == 'd' else ms.POLISH
            task_deadline = deadline
            if root.name.endswith('-r25') and not job.name.startswith('final-'):
                task_deadline = deadline - 1800
            end, y = ms.quench(fq, str(root / 'tmp'), side, x, flags,
                               timeout=max(.01, min(600, task_deadline - time.time())))
            if y is not None:
                path = root / 'results' / (job.stem + '.csv')
                fc.write_csv(str(path) + '.tmp', meta['n'], ms.from_fq(y))
                os.replace(str(path) + '.tmp', path)
            result = dict(meta, start=side, end=end, seconds=time.time() - t, worker=wk)
        except Exception as error:
            result = dict(meta, error=repr(error), end=None, seconds=time.time() - t)
        atomic_json(root / 'results' / (job.stem + '.json'), result)
        print(stamp(), job.stem, result.get('start'), result.get('end'), result['seconds'], flush=True)
    print(stamp(), 'worker stopped', wk, flush=True)


class AdoptedProcess:
    """Track a detached rectangle job after its collector restarts."""
    def __init__(self, pid):
        self.pid = pid
        self.returncode = None

    def poll(self):
        if self.returncode is not None:
            return self.returncode
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            self.returncode = 0
        return self.returncode

    def terminate(self):
        os.kill(self.pid, signal.SIGTERM)

    def wait(self, timeout):
        end = time.time() + timeout
        while self.poll() is None and time.time() < end:
            time.sleep(.1)
        if self.returncode is None:
            raise TimeoutError('rectangle process did not stop')
        return self.returncode


def local(scratch, deadline, stop_scan, adopt_pid=None, round_no=25):
    import faulthandler
    faulthandler.register(signal.SIGUSR1)
    print(stamp(), 'collector traceback signal enabled', flush=True)
    import floatsafe
    scratch = Path(scratch)
    take = scratch / ('take-forensics-r%d' % round_no)
    held_round = round_no - (1 if round_no >= 24 else 2)
    held_tag = 'round%d-1113a' % held_round
    held_file = 'round%d-2026-11-13a.csv' % held_round
    held_ledger = 'results/round%d-best-2026-11-13.tsv' % held_round
    handoff_file = 'handoff-r%d.log' % round_no
    work = take / 'work'
    for name in ('tasks', 'inputs', 'received', 'certified'):
        (work / name).mkdir(exist_ok=True)
    state_path = work / 'watch-state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else dict(
        queued=[], processed=[], rows={}, scan=0, signatures={}, raw_seen=[], near={})
    state['queued'] = sorted(set(state['queued']) | {p.stem for p in (work / 'tasks').glob('*.json')})
    import forensics_round25 as r25
    held = r25.base(scratch, work)
    held_ledger = 'results/round23-best-2026-11-13.tsv'
    r25.SCRATCH = scratch
    r25.WORK = work
    import forensics_policy as seed_policy
    held22 = {int(r['n']): float(r['score']) for r in csv.DictReader(open(scratch / 'gate/cand-round22-1113b/details.csv'))} if round_no >= 24 else dict(held)
    priority_bars = dict(held)
    board = {int(r['n']): float(r['board_L']) / math.sqrt(int(r['n'])) - 1
             for r in csv.DictReader(open(scratch / 'main-r17/gap-by-n.tsv'), delimiter='\t')}
    remote = 'boxE:scratch/squares-forensics-r%d/' % round_no
    seen = set(state['raw_seen'])
    raw_files = set(state.get('raw_files', []))

    def log(message):
        line = stamp() + ' boxA ' + message
        print(line, flush=True)
        with open(take / 'STATE.txt', 'a') as h:
            h.write(line + '\n')

    def handoff(message):
        with open(scratch / handoff_file, 'a') as h:
            h.write(stamp() + ' forensics -> all: ' + message + '\n')

    def save():
        state['raw_seen'] = sorted(seen)
        state['raw_files'] = sorted(raw_files)
        atomic_json(state_path, state)

    def bests(free=False):
        held.update(r25.base(scratch, work))
        out = dict(held)
        if False:
            for n in seed_policy.RELAXED:
                out[n] = held22[n]
        for path in sorted(([] if round_no >= 24 else glob.glob(str(scratch / ('take-*-r%d/take.tsv' % (round_no - 1))))) +
                           glob.glob(str(scratch / ('take-*-r%d/take.tsv' % round_no)))):
            try:
                rows = list(csv.reader(open(path), delimiter='\t'))[1:]
            except OSError:
                continue
            for r in rows:
                try:
                    n, score = int(r[0]), float(r[2])
                    if False and n in seed_policy.RELAXED and seed_policy.classify_text(r[4] + ' ' + r[5])['status'] == 'seeds':
                        continue
                    if (Path(path).parent / (str(n) + '.csv')).exists():
                        out[n] = min(out[n], score)
                except (ValueError, IndexError, KeyError):
                    pass
        return out

    def policy(meta):
        ok, proof = r25.check_parts(meta.get('parts', {}), scratch)
        meta['samanyu_policy'] = dict(status='none' if ok else 'unknown', seeds=[])
        return meta['samanyu_policy']

    def acceptance_bars(meta):
        free = False
        return bests(free=free)

    def inputs():
        files = sorted(p for rnd in (24,25) for p in scratch.glob('take-*-r%d/*.csv' % rnd) if p.stem.isdigit())
        files += sorted(scratch.glob('take-*-r25/near/*.csv'))
        files += sorted(work.glob('interior/*/*-interior-*.csv'))
        handoffs = scratch / handoff_file
        if handoffs.exists():
            # Work files handed off explicitly are starts too. Library formats
            # that this reader does not understand stay with their builders.
            for path in re.findall(r'$SCRATCH/bounties-squares/[^\s,;]+\.csv', handoffs.read_text()):
                candidate = Path(path)
                if candidate.exists() and take not in candidate.parents and 'broken' not in candidate.name.lower():
                    files.append(candidate)
        files = sorted(set(p for p in files if (take / 'work' not in p.parents or work / 'interior' in p.parents) and take / 'near' not in p.parents))
        if round_no >= 24:
            # Unchanged inputs already reside in the part cache and would be
            # skipped below. Trace only the files this scan can actually read.
            changed = []
            for path in files:
                try:
                    if state['signatures'].get(str(path)) != signature(path):
                        changed.append(path)
                except OSError:
                    continue
            import forensics_sources as provenance
            return r25.admit(changed, scratch, work)
        return files

    def signature(path):
        st = path.stat()
        return [st.st_size, st.st_mtime_ns]

    def queue(path, meta, final=False):
        if round_no >= 24:
            import forensics_sources as provenance
            if not r25.check_parts(meta.get('parts', {}), scratch)[0]:
                log('REFUSE queued ancestry n=%d' % meta['n'])
                return
        if round_no >= 24 and policy(meta)['status'] != 'none':
            log('DEFER unknown Samanyu seed n=%d' % meta['n'])
            return
        if not final and not raw_allowed(work, meta['flags']):
            state.setdefault('deferred_files', []).append(str(path))
            return
        data = Path(path).read_bytes()
        key = ('final-' if final else 'raw-') + hashlib.sha256(data).hexdigest()[:24]
        if key in state['queued']:
            return
        (work / 'inputs' / (key + '.csv')).write_bytes(data)
        task_path = work / 'tasks' / (key + '.json')
        now = time.time()
        gap = priority_bars[meta['n']] - board[meta['n']]
        meta = dict(meta, queued_at=now, priority_gap=gap)
        atomic_json(task_path, meta)
        if not final:
            rank_time = priority_time(now - 3600 if meta.get('parts', {}).get('saved_start') else now, gap)
            os.utime(task_path, (rank_time, rank_time))
        state['queued'].append(key)

    def publish(n, score, rows, meta):
        if round_no >= 24:
            import forensics_sources as provenance
            ok, evidence = r25.check_parts(meta.get('parts', {}), scratch)
            atomic_json(work / 'certified' / ('ancestry-%d.json' % n), evidence)
            if not ok:
                log('REFUSE untraced ancestry n=%d' % n)
                return
        seed_info = policy(meta) if round_no >= 24 else dict(status='none', seeds=[])
        if seed_info['status'] != 'none':
            log('REFUSE unresolved Samanyu seed n=%d' % n)
            return
        relaxed = False
        bar = acceptance_bars(meta)[n]
        reference = held[n]
        if score >= bar - 1e-10:
            log('DROP superseded final n=%d score=%.12f bar=%.12f' % (n, score, bar))
            return
        old = state['rows'].get(str(n))
        if old and score >= float(old['new']):
            old_policy = seed_policy.classify_text(old['source'] + ' ' + old['licence'])
            if not relaxed or old_policy['status'] == 'none':
                return
            alternate = work / 'samanyu-alternates'
            alternate.mkdir(exist_ok=True)
            shutil.copyfile(take / (str(n) + '.csv'), alternate / ('%d-%.12f.csv' % (n, float(old['new']))))
            atomic_json(alternate / ('%d.json' % n), old)
        path = take / (str(n) + '.csv')
        with open(str(path) + '.tmp', 'w', newline='') as h:
            writer = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle'])
            writer.writeheader()
            writer.writerows({k: row[k] for k in writer.fieldnames} for row in rows)
        os.replace(str(path) + '.tmp', path)
        source = meta.get('kind', 'rectangle windows') + ' ' + json.dumps(meta.get('parts'), separators=(',', ':'))
        source += '; origins: ' + held_ledger + ' and named donor take.tsv/near files; '
        source += meta.get('initial_flags', meta['flags']) + ' quench, floatsafe, one boxE polish from certified file'
        notices = gather_notices(meta.get('parts', {}))
        if round_no >= 24:
            seen_notices = {(r['ledger'], r['n']) for r in notices}
            for notice in ancestry_notices(meta.get('parts', {}), scratch):
                if (notice['ledger'], notice['n']) not in seen_notices:
                    notices.append(notice)
                    seen_notices.add((notice['ledger'], notice['n']))
        if notices:
            source += '; donor notices: ' + json.dumps(notices, separators=(',', ':'))
        by_tag = {notice['part']: notice for notice in notices}
        if relaxed:
            source += '; source-policy exception: row compared with held round22 per main20:05 directive'
        state['rows'][str(n)] = dict(n=n, held=reference, new=score, gain=reference - score,
                                    source=source, licence='own composition; ' + '; '.join(
                                        str(by_tag.get(tag, v).get('licence', 'source notices in named donor'))
                                        for tag, v in meta.get('parts', {}).items() if isinstance(v, dict)) +
                                    ('; root notices: ' + '; '.join(r['licence'] for r in notices) if notices else ''))
        state['rows'][str(n)]['licence'] += '; ' + seed_policy.label(seed_info)
        with open(take / 'take.tsv.tmp', 'w', newline='') as h:
            writer = csv.DictWriter(h, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t')
            writer.writeheader()
            for k in sorted(state['rows'], key=int):
                writer.writerow(state['rows'][k])
        os.replace(take / 'take.tsv.tmp', take / 'take.tsv')
        log('CERTIFIED n=%d new=%.12f gain held=%.3e gain merge=%.3e' % (n, score, held[n] - score, bar - score))
        handoff('certified rectangle composition n=%d, fresh build for kicks, gain %.3e on current merge, %s' %
                (n, bar - score, path))
        save()

    def collect():
        r25.collect_scans(work)
        subprocess.run(['rsync', '-az', '--exclude=*.tmp', remote + 'results/', str(work / 'received') + '/'], check=True)
        diverse_raw = work / 'scan-diverse/raw'
        diverse_raw.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsync', '-az', remote + 'diverse/raw/', str(diverse_raw) + '/'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        bars = bests()
        free_bars = bests(free=True)
        for p in sorted((work / 'received').glob('*.json')):
            if p.stem in state['processed']:
                continue
            meta = json.loads(p.read_text())
            end, n = meta.get('end'), meta['n']
            if round_no >= 24:
                import forensics_sources as provenance
                if not r25.check_parts(meta.get('parts', {}), scratch)[0]:
                    state['processed'].append(p.stem)
                    log('REFUSE returned ancestry n=%d' % n)
                    continue
            csvpath = p.with_suffix('.csv')
            if end is None or not csvpath.exists():
                state['processed'].append(p.stem)
                continue
            score0 = end / math.sqrt(n) - 1
            free = False
            active_bar = free_bars[n] if free else bars[n]
            if meta.get('final'):
                # The box has now quenched the certified file. Keep the lower
                # valid certificate if its extra quench only adds padding.
                options = [csvpath, work / 'certified' / meta['certfile']]
                certified = []
                for op in options:
                    rr = list(csv.DictReader(open(op)))
                    _, fr, score, err = floatsafe.work((n, rr))
                    if fr is not None:
                        certified.append((score, fr))
                if certified:
                    score, fr = min(certified, key=lambda item: item[0])
                    publish(n, score, fr, meta)
            elif score0 < active_bar - 1e-10:
                rr = list(csv.DictReader(open(csvpath)))
                _, fr, score, err = floatsafe.work((n, rr))
                if fr is not None and score < acceptance_bars(meta)[n] - 1e-10:
                    certfile = p.stem + '.csv'
                    cp = work / 'certified' / certfile
                    with open(cp, 'w', newline='') as h:
                        writer = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle'])
                        writer.writeheader()
                        writer.writerows({k: row[k] for k in writer.fieldnames} for row in fr)
                    queue(cp, dict(meta, final=True, certfile=certfile, initial_flags=meta['flags'], flags='p'), final=True)
                    log('QUEUE final quench n=%d score=%.12f source=%s' % (n, score, p.stem))
            elif end < (active_bar + 1) * math.sqrt(n) + (0.015 if round_no >= 24 else 2e-4):
                prev = state['near'].get(str(n), math.inf)
                if end < prev - 2e-8:
                    dest = take / 'near' / ('%d-rect.csv' % n)
                    shutil.copyfile(csvpath, dest)
                    atomic_json(str(dest) + '.json', meta)
                    state['near'][str(n)] = end
                    handoff('quenched rectangle near n=%d, side %.12f, margin %+.3e, %s' %
                            (n, end, end - (bars[n] + 1) * math.sqrt(n), dest))
            state['processed'].append(p.stem)
        save()

    # A first complete run provides a new baseline. Later runs add only changed
    # layouts and require one newly read part in every pair.
    proc = AdoptedProcess(adopt_pid) if adopt_pid else None
    last_sync = 0
    while time.time() < deadline:
        if round_no >= 24 and time.time() >= stop_scan:
            (work / 'POLISH_ONLY').touch()
        if round_no >= 24 and time.time() >= stop_scan:
            (work / 'STOP_NEW_RAW').touch()
        try:
            priority_bars = bests(free=round_no >= 24)
            for raw in work.glob('scan-*/raw/*.csv'):
                if (work / 'STOP_NEW_RAW').exists():
                    break
                if str(raw) in raw_files:
                    continue
                sidecar = Path(str(raw) + '.json')
                if not sidecar.exists():
                    continue
                ready = ready_raw(raw)
                if ready is None:
                    continue
                parts, data = ready
                _, q = fc.frame(data)
                digest = hashlib.sha256(np.round(q, 7).tobytes()).hexdigest()
                if digest in seen:
                    raw_files.add(str(raw))
                    continue
                for tag in ('A', 'B', 'C'):
                    if tag not in parts:
                        continue
                    donor, dn = parts[tag]['source']
                    donor = Path(donor)
                    origin = Path(str(donor) + '.origin.json')
                    origin_data = json.loads(origin.read_text()) if origin.exists() else None
                    if origin_data is not None:
                        parts[tag]['snapshot'] = str(donor)
                        donor = Path(origin_data['path'])
                        parts[tag]['original_file'] = str(donor)
                    ledger = donor.parent / 'take.tsv'
                    if donor.parent.name == 'near':
                        ledger = donor.parent.parent / 'take.tsv'
                    if donor.parent.name == 'gather':
                        match = re.match(r'(round\d+)-(\d{4}-\d{2}-\d{2})[a-z]*\.csv$', donor.name)
                        ledger = CODE / ('results/%s-best-%s.tsv' % match.groups()) if match else CODE / held_ledger
                    parts[tag]['ledger'] = str(ledger)
                    if ledger.exists() and not origin_data:
                        donor_rows = [r for r in csv.DictReader(open(ledger), delimiter='\t') if int(r['n']) == dn]
                        if donor_rows:
                            parts[tag]['source_record'] = donor_rows[0].get('source', '')
                            parts[tag]['licence'] = donor_rows[0].get('licence', '')
                    notices = [] if origin_data else gather_notices({tag: parts[tag]})
                    if notices:
                        notice = notices[0]
                        parts[tag].update(ledger=notice['ledger'], held_ledger=notice['requested_ledger'],
                                          source_record=notice['source'], licence=notice['licence'])
                    if 'licence' not in parts[tag]:
                        parts[tag]['licence'] = 'held source notices in ' + held_ledger + ' and results/harvest-best-2026-11-09.tsv'
                    if origin_data and origin_data.get('verified_ancestry'):
                        parts[tag]['source_record'] = 'immutable ancestry in ' + str(origin)
                        parts[tag]['licence'] = 'upstream notices in pinned source ancestry'
                queue(raw, dict(n=len(q), flags='d' if '-c' in raw.name else 'p', parts=parts, kind=parts.get('kind', 'rectangle windows'),
                                raw=str(raw), final=False))
                seen.add(digest)
                raw_files.add(str(raw))
            if time.time() - last_sync >= 20:
                collect()
                subprocess.run(['rsync', '-az', str(work / 'inputs') + '/', remote + 'inputs/'], check=True)
                sync_tasks = ['rsync', '-az']
                if (work / 'STOP_NEW_RAW').exists():
                    sync_tasks += ['--include=final-*.json', '--exclude=*']
                subprocess.run(sync_tasks + [str(work / 'tasks') + '/', remote + 'tasks/'], check=True)
                handoffs = scratch / handoff_file
                if handoffs.exists():
                    shutil.copyfile(handoffs, work / 'handoff-last.log')
                last_sync = time.time()
        except (OSError, ValueError, StopIteration, KeyError, subprocess.CalledProcessError) as error:
            log('RETRY transient collector input error: %r' % error)
        finally:
            pass
        if proc is not None and proc.poll() is not None:
            log('FINISH scan=%d exit=%d log=%s/scan-%03d/rect.log' %
                (state['scan'], proc.returncode, work, state['scan']))
            if proc.returncode != 0:
                for path in state.get('active_files', []):
                    state['signatures'].pop(path, None)
            state['active_files'] = []
            proc = None
            save()
        if proc is None and time.time() < stop_scan and not (work / 'PAUSE_SCAN').exists():
            files = inputs()
            changed = []
            signatures = {}
            for path in files:
                try:
                    signatures[str(path)] = signature(path)
                except OSError:
                    continue
                if state['signatures'].get(str(path)) != signatures[str(path)]:
                    changed.append(path)
            triple = (not (work / 'STOP_THREE').exists() and (work / 'windows.pkl').exists() and
                      time.time() - state.get('last_three', 0) > 1800)
            if changed or triple:
                state['scan'] += 1
                run = work / ('scan-%03d' % state['scan'])
                run.mkdir(exist_ok=True)
                bars = bests(free=round_no >= 24)
                with open(run / 'details.csv', 'w') as h:
                    h.write('n,L,score\n')
                    for n, sc in sorted(bars.items()):
                        h.write('%d,%r,%r\n' % (n, (sc + 1) * math.sqrt(n), sc))
                broad = state['scan'] % 3 == 0
                args = [sys.executable, '-I', str(CODE / 'forensics_rect.py'), str(run / 'details.csv'), str(run / 'raw'),
                        '--cache', str(work / 'windows.pkl'),  '--gap', str(scratch / 'main-r17/gap-by-n.tsv'), '--slack', '0.012' if broad else '0.004', '--keep', '8', '--per-n', '16' if broad else '8',
                        '--max-mesh', '600' if broad else '400', '--strict-single', '--skip-ties', '--collide', '0.06' if broad else '0.03']
                if triple:
                    args = [sys.executable, '-I', str(CODE / 'forensics_three.py'), str(work / 'windows.pkl'),
                            str(run / 'details.csv'), str(run / 'raw'), '--max-mesh', '80', '--per-n', '4',
                            '--fresh-start', str(state.get('three_fresh', 0))]
                    state['last_three'] = time.time()
                    import pickle
                    with open(work / 'windows.pkl', 'rb') as cache_file:
                        state['three_fresh'] = len(pickle.load(cache_file)['src'])
                    changed = []
                else:
                    if state['scan'] > 1:
                        args += ['--fresh-only']
                    args += [str(p) for p in changed]
                state['active_files'] = [str(p) for p in changed]
                for p in changed:
                    state['signatures'][str(p)] = signatures[str(p)]
                log('START scan=%d files=%d cmd=%r log=%s deadline=%s' %
                    (state['scan'], len(changed), args[:24], run / 'rect.log', deadline))
                proc = r25.start_scan(args, run, stop_scan)
                save()
        time.sleep(min(20, max(0, deadline - time.time())))
    if proc is not None and proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=30)
        log('KILL rectangle scan at deadline')
    collect()
    log('FINISH live loop deadline reached')


if __name__ == '__main__':
    if sys.argv[1] == 'worker':
        worker(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5])
    else:
        stop = float(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[4] == '--stop-scan' else float(sys.argv[3]) - 300
        adopt = int(sys.argv[sys.argv.index('--adopt') + 1]) if '--adopt' in sys.argv else None
        round_no = int(sys.argv[sys.argv.index('--round') + 1]) if '--round' in sys.argv else 22
        local(sys.argv[2], float(sys.argv[3]), stop, adopt, round_no)
