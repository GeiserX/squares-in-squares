#!/usr/bin/env python3
"""rebuild_anc.py ANCDIR N RECIPE PARENT_N:CSV:TAKE.tsv|SIDECAR.json [...] (list every ancestor, not only the parents) -> prints the JSON of one take row's source and licence.

Stores the parents once by hash: ANCDIR/<sha256 of the parent records>.json holds, for each parent, its csv path
and geometry SHA-256 and the full source and licence cells of its take.tsv row (or the base file row). The
source cell names the recipe, the parents with their hashes and that record. The licence cell joins the parent
licence cells and states the Samanyu-dev seed status that forensics_policy.classify_text reads from the parents:
a parent that is not status none stops the script. Our own code; it imports forensics_policy unchanged."""
import csv, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forensics_policy as fp  # noqa: E402
csv.field_size_limit(1 << 28)


def row(take, n):
    if take.endswith('.json'):
        d = json.load(open(take))
        return str(d.get('source', '')), str(d.get('licence', ''))
    for r in csv.DictReader(open(take), delimiter='\t'):
        if int(r['n']) == n:
            return r['source'], r['licence']
    raise SystemExit('no row %d in %s' % (n, take))


def main():
    anc, n, recipe = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    parents = []
    for spec in sys.argv[4:]:
        pn, path, take = spec.split(':', 2)
        src, lic = row(take, int(pn))
        c = fp.classify_text(src + ' ' + lic)
        if c['status'] != 'none':
            raise SystemExit('parent %s %s has Samanyu status %s %s' % (pn, path, c['status'], c['seeds']))
        parents.append(dict(n=int(pn), csv=path, sha256=hashlib.sha256(open(path, 'rb').read()).hexdigest(),
                            take=take, source=src, licence=lic))
    blob = json.dumps(parents, sort_keys=True).encode()
    h = hashlib.sha256(blob).hexdigest()
    os.makedirs(anc, exist_ok=True)
    p = os.path.join(anc, h + '.json')
    if not os.path.exists(p):
        open(p, 'wb').write(blob)
    names = '; '.join('n=%d from %s (geometry sha256 %s, row in %s)' % (q['n'], q['csv'], q['sha256'][:16], q['take']) for q in parents)
    source = '%s; %s; full parent records %s' % (recipe, names, p)
    licence = 'ours, on: ' + ' | '.join(q['licence'] for q in parents) + '; Samanyu-dev seed ancestry: no (rebuild lane walked the parent records)'
    print(json.dumps(dict(source=source, licence=licence)))


if __name__ == '__main__':
    main()
