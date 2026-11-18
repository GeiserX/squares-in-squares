from pathlib import Path
import csv
import datetime
import json
import re
import shutil

SCRATCH = Path('$SCRATCH/bounties-squares')
PREVIOUS = SCRATCH / 'take-k123-r36/work'
TAKE = SCRATCH / 'take-k123-r37'
WORK = TAKE / 'work'
REPOSITORY = Path('.')


def replace_exact(text, old, new):
    if old not in text:
        raise ValueError(f'Missing expected source: {old}')
    return text.replace(old, new)


def prepare():
    for directory in ['near', 'work/share', 'work/out', 'work/tasks', 'work/taskdone', 'work/certs', 'work/boxD']:
        (TAKE / directory).mkdir(parents=True, exist_ok=True)
    for source in PREVIOUS.glob('*.py'):
        text = source.read_text()
        for old, new in [
            ('squares-k123-r36', 'squares-k123-r37'),
            ('handoff-r36.log', 'handoff-r37.log'),
            ('round36-briefs/bar36.tsv', 'round37-briefs/bar37.tsv'),
            ('take-*-r36', 'take-*-r37'),
            ('23:45', '06:45'),
            ('23:25', '05:45'),
            ('23:40', '06:50'),
        ]:
            text = text.replace(old, new)
        if source.name == 'base25.py':
            text = text.replace('round35-2026-11-17a.csv', 'round36-2026-11-18b.csv')
            text = text.replace('cand-round35-1117a', 'cand-round36-1118b')
            text = text.replace("(35,'17')]", "(35,'17'),(36,'18')]")
            text = text.replace('held round35', 'held round36').replace('of round 35', 'of round 36')
            text = text.replace('round35-best-2026-11-17.tsv', 'round36-best-2026-11-18.tsv')
        if source.name == 'stage24.py':
            text = text.replace('take-*-r35', 'take-*-r36')
            text = text.replace("'-r36/'", "'-r37/'").replace("'-r35/'", "'-r36/'")
            text = text.replace("endswith('-r36')", "endswith('-r37')")
        if source.name == 'admission32.py':
            text = text.replace("['round35-2026-11-17a.csv'", "['round36-2026-11-18b.csv','round35-2026-11-17a.csv'")
            text = text.replace("[(35,'round35-2026-11-17a.csv')", "[(36,'round36-2026-11-18b.csv'),(35,'round35-2026-11-17a.csv')")
        if source.name == 'provenance24.py':
            text = text.replace('|34|35|36)/', '|34|35|36|37)/')
            text = text.replace("{'17' if held_round33", "{'18' if held_round33 == 36 else '17' if held_round33")
        if source.name == 'walker30.py':
            text = text.replace("'QUENCH_LIVE_ROUND', '36'", "'QUENCH_LIVE_ROUND', '37'")
        if source.name == 'bridge34.py':
            text = text.replace("boxes={'boxD':['j22e','j22f','j22g']}", "boxes={'boxD':['j22e']}")
        if source.name == 'near36.py':
            text = text.replace('join36-', 'join37-')
        if source.name == 'resume26.py':
            text = text.replace('take-k123-r35/', 'take-k123-r36/').replace("'resume36'", "'resume37'")
        if source.name == 'deferred28.py':
            text = text.replace('take-k123-r35/', 'take-k123-r36/').replace("'deferred36'", "'deferred37'")
        compile(text, str(WORK / source.name), 'exec')
        (WORK / source.name).write_text(text)
    shutil.copytree(PREVIOUS / 'lane', WORK / 'lane', ignore=shutil.ignore_patterns('__pycache__'), dirs_exist_ok=True)
    for name in ['base-credit24.json', 'completed-geometries26.json', '444-control.csv', 'board.tsv', 'fivebins30-control-passed', 'enable-wide30', 'runtime33.json', 'box33']:
        if (PREVIOUS / name).exists():
            shutil.copy(PREVIOUS / name, WORK / name)
    shutil.copy(PREVIOUS / 'share/zips.json', WORK / 'share/zips.json')
    for name, content in [('take.tsv', 'n\theld\tnew\tgain\tsource\tlicence\n')]:
        (TAKE / (name + '.tmp')).write_text(content)
        (TAKE / (name + '.tmp')).replace(TAKE / name)
    for name, content in [('records.jsonl', ''), ('queue.tsv', ''), ('refused-inputs26.json', '{}'), ('measurements28.json', '[]')]:
        (WORK / name).write_text(content)
    for name, hour, minute in [('deadline', 6, 45), ('search-deadline', 5, 45), ('finalize-at32', 6, 50)]:
        cutoff = datetime.datetime(2026, 11, 18, hour, minute, tzinfo=datetime.timezone.utc)
        (WORK / name).write_text(str(cutoff.timestamp()))
    with (SCRATCH / 'gate/cand-round36-1118b/details.csv').open() as stream:
        details = list(csv.DictReader(stream))
    bars = {int(row['n']): row['bar'] for row in csv.DictReader((SCRATCH / 'round37-briefs/bar37.tsv').open(), delimiter='\t')}
    for row in details:
        row['score'] = bars[int(row['n'])]
    with (WORK / 'details-base25.csv').open('w') as stream:
        writer = csv.DictWriter(stream, details[0].keys())
        writer.writeheader()
        writer.writerows(details)
    changed = list(csv.DictReader((REPOSITORY / 'results/round36-best-2026-11-18.tsv').open(), delimiter='\t'))
    priority = [793, 597, 698, 812, 972, 539, 692, 976, 911]
    priority += [int(row['n']) for row in changed if int(row['n']) not in priority]
    seed = (PREVIOUS / 'seed36.py').read_text()
    start = seed.index('for n in [')
    finish = seed.index(':', start)
    seed = seed[:start] + 'for n in ' + repr(priority) + seed[finish:]
    seed = seed.replace('licensed36', 'licensed37').replace('round 35', 'round 36').replace('round36 lowest', 'round37 lowest')
    (WORK / 'seed37.py').write_text(seed)
    (WORK / 'force-fresh28.json').write_text('[]')
    (WORK / 'priority-inputs31.json').write_text('[]')
    (WORK / 'next28.json').write_text(json.dumps(json.loads((SCRATCH / 'round37-briefs/r36-results.json').read_text())['k123']['next']))
    history = {tuple(entry) for entry in json.loads((WORK / 'completed-geometries26.json').read_text())}
    initial = len(history)
    missing = []
    for line in (PREVIOUS / 'records.jsonl').read_text().splitlines():
        record = json.loads(line)
        match = re.match(r'(\d+)r?-(\d+)r?-j', record['tag'])
        if not match:
            continue
        candidates = [PREVIOUS / record['pool'] / ('sources-' + record['pool'] + '.json'), PREVIOUS / 'boxE-final' / ('sources-' + record['pool'] + '.json')]
        manifest = next((candidate for candidate in candidates if candidate.is_file()), None)
        if manifest is None:
            missing.append(record['pool'])
            continue
        metadata = json.loads(manifest.read_text())
        signature = (record['tag'], *(metadata[number]['sha256_geometry'] for number in match.groups()))
        if record.get('mechanism'):
            signature += (record['mechanism'],)
        history.add(signature)
    (WORK / 'completed-geometries26.json').write_text(json.dumps(sorted(history)))
    receipt = {'old': initial, 'new': len(history) - initial, 'total': len(history), 'missing': sorted(set(missing)), 'priority': priority}
    (WORK / 'setup37.json').write_text(json.dumps(receipt, indent=2))
    config = json.loads((WORK / 'runtime33.json').read_text())
    config['slots'] = {'j22a': ['qrun22.py', 'j22a'], 'j22d': ['qrun22.py', 'j22d'], 'third': ['third22.py']}
    (WORK / 'runtime33.json').write_text(json.dumps(config))
    extra = json.loads((PREVIOUS / 'boxD/runtime33.json').read_text())
    extra['python'] = '/Users/boxD/scratch/squares-readers/venv/bin/python'
    extra['slots'] = {'j22e': ['qrun22.py', 'j22e']}
    extra['load_limit'] = 10
    (WORK / 'boxD/runtime33.json').write_text(json.dumps(extra))
    (WORK / 'boxD/box33').write_text('boxD')
    for overlay in (Path(__file__).resolve().parent / 'runtime').glob('*.py'):
        shutil.copy(overlay, WORK / overlay.name)
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ') + ' boxA SETUP37 ' + json.dumps(receipt) + '. Fresh changed geometries first because they supplied the largest r36 follow gains. boxE3 boxD:1. Search stops05:45Z, shared hard search/quench deadline06:45Z.\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    prepare()
