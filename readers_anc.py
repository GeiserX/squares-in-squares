"""Store shared ancestry once by content hash.

Reader evidence nests the full evidence of each parent version. Saved as plain
JSON, every child repeats its whole parent tree, and the round 24 state files
reached 175 MB and 217 MB. Here each large subtree is written once to
<store>/<sha256>.json and replaced by {"$anc": sha256}. Loading restores the
same Python object for every reference, so memory holds one copy as well.
"""
import hashlib
import json
from pathlib import Path

LIMIT = 2048


def _canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def intern(value, store, memo=None):
    """Return value with every subtree over LIMIT bytes replaced by a reference."""
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    memo = {} if memo is None else memo

    def walk(v):
        """Return (interned value, size of the fully expanded JSON)."""
        if isinstance(v, (dict, list, str)) and id(v) in memo:
            return memo[id(v)][1:]
        if isinstance(v, dict):
            parts = {k: walk(c) for k, c in v.items()}
            out = {k: c[0] for k, c in parts.items()}
            size = 2 + sum(len(k) + 4 + c[1] for k, c in parts.items())
        elif isinstance(v, list):
            parts = [walk(c) for c in v]
            out = [c[0] for c in parts]
            size = 2 + sum(c[1] + 1 for c in parts)
        else:
            out, size = v, len(_canon(v))
        # The expanded size decides, so a parent of interned children is
        # itself stored once and shared, not repeated in every child record.
        if isinstance(v, (dict, list, str)) and size > LIMIT:
            text = _canon(out)
            h = hashlib.sha256(text.encode()).hexdigest()
            path = store / (h + '.json')
            if not path.exists():
                tmp = path.with_suffix('.tmp')
                tmp.write_text(text)
                tmp.replace(path)
            out = {'$anc': h}
        if isinstance(v, (dict, list, str)):
            # Keep v alive so its id is not reused while memo holds it.
            memo[id(v)] = (v, out, size)
        return out, size
    # The root stays a plain object, so the state file still lists its keys.
    if isinstance(value, dict):
        return {k: walk(c)[0] for k, c in value.items()}
    return walk(value)[0]


def expand(value, store, cache=None):
    """Inverse of intern. Equal references resolve to one shared object."""
    store = Path(store)
    cache = {} if cache is None else cache

    def walk(v):
        if isinstance(v, dict):
            if set(v) == {'$anc'}:
                h = v['$anc']
                if h not in cache:
                    cache[h] = walk(json.loads((store / (h + '.json')).read_text()))
                return cache[h]
            return {k: walk(c) for k, c in v.items()}
        if isinstance(v, list):
            return [walk(c) for c in v]
        return v
    return walk(value)


def save(path, value, store):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(intern(value, store), separators=(',', ':')))
    tmp.replace(path)


def load(path, store):
    return expand(json.loads(Path(path).read_text()), store)


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        parent = {'path': '/x/990.csv', 'steps': ['step %d of the 990 parent' % i for i in range(200)], 'seed': 'Samanyu ancestry: none'}
        state = {'a': {'pinned_parent': parent}, 'b': {'pinned_parent': parent}, 'small': [1, 2]}
        save(Path(tmp) / 's.json', state, Path(tmp) / 'anc')
        size = (Path(tmp) / 's.json').stat().st_size
        back = load(Path(tmp) / 's.json', Path(tmp) / 'anc')
        assert back == state, 'round trip changed the state'
        assert back['a']['pinned_parent'] is back['b']['pinned_parent'], 'shared parent loaded twice'
        assert size < 400, size
        files = list((Path(tmp) / 'anc').glob('*.json'))
        assert len(files) == 3, files  # step list, parent, and the equal records a and b: once each
        print('CONTROL PASSES: shared parent stored once (%d anc files, state %d bytes); round trip equal' % (len(files), size))


if __name__ == '__main__':
    selftest()
