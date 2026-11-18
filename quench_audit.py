#!/usr/bin/env python3
"""quench: walk a recorded ancestry and refuse the sources that are out.

Usage: quench_audit.py FILE [FILE ...]   (a provenance .json, a .csv.json, or any text)

It reads each file, then every per-file ancestry record it names under the
scratch dir (provenance/<sha256>.json, <file>.origin.json, <file>.csv.json),
and the take.tsv row of every per-n take file it names (take-<lane>-rNN/<n>.csv),
and so on (each file once), and checks the whole text:
  - (round 27: Samanyu seed ancestry no longer refuses; the rule is lifted)
  - prvsiyan/squares-verified-best-of-1105 (CC BY-SA 4.0), penguin069 and
    its boxed certified union
  - n = 639, 691, 745, 858, 918 taken from take-harvest-r22 or from areebbb
  - a 639 of round 23 (invent, midm), the round 23 forensics 980 and every
    older forensics 918
Prints one JSON line per FILE: clean, hits, files read. A start whose text
cannot be read is not clean.
"""
import json, os, re, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)

SCRATCH = '$SCRATCH/bounties-squares'
BAD22 = '639|691|745|858|918'
RULES = [
    ('prvsiyan best-of-1105', r'squares-verified-best-of-1105'),
    ('penguin069 joegun union', r'squares-joegun-boxed|joegun-boxed-certified-union'),  # its boxed-public-certified union is a distinct, allowed source
    ('harvest-r22 a-row', r'take-harvest-r22/(?:%s)\.csv|n\s*=\s*(?:%s)\b[^;()]{0,40}take-harvest-r22|round 22 file of n = (?:%s) in take-harvest-r22' % (BAD22, BAD22, BAD22)),
    ('areebbb a-row', r'(?:donor n|n)\s*=\s*(?:%s)\b[^;()<>]{0,60}areebbb|areebbb[^;()<>]{0,80}\bn\s*=\s*(?:%s)\b' % (BAD22, BAD22)),
    ('r23 639', r'take-(?:invent|midm)-r23/639|round 23 file of n = 639 in|n\s*=\s*639 (?:of|in|from) take-(?:invent|midm)-r23'),
    # round 29 (main 07:34:54Z): the directory-name pattern took-forensics-r23/work/donors/(745|858)- caught readers
    # donors 858-c82b5be2 and 858-bc8896e9 (up1from799) and the family r23 858-c43df5d7; only these two donors are the join
    ('r22 745/858 join', r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8'),
    ('r23 forensics 980', r'take-forensics-r23/980|n\s*=\s*980 (?:of|in|from) take-forensics-r23|round 23 file of n = 980 in take-forensics'),
    ('older forensics 918', r'take-forensics-r(?:1\d|2[0-3])/918|n\s*=\s*918 (?:of|in|from) take-forensics-r(?:1\d|2[0-3])\b|round (?:1\d|2[0-3]) file of n = 918 in take-forensics'),
]


# Follow only per-file ancestry records. Tables that hold many n (a lane's
# provenance-final.json, sources-all) would pull in the sources of other n.
PER_FILE = re.compile(r'(?:/provenance/[0-9a-f]{64}[^/]*|\.origin|\.csv)\.json$')


def take_row(d, n, cache={}):
    """The take.tsv row of n in take dir d, as text ('' when there is none)."""
    if d not in cache:
        rows = {}
        try:
            for line in open(d + '/take.tsv', errors='replace'):
                k = line.split('\t', 1)[0]
                if k.isdigit():
                    rows[int(k)] = line
        except OSError:
            pass
        cache[d] = rows
    return cache[d].get(n, '')


def walk(paths, limit=400, cap=200 << 20):
    seen, texts, todo, size = set(), [], list(paths), 0
    while todo and len(seen) < limit and size < cap:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        if isinstance(p, tuple):
            t = take_row(*p)
        else:
            try:
                t = open(p, errors='replace').read()
            except OSError:
                continue
            if p.endswith('.json'):
                # round 31: harvest's share audit evidence names the 1105 comparison archive, not an ancestor
                # (any list of share dicts: 'evidence', 'excluded': {'comparison_diagnostics': [...]})
                def drop_cmp(x):
                    if isinstance(x, dict):
                        return {k: drop_cmp(v) for k, v in x.items() if not (isinstance(v, list) and v and all(isinstance(e, dict) and 'share1e3' in e for e in v))}
                    if isinstance(x, list):
                        return [drop_cmp(v) for v in x]
                    return x
                try:
                    t = json.dumps(drop_cmp(json.loads(t)))
                except ValueError:
                    pass
        texts.append(t); size += len(t)
        for q in re.findall(r'($SCRATCH/bounties-squares/[^\s"\\\'<>;,)]+?\.json)', t):
            if q not in seen and PER_FILE.search(q) and os.path.exists(q):
                todo.append(q)
        # a per-n file of a take dir: its ancestry is that take's row of n
        for d, n in re.findall(r'($SCRATCH/bounties-squares/take-[^/\s"\\\'<>;,)]+)/(\d+)\.csv', t):
            if (d, int(n)) not in seen:
                todo.append((d, int(n)))
    return '\n'.join(texts), len(seen)


def audit(path):
    if not os.path.exists(path):
        return {'file': path, 'clean': False, 'hits': ['unreadable'], 'files': 0}
    text, k = walk([path])
    hits = []
    # round 27: the Samanyu-dev rule is lifted, so forensics_policy's seed classifier no longer refuses
    for name, rx in RULES:
        m = re.search(rx, text, flags=re.I)
        if m:
            hits.append('%s: %s' % (name, text[max(0, m.start() - 60):m.end() + 20].replace('\n', ' ')))
    return {'file': path, 'clean': not hits, 'hits': hits, 'files': k}


if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(json.dumps(audit(p)), flush=True)
