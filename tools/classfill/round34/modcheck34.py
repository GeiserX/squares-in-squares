"""Which inputs give a readable two-arm cut (M.cut), and which n changed between round 32 a and round 33 a."""
import sys, csv, json, hashlib
sys.path.insert(0, '$SCRATCH/bounties-squares/take-classfill-r34/work/stage/lane')
import modules as M
def rowsets(p):
    g = {}
    for r in csv.DictReader(open(p)):
        g.setdefault(int(r['n']), []).append((r['square_id'] if 'square_id' in r else r['id'], r['x'], r['y'], r['angle']))
    return g
if sys.argv[1] == 'changed':
    a = rowsets(sys.argv[2]); b = rowsets(sys.argv[3])
    print(json.dumps(sorted(n for n in b if sorted(b[n]) != sorted(a.get(n, [])))))
else:
    for p in sys.argv[2:]:
        try:
            lay = M.read_layouts(p)
            n = next(iter(lay))
            d, why = M.cut(lay[n], n)
            print('CUT ' + json.dumps(dict(path=p, n=n, ok=d is not None, why=None if d is not None else str(why)[:120])), flush=True)
        except Exception as e:
            print('CUT ' + json.dumps(dict(path=p, ok=False, why=repr(e)[:120])), flush=True)
