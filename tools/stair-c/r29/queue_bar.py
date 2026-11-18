"""Reprice saved builds when a live take lowers their comparison side."""
import json
from pathlib import Path


def reprice(jobs, bars):
    changed = 0
    for job in jobs:
        value = min(job['bar'], bars.get(job['n'], job['bar']))
        if value < job['bar']:
            job['bar'] = value
            changed += 1
    jobs.sort(key=lambda job: job['predicted'] - job['bar'])
    return changed


def losing_builds(folder, bars):
    recipes = {}
    complete = set()
    for path in Path(folder).glob('*.json'):
        value = json.loads(path.read_text())
        n, side = value.get('n'), value.get('built')
        if n not in bars or side is None:
            continue
        key = (n, path.stem.removesuffix('-slp'))
        recipes[key] = min(recipes.get(key, float('inf')), side)
        if not value.get('early_stage'):
            complete.add(key)
    return {n: sum(key[0] == n and side > bars[n] - 1e-8
                   for key, side in recipes.items() if key in complete)
            for n in bars}


if __name__ == '__main__':
    import tempfile
    jobs = [dict(n=805, bar=28.8427, predicted=28.839),
            dict(n=812, bar=28.923, predicted=28.92301)]
    assert reprice(jobs, {805: 28.838675}) == 1
    assert jobs[0]['n'] == 812
    assert abs(jobs[1]['predicted'] - jobs[1]['bar'] - .000325) < 1e-12
    assert reprice(jobs, {805: 28.9}) == 0
    with tempfile.TemporaryDirectory() as folder:
        for name, value in {
            'a': dict(n=805, built=28.839),
            'a-slp': dict(n=805, built=28.8387, early_stage=True),
            'b': dict(n=805, built=28.8386),
            'c-slp': dict(n=805, built=28.839, early_stage=True),
        }.items():
            Path(folder, name + '.json').write_text(json.dumps(value))
        assert losing_builds(folder, {805: 28.838675}) == {805: 1}
    print('CONTROL live queue: n805 repriced to +0.000325, n812 takes priority; '
          'higher bars ignored; stages deduplicated; unfinished recipe excluded')
