#!/usr/bin/env python3
"""Follow fresh layouts with two bounded fq slots and checkpoint each result.

Public merges and remote proofs pause local slot launches when needed.
Fetched files are data. This runner never executes their code.
"""
import argparse
import csv
import functools
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import signal
import shlex
import subprocess
import sys
import time
import zipfile
from types import SimpleNamespace

LANE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LANE))
sys.path.insert(0, str(LANE / 'tools'))
from harvest_collect import Collector, rows_write, table
from engine_lib import normalize
from engine_fq import FQ, read_txt, write_txt
from engine_polish import to_rows
from harvest_merge import side_est
from angle_take import accepted
from harvest_seeds import SeedPolicy, SPECIAL

csv.field_size_limit(16 * 1024 * 1024)

COLS = ('n', 'held', 'new', 'gain', 'source', 'licence', 'start', 'polish_gain')


def owned_public_fetch(command, script):
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    return len(words) == 2 and Path(words[0]).name == 'bash' and words[1] == str(script)


def csv_rows(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def write_table(path, rows):
    temp = path.with_suffix('.tmp')
    with temp.open('w') as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter='\t', extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    temp.replace(path)


def public_origin(data, row):
    """Trace per-n public credits, including the baseline of a polished output."""
    root = Path(data)
    n = str(row['n'])
    source = row.get('source', '')
    licences = [row.get('licence', '')]
    visited = set()
    reported_sides = {float(row['L'])}

    def trace(ref, side):
        if ref in visited:
            return
        visited.add(ref)
        folder = next((root/kind/ref.replace('/', '__') for kind in ('nb', 'ds')
                       if (root/kind/ref.replace('/', '__')).is_dir()), None)
        if folder is None:
            if ref != source.split(' :: ', 1)[0]:
                notices.append('unresolved public upstream ' + ref)
            return
        # Delta folders can carry only metadata. Walk their saved previous roots
        # to read the source's actual credit table rather than dropping it.
        checked = set()
        while not any((folder/name).is_file() for name in ('per_n.csv', 'per_n_source_table.csv', 'submission_sources.csv', 'sources.csv')):
            meta = folder/'meta.json'
            if not meta.exists() or str(folder) in checked:
                break
            checked.add(str(folder))
            carried = json.loads(meta.read_text()).get('carried')
            if not carried:
                break
            older = Path(carried)/folder.parent.name/folder.name
            if not older.is_dir():
                break
            folder = older
        names = ('per_n.csv', 'per_n_source_table.csv', 'submission_sources.csv', 'sources.csv')
        credit_files = []
        for name in names:
            path = folder/name
            if path.is_file() and path.stat().st_size <= 8_000_000:
                credit_files.append((name, str(path), path.read_text()))
        for archive in folder.glob('*.zip'):
            try:
                with zipfile.ZipFile(archive) as zipped:
                    for item in zipped.infolist():
                        if Path(item.filename).name in names and item.file_size <= 8_000_000:
                            credit_files.append((Path(item.filename).name, str(archive)+'!'+item.filename,
                                                 zipped.read(item).decode('utf-8-sig')))
            except (OSError, UnicodeError, zipfile.BadZipFile):
                continue
        for name, path, content in credit_files:
            credits = list(csv.DictReader(io.StringIO(content)))
            for credit in credits:
                if credit.get('n', credit.get('N')) != n:
                    continue
                reported = credit.get('L', credit.get('official_side_L'))
                baseline = name == 'per_n_source_table.csv'
                if reported and abs(float(reported)-side) > 1e-6:
                    if not baseline or float(reported) < side:
                        continue
                fields = {k: credit[k] for k in ('src', 'source', 'source_ref', 'source_file', 'license', 'licence') if credit.get(k)}
                if not fields:
                    continue
                if reported:
                    reported_sides.add(float(reported))
                notices.append('per-n origin ' + json.dumps(fields, sort_keys=True) + ' (' + str(path) + ')')
                for key in ('license', 'licence'):
                    if credit.get(key):
                        licences.append(credit[key])
                for value in fields.values():
                    match = re.search(r'kaggle\.com/(?:code|datasets)/([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', value) or re.match(r'^(?:notebooks/|datasets/)?([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', value)
                    if match and not value.startswith('/kaggle/'):
                        parent = match[1]
                        parent_folder = root/'nb'/parent.replace('/', '__')
                        meta = parent_folder/'meta.json'
                        if meta.exists():
                            notice = json.loads(meta.read_text()).get('license')
                            if notice:
                                licences.append(parent + ': ' + notice)
                        trace(parent, float(reported) if reported else side)
                return

    notices = []
    trace(source.split(' :: ', 1)[0], float(row['L']))
    # The old per-n record is evidence that these identical side families have
    # unresolved excluded ancestry, even when a later merge names itself.
    if int(n) in (639, 691, 745, 858, 918):
        scratch = next((p for p in root.parents if (p/'take-harvest-r22').is_dir()), None)
        if scratch is not None:
            credit_path = scratch/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
            if credit_path.exists():
                with credit_path.open() as stream:
                    for credit in csv.DictReader(stream):
                        if credit.get('n') == n and any(abs(float(credit['L'])-side) < 1e-6 for side in reported_sides):
                            notices.append('unresolved excluded ancestry at matching side: ' + json.dumps(credit, sort_keys=True) + ' (' + str(credit_path) + ')')
                            licences.append('unresolved upstream notices at excluded side')
    return dict(row, source=source + ('; ' + '; '.join(notices) if notices else ''),
                licence='; '.join(dict.fromkeys(filter(None, licences))))


@functools.lru_cache(maxsize=4)
def refused_proofs(scratch):
    proofs = set()
    for lane in ('harvest', 'polish'):
        for row in table(Path(scratch) / ('take-' + lane + '-r22') / 'take.tsv'):
            if int(row['n']) in (639, 691, 745, 858, 918):
                proof = row.get('remote_quench', '')
                if proof:
                    proofs.add(Path(proof).stem.replace('remote-', ''))
    return proofs


def nonancestral_key(key):
    return bool(re.search(r'(?:^|_)(?:policy|excluded?|rejected?|ban|control|tested?|unused)(?:_|$)', key, re.I))


def provenance_text(value, include=False):
    if isinstance(value, dict):
        parts = []
        for key, child in value.items():
            if nonancestral_key(key):
                continue
            source = key in ('source', 'source_record', 'source_ref', 'src', 'licence', 'license',
                             'licences', 'licenses', 'donor_source', 'donor_licence',
                             'original_file', 'ledger', 'input_file', 'parent_file') or key.endswith(('_source', '_licence', '_license', '_file', '_path'))
            if isinstance(child, (dict, list)) or source:
                parts.append(provenance_text(child, source))
        return ' '.join(parts)
    if isinstance(value, list):
        return ' '.join(provenance_text(child, include) for child in value)
    return str(value) if include else ''


def source_text(row, scratch):
    """Read ancestry sidecars recursively without treating policy as a donor."""
    text = row.get('source', '') + ' ' + row.get('licence', '')
    seen = set()
    for _ in range(128):
        paths = [p for p in dict.fromkeys(re.findall(r'source metadata ([^)]+?\.json)', text)) if p not in seen]
        if not paths:
            break
        for name in paths:
            seen.add(name)
            path = Path(name)
            if path.suffix == '.json' and path.resolve().is_relative_to(Path(scratch).resolve()) and path.is_file():
                text += ' ' + provenance_text(json.loads(path.read_text()))
    return text


def refused_source(row, scratch):
    text = source_text(row, scratch)
    if 'unresolved public upstream ' in text:
        return 'unresolved public upstream'
    if re.search(r'cc[ -]by[ -]sa', text, re.I):
        return 'CC BY-SA donor'
    if 'penguin069/squares-joegun-boxed-certified-union' in text:
        return 'unread penguin source'
    if any(proof in text for proof in refused_proofs(str(scratch))):
        return 'excluded round22 harvest ancestor proof'
    if re.search(r'take-(?:harvest|polish)-r22/(?:work/public/starts/)?(?:639|691|745|858|918)(?:/|\.csv)', text):
        return 'excluded round22 harvest packing'
    if re.search(r'take-[a-z0-9-]+-r23/(?:near/)?(?:639|980|981)(?:[-/.]|$)', text):
        return 'excluded round23 descendant'
    if re.search(r'take-forensics-r(?:19|20|21|22|23)/(?:near/)?918(?:[-/.]|$)', text):
        return 'excluded older forensics n918'
    if re.search(r'take-(?:invent|midm)-r23(?: n\s*[=:]?\s*639|/[^ ;]*639)', text):
        return 'excluded round23 n639 descendant'
    if re.search(r'(?:held(?: packing| file)?|round 21 (?:file|packing))(?: of)?(?: n)?\s*[=:]?\s*801\b', text, re.I):
        return 'held n801 donor'
    return None


class DeadlineCollector(Collector):
    def run(self):
        scratch = Path(self.args.details).resolve().parents[2]
        if getattr(self, 'seed_policy', None) is not None:
            self.seed_policy.prepare(self)
        for directory in self.args.own + self.args.out:
            path = Path(directory) / 'take.tsv'
            rows = table(path)
            keep = []
            for row in rows:
                reason = refused_source(row, scratch)
                policy = getattr(self, 'seed_policy', None)
                if policy is not None:
                    row, flag, roots = policy.mark(row)
                    reason = reason or refused_source(row, scratch)
                    if flag == 'unknown':
                        reason = reason or 'unknown seed roots'
                    elif directory in self.args.out and not policy.peer_allowed(row):
                        reason = reason or 'old result belongs to the other seed group'
                if reason:
                    print('source exclusion', row['n'], reason, flush=True)
                else:
                    keep.append(row)
            if keep != rows:
                temp = path.with_suffix('.source.tmp')
                with temp.open('w') as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
                    writer.writeheader()
                    writer.writerows(keep)
                temp.replace(path)
        archive = self.work.parent / 'excluded-near'
        for directory in self.args.out:
            for metadata in (Path(directory) / 'near').glob('*.csv.json'):
                row = json.loads(metadata.read_text())
                reason = refused_source(row, scratch)
                if reason:
                    archive.mkdir(exist_ok=True)
                    packing = Path(str(metadata)[:-5])
                    if packing.exists():
                        packing.replace(archive / packing.name)
                    metadata.replace(archive / metadata.name)
                    print('archive excluded near', packing, reason, flush=True)
        return super().run()

    def peer_allowed(self, row):
        policy = getattr(self, 'seed_policy', None)
        return policy is None or policy.peer_allowed(row)

    def remote(self, cert, n):
        proof = self.work / ('remote-' + cert[2] + '.json')
        if time.time() >= self.deadline and not proof.exists():
            raise RuntimeError('common search and quench deadline reached')
        result = super().remote(cert, n)
        if getattr(self, 'on_remote', None):
            self.on_remote()
        return result


class Follow:
    def __init__(self, args):
        self.a = args
        self.round = getattr(args, 'round', 23)
        self.base_round = getattr(args, 'base_round', 21)
        self.base_gate = getattr(args, 'base_gate', 'cand-round21-1113a')
        self.live_rounds = [self.round] if self.round >= 24 else [22, 23]
        self.s = Path(args.scratch)
        self.t = Path(args.take)
        self.w = self.t / 'work'
        self.raw = self.w / 'candidates'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.starts = self.w / 'starts'
        self.starts.mkdir(exist_ok=True)
        self.deadline = int((self.w / 'deadline').read_text())
        self.deadline_label = dt.datetime.fromtimestamp(self.deadline, dt.timezone.utc).strftime('%H:%MZ')
        self.done_path = self.w / 'follow-seen.json'
        self.done = set(json.loads(self.done_path.read_text())) if self.done_path.exists() else set()
        self.pending = {}
        self.child = None
        self.run_item = None
        self.last_scan = 0
        self.last_collect = 0
        self.public_stage = 'fetch'
        self.public_child = None
        processed = self.w/'public-processed.json'
        if processed.exists():
            self.public_stage = 'done'
        self.public_log = None
        self.stats = dict(queued=0, completed=0, finds=0, public_starts=0, timeout=0)
        self.collector = DeadlineCollector(SimpleNamespace(
            details=str(self.s / 'gate' / self.base_gate / 'details.csv'),
            work=str(self.w / 'collector'), own=[str(self.raw)],
            live=[str(self.s / f'take-*-r{r}') for r in self.live_rounds],
            out=[str(self.t)] if self.round >= 24 else [str(self.t), str(self.s / f'take-polish-r{self.round}')], exclude=[],
            host='boxD', remote_dir=f'scratch/squares-harvest/r{self.round}',
            handoff=str(self.s / f'handoff-r{self.round}.log'), control=False))
        self.collector.deadline = self.deadline
        self.collector.on_remote = self.progress
        self.held = dict(self.collector.held)
        self.collector.strict_held = dict(self.held)
        self.seed_policy = SeedPolicy(self.s, self.t, source_text, table, rows_write) if self.round >= 24 else None
        self.collector.seed_policy = self.seed_policy
        self.clean_raw = self.w/'clean-candidates'
        self.clean_raw.mkdir(exist_ok=True)
        self.scan_seen = {}
        self.freeze_start = time.time()
        self.shapes = set()
        previous = self.s / f'take-harvest-r{self.round-1}' / 'work'
        previous_done = previous / 'follow-seen.json'
        if self.round >= 24 and previous_done.exists():
            old_done = set(json.loads(previous_done.read_text()))
            for p in (previous/'starts').glob('*.csv'):
                if hashlib.sha256(p.read_bytes()).hexdigest() in old_done:
                    self.shapes.add(self.shape(csv_rows(p)))
        for p in self.starts.glob('*.csv'):
            if hashlib.sha256(p.read_bytes()).hexdigest() in self.done:
                self.shapes.add(self.shape(csv_rows(p)))

    def state(self, msg):
        msg = dt.datetime.now(dt.timezone.utc).isoformat() + ' boxA ' + msg
        print(msg, flush=True)
        with (self.t / 'STATE.txt').open('a') as f:
            f.write(msg + '\n')

    def hand(self, msg):
        with (self.s / f'handoff-r{self.round}.log').open('a') as f:
            f.write(dt.datetime.now(dt.timezone.utc).isoformat() + ' harvest -> all: ' + msg + '\n')

    def bars(self):
        bars = dict(self.held)
        if self.seed_policy:
            self.clean_bars = {n:self.seed_policy.relaxed.get(n,self.held.get(n,math.inf)) for n in SPECIAL}
        for pat in (f'take-*-r{r}/take.tsv' for r in self.live_rounds):
            for p in self.s.glob(pat):
                for r in table(p):
                    n = int(r['n'])
                    if (p.parent / f'{n}.csv').exists():
                        bars[n] = min(bars[n], float(r['new']))
                        if self.seed_policy and n in SPECIAL and self.seed_policy.mark(r)[1] == 'no':
                            self.clean_bars[n] = min(self.clean_bars[n], float(r['new']))
        return bars

    @staticmethod
    def shape(rows):
        return tuple(sorted((int(r['square_id']), round(float(r['x']), 8),
                             round(float(r['y']), 8), round(float(r['angle']), 10))
                            for r in rows))

    def enqueue(self, path, origin, kind, priority=1):
        path = Path(path)
        try:
            reason = refused_source(origin, self.s)
            if reason:
                return
            raw = path.read_bytes()
            key = hashlib.sha256(raw).hexdigest()
            if key in self.pending:
                return
            rows = list(csv.DictReader(raw.decode().splitlines()))
            n = int(rows[0]['n'])
            shape = self.shape(rows)
            if len(rows) != n or any(int(r['n']) != n for r in rows):
                return
            score = side_est(rows) / math.sqrt(n) - 1
            policy_row, seed_flag, seed_ns = self.seed_policy.mark(origin) if self.seed_policy else (origin, 'no', ())
            origin = policy_row
            if refused_source(origin, self.s):
                return
            eligibility_bar = self.clean_bars.get(n, self.seed_policy.relaxed[n]) if self.seed_policy and n in SPECIAL and seed_flag == 'no' else self.current_bars[n]
            winning = (score < eligibility_bar - 1e-10
                       and bool(origin.get('licence'))
                       and not origin['licence'].startswith(('unknown', 'unresolved')))
            if not winning and (key in self.done or shape in self.shapes):
                return
            slack = 0.015 / math.sqrt(n) if self.round >= 24 and kind == 'design' else 2e-5
            if score > eligibility_bar + slack:
                return
            target = self.starts / (str(n) + '-' + key[:16] + '.csv')
            if not target.exists():
                target.write_bytes(raw)
            # Keep producer metadata beside the immutable start rather than
            # referring to a mutable generic near sidecar.
            for index, name in enumerate(dict.fromkeys(re.findall(r'source metadata ([^)]+?\.json)', origin['source']))):
                metadata = Path(name)
                if metadata.suffix == '.json' and metadata.resolve().is_relative_to(self.s.resolve()) and metadata.is_file():
                    snapshot = Path(str(target) + '.source-' + str(index) + '-' + hashlib.sha256(metadata.read_bytes()).hexdigest()[:12] + '.json')
                    snapshot.write_bytes(metadata.read_bytes())
                    origin = dict(origin, source=origin['source'].replace(name, str(snapshot)))
            row = dict(n=n, held=repr(self.held[n]), new=repr(score),
                       gain=repr(self.held[n] - score), source=origin['source'],
                       licence=origin.get('licence') or '', start=repr(score), polish_gain='0')
            self.shapes.add(shape)
            if self.seed_policy and n in SPECIAL and seed_flag == 'no':
                priority = min(priority, -3)
            self.pending[key] = dict(path=str(target), row=row, key=key, kind=kind,
                                     priority=priority, created=path.stat().st_mtime, queued=time.time())
            Path(str(target) + '.json').write_text(json.dumps(self.pending[key], indent=2) + '\n')
            self.stats['queued'] += 1
            # A new winning build can reach the followers after its certified
            # remote quench, while the optional local search still waits.
            if score < eligibility_bar - 1e-10:
                self.add_raw(target, row)
            self.state(f'QUEUE {kind} n={n} gap={score-self.current_bars[n]:.3e} source={path}. Deadline {self.deadline_label}, log work/runs/{key[:16]}.log')
        except (OSError, ValueError, KeyError, IndexError) as exc:
            self.state('skip unreadable start ' + str(path) + ': ' + repr(exc))

    def scan(self):
        self.current_bars = self.bars()
        manual = self.w / 'manual-starts.json'
        if manual.exists() and getattr(self, 'manual_stamp', None) != manual.stat().st_mtime_ns:
            for item in json.loads(manual.read_text()):
                self.enqueue(item['path'], item, 'backlog', 4)
            self.manual_stamp = manual.stat().st_mtime_ns
        hand = self.s / f'handoff-r{self.round}.log'
        text = hand.read_text() if hand.exists() else ''
        (self.w / 'handoff-last-read.txt').write_text(text)
        for p in sorted(self.s.glob(f'take-*-r{self.round}/take.tsv')):
            if p.parent in (self.t, self.s / f'take-polish-r{self.round}'):
                continue
            for row in table(p):
                n = int(row['n'])
                marked, flag, roots = self.seed_policy.mark(row) if self.seed_policy else (row, 'no', ())
                bar = self.clean_bars.get(n, self.seed_policy.relaxed[n]) if self.seed_policy and n in SPECIAL and flag == 'no' else self.current_bars[n]
                if float(row['new']) <= bar + 1e-10:
                    self.enqueue(p.parent / f'{n}.csv', dict(row, source=row['source'] + ' (' + str(p) + ')'), 'take', 2)
        paths = []
        for line in reversed(text.splitlines()):
            if 'harvest ->' in line or '->' not in line:
                continue
            paths.extend(re.findall(r'$SCRATCH/bounties-squares/[^\s,;]+\.csv', line))
        for p in self.s.glob(f'take-*-r{self.round}/near/*.csv'):
            if p.parent.parent not in (self.t, self.s / f'take-polish-r{self.round}'):
                paths.append(str(p))
        for raw in dict.fromkeys(paths):
            p = Path(raw)
            if not p.exists():
                continue
            stat = p.stat()
            token = (stat.st_mtime_ns, stat.st_size)
            if self.scan_seen.get(raw) == token:
                continue
            self.scan_seen[raw] = token
            source = 'fresh layout ' + raw
            licence = ''
            if 'take-readers-' in str(p):
                donor = re.search(r'from(.+)\.csv$', p.name)
                root = next((q for q in p.parents if q.name.startswith('take-readers-')), None)
                if donor and root:
                    for origin in table(root / 'work/sources-all.tsv'):
                        if origin.get('donor') == donor[1]:
                            source = 'layer walk ' + p.name + ' from ' + origin['source'] + ' (' + str(root / 'work/sources-all.tsv') + ')'
                            licence = origin.get('licence') or ''
                            break
            # Producers retain the exact source in their take, near table or sidecar.
            for name in ('near.tsv', 'take.tsv'):
                for row in table(p.parent / name):
                    if row.get('file') == p.name or (row.get('n') == p.stem and name == 'take.tsv'):
                        source = row.get('source') or source
                        licence = row.get('licence') or licence
            metas = [Path(str(p) + '.json'), p.with_suffix('.json')]
            if p.parent.parent.name == f'take-stair-c-r{self.round}':
                stem = p.stem.rsplit('-', 1)[0]
                boxkey = p.stem.rsplit('-', 1)[-1]
                metas.append(p.parent.parent / 'work' / 'boxcopy' / boxkey / 'raw-a' / (stem + '.json'))
            for meta in metas:
                if meta.exists():
                    try:
                        d = json.loads(meta.read_text())
                        stack = [d]
                        notices = set()
                        while stack:
                            node = stack.pop()
                            if isinstance(node, dict):
                                for k, v in node.items():
                                    if not nonancestral_key(k) and k in ('licence', 'license', 'donor_licence') and isinstance(v, str):
                                        notices.add(v)
                                    elif isinstance(v, (dict, list)) and not nonancestral_key(k):
                                        stack.append(v)
                            elif isinstance(node, list):
                                stack.extend(v for v in node if isinstance(v, (dict, list)))
                        licence = '; '.join(sorted(notices)) or licence
                        source += ' (source metadata ' + str(meta) + ')'
                        licence = d.get('licence') or d.get('donor_licence') or licence
                        m = d.get('manifest')
                        if isinstance(m, dict):
                            source += ' from ' + str(m.get('donor_source', ''))
                            licence = m.get('donor_licence') or licence
                    except (OSError, ValueError):
                        pass
            # Missing upstream terms remain explicit and cannot become an accepted take.
            licence = licence or 'unresolved upstream notices: ' + str(p.parent) + f' and results/round{self.base_round}-best-2026-11-13.tsv'
            self.enqueue(p, dict(source=source, licence=licence), 'design', 0 if 'readers' in raw else 1)
        self.last_scan = time.time()
        self.state(f'SCAN handoff lines={len(text.splitlines())}, waiting={len(self.pending)}. Next fresh unquenched reader ends before repeated certified copies.')

    def add_raw(self, path, row):
        n = int(row['n'])
        if refused_source(row, self.s):
            return
        row, flag, seed_ns = self.seed_policy.mark(row) if self.seed_policy else (row, 'no', ())
        if refused_source(row, self.s):
            return
        if flag == 'unknown':
            return
        clean = bool(self.seed_policy and n in SPECIAL and flag == 'no')
        raw = self.clean_raw if clean else self.raw
        reference = self.seed_policy.relaxed[n] if clean else self.held[n]
        result = self.collector.cert(path, n)
        if not result:
            return
        score, cert, key = result
        if score >= reference - 1e-10:
            return
        old = {int(r['n']): r for r in table(raw / 'take.tsv')}
        if n in old and score >= float(old[n]['new']):
            return
        if not row.get('licence') or row['licence'].startswith(('unresolved', 'unknown')):
            self.state(f'HOLD n={n} unresolved/refused licence: {row.get("licence")}')
            return
        rows_write(raw / f'{n}.csv', csv_rows(cert))
        old[n] = dict(row, new=repr(score), held=repr(reference), gain=repr(reference-score),
                      polish_gain=repr(float(row['start'])-score))
        write_table(raw / 'take.tsv', [old[n] for n in sorted(old)])
        self.stats['finds'] += 1

    def start(self):
        if not self.pending or time.time() >= self.deadline:
            return
        def rank(x):
            age = max(0, time.time() - x.get('queued', x['created']))
            copy = x['kind'] == 'take'
            slot = copy if self.round >= 24 else ((not copy) if getattr(self, 'fast', False) else copy)
            return slot, x['priority'] - min(2, age / 300), -x['created']
        item = min(self.pending.values(), key=rank)
        self.pending.pop(item['key'])
        self.done.add(item['key'])
        self.done_path.write_text(json.dumps(sorted(self.done)) + '\n')
        n = int(item['row']['n'])
        run = self.w / 'runs' / item['key'][:16]
        run.parent.mkdir(exist_ok=True)
        rows = csv_rows(item['path'])
        side, a = normalize([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows])
        write_txt(run.with_suffix('.txt'), side, a)
        flags = [] if item['kind'] in ('design', 'backlog') and not getattr(self, 'fast', False) else ['--no-alm', '--loosen', '1.0', '--pit', '80', '--flip-top', '8']
        cmd = [FQ, 'quench', '--in', str(run.with_suffix('.txt')), '--out', str(run.with_suffix('.out'))] + flags
        with run.with_suffix('.log').open('w') as log:
            self.child = subprocess.Popen(['nice', '-n', '5'] + cmd, stdout=log, stderr=log, start_new_session=True)
        item.update(run=str(run), started=time.time(), pid=self.child.pid, limit=45 if getattr(self, 'fast', False) or item['kind'] == 'backlog' else 180)
        if getattr(self, 'fast', False):
            item['kind'] = 'fast-' + item['kind']
        self.run_item = item
        self.state(f'START fq pid={self.child.pid} n={n} kind={item["kind"]} limit={item['limit']}s command={cmd} deadline={self.deadline_label}')

    def finish(self):
        if self.child is None:
            return
        item = self.run_item
        rc = self.child.poll()
        if rc is None and time.time() < min(item['started'] + item.get('limit', 180), self.deadline):
            return
        if rc is None:
            os.killpg(self.child.pid, signal.SIGKILL)
            rc = self.child.wait()
            self.stats['timeout'] += 1
        n = int(item['row']['n'])
        p = Path(item['run']).with_suffix('.out')
        gain = None
        if rc == 0 and p.exists():
            self.add_raw(item['path'], item['row'])
            side, a = read_txt(p)
            candidate = Path(item['run']).with_suffix('.csv')
            rows_write(candidate, to_rows(n, a))
            result = self.collector.cert(candidate, n)
            if result:
                score, cert, key = result
                gain = float(item['row']['start']) - score
                self.add_raw(cert, dict(item['row'], source='fq quench of ' + item['row']['source']))
                if gain > 1e-8 and score < self.current_bars[n] + (0.015/math.sqrt(n) if self.round >= 24 else 2e-5) and not refused_source(item['row'], self.s):
                    near = self.t / 'near' / f'{n}-fq-{key[:16]}.csv'
                    rows_write(near, csv_rows(cert))
                    Path(str(near) + '.json').write_text(json.dumps(dict(item['row'], new=score, polish_gain=gain), indent=2) + '\n')
                    self.hand(f'certified fq layout n={n}, gain on start={gain:.3e}, source/licence in sidecar, {near}')
        item.update(exit=rc, gain=gain, finished=time.time())
        Path(item['run']).with_suffix('.json').write_text(json.dumps(item, indent=2) + '\n')
        self.stats['completed'] += 1
        self.state(f'FINISH fq n={n} exit={rc} gain={gain} log={item["run"]}.log')
        self.child = None
        self.run_item = None

    def public(self):
        plan = self.w / 'public-next.json'
        if self.public_stage == 'done' and plan.exists():
            config = json.loads(plan.read_text())
            if time.time() >= config['not_before'] and time.time() < self.deadline:
                destination = Path(config['out'])
                destination.mkdir(parents=True, exist_ok=True)
                script = self.w / 'public.sh'
                commands = [
                    [sys.executable, '-I', str(LANE/'harvest_delta.py'), config['previous'], str(destination/'data')],
                    [sys.executable, '-I', str(LANE/'harvest_register.py'), str(self.s/'register-clones'), str(destination/'data')]]
                script.write_text('#!/bin/bash\nset -eu\nexport OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1\n'
                                  + '\n'.join(shlex.join(cmd) + ' > ' + shlex.quote(str(destination/name)) + ' 2>&1'
                                              for cmd, name in zip(commands, ('delta.log', 'register.log'))) + '\n')
                log = (destination/'fetch.log').open('a')
                self.fetch_child = subprocess.Popen(['nohup', 'nice', '-n', '5', 'bash', str(script)],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
                log.close()
                (self.w/'public.pid').write_text(str(self.fetch_child.pid) + '\n')
                (self.w/'public-active.txt').write_text(str(destination) + '\n')
                plan.replace(self.w/'public-plan-started.json')
                (self.w/'public-processed.json').unlink(missing_ok=True)
                self.public_stage = 'fetch'
                self.state('START second full public delta pid=' + str(self.fetch_child.pid) + ' log=' + str(destination/'delta.log') + ' deadline=' + self.deadline_label)
        active = self.w / 'public-active.txt'
        p = Path(active.read_text().strip()) if active.exists() else self.w / 'public'
        if self.public_stage == 'fetch':
            pid = int((self.w / 'public.pid').read_text())
            if getattr(self, 'fetch_child', None) is not None:
                if self.fetch_child.poll() is None:
                    return
            else:
                try:
                    os.kill(pid, 0)
                    return
                except ProcessLookupError:
                    pass
            self.public_stage = 'merge-wait'
            self.state('FINISH public fetch. Next metric merge with one worker, before public publication.')
        if self.public_stage == 'merge-wait':
            bars = self.bars()
            if self.seed_policy:
                bars.update(self.clean_bars)
            with (p / 'base.tsv').open('w') as f:
                w = csv.writer(f, delimiter='\t')
                w.writerow(('n', 'score', 'L', 'reason'))
                w.writerows((n, score, (score+1)*math.sqrt(n), 'ok') for n, score in sorted(bars.items()))
            self.public_log = (p / 'merge.log').open('w')
            self.public_child = subprocess.Popen([sys.executable, '-I', str(LANE / 'harvest_merge.py'), '--harvest', str(p/'data'), '--base', str(self.s/f'gather/round{self.base_round}-2026-11-13a.csv'), '--base-tsv', str(p/'base.tsv'), '--out', str(p/'merged'), '--procs', '1'], stdout=self.public_log, stderr=self.public_log, start_new_session=True)
            self.public_stage = 'merging'
            self.state('START public metric merge pid=' + str(self.public_child.pid) + ' log ' + str(p/'merge.log') + ' deadline ' + self.deadline_label)
        if self.public_stage == 'merging' and self.public_child.poll() is not None:
            self.public_log.close()
            self.public_stage = 'done'
            self.current_bars = self.bars()
            for folder in ('best', 'alt'):
                for row in table(p / 'merged' / (folder + '.tsv')):
                    if row['source'] == 'seed merged0' or not accepted(row['licence']):
                        continue
                    row = public_origin(p / 'data', row)
                    if refused_source(row, self.s):
                        continue
                    n = int(row['n'])
                    path = p / 'merged' / folder / f'{n}.csv'
                    result = self.collector.cert(path, n)
                    row, flag, roots = self.seed_policy.mark(row) if self.seed_policy else (row, 'no', ())
                    bar = self.clean_bars.get(n, self.seed_policy.relaxed[n]) if self.seed_policy and n in SPECIAL and flag == 'no' else self.current_bars[n]
                    if result and result[0] < bar - 1e-10:
                        score, cert, key = result
                        row.update(held=repr(self.held[n]), new=repr(score), gain=repr(self.held[n]-score), start=repr(score), polish_gain='0')
                        self.add_raw(cert, row)
                        dest = p / 'starts' / f'{n}.csv'
                        dest.parent.mkdir(exist_ok=True)
                        rows_write(dest, csv_rows(cert))
                        Path(str(dest)+'.json').write_text(json.dumps(row, indent=2)+'\n')
                        self.hand(f'new certified public n={n}, score={score}, source={row["source"]}, licence={row["licence"]}, {dest}')
                        self.enqueue(dest, row, 'public', -1)
                        self.stats['public_starts'] += 1
                        self.progress()
            (self.w/'public-processed.json').write_text(json.dumps(dict(path=str(p), finished=time.time())) + '\n')
            self.state('FINISH public merge, fresh starts=' + str(self.stats['public_starts']))

    def second(self):
        # The foreground certificate slot can run one short quench after the
        # public fetch and metric merge release it. It never overlaps scoring.
        if self.public_stage != 'done' or not self.pending or self.child is None:
            return
        primary, original = self.child, self.run_item
        self.child, self.run_item = None, None
        self.fast = True
        try:
            self.start()
            if self.child is not None:
                while self.child.poll() is None and time.time() < min(self.run_item['started'] + 45, self.deadline):
                    time.sleep(.2)
                self.finish()
        finally:
            self.child, self.run_item = primary, original
            self.fast = False

    def progress(self):
        self.finish()
        if time.time() - self.last_scan > 60:
            self.scan()
        if self.child is None and time.time() < self.deadline:
            self.start()

    def run(self):
        self.state('START follow: one fq worker, one discovery/certificate slot. Common deadline ' + self.deadline_label + '. Remote proof uses one brief boxD quench while the certificate slot waits.')
        try:
            while time.time() < self.deadline:
                try:
                    self.finish()
                    self.public()
                    if time.time() - self.last_scan > 60 and self.public_stage != 'merging':
                        self.scan()
                    if self.public_stage != 'merge-wait':
                        self.start() if self.child is None else None
                    if time.time() - self.last_collect > 60 and self.public_stage != 'merging':
                        self.collector.run()
                        self.last_collect = time.time()
                    self.second()
                    (self.w/'stats.json').write_text(json.dumps(self.stats, indent=2)+'\n')
                    (self.w/'pending.json').write_text(json.dumps(list(self.pending.values()), indent=2)+'\n')
                except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                    self.state('RETRY after transient follow error ' + repr(exc))
                time.sleep(2)
        finally:
            try:
                pid = int((self.w / 'public.pid').read_text())
                command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout
                if self.public_stage == 'fetch' and owned_public_fetch(command, self.w / 'public.sh'):
                    os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            if self.child is not None:
                self.finish()
            if self.public_child is not None and self.public_child.poll() is None:
                os.killpg(self.public_child.pid, signal.SIGKILL)
                self.public_child.wait()
            self.collector.run()
            self.state('FINISH follow at common deadline. Final raw results drained. Stats ' + json.dumps(self.stats))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scratch', required=True)
    ap.add_argument('--take', required=True)
    ap.add_argument('--round', type=int, default=23)
    ap.add_argument('--base-round', type=int, default=21)
    ap.add_argument('--base-gate', default='cand-round21-1113a')
    args = ap.parse_args()
    Follow(args).run()


if __name__ == '__main__':
    main()
