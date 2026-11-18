"""Admit reader donors from the clean pool and retain ancestry evidence."""
import csv
import hashlib
import json
from pathlib import Path
import re
from functools import lru_cache


@lru_cache(None)
def archived_state(path):
    return json.loads(Path(path).read_text())
import sys
sys.path.insert(0, str(Path(__file__).parent))
import forensics_sources

csv.field_size_limit(16 * 1024 * 1024)
_BASE_TRACE = forensics_sources.trace


@lru_cache(None)
def archived_polish(scratch, n):
    scratch = Path(scratch)
    saved = scratch / f'take-polish-r22/work/candidates/{n}.csv'
    public = scratch / 'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
    row = next(r for r in csv.DictReader(open(public)) if int(r['n']) == n)
    expected = 'notebooks/malyshevdanil/squares-in-squares-living-atlas-of-tight-packings|ms'
    if row['src'] != expected or len(list(csv.DictReader(open(saved)))) != n:
        raise ValueError('archived public input control failed')
    return dict(path=str(saved), sha256=sha(saved), n=n, per_n_csv=str(public), per_n_row=row,
                source='areebbb/sis-certified-union-micro-shrink-lb-22-17479 -> malyshevdanil/squares-in-squares-living-atlas-of-tight-packings',
                licence='Apache 2.0 (Kaggle default for both public notebooks)', reason='retained polished public input and verified upstream row')


def pure_reader_parent(source):
    if not source.startswith('invent_rest.py'):
        return None
    match = re.search(r'from the readers near miss of n = (\d+) \((\d+-[^, )]+\.csv)', source[:1500])
    if not match or re.search(r'join|composition|rectangle|modules\.py', source[:match.start()]):
        return None
    if int(match[1]) != int(match[2].split('-')[0]):
        return None
    return match[2], int(match[1])


def trace_with_archive(path, n, scratch, active=None):
    path = Path(path)
    if not path.is_absolute() and str(path).startswith(('take-', 'gather/')):
        path = Path(scratch) / path
    # The round 22 source table names the old top-level file. Its exact
    # certified copy remains under work/candidates after the take dropped it.
    old = Path(scratch) / f'take-polish-r22/{n}.csv'
    if Path(path) == old and n not in {639, 691, 745, 858, 918, 801, 907} and not old.exists():
        try:
            return True, archived_polish(str(scratch), n)
        except (OSError, ValueError, KeyError, StopIteration) as ex:
            return False, dict(path=str(path), n=n, reason=str(ex))
    # A metadata field named raw identifies this layout's output, not a donor.
    # Follow its source references only after exact bytes prove that identity.
    if active and re.search(r'/work/boxE\d+/runs/[^/]+/raw/', str(path)) and Path(path).exists():
        for ancestor, count in active:
            if count != n or not Path(ancestor).exists():
                continue
            record, ledger = forensics_sources.record(ancestor, n)
            if not isinstance(record, dict) or record.get('raw') != str(path) or sha(path) != sha(ancestor):
                continue
            refs = set(re.findall(r'($SCRATCH/bounties-squares/[^\s";,()]+?/(\d+)[^\s";,()]*?\.csv)', str(record.get('source', ''))))
            parents = []
            for ref, count in sorted(refs):
                if ref == str(path) or ref == str(ancestor):
                    continue
                ok, parent = trace_with_archive(ref, int(count), scratch, active)
                if not ok:
                    return False, dict(path=str(path), n=n, reason='output-copy source refused', parent=parent)
                parents.append(parent)
            if parents:
                return True, dict(path=str(path), n=n, sha256=sha(path), same_bytes_as=ancestor,
                                  ledger=ledger, parents=parents, reason='recorded raw output copy with verified sources')
    if path.parent.name == 'take-invent-r24' and path.exists():
        record, ledger = forensics_sources.record(path, n)
        parent = pure_reader_parent(record.get('source', '')) if isinstance(record, dict) else None
        if parent:
            parent_path = Path(scratch) / 'take-readers-r24/near' / parent[0]
            if parent_path.exists():
                ok, proof = trace_with_archive(parent_path, parent[1], scratch, active)
                if ok:
                    return True, dict(path=str(path), n=n, parent=proof, record=record, ledger=ledger,
                                      reason='recorded pure kick and family step from reader end')
    return _BASE_TRACE(path, n, scratch, active)


# Its recursive calls use this adapter too. The imported file stays unchanged.
forensics_sources.trace = trace_with_archive


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def proof_clean(value):
    if isinstance(value, dict):
        if str(value.get('path', '')).endswith('/gather/round23-2026-11-13a.csv') and value.get('n') in (801, 907):
            return False
        return all(proof_clean(v) for v in value.values())
    if isinstance(value, list):
        return all(proof_clean(v) for v in value)
    return not (isinstance(value, str) and any(t in value for t in (
        'prvsiyan/squares-verified-best-of-1105', 'penguin069/squares-joegun-boxed-certified-union')))


def sha_from_donor(state, donor):
    return next((h for h, value in state['seen'].items() if value['donor'] == donor), '')


def audit(item, scratch, data):
    path, n, rnd, near, source, licence = item
    scratch = Path(scratch)
    text = source + ' ' + licence
    if ('penguin069/squares-joegun-boxed-certified-union' in text or
            'prvsiyan/squares-verified-best-of-1105' in text or
            re.search(r'(?:held|donor)[^.;]{0,20}\b(?:801|907)\b', text, re.I) or
            (n == 639 and re.search(r'take-[^/]+-r23/', str(path)))):
        return False, dict(path=str(path), n=n, reason='excluded upstream in recorded ancestry')
    # Immutable reader ends carry their parent's version in the file name.
    match = re.search(r'from(\d+-r\d+h[0-9a-f]+)', path.name)
    if match and path.parent.name == 'near' and 'take-readers-' in str(path):
        donor = match[1]
        states = [data]
        for rn in (23, 22):
            state = scratch / f'take-readers-r{rn}/work/follow.json'
            if state.exists():
                states.append(archived_state(str(state)))
        for state in states:
            parent = next((v for v in state['seen'].values() if v['donor'] == donor), None)
            if parent:
                pinned = state.get('source_evidence', {}).get(sha_from_donor(state, donor))
                if pinned and pinned.get('ok') and proof_clean(pinned):
                    return True, dict(path=str(path), n=n, pinned_parent=pinned, reason='retained immutable ancestry evidence')
                oldsource, oldlic = state['sources'][donor]
                parentitem = (Path(parent['path']), int(donor.split('-')[0]), rnd, False, oldsource, oldlic)
                ok, record = audit(parentitem, scratch, state)
                return ok, dict(path=str(path), n=n, parent=record, reason='reader version ancestry')
        return False, dict(path=str(path), n=n, reason='missing reader parent version')
    ok, record = forensics_sources.trace(path, n, scratch)
    # A historical immutable donor has a retained original path in the previous state.
    if not ok and '/box/donors/' in str(path):
        statepath = path.parent.parent.parent / 'follow.json'
        if statepath.exists():
            state = archived_state(str(statepath))
            original = next((v for v in state['seen'].values() if v['donor'] == path.stem), None)
            if original and Path(original['path']).exists() and sha(path) == sha(original['path']):
                ok, parent = forensics_sources.trace(original['path'], n, scratch)
                record = dict(path=str(path), n=n, immutable_parent=parent, reason='verified immutable donor bytes')
    return ok, record


def admit(found, scratch, work, data):
    work = Path(work)
    cachepath = work / 'source-admission.json'
    import readers_anc
    # Evidence trees are stored once by hash; the round 24 cache reached 217 MB.
    cache = readers_anc.load(cachepath, work / 'anc') if cachepath.exists() else {}
    allowed = []
    for item in found:
        path, n, rnd, near, source, licence = item
        if not path.exists():
            continue
        h = sha(path)
        key = 'audit-v2:' + str(path) + ':' + h + ':' + hashlib.sha256((source + licence).encode()).hexdigest()
        entry = cache.get(key)
        if not entry or not entry['ok']:
            try:
                ok, evidence = audit(item, scratch, data)
            except (ValueError, KeyError, OSError, RecursionError) as ex:
                ok, evidence = False, dict(reason=str(ex))
            entry = cache[key] = dict(ok=ok, evidence=evidence, n=n, sha256=h)
        if entry['ok'] and not proof_clean(entry):
            entry = cache[key] = dict(ok=False, n=n, sha256=h, evidence=dict(reason='prohibited ancestry in retained proof'))
        if entry['ok']:
            data.setdefault('source_evidence', {})[h] = entry
            if licence == 'see source':
                full_source, full_licence = credit_notices(entry)
                if full_source:
                    source += '; retained source records: ' + full_source
                if full_licence:
                    licence = full_licence
            # Credit the candidate's complete source table when a frozen row is clean.
            if rnd == 23 and not near:
                table = work / 'round23a-sources-58.tsv'
                if not table.exists():
                    table = Path(__file__).parent / 'results/round23-best-2026-11-13.tsv'
                parent = next((r for r in csv.DictReader(open(table), delimiter='\t') if int(r['n']) == n), None)
                if parent:
                    source += '; results/round23-best-2026-11-13.tsv: ' + parent['source']
                    licence = parent['licence']
            notices = []
            def public_notices(value):
                if isinstance(value, dict):
                    if value.get('reason') == 'retained polished public input and verified upstream row':
                        row = value['per_n_row']
                        notices.append('areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n=' + row['n'] + ', src=' + row['src'] + '; upstream malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: submission_merged.csv; both public notebooks Apache 2.0')
                    for child in value.values():
                        public_notices(child)
                elif isinstance(value, list):
                    for child in value:
                        public_notices(child)
            public_notices(entry)
            if notices:
                notice = ' | '.join(sorted(set(notices)))
                source += ' | Upstream per-n records: ' + notice
                licence += ' | ' + notice
            allowed.append((path, n, rnd, near, source, licence))
    readers_anc.save(cachepath, cache, work / 'anc')
    return allowed


def classify_seed_text(text):
    import forensics_policy
    text = re.sub(r'Samanyu(?:-dev)? seed ancestry:\s*(?:no|none)\b', '', text, flags=re.I)
    result = forensics_policy.classify_text(text)
    if re.search(r'Samanyu(?:-dev)?(?: seed)? ancestry:\s*(?:unresolved|unknown)', text, flags=re.I) or re.search(r'"samanyu_policy"\s*:\s*\{[^{}]{0,200}"status"\s*:\s*"unknown"', text, flags=re.I):
        result['status'] = 'unknown'
    return result


# Round 25 source rule: any Samanyu seed, an unresolved seed, or a path into the
# withdrawn lineages keeps a layout out. Nothing here makes an exception.
OUT_COUNTS = {639, 691, 745, 858, 918, 801, 980, 981}
OUT_PATTERNS = [
    r'prvsiyan/squares-verified-best-of-1105', r'penguin069/squares-joegun-boxed-certified-union',
    r'take-harvest-r22/(?:near/)?(?:639|691|745|858|918)[-.]',
    r'take-(?:invent|midm)-r23/(?:near/|work/[^"\s]*/)?639[-.]',
    r'take-forensics-r23/(?:near/|work/[^"\s]*/)?(?:980|918)[-.]',
    r'take-forensics-r2[0-2]/(?:near/)?918[-.]',
    # The border 735/790 tree reached seed 365 past its local labels (round 24).
    r'take-border-r24/(?:near/|work/[^"\s]*/)?(?:735|790)[-.]',
    # k123 withdrew its round 25 534: the 172 parent had no traceable licence.
    r'take-k123-r25/(?:near/|work/[^"\s]*/)?534[-.]', r'j22a-licensed20003-172r',
]


def out_reason(n, text):
    """Why a layout is out under the round 25 rule, or None when it is clean."""
    if n in OUT_COUNTS:
        return 'count %d is out in round 25' % n
    for pattern in OUT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return 'excluded lineage ' + match[0]
    seed = classify_seed_text(text)
    if seed['status'] != 'none':
        return 'Samanyu ' + seed['status'] + (' ' + ','.join(map(str, seed['seeds'])) if seed['seeds'] else '')
    return None


def credit_notices(entry):
    sources, licences = set(), set()
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('source'), str):
                sources.add(value['source'])
            if isinstance(value.get('licence'), str) and value['licence'] != 'see source':
                licences.add(value['licence'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(entry)
    return ' | '.join(sorted(sources)), ' | '.join(sorted(licences))


def write_near_source(path, data, work):
    path, work = Path(path), Path(work)
    match = re.search(r'from(\d+-r\d+h[0-9a-f]+)', path.name)
    if not match:
        return
    donor = match[1]
    parent = next(((h, v) for h, v in data['seen'].items() if v['donor'] == donor), None)
    if not parent:
        return
    h, info = parent
    source, licence = data['sources'][donor]
    import forensics_policy
    seed_info = classify_seed_text(source + ' ' + licence + json.dumps(data.get('source_evidence', {}).get(h, {})))
    if seed_info['status'] == 'none' and licence == 'see source':
        seed_info['status'] = 'unknown'
    licence += '; ' + forensics_policy.label(seed_info)
    record = dict(n=int(path.name.split('-')[0]), source='family_readers.py ' + path.stem.split('from')[0] + ' from ' + source,
                  licence=licence, parent_donor=donor, parent_sha256=h, parent_path=info['path'],
                  admission=data.get('source_evidence', {}).get(h))
    entry = data.get('source_evidence', {}).get(h)
    if not entry and Path(info['path']).exists() and sha(info['path']) == h:
        ok, evidence = audit((Path(info['path']), int(donor.split('-')[0]), 24, info.get('near', False), source, licence), work.parents[1], data)
        entry = dict(ok=ok, evidence=evidence, sha256=h)
    origin = dict(path=info['path'], n=int(donor.split('-')[0]), sha256=h, samanyu_policy=seed_info,
                  immutable_donor=str(work / 'box/donors' / (donor + '.csv')), method='family_readers layer walk')
    if entry and entry['ok'] and proof_clean(entry):
        origin.update(verified_ancestry=True, snapshot_sha256=sha(path), ancestry=entry['evidence'])
    for suffix, value in (('.json', record), ('.origin.json', origin)):
        destination = Path(str(path) + suffix)
        tmp = Path(str(destination) + '.tmp')
        tmp.write_text(json.dumps(value, indent=2) + '\n')
        tmp.replace(destination)


def selftest():
    # The trace checks the path before accepting a changed-count root.
    root = '$SCRATCH/bounties-squares'
    good, _ = forensics_sources.trace(root + '/gather/round23-2026-11-13a.csv', 639, root)
    bad, _ = forensics_sources.trace(root + '/take-harvest-r22/639.csv', 639, root)
    assert good and not bad
    good, _ = forensics_sources.trace(root + '/take-k123-r23/581.csv', 581, root)
    bad, _ = forensics_sources.trace(root + '/take-forensics-r23/980.csv', 980, root)
    assert good and not bad
    ok, evidence = trace_with_archive(root + '/take-polish-r22/538.csv', 538, root)
    assert ok and evidence['per_n_row']['src'].endswith('|ms')
    assert not trace_with_archive(root + '/take-polish-r22/639.csv', 639, root)[0]
    print('CONTROL PASSES: archived public538 upstream verified; unrelated missing639 still refused')
    parent = '900-r24h0123456789abcdef'
    state = dict(seen={'parenthash': dict(donor=parent, path='/missing/replaced-parent.csv')},
                 sources={parent: ['candidate clean pool', 'own search']},
                 source_evidence={'parenthash': dict(ok=True, evidence=dict(reason='candidate clean pool'))})
    end = Path(root + '/take-readers-r24/near/839-down2from' + parent + '.csv')
    ok, evidence = audit((end, 839, 24, True, 'return', 'own'), root, state)
    assert ok and evidence['reason'] == 'retained immutable ancestry evidence'
    state['source_evidence'].clear()
    assert not audit((end, 839, 24, True, 'return', 'own'), root, state)[0]
    print('CONTROL PASSES: retained immutable ancestry survives a replaced live path; missing evidence refuses it')
    print('CONTROL PASSES: candidate639 and clean581 admitted; excluded harvest639 and forensics980 refused')


if __name__ == '__main__':
    selftest()
