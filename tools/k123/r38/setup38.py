"""Prepare isolated round 38 runtime files from the frozen round 37 take."""
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

SCRATCH = Path('$SCRATCH/bounties-squares')
PREVIOUS = SCRATCH / 'take-k123-r37/work'
TAKE = SCRATCH / 'take-k123-r38'
WORK = TAKE / 'work'
LANE = Path('.')
HELD = 'round37-2026-11-18a.csv'
ROW_FIELDS = ['n', 'held', 'new', 'gain', 'source', 'licence']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare():
    for directory in ['near', 'work/scripts', 'work/share', 'work/out', 'work/taskdone', 'work/tasks', 'work/certs', 'work/boxD']:
        (TAKE / directory).mkdir(parents=True, exist_ok=True)
    if (PREVIOUS / 'scripts').is_dir():
        shutil.copytree(PREVIOUS / 'scripts', WORK / 'scripts', dirs_exist_ok=True)
    for source in [*PREVIOUS.glob('*.py'), *PREVIOUS.glob('*.sh')]:
        body = source.read_text()
        for old, new in [
            ('squares-k123-r37', 'squares-k123-r38'),
            ('handoff-r37.log', 'handoff-r38.log'),
            ('round37-briefs/bar37.tsv', 'round38-briefs/bar38.tsv'),
            ('take-*-r37', 'take-*-r38'),
            ('06:45', '13:45'), ('05:45', '12:45'), ('06:50', '13:50'),
        ]:
            body = body.replace(old, new)
        if source.name in {'base25.py', 'held_share37.py'}:
            body = body.replace('round36-2026-11-18b.csv', HELD)
        if source.name == 'base25.py':
            body = body.replace('cand-round36-1118b', 'cand-round37-1118a')
            body = body.replace("(36,'18')]", "(36,'18'),(37,'18')]")
            body = body.replace('held round36', 'held round37').replace('of round 36', 'of round 37')
            body = body.replace('round36-best-2026-11-18.tsv', 'round37-best-2026-11-18.tsv')
            body = body.replace("[*S.glob('take-*-r38/take.tsv'),*S.glob('take-*-r38/take.tsv')]", "S.glob('take-*-r38/take.tsv')")
        if source.name == 'admission32.py':
            body = body.replace("['round36-2026-11-18b.csv'", f"['{HELD}','round36-2026-11-18b.csv'")
            body = body.replace("[(36,'round36-2026-11-18b.csv')", f"[(37,'{HELD}'),(36,'round36-2026-11-18b.csv')")
        if source.name == 'provenance24.py':
            body = body.replace('|36|37)/', '|36|37|38)/')
            body = body.replace("'18' if held_round33 == 36", "'18' if held_round33 in (36,37)")
            body = body.replace("per-n source table results/round{held_round33}", "per-n source table {R}/results/round{held_round33}")
        if source.name == 'walker30.py':
            body = body.replace("'QUENCH_LIVE_ROUND', '37'", "'QUENCH_LIVE_ROUND', '38'")
        if source.name == 'near36.py':
            body = body.replace('join37-', 'join38-')
        if source.suffix == '.py':
            compile(body, str(WORK / source.name), 'exec')
        (WORK / source.name).write_text(body)
    shutil.copytree(PREVIOUS / 'lane', WORK / 'lane', ignore=shutil.ignore_patterns('__pycache__'), dirs_exist_ok=True)
    for name in ['base-credit24.json', 'completed-geometries26.json', '444-control.csv', 'board.tsv', 'enable-wide30', 'runtime33.json', 'box33', 'share/zips.json', 'boxD/runtime33.json']:
        shutil.copy(PREVIOUS / name, WORK / name)
    (WORK / 'boxD/box33').write_text('boxD')
    (WORK / 'fq').write_bytes((SCRATCH / 'take-k123-r33/work/fq-boxCD33').read_bytes())
    (WORK / 'fq').chmod(0o755)
    for name, hour, minute in [
        ('deadline', 13, 45), ('search-deadline', 12, 45),
        ('own-follow-deadline', 13, 10), ('finalize-at32', 13, 50),
    ]:
        cutoff = datetime(2026, 11, 18, hour, minute, tzinfo=timezone.utc)
        (WORK / name).write_text(str(cutoff.timestamp()))
    with (SCRATCH / 'gate/cand-round37-1118a/details.csv').open() as stream:
        details = list(csv.DictReader(stream))
    with (SCRATCH / 'round38-briefs/bar38.tsv').open() as stream:
        bars = {int(row['n']): row['bar'] for row in csv.DictReader(stream, delimiter='\t')}
    with (WORK / 'details-base25.csv').open('w') as stream:
        writer = csv.DictWriter(stream, details[0].keys())
        writer.writeheader()
        for row in details:
            assert float(row['score']) == float(bars[int(row['n'])]), row['n']
            writer.writerow(row)
    with (LANE / 'results/round37-best-2026-11-18.tsv').open() as stream:
        priority = [int(row['n']) for row in csv.DictReader(stream, delimiter='\t')]
    write_json(WORK / 'setup38.json', {
        'priority': priority,
        'history_signatures': len(json.loads((WORK / 'completed-geometries26.json').read_text())),
    })
    for name, content in [('records.jsonl', ''), ('queue.tsv', ''), ('refused-inputs26.json', '{}')]:
        (WORK / name).write_text(content)
    initial = TAKE / 'take.tsv.tmp'
    initial.write_text('\t'.join(ROW_FIELDS) + '\n')
    initial.replace(TAKE / 'take.tsv')
    for overlay in (Path(__file__).resolve().parent / 'runtime').glob('*.py'):
        shutil.copy(overlay, WORK / overlay.name)
    # Staging scans only new held picks, exact live certificates and our changed third seams.
    controller = WORK / 'resident25.py'
    body = controller.read_text().replace("['collect22.py','follow37.py']", "['collect22.py','own_follow38.py']")
    body = body.replace("['stage24.py','deferred28.py','resume26.py']", "['feed38.py']")
    controller.write_text(body)
    print((WORK / 'setup38.json').read_text(), end='')


if __name__ == '__main__':
    prepare()
