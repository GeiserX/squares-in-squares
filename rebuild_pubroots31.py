"""pubroots29.py START N [OUT.json]: the public-first roots of one start, round 29 rule (forensics 08:32Z gate, brief rule 3):
walk START with quench_walk.walk; for every held row it reaches (label 'held N R'), split its table text into source and
licence; a held row whose first source is a public notebook or dataset ('owner/slug :: file', after 'fq quench of' and
similar) is public-first: its licence must name Apache 2.0, CC BY 4.0 or CC0, and the share of its bytes (gather/roundR,
latest file of that round) against the best-of-1105 row must be below 0.4 at 1e-3. Own rows (modules, joins, family,
the held 801, Samanyu seeds) pass. Also lists the harvest records the walk reaches (public-first starts) for review.
Prints one JSON object: start, n, helds [{n, round, kind, licence, share1e3, ok, why}], harvest [labels], bad (count)."""
import csv, glob, json, os, re, sys
sys.path.insert(0, '.')
import quench_walk as qw  # noqa: E402
import rebuild_walk27 as w27  # noqa: E402
csv.field_size_limit(1 << 28)
S = qw.S
ALLOWED = re.compile(r'Apache 2\.0|Apache-2\.0|CC BY 4\.0|CC-BY-4\.0|CC0', re.I)
NOTALLOWED = re.compile(r'BY-SA|ShareAlike|Other \(specified|GPL|non-?commercial|BY-NC', re.I)
LEAD = re.compile(r'^(?:fq quench(?: check)? of |fq follow of |donor n = \d+ retained source: (?:fq quench(?: check)? of )?)', re.I)
PUB = re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+ :: ')
_rows = {}


def held_rows(r):
    if r not in _rows:
        fs = sorted(glob.glob(S + 'gather/round%d-2026-*.csv' % r))
        if not fs:   # no held file of that round: the latest earlier one
            allf = [(int(re.search(r'round(\d+)-', f).group(1)), f) for f in glob.glob(S + 'gather/round*-2026-*.csv')]
            fs = [f for k, f in sorted(allf) if k <= r][-1:]
        _rows[r] = {}
        if fs:
            for row in csv.DictReader(open(fs[-1])):
                _rows[r].setdefault(int(row['n']), []).append(row)
            _rows[r]['file'] = fs[-1]
    return _rows[r]


def share_held(n, r):
    rows = held_rows(r).get(n)
    if not rows or len(rows) != n:
        return None
    tmp = S + 'take-rebuild-r31/work/pubroots/held-%d-%d.csv' % (n, r)
    if not os.path.isfile(tmp):
        with open(tmp, 'w', newline='') as h:
            w = csv.DictWriter(h, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return w27.prv_share(tmp, n)


def main(start, n):
    texts, missing, seen, helds, refused = qw.walk(start, n)
    out, harvest = [], []
    for label, t in texts:
        lb = str(label)
        if lb.startswith('held '):
            _, hn, hr = lb.split()[:3]
            hn, hr = int(hn), (int(hr) if hr.isdigit() else 29)   # 'held N None': the latest held file
            body = t.split(': ', 1)[1] if ': ' in t else t
            src, _, lic = body.partition(' || ')
            first = LEAD.sub('', src.strip())
            if hn == 801:
                out.append(dict(n=hn, round=hr, kind='own (held 801, round 29 rule 3)', licence=lic.strip()[:120], ok=True)); continue
            if t.startswith('original seed'):
                own = 'Samanyu' in t or 'samanyu' in t
                out.append(dict(n=hn, round=hr, kind='original seed', src=t[:160], ok=own, why='' if own else 'non-Samanyu original seed: review')); continue
            if not PUB.match(first):
                out.append(dict(n=hn, round=hr, kind='own', src=first[:120], ok=True)); continue
            row = dict(n=hn, round=hr, kind='public-first', src=first[:160], licence=lic.strip()[:200])
            if NOTALLOWED.search(lic) or not ALLOWED.search(lic):
                row.update(ok=False, why='licence not Apache 2.0, CC BY 4.0 or CC0')
            else:
                sh = share_held(hn, hr)
                row['share1e3'] = sh and sh['share1e3']
                row['share1e2'] = sh and sh['share1e2']
                row.update(ok=bool(sh) and sh['share1e3'] < 0.4, why='' if (sh and sh['share1e3'] < 0.4) else ('share 0.4 or more' if sh else 'held bytes not found'))
            out.append(row)
        elif 'take-harvest-r' in lb:
            harvest.append(lb.replace(S, '')[:140])
    return dict(start=start.replace(S, ''), n=n, texts=len(texts), missing=len(missing), helds=out, harvest=sorted(set(harvest))[:40],
                bad=sum(1 for x in out if not x['ok']))


if __name__ == '__main__':
    st = sys.argv[1] if sys.argv[1].startswith('/') else S + sys.argv[1]
    res = main(st, int(sys.argv[2]))
    s = json.dumps(res, indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w').write(s)
    print(s)
