#!/usr/bin/env python3
"""midm round 31: pub-near starts from every harvested public file of rounds 28 to 31 (tools/midm/pubnear31.py on many files).

Measured first: the round 31 jazivxt pub-near starts gave 812 (start 4.59e-5 above bar31, certified 3.606e-5 below it
after one 900 s kick), and 503 gained 2.39e-5 on its start. The harvest dirs of rounds 28 to 31 hold 244 public files
of distinct size (work/pubnear/nearcount.txt), most of them copies of the same rows. This tool
  - reads the near rows (1e-6 to 1e-4 above bar31) of the files listed in nearcount.txt;
  - drops a file whose owner is prvsiyan, a file whose sha256 a WITHDRAW line names, and the n of override 3;
  - keeps one copy of each exact row (the first file in name order), then per n drops rows that share 0.9 or more at
    1e-3 with our held row (our own layout, polished less) or with a lower candidate of the same n;
  - takes the licence from the file's meta.json for a dataset (CC0, CC BY 4.0 or Apache 2.0 only) and Apache 2.0 for a
    public notebook (Kaggle default);
  - runs the harvest round 31 share audit (policy.audit) on each row that is left and keeps it only when it passes.
Output as pubnear31.py: work/pubnear/<n>-<tag>-<sha12>.csv with a .json record, and one "pub" line per start on stdout.
  - drops a row that shares 0.9 or more at 1e-3 with a start already in work/pubnear (the same layout from another file).
Usage: pubnear31m.py NEARCOUNT_TXT [max_per_n [lo hi]]
"""
import csv, hashlib, json, math, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pubnear31 as P  # noqa: E402
import round31 as R    # noqa: E402

B = P.B
LIC_OK = re.compile(r'Apache 2\.0|CC BY 4\.0|CC0', re.I)


def licence_of(path):
    p = Path(path)
    if '/data/nb/' in str(p):
        return 'Apache 2.0 (Kaggle default for public notebooks)'
    meta = p.parent / 'meta.json'
    try:
        m = json.loads(meta.read_text())
    except (OSError, ValueError):
        return ''
    lic = str(m.get('license') or m.get('licence') or m.get('licenseName') or '')
    if re.search(r'CC0', lic):
        return 'CC0 (dataset meta.json: %s)' % lic
    if re.search(r'CC[ -]?BY[ -]?4\.0|Attribution 4\.0', lic, re.I) and not re.search(r'NC|SA|ND', lic):
        return 'CC BY 4.0 (dataset meta.json: %s)' % lic
    if re.search(r'Apache', lic, re.I):
        return 'Apache 2.0 (dataset meta.json: %s)' % lic
    return lic or 'unknown'


def owner_name(path):
    m = re.search(r'/data/(?:nb|ds)/([^/_]+(?:_[^/_]+)*?)__([^/]+)/', str(path))
    return (m.group(1), m.group(2)) if m else ('?', '?')


def main():
    listing = sys.argv[1]
    per_n = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    lo, hi = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (1e-6, 1e-4)
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(P.BAR), delimiter='\t')}
    wd = R.withdrawn()
    files = []
    for line in open(listing):
        parts = line.split()
        if len(parts) < 4 or not parts[0].isdigit() or int(parts[0]) == 0:
            continue
        files.append(str(B / parts[3]))
    files.sort()
    seen = {}; cand = {}
    for f in files:
        own, name = owner_name(f)
        if own.lower() == 'prvsiyan':
            print('# skip file %s: prvsiyan' % f); continue
        lic = licence_of(f)
        if not LIC_OK.search(lic):
            print('# skip file %s: licence %r' % (f, lic)); continue
        fsha = hashlib.sha256(Path(f).read_bytes()).hexdigest()
        if fsha in wd:
            print('# skip file %s: withdrawn (%s)' % (f, wd[fsha][:80])); continue
        pub = P.rows_by_n(f)
        for n, rows in pub.items():
            if len(rows) != n or n in P.OUT_N or n not in bar:
                continue
            m = P.side(rows) / math.sqrt(n) - 1 - bar[n]
            if not (lo < m <= hi):
                continue
            key = hashlib.sha256(''.join('%s,%s,%s;' % (r['x'], r['y'], r['angle']) for r in rows).encode()).hexdigest()
            if key in seen:
                continue
            seen[key] = f
            cand.setdefault(n, []).append((m, f, fsha, lic, own, name, rows))
    print('# %d files, %d distinct near rows over %d n' % (len(files), sum(len(v) for v in cand.values()), len(cand)))
    held = P.rows_by_n(P.HELD, set(cand))
    od = P.W / 'pubnear'; od.mkdir(parents=True, exist_ok=True)
    out = []
    for n in sorted(cand):
        hc = P.centres(held[n])
        kept = [P.centres(P.rows_by_n(str(q))[n]) for q in sorted(P.W.glob('pubnear/%d-*.csv' % n))]
        per = per_n + len(kept)
        for m, f, fsha, lic, own, name, rows in sorted(cand[n], key=lambda c: c[0]):
            if len(kept) >= per:
                break
            c = P.centres(rows)
            hs = P.policy.share(c, hc)
            if hs[1] >= 0.9:
                continue
            if any(P.policy.share(c, k)[1] >= 0.9 for k in kept):
                continue
            ok, ev = P.policy.audit([dict(r, n=str(n)) for r in rows])
            mx = max([max(e['share1e3'], e['share1e2']) for e in ev] or [0.0])
            why = 'margin %+.3g, 1105 share max %.3f, share with our held row %.3f/%.3f at 1e-3/1e-2, %s/%s' % (m, mx, hs[1], hs[2], own, name)
            if not ok:
                print('# skip n=%d: %s (1105 share)' % (n, why)); continue
            kept.append(c)
            body = 'n,square_id,x,y,angle\n' + ''.join('%d,%d,%s,%s,%s\n' % (n, i, r['x'], r['y'], r['angle']) for i, r in enumerate(rows))
            h = hashlib.sha256(body.encode()).hexdigest()
            if list(od.glob('%d-*-%s.csv' % (n, h[:12]))):
                print('# skip n=%d: start bytes already written (%s)' % (n, h[:12])); continue
            tag = re.sub(r'[^a-z0-9]', '', own.lower())[:12] + '31m'
            p = od / ('%d-%s-%s.csv' % (n, tag, h[:12]))
            p.write_text(body)
            rel = str(Path(f).relative_to(B))
            meta = Path(f).parent / 'meta.json'
            stext = '%s/%s :: %s (fetched by the harvest lane, %s%s)' % (
                own, name, Path(f).name, rel, '; meta %s' % meta.relative_to(B) if meta.exists() else '')
            rec = dict(n=n, kind='public-near', public_first=True,
                       source='public %s, row n = %d as published (public file sha256 %s), %.3g of score above bar31; '
                              'no fq, no change' % (stext, n, fsha, m),
                       licence=lic, evidence=ev, held_share=dict(share1e3=hs[1], share1e2=hs[2]), path=str(p), sha256=h,
                       public_file=f, public_file_sha256=fsha)
            Path(str(p) + '.json').write_text(json.dumps(rec, indent=1))
            out.append((m, p, why))
    for m, p, why in sorted(out, key=lambda o: o[0]):
        print('pub %s %.5f %s' % (p, 0.06 + m * 400, why))
    print('# %d starts kept' % len(out))


if __name__ == '__main__':
    main()
