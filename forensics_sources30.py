"""Round 30 donor admission and retained ancestry evidence."""
import csv
import hashlib
from functools import lru_cache
import json
import re
from pathlib import Path

csv.field_size_limit(16 * 1024 * 1024)
OUT = {639, 691, 745, 858, 918, 980}
_READER_ACTIVE = set()


@lru_cache(maxsize=8)
def accepted(scratch):
    data = json.loads((Path(scratch) / 'gate/cand-round23-1113a/gate.json').read_text())
    return {int(row['n']) for row in data['moved']}


@lru_cache(maxsize=512)
def _record(path, n, token):
    path = Path(path)
    ledger = path.parent / 'take.tsv'
    if path.parent.name == 'near':
        ledger = path.parent.parent / 'take.tsv'
    if path.stem.isdigit() and ledger.exists():
        rows = [r for r in csv.DictReader(open(ledger), delimiter='\t') if int(r['n']) == n]
        if rows:
            return rows[0], str(ledger)
    for sidecar in (Path(str(path) + '.json'), path.with_suffix('.json')):
        if sidecar.exists():
            return json.loads(sidecar.read_text()), str(sidecar)
    root = path.parent.parent if path.parent.name == 'near' else path.parent
    sources = root / 'work/sources-all.tsv'
    if sources.exists():
        rows = [r for r in csv.DictReader(open(sources), delimiter='\t')
                if str(path) in json.dumps(r) or path.name in json.dumps(r)]
        if rows:
            return rows, str(sources)
    return None, str(ledger)


def record(path, n):
    path = Path(path)
    root = path.parent.parent if path.parent.name == 'near' else path.parent
    candidates = [root / 'take.tsv', Path(str(path) + '.json'), path.with_suffix('.json'), root / 'work/sources-all.tsv']
    token = tuple((str(p), p.stat().st_mtime_ns) for p in candidates if p.exists())
    return _record(str(path), n, token)


def compact_ancestry(value, origin_file):
    """Return unique roots and keep the full derivation at its immutable file."""
    import forensics_policy
    roots = {}
    def add(root):
        roots[json.dumps(root, sort_keys=True)] = root
    def visit(item):
        if isinstance(item, list):
            return any([visit(child) for child in item])
        if not isinstance(item, dict):
            return False
        path, n = item.get('path'), item.get('n')
        if path and isinstance(n, int):
            donor = Path(path)
            if donor.parent.name == 'gather' or (re.fullmatch(r'take-.+-r23', donor.parent.name) and donor.stem.isdigit()):
                add(dict(path=path, n=n, reason=item.get('reason', 'recorded root')))
                return True
        if item.get('reason') == 'retained polished public input and verified upstream row':
            add(item)
            return True
        if item.get('reason') == 'declared root retained by reference':
            add(item)
            return True
        found = any([visit(child) for key, child in item.items() if key != 'record'])
        if not found and path and isinstance(n, int):
            rec = item.get('record', item)
            source = str(rec.get('source', '')) if isinstance(rec, dict) else ''
            licence = rec.get('licence', '') if isinstance(rec, dict) else ''
            seed = forensics_policy.classify_text(json.dumps(rec))
            if source.strip() == 'seed merged0' and seed['status'] == 'none':
                seed['status'] = 'unknown'
            add(dict(path=path, n=n, reason='declared root retained by reference',
                     source=source[:1000], licence=licence, seed_policy=seed,
                     source_proof=str(origin_file)))
            return True
        return found
    visit(value)
    return dict(reason='unique immutable ancestry roots', source_proof=str(origin_file), roots=list(roots.values()))


def packing_refs(text):
    """Split notice tokens before reading a packing path and count."""
    for token in re.split(r'[\s";,()]+', text):
        start = token.find('$SCRATCH/bounties-squares/take-')
        if start < 0:
            start = token.find('take-')
        if start < 0:
            continue
        token = token[start:]
        end = token.find('.csv')
        if end < 0:
            continue
        token = token[:end + 4]
        tail = token.rsplit('/', 1)[-1]
        match = re.fullmatch(r'(\d+)(?:-[^/]*)?\.csv', tail)
        if match and '/' in token:
            yield token, match[1]


def source_pairs(text):
    """Read take and gather identities from retained source strings."""
    if '.csv' not in text or ('take-' not in text and 'gather/' not in text):
        return frozenset()
    found = set((path, int(n)) for path, n in packing_refs(text))
    values = {text, text.replace('\\"', '"'), text.replace('\\"', '"').replace('\\"', '"')}
    for value in values:
        for path, n in re.findall(r'["\']([^"\']*gather/[^"\']+\.csv)["\']\s*,\s*(\d+)', value):
            found.add((path, int(n)))
    return found


def declared_withdrawal(value, scratch):
    if not isinstance(value, dict):
        return False
    raw_n = value.get('n')
    try:
        n = int(raw_n) if raw_n is not None else None
    except (TypeError, ValueError):
        n = None
    if n is not None and value.get('path') and withdrawn(value['path'], n, scratch):
        return True
    src = value.get('source')
    if isinstance(src, (list, tuple)) and len(src) == 2 and isinstance(src[0], str):
        try:
            if withdrawn(src[0], int(src[1]), scratch):
                return True
        except (ValueError, TypeError):
            pass
    origin_text = value.get('origin')
    origin = re.match(r'(?:held|candidate) round(\d+)', origin_text) if isinstance(origin_text, str) else None
    return False  # The held813/933 withdrawal reached only the lifted seed503 rule.


def withdrawn_paths(root):
    return frozenset()  # Those paths were excluded only for Samanyu ancestry.


@lru_cache(maxsize=32768)
def withdrawn(path, n, scratch):
    """Keep public source failures. Own-layout share withdrawals are lifted."""
    path = Path(path)
    # The first r28 original pool mislabelled these direct Couzo selections as owned.
    if 'take-forensics-r28' in path.parts and path.parent.name == 'own-originals' and n in {5, 10, 11, 17, 530, 531, 534, 535, 26, 27, 28, 29, 538, 37, 38, 39, 40, 41, 50, 52, 55, 65, 577, 67, 68, 69, 578, 71, 581, 583, 584, 585, 586, 82, 83, 84, 85, 86, 87, 88, 89, 101, 102, 103, 104, 105, 106, 635, 108, 109, 110, 626, 627, 630, 631, 632, 634, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 636, 145, 146, 147, 148, 149, 152, 154, 155, 156, 677, 678, 679, 680, 681, 170, 171, 684, 173, 174, 175, 176, 177, 686, 179, 180, 181, 687, 183, 688, 197, 198, 199, 200, 201, 202, 205, 206, 208, 209, 210, 211, 730, 731, 732, 733, 734, 226, 227, 228, 229, 230, 231, 741, 233, 235, 236, 237, 238, 239, 240, 241, 257, 258, 259, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 785, 786, 787, 788, 789, 290, 292, 295, 296, 297, 298, 300, 301, 302, 304, 305, 306, 308, 325, 326, 328, 329, 330, 331, 332, 842, 843, 844, 336, 337, 845, 339, 340, 341, 847, 850, 853, 362, 363, 366, 367, 368, 369, 371, 374, 375, 380, 381, 901, 902, 903, 909, 912, 401, 402, 403, 407, 408, 442, 443, 444, 447, 448, 449, 962, 963, 452, 964, 970, 974, 975, 464, 485, 486, 487, 488, 489, 490, 491, 492, 493}:
        return True
    if ('take-forensics-r23' in path.parts and 'donors' in path.parts and
            path.name.startswith(('858-ec97a452', '745-64c4b4f8'))):
        return True
    if path.parent.name == 'take-forensics-r23' and n == 980:
        return True
    if re.fullmatch(r'take-forensics-r(?:1\d|2[0-3])', path.parent.name) and n == 918:
        return True
    if path.parent.name in {'take-invent-r23','take-midm-r23'} and n == 639:
        return True
    if 'take-harvest-r27' in path.parts and n == 916:
        return True  # Missing public upstream lineage, not a geometric match.
    if 'take-harvest-r26' in path.parts and 'near-pub' in path.parts:
        return True  # This archive lacks a complete per-layout source proof.
    return False


def _trace(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    if not path.is_absolute() and str(path).startswith(('take-', 'gather/')):
        path = Path(scratch) / path
    active = set() if active is None else set(active)
    key = (str(path), n)
    evidence = dict(path=str(path), n=n)
    if withdrawn(path, n, scratch):
        return False, dict(evidence, reason='explicit frozen withdrawal in round25 brief')
    if 'take-harvest-r22' in path.parts and n in {639, 691, 745, 858, 918}:
        return False, dict(evidence, reason='excluded round22 public donor and its archived copies')
    if path.exists() and (path.name in {'samanyu_bestfit.csv', '921-29e12ff3.csv'} or 'samanyu_bestfit.csv' in str(path)):
        return True, dict(evidence, reason='own discovered seed, round27 source clarification', source='own discovered packing, later matched by Samanyu-dev/squares_in_squares')
    if not path.exists():
        old703 = Path(scratch) / 'take-harvest-r22/703.csv'
        if path == old703 and n == 703:
            table = Path(__file__).parent / 'results/round22-best-2026-11-13.tsv'
            row = next((r for r in csv.DictReader(open(table), delimiter='\t') if int(r['n']) == n), None)
            notice = 'archived public donor n = 703: areebbb/sis-certified-union-micro-shrink-lb-22-17479'
            if row and notice in row['source']:
                import readers_sources
                proof = readers_sources.archived_polish(str(scratch), n)
                return True, dict(proof, requested_path=str(path), ledger=str(table))
        return False, dict(evidence, reason='missing donor file')
    if path.stem.isdigit() and int(path.stem) != n:
        return False, dict(evidence, reason='donor count differs from requested count')
    if key in active:
        return False, dict(evidence, reason='ancestry cycle')
    active.add(key)
    candidate = Path(scratch) / 'gather/round23-2026-11-13a.csv'
    if path.parent.name == 'gather' and path.name in {'round23-2026-11-13b.csv', 'round24-2026-11-13a.csv'}:
        return True, dict(evidence, reason='submitted own held root under 00:19 rule')
    if path == candidate:
        return True, dict(evidence, reason='clean round23 candidate')
    if 'take-' in str(path) and '-r23/' in str(path) and path.stem.isdigit():
        ok = n not in OUT
        return ok, dict(evidence, reason='round23 changed-count whitelist' if ok else 'not in clean round23 take pool')
    # This frozen box export has a later local-parent proof for identical bytes.
    boxed = Path(scratch) / 'take-k123-r24/work/cc0/parts/847-licensed-parts.csv'
    local = Path(scratch) / 'take-k123-r24/near/847-cc0-rectangle-local-proof.csv'
    if path == boxed and local.exists():
        local_record, _ = record(local, n)
        if (isinstance(local_record, dict) and local_record.get('same_bytes_as') == str(path) and
                hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(local.read_bytes()).digest()):
            ok, parent = trace(local, n, scratch, active)
            return ok, dict(evidence, parent=parent, reason='byte-identical local parent proof')
    origin = Path(str(path) + '.origin.json')
    if origin.exists() and recorded is None:
        try:
            old = json.loads(origin.read_text())
        except (OSError, ValueError):
            return False, dict(evidence, reason='incomplete immutable origin record')
        if old.get('path') and withdrawn(old['path'], int(old.get('n', n)), scratch):
            return False, dict(evidence, reason='snapshot of explicitly withdrawn frozen row')
        if old.get('verified_ancestry') and 'ancestry' in old:
            # Re-check exclusions even when the proof predates a new exclusion.
            def clean(value,under_held=False):
                if isinstance(value, dict):
                    import forensics_public30
                    under_held=under_held or bool(forensics_public30.is_held_node(value))
                    if not under_held and value.get('path') and isinstance(value.get('n'), int) and withdrawn(value['path'], value['n'], scratch):
                        return False
                    return all(clean(v,under_held) for v in value.values())
                if isinstance(value, list):
                    return all(clean(v,under_held) for v in value)
                if isinstance(value, str):
                    return True
                return True
            ok = (hashlib.sha256(path.read_bytes()).hexdigest() == old.get('snapshot_sha256') and
                  clean(old['ancestry']))
            return ok, dict(evidence, origin=compact_ancestry(old['ancestry'], origin),
                            full_ancestry=old.get('full_ancestry'), reason='pinned immutable ancestry')
        ok, parent = trace(old['path'], old.get('n', n), scratch, active)
        return ok, dict(evidence, origin=parent)
    if path.parent.name == 'near' and 'take-readers-' in str(path) and re.search(r'from\d+-r\d+h[0-9a-f]+', path.name):
        if key in _READER_ACTIVE:
            return False, dict(evidence, reason='reader ancestry cycle')
        statefile = path.parent.parent / 'work/follow.json'
        if statefile.exists():
            import readers_sources
            _READER_ACTIVE.add(key)
            try:
                data = json.loads(statefile.read_text())
                ok, parent = readers_sources.audit((path, n, 24, True, '', ''), scratch, data)
                return ok, dict(evidence, reader_parent=parent, reason='reader version ancestry')
            finally:
                _READER_ACTIVE.remove(key)
    try:
        rec, ledger = (recorded, 'retained source record from rectangle metadata') if recorded is not None else record(path, n)
    except (OSError, ValueError, KeyError):
        return False, dict(evidence, reason='incomplete donor source record')
    if rec is None and path == Path(scratch) / 'take-midm-r24/work/fq-send/548.csv' and n == 548:
        root = Path(scratch) / 'take-midm-r24/work'
        expected = {
            'fq-send/548.csv': '45d4c7bc95d0c40322511bb60f25fde70253e6d5d4f3c2df50fd028f74b3e743',
            'boxE-final/r25092/548.csv': '0dcee6f12c25708cbebad667087c6324e7c719b55113902c9950bd915f2bace5',
            'boxE-final/run/s25092/raw/548-lkick-6748-2.csv': '745a8510f4815edfda42f95e4cfc97b9fafea98b49f3820a925ac33d0a9adaf3',
            'boxE-final/jobs/25092-548.json': '523d320320ddb67a99c15d4a4d1a4f093d1aa579a9af8ab78af90e162eb464c6',
            'boxE-final/done/25092-548.json': '7223d672697a9a3fdbdce8bad123639512a44f4dcc8d051022f50da4ca2c00b8',
            'provenance/0dcee6f12c25708cbebad667087c6324e7c719b55113902c9950bd915f2bace5-29fcc7efaae1f724.json': 'cad5e73c52b65f62e8c9f37571b26ed6dadf697bbbbef879ebfe872cf35ce2de',
        }
        if not all((root / name).exists() and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
                   for name, digest in expected.items()):
            return False, dict(evidence, reason='changed archived 548 certificate chain')
        source = next(root / name for name in expected if name.startswith('provenance/'))
        parts = json.loads(source.read_text())['record']['parts']
        parents = []
        for tag in ('A', 'B'):
            donor, count = parts[tag]['source']
            ok, parent = trace(donor, int(count), scratch, active)
            parents.append(parent)
            if not ok:
                return False, dict(evidence, parents=parents, reason='refused archived 548 parent')
        return True, dict(evidence, parents=parents, ancestry_file=str(source),
                          ancestry_sha256=expected[str(source.relative_to(root))],
                          certificate_chain=expected, reason='exact reproduced archived 548 certificate')
    if rec is None:
        snapshot = Path(scratch) / 'take-midm-r22/work/r2462/462.csv'
        public = Path(scratch) / 'take-harvest-r22/work/public/starts/462/462.csv'
        if path == snapshot and n == 462 and public.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest == hashlib.sha256(public.read_bytes()).hexdigest():
                ok, parent = trace(public, n, scratch, active)
                return ok, dict(evidence, parent=parent, sha256=digest,
                                reason='byte-identical retained public start')
        return False, dict(evidence, reason='missing source record', ledger=ledger)
    text = json.dumps(rec)
    evidence.update(ledger=ledger, record=rec)
    forbidden = ('penguin069/squares-joegun-boxed-certified-union',
                 'prvsiyan/squares-verified-best-of-1105', 'CC BY-SA')
    if any(term in text for term in forbidden):
        return False, dict(evidence, reason='prohibited upstream notice')
    # A kick or polish can name its actual frozen parent before its history.
    source_text = rec.get('source', '') if isinstance(rec, dict) else ''
    parent_match = re.search(r'from the round 23 file of n = (\d+) in (take-[a-z-]+-r23)', source_text)
    if (parent_match and int(parent_match[1]) == n and
            source_text.startswith(('fq quench', 'fq kick', 'midm_scan.py')) and
            not re.search(r'join|composition|rectangle', source_text[:parent_match.start()])):
        parent_n = int(parent_match[1])
        ok, parent = trace(Path(scratch) / parent_match[2] / (str(parent_n) + '.csv'), parent_n, scratch, active)
        if ok:
            return True, dict(evidence, parent=parent, reason='recorded frozen parent before inherited history')

    # This public r22 input has a retained per-count upstream notice.
    if ('take-harvest-r22' in path.parts and n not in {639, 691, 745, 858, 918, 801, 907} and
            'areebbb/sis-certified-union-micro-shrink-lb-22-17479' in text and 'Apache' in text):
        per_n = Path(scratch) / 'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
        public_row = next((r for r in csv.DictReader(open(per_n)) if int(r['n']) == n), None)
        expected = 'notebooks/malyshevdanil/squares-in-squares-living-atlas-of-tight-packings|ms'
        if public_row and public_row['src'] == expected:
            return True, dict(evidence, per_n_csv=str(per_n), per_n_row=public_row,
                source='areebbb/sis-certified-union-micro-shrink-lb-22-17479 -> malyshevdanil/squares-in-squares-living-atlas-of-tight-packings',
                licence='Apache 2.0 (Kaggle default for both public notebooks)',
                reason='retained polished public input and verified upstream row')
        return False, dict(evidence, reason='unsupported or unverified public upstream row')
    # A frozen take outside the clean pool is never an admission root.
    refs = set()
    retained = {}
    pinned_band = source_text.startswith('k123_join.py ') and 'pinned donor ancestry: ' in source_text
    # Rectangle metadata separates direct parents from inherited notice text.
    def structured(value):
        if isinstance(value, dict):
            src = value.get('source')
            if isinstance(src, (list, tuple)) and len(src) == 2 and isinstance(src[0], str):
                origin = Path(str(src[0]) + '.origin.json')
                pinned = origin.exists() and json.loads(origin.read_text()).get('verified_ancestry')
                parent = src[0] if pinned else value.get('original_file', src[0])
                original = Path(value.get('original_file', src[0]))
                if not pinned and original.parent.name == 'take-forensics-r24' and value.get('source_record'):
                    parent = src[0]
                    retained[(parent, int(src[1]))] = dict(source=value['source_record'], licence=value.get('licence', ''))
                refs.add((parent, int(src[1])))
            for item in value.values():
                structured(item)
        elif isinstance(value, list):
            for item in value:
                structured(item)
    direct = rec.get('parts') if isinstance(rec, dict) else None
    source_text = rec.get('source', '') if isinstance(rec, dict) else ''
    if not direct and isinstance(source_text, str) and '{' in source_text:
        try:
            parsed, _ = json.JSONDecoder().raw_decode(source_text[source_text.index('{'):])
            if (isinstance(parsed, dict) and isinstance(parsed.get('A'), dict) and
                    isinstance(parsed['A'].get('source'), list) and len(parsed['A']['source']) == 2):
                direct = parsed
        except ValueError:
            pass
    explicit = rec.get('parents') if isinstance(rec, dict) else None
    if explicit and isinstance(explicit, list):
        direct = {'parents': explicit}
        for parent in explicit:
            if isinstance(parent, (list, tuple)) and len(parent) == 2 and isinstance(parent[1], int):
                refs.add((str(parent[0]), parent[1]))
            elif isinstance(parent, str):
                count = re.match(r'(\d+)', Path(parent).stem)
                if count:
                    refs.add((parent, int(count[1])))
                else:
                    return False, dict(evidence, reason='explicit parent count unresolved')
            else:
                return False, dict(evidence, reason='explicit parent format unresolved')
    elif direct:
        structured(direct)
    elif not pinned_band:
        structured(rec)
        for ref, count in packing_refs(text):
            if ref != str(path):
                refs.add((ref, int(count)))
    if not direct and not pinned_band and str(candidate) in text:
        donor_n = n
        if isinstance(rec, dict):
            for field in ('host_n', 'donor_n', 'parent_n'):
                try:
                    if field in rec:
                        donor_n = int(rec[field])
                        break
                except (TypeError, ValueError):
                    continue
        refs.add((str(candidate), donor_n))
    # A band join lists every direct donor group, including held-file rows.
    if isinstance(rec, dict) and 'pinned donor ancestry: ' in source_text:
        tail = source_text.split('pinned donor ancestry: ', 1)[1]
        groups = None
        for candidate_text in (tail, tail.replace('\\"', '"')):
            try:
                groups, _ = json.JSONDecoder().raw_decode(candidate_text)
                break
            except ValueError:
                continue
        if not isinstance(groups, list):
            return False, dict(evidence, reason='unreadable pinned donor groups')
        for group in groups:
            if group.get('ancestry_file'):
                proof_file = Path(group['ancestry_file'])
                digest = hashlib.sha256(proof_file.read_bytes()).hexdigest()
                if digest != group['ancestry_sha256']:
                    return False, dict(evidence, reason='changed immutable donor group')
                evidence.setdefault('group_proofs', []).append(dict(
                    reason='verified immutable donor group', source_proof=str(proof_file), sha256=digest))
            count, origin = int(group['n']), group.get('origin', '')
            if origin == 'held round23b':
                refs.add((str(Path(scratch) / 'gather/round23-2026-11-13b.csv'), count))
            elif origin == 'held round25b':
                refs.add((str(Path(scratch) / 'gather/round25-2026-11-14b.csv'), count))
            elif origin in {'candidate round23', 'candidate round23a'}:
                refs.add((str(candidate), count))
            elif origin.startswith('/Volumes/'):
                refs.add((origin, count))
            elif group.get('ancestry_file'):
                proof_file = Path(group['ancestry_file'])
                if hashlib.sha256(proof_file.read_bytes()).hexdigest() != group['ancestry_sha256']:
                    return False, dict(evidence, reason='changed immutable donor group')
            elif not any(v in str(group.get('licence','')) for v in ('Apache', 'CC0', 'CC BY 4.0', 'MIT')):
                return False, dict(evidence, reason='unresolved pinned donor group')
    parents = []
    for ref, count in sorted(refs):
        if (ref, count) in retained:
            ok, parent = _trace(ref, count, scratch, active, recorded=retained[(ref, count)])
        else:
            ok, parent = trace(ref, count, scratch, active)
        parents.append(parent)
        if not ok:
            return False, dict(evidence, parents=parents, reason='refused parent')
    evidence['parents'] = parents
    root = (bool(refs) or 'round23-2026-11-13a.csv' in text or
            'round23-best-2026-11-13.tsv' in text or
            any(term in text for term in ('Apache', 'CC0', 'CC BY 4.0', 'MIT', 'Samanyu', 'samanyu', 'our own design')))
    return root, dict(evidence, reason='recorded ancestry' if root else 'unresolved ancestry')


def trace(path, n, scratch, active=None):
    """Four-argument public interface used by lane-specific source adapters."""
    return _trace(path, n, scratch, active)


def admit(files, scratch, work):
    allowed, evidence = [], []
    for path in files:
        path = Path(path)
        if path == Path(scratch) / 'gather/round23-2026-11-13a.csv':
            allowed.append(path)
            continue
        match = re.match(r'(\d+)', path.stem)
        if not match:
            continue
        try:
            ok, detail = trace(path, int(match[1]), scratch)
        except (OSError, ValueError, KeyError, RecursionError) as error:
            ok, detail = False, dict(path=str(path), n=int(match[1]), reason='incomplete ancestry: ' + str(error))
        proof_ref = detail.get('ledger', str(path) + '.origin.json')
        evidence.append(dict(path=str(path), n=int(match[1]), admitted=ok, reason=detail.get('reason'),
                             ancestry=compact_ancestry(detail, proof_ref)))
        if ok:
            allowed.append(path)
    dest = Path(work) / 'source-admission.json'
    dest.with_suffix('.tmp').write_text(json.dumps(evidence, indent=2))
    dest.with_suffix('.tmp').replace(dest)
    # Fresh k123 joins enter the scanner before every older source.
    return sorted(allowed, key=lambda p: (not ('take-k123-r24' in str(p)), str(p)))


def trace_part(part, scratch):
    path, n = part['source']
    original = Path(part.get('original_file', path))
    origin = Path(str(path) + '.origin.json')
    pinned = origin.exists() and json.loads(origin.read_text()).get('verified_ancestry')
    if pinned:
        return trace(path, int(n), scratch)
    if original.parent.name == 'take-forensics-r24' and part.get('source_record'):
        recorded = dict(source=part['source_record'], licence=part.get('licence', ''))
        return _trace(path, int(n), scratch, recorded=recorded)
    return trace(original, int(n), scratch)


def check_parts(parts, scratch):
    evidence = []
    for tag in ('A', 'B', 'C'):
        part = parts.get(tag)
        if not part:
            continue
        path, n = part['source']
        try:
            ok, detail = trace_part(part, scratch)
        except (OSError, ValueError, KeyError, RecursionError) as error:
            ok, detail = False, dict(path=str(path), n=int(n), reason='incomplete ancestry: ' + str(error))
        evidence.append(dict(detail, tag=tag, admitted=ok))
    return bool(evidence) and all(row['admitted'] for row in evidence), evidence
