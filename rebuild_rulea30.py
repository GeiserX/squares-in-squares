"""rulea28.py START [START ...]: walk each start with quench_walk.walk (imported) and search every text it reaches for
references to the rule-a family (penguin069 joegun union counts 639 691 745 858 918, and the round 23 forensics donors
of those counts, e.g. donor858-..., donor745-...). One JSON line per start: the matching labels and snippets."""
import json, re, sys
sys.path.insert(0, '.')
import quench_walk as qw  # noqa: E402
import csv
csv.field_size_limit(1 << 28)
import quench_audit as qa  # noqa: E402
# round 29 (main 07:34:54Z): the rule-a set is quench_audit.RULES (the 745/858 join narrowed to its two real donors and the
# 745r-858r names) plus the forensics r23 rectangle cut from the midm r23 639; the old directory-name and 800-7a2b
# alternatives were false matches
PAT = re.compile('|'.join('(?:%s)' % rx for _, rx in qa.RULES) + r'|take-forensics-r23/near/639-rect', re.I)
for start in sys.argv[1:]:
    n = int(next(csv.DictReader(open(start)))['n'])
    texts, missing, seen, helds, refused = qw.walk(start, n)
    hits = []
    for label, t in texts:
        for m in PAT.finditer(t):
            a = max(0, m.start() - 160)
            hits.append({'label': str(label).replace(qw.S, '')[:120], 'match': m.group(0), 'ctx': ' '.join(t[a:m.end() + 120].split())})
    print(json.dumps({'start': start.replace(qw.S, ''), 'n': n, 'texts': len(texts), 'missing': len(missing), 'hits': hits[:40], 'nhits': len(hits)}), flush=True)
