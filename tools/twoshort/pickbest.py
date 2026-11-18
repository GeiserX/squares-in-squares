# pickbest.py N DIR [DIR ...] : the raw file of invent_rest.py with the lowest side over the BEST lines of DIR/slide-N-*.tsv
import glob, sys
n = sys.argv[1]; best = None
for d in sys.argv[2:]:
    for t in glob.glob("%s/slide-%s-*.tsv" % (d, n)):
        seed = t.rsplit("-", 1)[1][:-4]
        for l in open(t):
            p = l.rstrip("\n").split("\t")
            if l.startswith("#") or len(p) < 7 or p[-1] != "BEST": continue
            if best is None or float(p[3]) < best[0]: best = (float(p[3]), "%s/raw/%s-sl%s-%s.csv" % (d, n, seed, p[0]))
print(best[1])
