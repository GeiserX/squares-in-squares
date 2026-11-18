from pathlib import Path
import csv
import importlib.util

_implementation = None


def share(path, count):
    global _implementation
    if _implementation is None:
        source = Path('tools/invent/round36/heldshare.py')
        specification = importlib.util.spec_from_file_location('k123_heldshare37', source)
        _implementation = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(_implementation)
        held = Path('$SCRATCH/bounties-squares/gather/round36-2026-11-18b.csv')
        with held.open() as stream:
            for row in csv.DictReader(stream):
                _implementation._h.setdefault(int(row['n']), []).append((float(row['x'].lstrip('s')), float(row['y'].lstrip('s'))))
    return _implementation.share(str(path), count)[1]
