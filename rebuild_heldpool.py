#!/usr/bin/env python3
"""rebuild_heldpool.py OUT.csv HELD.csv N[,N...] [--extra N:FILE:RECORD ...]: a join pool of held layouts whose
recorded ancestry is clean.

For each N it takes the layout from HELD.csv (the held file) and the source and licence of that n from the
newest results/round*-best table that lists it (a held row keeps its table row until a later round moves it).
It walks that text with quench_audit.walk (every per-file record and per-n take row it names) and checks it
with quench_audit's rules and forensics_policy.classify_text, both imported unchanged. It also refuses a text
that names a bare per-n file (a name like 921-29e12ff3.csv with no directory): round 25 lost a row to such a
name, which a path walk does not follow. --extra adds a layout from FILE with its record file RECORD (a take.tsv
or a .json), audited the same way. Writes OUT.csv (n, square_id, x, y, angle) and OUT.csv.map (n, file, table,
verdict). Our own code."""
import csv, glob, json, os, re, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import methods_lp as m  # noqa: E402
import quench_audit as qa  # noqa: E402
import forensics_policy as fp  # noqa: E402

csv.field_size_limit(1 << 28)
BARE = re.compile(r'(?<![/\w.-])\d{1,4}-[0-9a-f]{6,}\.csv')


def tables():
    def key(p):
        r = re.search(r'round(\d+)-best-(\d{4}-\d{2}-\d{2})', p)
        return (r.group(2), int(r.group(1)))
    out = []
    for p in sorted(glob.glob(os.path.join(LANE, 'results', 'round*-best-*.tsv')), key=key, reverse=True):
        rows = {}
        for r in csv.DictReader(open(p), delimiter='\t'):
            try:
                rows[int(r['n'])] = r
            except (KeyError, ValueError):
                pass
        out.append((p, rows))
    return out


def verdict(text, seeds=()):
    full, k = qa.walk(seeds) if seeds else ('', 0)
    full = text + '\n' + full
    hits = []
    pol = fp.classify_text(full)
    if pol['status'] != 'none':
        hits.append('Samanyu %s %s' % (pol['status'], pol['seeds']))
    for name, rx in qa.RULES:
        if re.search(rx, full, flags=re.I):
            hits.append(name)
    b = sorted(set(BARE.findall(full)))
    if b:
        hits.append('bare names %s' % b[:4])
    return hits, k


def main():
    out, held, ns = sys.argv[1], sys.argv[2], [int(v) for v in sys.argv[3].split(',') if v]
    extra = []
    if '--extra' in sys.argv:
        extra = sys.argv[sys.argv.index('--extra') + 1:]
    T = tables()
    H = m.load(held, set(ns))
    keep, mp = {}, []
    for n in ns:
        row = next(((p, r[n]) for p, r in T if n in r), None)
        if row is None:
            mp.append((n, held, '-', 'no table row')); continue
        text = row[1]['source'] + ' ' + row[1]['licence']
        tmp = '/tmp/rb-heldpool-%d.txt' % os.getpid()
        open(tmp, 'w').write(text)
        hits, k = verdict(text, [tmp])
        mp.append((n, held, os.path.basename(row[0]), 'clean' if not hits else 'OUT ' + '; '.join(hits)))
        if not hits:
            keep[n] = H[n]
    for spec in extra:
        n, f, rec = spec.split(':', 2); n = int(n)
        if rec.endswith('.tsv'):
            r = qa.take_row(os.path.dirname(rec), n)
            hits, k = verdict(r, [(os.path.dirname(rec), n)])
        else:
            hits, k = verdict(open(rec).read(), [rec])
        mp.append((n, f, rec, 'clean' if not hits else 'OUT ' + '; '.join(hits)))
        if not hits:
            keep[n] = m.load(f, {n})[n]
    with open(out, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for n in sorted(keep):
            w.writerows((n, i, *r) for i, r in enumerate(keep[n]))
    with open(out + '.map', 'w') as g:
        for r in mp:
            g.write('\t'.join(map(str, r)) + '\n')
            print(*r, sep='\t')


if __name__ == '__main__':
    main()
