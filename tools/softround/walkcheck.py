"""walkcheck.py FILE: backlog's assembler-style walk (quench_walk.check) with the round 29 fix of main's 07:34:54Z note.
quench_audit's rule "r22 745/858 join" matches take-forensics-r23/work/donors/(745|858)- by directory name, so readers and
family donors (858-c82b5be2, 858-bc8896e9, 858-c43df5d7) read as the excluded join. Only 745r-858r, 858r-745r,
858-ec97a452 (k123 r22 745r-858r) and 745-64c4b4f8 are the join. A hit of that rule is replaced by the narrowed pattern over
the same walk texts. We import the quench lane's tools and never edit them. Prints one JSON line like quench_walk."""
import json, re, sys
sys.path.insert(0, '.')
import quench_walk as qw

NARROW = re.compile(r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8')
path = sys.argv[1]
res = qw.check(path)
hits = res.get('hits', [])
if any(h.startswith('r22 745/858 join') for h in hits):
    texts = qw.walk(path, res['n'])[0]
    alltext = '\n'.join(t for lb, t in texts if not str(lb).startswith('held 801 '))
    hits = [h for h in hits if not h.startswith('r22 745/858 join')]
    m = NARROW.search(alltext)
    if m:
        hits.append('r22 745/858 join (narrowed, main 07:34:54Z): ' + alltext[max(0, m.start() - 60):m.end() + 20].replace('\n', ' '))
    res['narrowed_745_858'] = True
res['hits'] = hits; res['clean'] = not hits
print(json.dumps(res), flush=True)
