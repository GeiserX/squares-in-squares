"""rulea28.py START [START ...]: walk each start with quench_walk.walk (imported) and search every text it reaches for
references to the rule-a family (penguin069 joegun union counts 639 691 745 858 918, and the round 23 forensics donors
of those counts, e.g. donor858-..., donor745-...). One JSON line per start: the matching labels and snippets."""
import json, re, sys
sys.path.insert(0, '.')
import quench_walk as qw  # noqa: E402
import csv
csv.field_size_limit(1 << 28)
PAT = re.compile(r'joegun|penguin069|donor[ _-]?(?:639|691|745|858|918)\b|donor(?:639|691|745|858|918)-|745r-858|858r-745|'
                 r'(?:639|691|745|858|918)-(?:rect|donor)', re.I)
for start in sys.argv[1:]:
    n = int(next(csv.DictReader(open(start)))['n'])
    texts, missing, seen, helds, refused = qw.walk(start, n)
    hits = []
    for label, t in texts:
        for m in PAT.finditer(t):
            a = max(0, m.start() - 160)
            hits.append({'label': str(label).replace(qw.S, '')[:120], 'match': m.group(0), 'ctx': ' '.join(t[a:m.end() + 120].split())})
    print(json.dumps({'start': start.replace(qw.S, ''), 'n': n, 'texts': len(texts), 'missing': len(missing), 'hits': hits[:40], 'nhits': len(hits)}), flush=True)
