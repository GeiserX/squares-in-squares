"""Check that an exhausted slot stops and a new scan wakes it."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json

from runtime.idle38 import mark_idle, queue_identity, should_start


def control():
    with TemporaryDirectory() as name:
        root = Path(name)
        tasks = root / 'tasks'
        tasks.mkdir()
        queue = root / 'queue.tsv'
        queue.write_text('')
        first = queue_identity(root)
        assert should_start(root, 'third', first, True)
        assert should_start(root, 'j22d', first, True)
        for slot in ['j22c', 'j22d']:
            mark_idle(root, slot, first)
        assert not should_start(root, 'third', first, True)
        assert not should_start(root, 'j22d', first, True)
        queue.write_text('new recipe\n')
        changed = queue_identity(root)
        assert should_start(root, 'third', changed, True)
        assert should_start(root, 'j22d', changed, True)
        assert not should_start(root, 'third', changed, False)
        (tasks / 'new-cert.json').write_text('{"kind":"verify","diversity_scan":true}')
        assert not should_start(root, 'third', changed, False)
        (tasks / 'own-follow.json').write_text('{"kind":"follow37"}')
        assert should_start(root, 'third', changed, False, following=True)
        (tasks / 'new-cert.json').write_text('{"kind":"cert"}')
        assert should_start(root, 'third', changed, False)
        assert not should_start(root, 'j22d', changed, False)
    return {'wait_with_empty_queue': True, 'restart_on_changed_queue': True, 'certification_after_search_cutoff': True}


if __name__ == '__main__':
    print(json.dumps(control()))
