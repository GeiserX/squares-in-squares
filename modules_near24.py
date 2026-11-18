"""Export traced fresh take and near designs for the module cut."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modules_near23 import side
from modules_sources24 import trace_file, clean_text


def export(out, directories):
    out.mkdir(exist_ok=True, parents=True)
    audits = []
    for directory in directories:
        if directory.name.startswith('take-modules-'):
            # Its raw module records already contain the full three sources.
            pass
        lane, rnd = directory.name[5:].rsplit('-r', 1)
        paths = list((directory / 'near').glob('*.csv'))
        for path in paths:
            try:
                n, length = side(path)
                if n < 300:
                    continue
                proof = trace_file(path, n)
                audits.append(proof)
                if not proof['ok']:
                    continue
                source = proof.get('source', '')
                licence = proof.get('licence', '')
                if not clean_text(source + ' ' + licence):
                    continue
                dest = out / ('n' + lane.replace('-', '') + '-r' + rnd + 'v' + hashlib.sha1(str(path).encode()).hexdigest()[:8])
                dest.mkdir(exist_ok=True)
                target = dest / f'{n}.csv'
                target.write_bytes(path.read_bytes())
                row = dict(n=n, source=f'{path}: {source}; ancestry record {proof.get("record", "")}',
                           licence=licence or f'own {lane}, sources in results/round23-best-2026-11-13.tsv')
                with (dest / 'take.tsv.tmp').open('w', newline='') as h:
                    w = csv.DictWriter(h, ['n', 'source', 'licence'], delimiter='\t')
                    w.writeheader()
                    w.writerow(row)
                os.replace(dest / 'take.tsv.tmp', dest / 'take.tsv')
            except (ValueError, TypeError, KeyError, IndexError, OSError):
                continue
    (out / 'ancestry-audit.json').write_text(json.dumps(audits))
    print('near proofs', len(audits), 'accepted', sum(x['ok'] for x in audits), flush=True)


if __name__ == '__main__':
    export(Path(sys.argv[1]), list(map(Path, sys.argv[2:])))
