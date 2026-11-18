"""rows28.py KEY [KEY ...]: write work/rows-<time>.json for pub28.py from the finals of collect28 (work/collect-state.json)
and the pin log (work/queue-log.tsv). Source text: our job, the pinned start, the side path, the quench, and the start's
own take.tsv row (source || licence). Licence: the start's licence cell plus 'own kick or turn on it'."""
import csv, json, math, os, sys, time
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r30/work/'
csv.field_size_limit(1 << 28)
st = json.load(open(W + 'collect-state.json'))
ql = {}
for l in open(W + 'queue-log.tsv'):
    f = l.rstrip('\n').split('\t')
    if len(f) >= 8:
        ql.setdefault(f[2], f)
out = {}
for key in sys.argv[1:]:
    fin = st['finals'][key]
    n = fin['n']; q = ql[key]
    src = q[4]; sha = q[5]; pin = q[6]; mode = q[7]
    rec = st['seen'][key]['rec']
    row = None
    d = os.path.dirname(S + src)
    if src.startswith('take-rebuild-r30/work/cert/'):
        # a kick of our own certified row: the start text is the row we wrote for that cert file (any rows-*.json),
        # else our current published row of n
        import glob
        for fj in sorted(glob.glob(W + 'rows-*.json'), key=os.path.getmtime):
            for v in json.load(open(fj)).values():
                if v.get('cert') == S + src:
                    row = {'source': v['source'], 'licence': v['licence'].replace('; own kick on it', '').replace('; own kicks on it', '')}
        if row is None:
            for r in csv.DictReader(open(W + '../take.tsv'), delimiter='\t'):
                if r.get('n') == str(n):
                    row = r
    elif os.path.basename(src) == '%d.csv' % n and os.path.isfile(d + '/take.tsv'):
        for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
            if r.get('n') == str(n):
                row = r
    fol = ''
    if key.startswith('f-') and os.path.isfile(W + 'follow-seen.json'):
        for v in json.load(open(W + 'follow-seen.json')).values():
            if v.get('key') == key:
                if 'score' in v:
                    fol = ('the file as it stood when we pinned it at %s (score %r); the row of that take as it reads now (the lane may '
                           'have moved that n since; its record has the history): ' % (v['t'], v['score']))
                else:   # a near file (no take row): pinned side and margin to the bar side
                    fol = ('the near file as it stood when we pinned it at %s (side %r, %.3e of side from the bar): ' % (v['t'], v.get('side'), v.get('margin', 0.0)))
    if row is None and not src.startswith('take-rebuild-r30/') and os.path.isdir(d + '/near'):
        # the lane moved that row to near/ (superseded): find the same bytes there and read its record
        import glob, hashlib
        size = os.path.getsize(S + 'take-rebuild-r30/' + pin.replace('take-rebuild-r30/', '')) if os.path.isfile(S + pin) else -1
        for c in sorted(glob.glob(d + '/near/%d-*.csv' % n)):
            if os.path.getsize(c) != size or hashlib.sha256(open(c, 'rb').read()).hexdigest() != sha:
                continue
            for j in (c + '.json', c[:-4] + '.json'):
                if os.path.isfile(j):
                    try:
                        rj = json.load(open(j))
                    except Exception:
                        continue
                    if rj.get('source'):
                        row = {'source': "the lane's record of the same bytes, %s (that lane moved the row to near/): %s" % (
                            j.replace(S, ''), ' '.join(str(rj['source']).split())), 'licence': ' '.join(str(rj.get('licence', '')).split())}
                        break
            if row:
                break
    if row is None and os.path.isfile(S + src + '.json'):
        # a near file with its record beside it (a forensics rectangle: parts A and B, their sources and records)
        try:
            rj = json.load(open(S + src + '.json'))
        except Exception:
            rj = {}
        pa = rj.get('parts') or {}
        segs, lics = [], []
        for k in ('A', 'B'):
            q = pa.get(k)
            if not q:
                continue
            segs.append('part %s: a %sx%s window (symmetry %s) of %s (snapshot %s; %s)' % (
                k, q.get('w'), q.get('h'), q.get('sym'), str(q.get('original_file', '')).replace(S, ''),
                str(q.get('snapshot', '')).replace(S, ''), str(q.get('source_record', '')).replace(S, '')))
            lics.append('part %s: %s' % (k, q.get('licence', '')))
        if segs or rj.get('source'):
            row = {'source': 'its record %s.json: %s; %s' % (src, rj.get('kind', ''), '; '.join(segs) if segs else ' '.join(str(rj.get('source')).split())),
                   'licence': '; '.join(lics) if lics else ' '.join(str(rj.get('licence', '')).split())}
    _nt = json.load(open(W + 'notes.json')).get(key, {}) if os.path.isfile(W + 'notes.json') else {}
    if row is None and _nt.get('source'):   # round 30: a start with no record of its own (a held row we extracted)
        row = {'source': _nt['source'], 'licence': _nt.get('licence', '')}
    what = {'': 'k123_turn.py --turns=0 and the fq loop (rebuild_run.py)', 'quench': 'one fq quench'}.get(mode, 'midm_scan.py lkick,kick %s s (rebuild_run.py kick mode)' % mode.split(':')[-1])
    qn = fin.get('quench') or {}
    s = ('rebuild lane round 30: our %s on %s, job %s, of %s (sha256 %s, byte copy take-rebuild-r30/%s), side %.10f to %.10f, '
         'then floatsafe (2.2e-11); one fq quench of the certified file (job %s, side %s), so the certified file stays; chain %s. '
         'The start: %s' % (what, {'boxB': 'boxB', 'boxE': 'boxE'}[fin['box']], key, src, sha[:16], pin.replace('take-rebuild-r30/', ''),
                            (rec.get('start_side') or float('nan')), (rec.get('side') or float('nan')), qn.get('key'), qn.get('side'),
                            ' -> '.join('%s %.12g' % (c['key'], c['score']) for c in fin['chain']),
                            (fol + 'its take.tsv row: ' + row['source']) if row else 'see its sidecar record'))
    lic = ((row.get('licence') or '') if row else 'see the start record') + '; own kick on it'
    notes = json.load(open(W + 'notes.json')) if os.path.isfile(W + 'notes.json') else {}
    if mode == 'reopen':
        side_rec = {}
        for ext in ('.json',):
            j = S + src + ext
            if os.path.isfile(j):
                side_rec = json.load(open(j))
        s = ('rebuild lane round 30: re-opened near file %s (sha256 %s, byte copy take-rebuild-r30/%s), certified by floatsafe (2.2e-11, bisected dilation of border finesafe.py) against bar29; '
             'one fq quench of the certified file (job %s, side %s), so the certified file stays; chain %s. %s Its record (the .json beside it): %s' % (
                 src, sha[:16], pin.replace('take-rebuild-r30/', ''), qn.get('key'), qn.get('side'),
                 ' -> '.join('%s %.12g' % (c['key'], c['score']) for c in fin['chain']), notes.get(key, {}).get('source', ''),
                 ' '.join(str(side_rec.get('source', 'none')).split())[:6000]))
        lic = notes.get(key, {}).get('licence', 'see its record')
    out[str(n)] = {'cert': fin['cert'], 'source': s, 'licence': lic}
fn = W + 'rows-%s.json' % time.strftime('%H%M%S', time.gmtime())
json.dump(out, open(fn, 'w'), indent=1)
print(fn)
