#!/usr/bin/env python3
"""One hopped corner carried to other side fractions, as start states for zone_corner.py search.

  twoshort_carry.py LIBWORK CORNER_ID OUT.pkl TAG F[,F...]

`zone_corner.py base` carries the corners that the library cut from held layouts. It leaves out the corners of a
zone search (tag z), which is what a staircase corner is after its hops. This tool takes one such corner from
LIBWORK/library.pkl, carries it to each F with zone_corner.carry (the knots of modules.path, then the contact LP with
free angles) and prints its loss there. OUT.pkl is a base file: `zone_corner.py search OUT.pkl DIR --id ID` hops from
the carried state, and with --down and --up it deletes and inserts squares from it.

Round 19 used it to show that the corner of two 9-arms at 3.03 squares (f = 0.63) is one state with its lowest loss,
2.99, at f = 0.64, and that the floor of 3.40 at f = 0.68 is the same state.

Control: carried to its own f the corner keeps its stored loss.

Our own code. Imports zone_corner of this lane.
"""
import os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zone_corner as ZC


def main():
    lib, cid, out, tag = sys.argv[1:5]
    fs = [float(v) for v in sys.argv[5].split(',')]
    q = next(m for m in pickle.load(open(lib + '/library.pkl', 'rb'))['mods'] if m['id'] == cid)
    print('%s count %d (class %d) at its own f %.4f: loss %.4f' % (cid, q['count'], q['count'] % q['c1'], q['f0'], q['loss0']), flush=True)
    res = []
    for f in fs:
        st = ZC.carry(q, f)
        if st is None:
            print('f %.4f: the carry does not reach it' % f, flush=True); continue
        y, x, P, mod = st
        i = 'cy%dx%d-%df%04d%s' % (q['c1'], q['c2'], q['count'], round(f * 10000), tag)
        res.append(dict(id=i, src='%s carried to f %.4f <%s>' % (cid, f, q['src']), licence=q['licence'], sig=q.get('sig'), count=q['count'],
                        c1=q['c1'], c2=q['c2'], lean1=q['lean1'], lean2=q['lean2'], f=f, y0=y, x0=x, P=P))
        print('f %.4f: y0 %.6f x0 %.6f loss %.4f id %s' % (f, y, x, ZC.loss_of(mod, f, q['count'], y, x), i), flush=True)
    pickle.dump(res, open(out, 'wb'))


if __name__ == '__main__':
    main()
