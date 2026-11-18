#!/usr/bin/env python3
"""midm round 32: pub-near starts from the CHANGED public files of round 32 only (midm round 31 next item 2).

Round 31 measured: 77 pub-near scans, 6 paid, 3.49e-4 gained on their starts, 2 crossings (812 certified 3.6e-5 below
bar31; 972 refused at a 1105 share of 0.460). Round 31 already ran the near rows of every public file harvested in
rounds 28 to 31 (pubnear31m.py, 244 files), so round 32 reads only public files whose sha256 is new:
  - files: take-harvest-r32/work/public*/data/{nb,ds}/<slug>/*.csv with columns n, x, y, angle;
  - a file is changed when its sha256 is not in round 31's listing (take-midm-r31/work/pubnear/nearcount.txt, 12-hex
    prefixes), not the public file of a round 31 pub-near start, and not already read by this tool (processed32.txt);
  - rows 1e-6 to 1e-4 of score above bar32 (at most PER_N per n), then 1e-4 to 2.5e-4 (at most 1 per n);
  - dropped: prvsiyan files, withdrawn bytes (WITHDRAW lines of handoff-r29 to r32), n of override 3, licences other
    than Apache 2.0, CC BY 4.0 or CC0, rows within share 0.9 at 1e-3 of our held round 31 b row (our own layout, polished
    less) or of a pub-near start of round 31 or 32 (the same layout again), and rows whose harvest32 policy.audit
    (frozen assembler share31 measure, every non-own 1105 version) reads 0.4 or more at 1e-3 or 1e-2.
Output: work/pubnear/<n>-<tag>32-<sha12>.csv with a .json record, and one "pub <path> <priority> <why>" line per start
on stdout (append these to work/extra-starts.txt).
Usage: pubnear32.py [--dry]
"""
import csv, hashlib, json, math, re, sys
from pathlib import Path

L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L / 'tools/harvest32'))
import policy  # noqa: E402  (harvest round 32 share audit: the frozen assembler share31 measure; imported, not edited)
import numpy as np  # noqa: E402

B = Path('$SCRATCH/bounties-squares')
W = B / 'take-midm-r32/work'
W31 = B / 'take-midm-r31/work'
BAR = B / 'round32-briefs/bar32.tsv'
HELD = B / 'gather/round31-2026-11-16b.csv'
OUT_N = {639, 691, 745, 858, 918}
LIC_OK = re.compile(r'Apache 2\.0|CC BY 4\.0|CC0', re.I)
PER_N = 2


def rows_by_n(path, want=None):
    out = {}
    with open(path, errors='replace') as f:
        rd = csv.DictReader(f)
        if not rd.fieldnames or not {'n', 'x', 'y', 'angle'} <= {c.strip().lower() for c in rd.fieldnames}:
            return {}
        for r in rd:
            r = {str(k).strip().lower(): v for k, v in r.items()}
            try:
                n = int(str(r['n']).lstrip('s'))
                r = dict(n=str(n), x=str(r['x']).lstrip('s'), y=str(r['y']).lstrip('s'), angle=str(r['angle']).lstrip('s'))
                float(r['x']); float(r['y']); float(r['angle'])
            except (ValueError, KeyError, TypeError):
                continue
            if want is None or n in want:
                out.setdefault(n, []).append(r)
    return out


def side(rows):
    lo = [math.inf] * 2; hi = [-math.inf] * 2
    for r in rows:
        a = float(r['angle']); x = float(r['x']); y = float(r['y'])
        h = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        lo[0] = min(lo[0], x - h); hi[0] = max(hi[0], x + h); lo[1] = min(lo[1], y - h); hi[1] = max(hi[1], y + h)
    return max(hi[0] - lo[0], hi[1] - lo[1])


def centres(rows):
    a = np.array([[float(r['x']), float(r['y'])] for r in rows])
    return a - (a.min(0) + a.max(0)) / 2


def withdrawn():
    wd = {}; re_in = []
    for q in ('handoff-r29.log', 'handoff-r30.log', 'handoff-r31.log', 'handoff-r32.log'):
        p = B / q
        if not p.exists():
            continue
        for line in p.read_text(errors='replace').splitlines():
            if 'REINSTATE' in line:
                re_in += re.findall(r'\b[0-9a-f]{16,64}\b', line)
            elif 'WITHDRAW' in line:
                for h in re.findall(r'\b[0-9a-f]{64}\b', line):
                    wd[h] = line[:300]
    for p in re_in:
        for h in [h for h in wd if h.startswith(p)]:
            del wd[h]
    return wd


def licence_of(path):
    p = Path(path)
    if '/data/nb/' in str(p):
        return 'Apache 2.0 (Kaggle default for public notebooks)'
    try:
        m = json.loads((p.parent / 'meta.json').read_text())
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


def known_shas():
    seen = set()
    nc = W31 / 'pubnear/nearcount.txt'
    if nc.exists():
        for line in nc.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 3 and re.fullmatch(r'[0-9a-f]{12}', parts[2]):
                seen.add(parts[2])
    for d in (W31 / 'pubnear', W / 'pubnear'):
        for j in d.glob('*.csv.json'):
            try:
                seen.add(json.loads(j.read_text()).get('public_file_sha256', '')[:12])
            except (OSError, ValueError):
                pass
    pr = W / 'pubnear/processed32.txt'
    if pr.exists():
        seen.update(line.split()[0][:12] for line in pr.read_text().splitlines() if line.strip())
    return seen


def main():
    dry = '--dry' in sys.argv
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BAR), delimiter='\t')}
    wd = withdrawn()
    seen_sha = known_shas()
    files = []
    for pub in sorted((B / 'take-harvest-r32/work').glob('public*')):
        for kind in ('nb', 'ds'):
            files += sorted((pub / 'data' / kind).glob('*/*.csv'))
    od = W / 'pubnear'; od.mkdir(parents=True, exist_ok=True)
    processed = []
    cand = {}; seen_rows = set()
    for f in files:
        own, name = owner_name(f)
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        fsha = hashlib.sha256(raw).hexdigest()
        if fsha[:12] in seen_sha:
            continue
        processed.append('%s %s' % (fsha, f))
        seen_sha.add(fsha[:12])
        if own.lower() == 'prvsiyan':
            print('# skip file %s: prvsiyan' % f); continue
        lic = licence_of(f)
        if not LIC_OK.search(lic):
            print('# skip file %s: licence %r' % (f, lic)); continue
        if fsha in wd:
            print('# skip file %s: withdrawn (%s)' % (f, wd[fsha][:80])); continue
        pub = rows_by_n(f)
        if not pub:
            continue
        nn = 0
        for n, rows in pub.items():
            if len(rows) != n or n in OUT_N or n not in bar:
                continue
            m = side(rows) / math.sqrt(n) - 1 - bar[n]
            if not (1e-6 < m <= 2.5e-4):
                continue
            key = hashlib.sha256(''.join('%s,%s,%s;' % (r['x'], r['y'], r['angle']) for r in rows).encode()).hexdigest()
            if key in seen_rows:
                continue
            seen_rows.add(key); nn += 1
            cand.setdefault(n, []).append((m, f, fsha, lic, own, name, rows))
        print('# changed file %s (%s/%s, sha256 %s): %d near rows' % (f, own, name, fsha[:16], nn))
    print('# %d changed files, %d distinct near rows over %d n' % (len(processed), sum(len(v) for v in cand.values()), len(cand)))
    held = rows_by_n(HELD, set(cand))
    out = []
    for n in sorted(cand):
        hc = centres(held[n])
        prior = [centres(rows_by_n(str(q))[n]) for q in sorted(list((W31 / 'pubnear').glob('%d-*.csv' % n)) + list(od.glob('%d-*.csv' % n)))]
        kept = []
        for m, f, fsha, lic, own, name, rows in sorted(cand[n], key=lambda c: c[0]):
            band = 0 if m <= 1e-4 else 1
            if band == 0 and sum(1 for k in kept if k[1] == 0) >= PER_N:
                continue
            if band == 1 and sum(1 for k in kept if k[1] == 1) >= 1:
                continue
            c = centres(rows)
            hs = policy.share(c, hc)
            if hs[1] >= 0.9:
                print('# skip n=%d %s/%s: margin %+.3g, share %.3f with our held row (our layout, polished less)' % (n, own, name, m, hs[1])); continue
            if any(policy.share(c, k)[1] >= 0.9 for k in prior + [k[0] for k in kept]):
                print('# skip n=%d %s/%s: margin %+.3g, same layout as a pub-near start of round 31 or 32' % (n, own, name, m)); continue
            ok, ev = policy.audit([dict(r, n=str(n)) for r in rows])
            mx = max([max(e['share1e3'], e['share1e2']) for e in ev] or [0.0])
            why = 'margin %+.3g, 1105 share max %.3f, share with our held row %.3f/%.3f at 1e-3/1e-2, %s/%s' % (m, mx, hs[1], hs[2], own, name)
            if not ok:
                print('# skip n=%d: %s (1105 share)' % (n, why)); continue
            kept.append((c, band))
            body = 'n,square_id,x,y,angle\n' + ''.join('%d,%d,%s,%s,%s\n' % (n, i, r['x'], r['y'], r['angle']) for i, r in enumerate(rows))
            h = hashlib.sha256(body.encode()).hexdigest()
            tag = re.sub(r'[^a-z0-9]', '', own.lower())[:12] + '32'
            p = od / ('%d-%s-%s.csv' % (n, tag, h[:12]))
            rel = str(Path(f).relative_to(B))
            meta = Path(f).parent / 'meta.json'
            stext = '%s/%s :: %s (fetched by the harvest lane in round 32, %s%s)' % (
                own, name, Path(f).name, rel, '; meta %s' % meta.relative_to(B) if meta.exists() else '')
            rec = dict(n=n, kind='public-near', public_first=True,
                       source='public %s, row n = %d as published (public file sha256 %s), %.3g of score above bar32; '
                              'no fq, no change' % (stext, n, fsha, m),
                       licence=lic, evidence=ev, held_share=dict(share1e3=hs[1], share1e2=hs[2]), path=str(p), sha256=h,
                       public_file=str(f), public_file_sha256=fsha)
            if not dry:
                p.write_text(body)
                Path(str(p) + '.json').write_text(json.dumps(rec, indent=1))
            out.append((m, p, why))
    for m, p, why in sorted(out, key=lambda o: o[0]):
        # priority: 1e-6 to 1e-4 above at 0.06 to 0.10, 1e-4 to 2.5e-4 above at 0.10 to 0.16 (round 31 pubnear31m)
        print('pub %s %.5f %s' % (p, 0.06 + m * 400, why))
    if not dry:
        with open(od / 'processed32.txt', 'a') as h:
            for line in processed:
                h.write(line + '\n')
    print('# %d starts kept' % len(out))


if __name__ == '__main__':
    main()
