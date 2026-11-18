"""Let a robot exit when its queue has no eligible claims."""
import hashlib
import json


def accepts_task(path, searching, following):
    if searching:
        return True
    try:
        task = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    kind = task.get('kind')
    if kind == 'follow37':
        return following
    return kind in {'cert', 'verify'} and not task.get('diversity_scan')


def queue_identity(root):
    return hashlib.sha256((root / 'queue.tsv').read_bytes()).hexdigest()


def mark_idle(root, slot, queue):
    (root / f'idle-{slot}38').write_text(queue)


def exhausted(root, slot, queue):
    marker = root / f'idle-{slot}38'
    return marker.is_file() and marker.read_text() == queue


def should_start(root, slot, queue, searching, following=False):
    if slot == 'third':
        return (
            any(accepts_task(path, searching, following) for path in (root / 'tasks').glob('*.json'))
            or (searching and not exhausted(root, 'j22c', queue))
        )
    return searching and not exhausted(root, slot, queue)
