#!/usr/bin/env python3
"""Import handed modules with their existing tables into a classfill library.

Report missing tables and continue with the usable modules. Inputs are trusted
lane libraries. This tool does not tabulate or execute harvested files.
"""
import argparse
import os
from pathlib import Path
import pickle


def import_handoff(base, source, output, needed):
    base, source, output = map(Path, (base, source, output))
    with open(base / 'library.pkl', 'rb') as h:
        library = pickle.load(h)
    with open(base / 'lens.pkl', 'rb') as h:
        tables = pickle.load(h)
    with open(source / 'library.pkl', 'rb') as h:
        donor = pickle.load(h)
    with open(source / 'lens.pkl', 'rb') as h:
        donor_tables = pickle.load(h)
    wanted = set(needed)
    selected, missing = [], []
    modules = {q['id']: q for q in library['mods']}
    for q in donor['mods']:
        key = q['id']
        if key not in wanted or key in tables:
            continue
        if key not in donor_tables:
            missing.append(key)
            continue
        modules[key] = dict(q, ours=True)
        tables[key] = donor_tables[key]
        selected.append(key)
    library['mods'] = list(modules.values())
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [('library.pkl', library), ('lens.pkl', tables)]:
        temporary = output / (name + '.tmp')
        with open(temporary, 'wb') as h:
            pickle.dump(value, h)
        os.replace(temporary, output / name)
    return selected, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('base')
    ap.add_argument('source')
    ap.add_argument('output')
    ap.add_argument('--need', required=True)
    ap.add_argument('--ids', required=True)
    a = ap.parse_args()
    selected, missing = import_handoff(a.base, a.source, a.output, Path(a.need).read_text().split())
    Path(a.ids).write_text(''.join(key + '\n' for key in selected))
    print('MISSING_HANDOFF_TABLES', len(missing), ','.join(missing), flush=True)
    print('IMPORTED_NEW_MODULES', len(selected), 'all in handed need list; exact owner tables', flush=True)


if __name__ == '__main__':
    main()
