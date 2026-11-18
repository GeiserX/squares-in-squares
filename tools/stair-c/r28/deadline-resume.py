"""Resume the finalizer from archives whose full verification already completed."""
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import tarfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('deadline28_resume', HERE / 'deadline.py')
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)


def finish_from_copies():
    F = sys.modules['finish_local28']
    D.stop_coordinator()
    verified = []
    for host, key, python in D.HOSTS:
        folder = D.WORK / 'archive' / key
        old = json.loads((folder / 'verify.json').read_text())
        receipt = json.loads((folder / 'receipt.json').read_text())
        assert F.sha(folder / 'final-copy.tar.gz') == old['archive_sha256']
        assert F.sha(folder / 'receipt.json') == old['receipt_sha256']
        base = D.WORK / 'boxcopy' / key
        restored = 0
        with tarfile.open(folder / 'final-copy.tar.gz') as archive:
            for item in archive:
                if item.name != 'worker.log' and item.name.split('/')[0] not in {'raw-a', 'final', 'logs', 'tables'}:
                    continue
                assert item.isfile() and not item.name.startswith('/') and '..' not in item.name.split('/')
                target = base / item.name
                expected = receipt['files'][item.name]
                if target.exists() and F.sha(target) == expected:
                    continue
                data = archive.extractfile(item).read()
                assert hashlib.sha256(data).hexdigest() == expected
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                restored += 1
        verified.append((host, key, python, old['receipt_sha256']))
        D.state(f'REVIVE VERIFIED {host} unchanged archive and receipt hashes; restored {restored} missing or partial collected files')
        print(D.stamp(), 'RESTORED', host, restored, flush=True)
    F.C.publish()
    F.C.save()
    measurement = F.measure()
    take = F.final_take()
    for host, key, python, digest in verified:
        result = D.run(['ssh', '-o', 'ConnectTimeout=15', host,
                        'cd $SCRATCH/squares-stair-c && ' + python +
                        ' finish-box.py --remove ' + digest], 60)
        if result.returncode:
            raise RuntimeError(host + ' scratch removal failed')
    (D.WORK / 'cleanup-final.json').write_text(json.dumps(dict(
        verified=[dict(host=host, receipt=digest) for host, key, python, digest in verified],
        processes_left=[]), indent=2))
    D.state('FINISH remote payloads verified and own scratch removed on all three boxes. Shared runtimes kept.')
    return measurement, take


if __name__ == '__main__':
    D.finish = finish_from_copies
    D.main()
