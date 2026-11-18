"""rects29.py OUT.tsv: list forensics rectangle compositions (take-forensics-r28/near and take-forensics-r29/near,
*-rect*.csv) with their side against the bar29 side, whether parts A and B come from different n (mixed donors),
a withdrawal by path or sha256 in handoff-r28/r29, our r28 kick of the same bytes, and a rule-a text hit in the
record or the part records it names. One row per file, sorted by side minus bar side."""
import csv, glob, hashlib, json, math, os, re, sys
S = '$SCRATCH/bounties-squares/'
sys.path.insert(0, '.')
import methods_lp as mlp  # noqa: E402
csv.field_size_limit(1 << 28)
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r30/work/bar30b.tsv'), delimiter='\t')}
PAT = re.compile(r'joegun-boxed|penguin069|donor[ _-]?(?:639|691|745|858|918)\b|donor(?:639|691|745|858|918)-|745r-858|858r-745|'
                 r'squares-verified-best-of-1105', re.I)
wd_txt = ''
for h in ('handoff-r28.log', 'handoff-r30.log'):
    if os.path.isfile(S + h):
        wd_txt += ''.join(l for l in open(S + h, errors='replace') if re.search(r'\bWITHDRAW\b', l) and 'REINSTATE' not in l)
kicked = set()
for l in open(S + 'take-rebuild-r28/work/queue-log.tsv'):
    f = l.rstrip('\n').split('\t')
    if len(f) >= 6:
        kicked.add(f[5])
out = []
files = sorted(glob.glob(S + 'take-forensics-r28/near/*-rect*.csv') + glob.glob(S + 'take-forensics-r29/near/*-rect*.csv'))
for p in files:
    m = re.match(r'(\d+)-', os.path.basename(p))
    if not m:
        continue
    n = int(m.group(1))
    b = open(p, 'rb').read(); sha = hashlib.sha256(b).hexdigest()
    try:
        P = mlp.load(p, {n})[n]
        side = float(mlp.side(P)); gap = float(mlp.min_gap(P))
    except Exception as e:
        continue
    rec = {}
    j = p + '.json'
    txt = ''
    if os.path.isfile(j):
        txt = open(j, errors='replace').read()
        try:
            rec = json.loads(txt)
        except Exception:
            rec = {}
    pa = (rec.get('parts') or {})
    na = (pa.get('A') or {}).get('source', [None, None])[1] if pa.get('A') else None
    nb = (pa.get('B') or {}).get('source', [None, None])[1] if pa.get('B') else None
    for k in ('A', 'B'):
        q = pa.get(k) or {}
        for fld in ('source_record', 'snapshot'):
            v = str(q.get(fld, ''))
            mm = re.search(r'(/Volumes/\S+?\.json)', v)
            cand = [mm.group(1)] if mm else []
            if fld == 'snapshot' and v:
                cand += [v + '.origin.json', v + '.json']
            for c in cand:
                if os.path.isfile(c) and os.path.getsize(c) < 20_000_000:
                    txt += open(c, errors='replace').read()
    hits = sorted(set(x.group(0).lower() for x in PAT.finditer(txt)))
    wd = (p in wd_txt) and (sha in wd_txt or sha[:12] in wd_txt or not re.search(re.escape(p) + r' sha256', wd_txt))
    bs = (1 + bar[n]) * math.sqrt(n)
    out.append((side - bs, n, p, sha, side, bs, gap, na, nb, int(sha in kicked), int(wd), ','.join(hits)))
out.sort()
with open(sys.argv[1], 'w') as h:
    h.write('d_side\tn\tpath\tsha256\tside\tbar_side\tmin_gap\tnA\tnB\tkicked_r28\twithdrawn\trulea\n')
    for r in out:
        h.write('\t'.join(str(x) for x in r) + '\n')
print(len(out), 'files')
