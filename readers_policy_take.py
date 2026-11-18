#!/usr/bin/env python3
"""Certify reader ends under the round 25 source rule: only layouts with no Samanyu seed and no withdrawn lineage."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).parent))
import family_readers as fr
import forensics_policy as policy
import forensics_watch
import readers_sources


def readrows(path, sep='\t'):
    return list(csv.DictReader(open(path), delimiter=sep))


def classify(donor, data, scratch, source, licence, cache):
    h = next((h for h, v in data['seen'].items() if v['donor'] == donor), '')
    token = hashlib.sha256(('policy-v6:' + donor + h + source + licence).encode()).hexdigest()
    if token in cache:
        return cache[token]
    roots = {}
    def visit(value):
        if isinstance(value, dict):
            path, n = value.get('path'), value.get('n')
            if path and isinstance(n, int):
                p = Path(path)
                if p.parent.name == 'gather' or (p.parent.name.endswith('-r23') and p.stem.isdigit()):
                    roots[(path, n)] = dict(source=[path, n])
            for key, child in value.items():
                if key != 'record':
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    entry = data.get('source_evidence', {}).get(h)
    if not entry:
        info = data['seen'].get(h)
        if info:
            try:
                ok, evidence = readers_sources.audit((Path(info['path']), int(donor.split('-')[0]), 24, info.get('near', False), source, licence), scratch, data)
                entry = dict(ok=ok, evidence=evidence)
            except (OSError, ValueError, KeyError, RecursionError):
                entry = {}
    if not entry or not entry.get('ok') or not readers_sources.proof_clean(entry):
        result = dict(status='unknown', seeds=[], roots=[], reason='missing or prohibited retained source proof')
        cache[token] = result
        return result
    visit(entry)
    notices = forensics_watch.gather_notices({str(i): r for i, r in enumerate(roots.values())})
    # Include the saved source text even when a path was superseded later.
    text = source + ' ' + licence + json.dumps(notices) + json.dumps(entry or {})
    result = readers_sources.classify_seed_text(text)
    if result['status'] == 'none' and ('seed merged0' in text or not (source.strip() and licence.strip()) or not entry or not entry.get('ok')):
        result['status'] = 'unknown'
    result['roots'] = sorted(n for _, n in roots)
    # The parent tree of the donor, checked against the withdrawn lineages too.
    result['out'] = readers_sources.out_reason(int(donor.split('-')[0]), text)
    cache[token] = result
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('details'); ap.add_argument('take'); ap.add_argument('outs', nargs='+')
    ap.add_argument('--sources', required=True); ap.add_argument('--beat', nargs='*', default=[])
    a = ap.parse_args()
    work = Path(a.sources).parent; scratch = work.parents[1]
    import readers_anc
    data = readers_anc.load(work / 'follow.json', work / 'anc')
    sources = {r['donor']: (r['source'], r['licence']) for r in readrows(a.sources)}
    cachepath = work / 'samanyu-policy-cache.json'
    cache = json.loads(cachepath.read_text()) if cachepath.exists() else {}
    temp = Path(a.take) / 'work/policy-stage'
    shutil.rmtree(temp, ignore_errors=True)
    for name in ('strict',):
        (temp / name / 'raw').mkdir(parents=True)
    tags = {}
    for directory in a.outs:
        for path in sorted((Path(directory) / 'raw').glob('*.csv')):
            tag = path.stem
            if 'from' not in tag:
                continue
            donor = tag.split('from', 1)[1]
            if donor not in sources:
                print('drop unknown source', tag)
                continue
            source, licence = sources[donor]
            seed = classify(donor, data, scratch, source, licence, cache)
            n = int(tag.split('-')[0])
            why = seed.get('out') or readers_sources.out_reason(n, source + ' ' + licence)
            if seed['status'] != 'none' or why:
                print('drop source out', tag, why or 'Samanyu ' + seed['status'])
                continue
            group = 'strict'
            destination = temp / group / 'raw' / path.name
            if destination.exists():
                destination.unlink()
            os.link(path, destination)
            tags[tag] = seed
    winners = {}
    # Every live r25 take is a competitor, whatever its own source cells say.
    for group in ('strict',):
        destination = temp / (group + '-take')
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            fr.cmd_take(SimpleNamespace(details=a.details, take=str(destination), outs=[str(temp / group)], sources=a.sources, beat=a.beat, table=None))
        keeps = {int(line.split()[1]): line for line in capture.getvalue().splitlines() if line.startswith('keep ')}
        for line in capture.getvalue().splitlines():
            if not line.startswith(('keep ', 'kept ')):
                print(line)
        for row in readrows(destination / 'take.tsv'):
            n = int(row['n']); line = keeps[n]; tag = line.split()[5]
            row['licence'] += '; ' + policy.label(tags[tag])
            winners[n] = (row, destination / f'{n}.csv', line)
    take = Path(a.take); take.mkdir(exist_ok=True)
    for n, (row, path, line) in winners.items():
        temporary = take / 'work' / f'{n}.csv.tmp'; shutil.copyfile(path, temporary); temporary.replace(take / f'{n}.csv')
        print(line)
    with open(take / 'work/take.tsv.tmp', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['n','held','new','gain','source','licence'], delimiter='\t', lineterminator='\n'); writer.writeheader(); writer.writerows(winners[n][0] for n in sorted(winners))
    (take / 'work/take.tsv.tmp').replace(take / 'take.tsv')
    cachepath.with_suffix('.tmp').write_text(json.dumps(cache, indent=2)); cachepath.with_suffix('.tmp').replace(cachepath)
    print('kept', len(winners), 'gain', sum(float(r[0]['held'])-float(r[0]['new']) for r in winners.values()))


if __name__ == '__main__':
    main()
