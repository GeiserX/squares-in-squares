#!/usr/bin/env python3
"""backlog_queue: one ranked queue over the saved queues the round 24 lanes left unstarted (avenues/backlog.md).

Reads the frozen take-<lane>-r24 dirs, never writes them. For each entry it takes the start score, sets it against
the clean base bar of backlog_base.py and walks the recorded ancestry: the entry's own source and licence text, then
every take-*/near/work file path that text names (its .json sidecars and the take.tsv row of its count), up to
depth 6, memoized once per path. An entry is dropped when that text reaches a source that is out:
  a Samanyu-dev seed (forensics_policy.classify_text status seeds or unknown), penguin069 / joegun, the prvsiyan
  best-of-1105 file, a path or count of the out counts 639 691 745 858 918 980 981 801, or the old forensics 918.
An entry whose start file is missing is dropped too.

Rank: predicted gain = queue hit rate (measured in round 24, or this round) x expected score drop, minus nothing;
entries with a start below the bar come first (they only need certification). Only the queues with an adapter in
backlog_worker.py are runnable; the others are counted so the report can say what stays.

  backlog_queue.py BASE.tsv OUT.json [--rates RATES.json]
"""
import csv, glob, json, math, os, re, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import forensics_policy  # noqa: E402  (the forensics lane's seed classifier, imported, not edited)

S = '$SCRATCH/bounties-squares'
OUT_N = {639, 691, 745, 858, 918, 980, 981, 801}
csv.field_size_limit(1 << 30)
BAD = re.compile(r'penguin069|joegun|squares-verified-best-of-1105|best-of-1105|take-harvest-r22/(?:\S*/)?(?:639|691|745|858|918)\b'
                 r'|take-forensics-r2[0-3]/(?:near/)?918|squares_in_squares|unresolved (?:ancestry|archived parent)'
                 # the 735 tree with seed 365, the 790 built with it, the 228 on it and the 985 follower, as they
                 # stand in rounds up to 23 (round 24 rebuilt 735 and 790 from CC0 inputs; those are traced apart)
                 r'|take-[\w-]+-r(?:1\d|2[0-3])/(?:\S*/)?(?:735|790|228|985)[-.]', re.I)
OUTPATH = re.compile(r'/(?:639|691|745|858|918|980|981|801)(?:[-.]|\.csv)')
PATH = re.compile(r'$SCRATCH/bounties-squares/[\w./+-]+?\.(?:csv|json|tsv)')
_memo = {}
_takes = {}


def take_row(d, n):
    if d not in _takes:
        rows = {}
        p = os.path.join(S, d, 'take.tsv')
        if os.path.exists(p):
            for r in csv.DictReader(open(p), delimiter='\t'):
                try:
                    rows[int(r['n'])] = (r.get('source') or '') + ' ' + (r.get('licence') or '')
                except (KeyError, ValueError):
                    pass
        _takes[d] = rows
    return _takes[d].get(n, '')


def own_text(p):
    """The records beside P: its .json sidecars and, for a take dir per-n file, the take.tsv row of its count."""
    parts = []
    for side in (p + '.json', p + '.origin.json', p[:-4] + '.json', p + '.source.json'):
        if side != p and os.path.exists(side) and os.path.getsize(side) < 16 << 20:
            try:
                parts.append(open(side, errors='replace').read())
            except OSError:
                pass
    m = re.match(re.escape(S) + r'/(take-[\w-]+?-r\d+)/(\d+)\.csv$', p)
    if m:
        parts.append(take_row(m[1], int(m[2])))
    return ' '.join(parts)


def text_verdict(text):
    if BAD.search(text):
        return 'out source ' + BAD.search(text)[0]
    if OUTPATH.search(text):
        return 'out-count parent ' + OUTPATH.search(text)[0]
    pol = forensics_policy.classify_text(text)
    if pol['status'] != 'none':
        return 'samanyu %s %s' % (pol['status'], pol['seeds'][:5])
    return 'clean'


def path_verdict(p, depth=6):
    """Verdict of the file P and every parent its records name, memoized once per path."""
    if p in _memo:
        return _memo[p]
    _memo[p] = 'clean'                 # cut cycles
    text = own_text(p)
    v = text_verdict(text)
    if v == 'clean' and depth > 0:
        for q in sorted(set(PATH.findall(text)) - {p}):
            v = path_verdict(q, depth - 1)
            if v != 'clean':
                v = v if ' via ' in v else v + ' via ' + os.path.relpath(q, S)
                break
    _memo[p] = v
    return v


def verdict(text, n, start=None):
    if n in OUT_N:
        return 'out count %d' % n
    v = text_verdict(text)
    if v != 'clean':
        return v
    for q in sorted(set(PATH.findall(text))) + ([start] if start else []):
        v = path_verdict(q, 5)
        if v != 'clean':
            return v
    return 'clean'


def load_base(p):
    return {int(r['n']): float(r['clean_score']) for r in csv.DictReader(open(p), delimiter='\t')}


def invent_items(base):
    W = S + '/take-invent-r24/work'
    out = []
    for e in json.load(open(W + '/pending-final.json')):
        n = int(e['n']); start = os.path.join(W, e['start'])
        sc = float(e['side']) / math.sqrt(n) - 1
        out.append(dict(owner='invent', queue=W + '/pending-final.json', id='invent:' + e['id'], n=n, start=start,
                        start_score=sc, gap=sc - base[n], tool='invent_rest.py', seconds=int(e['seconds']),
                        seed=int(e['seed']), fq=bool(e.get('fq')), text=str(e.get('source', '')) + ' ' + str(e.get('licence', ''))))
    return out


def harvest_items(base):
    W = S + '/take-harvest-r24/work'
    out = []
    for e in json.load(open(W + '/pending.json')):
        r = e['row']; n = int(r['n'])
        sc = float(r.get('start') or r['new'])
        out.append(dict(owner='harvest', queue=W + '/pending.json', id='harvest:' + e['key'][:16], n=n, start=e['path'],
                        start_score=sc, gap=sc - base[n], tool='fq quench (harvest remote_run flags)', seconds=120,
                        text=str(r.get('source', '')) + ' ' + str(r.get('licence', ''))))
    return out


def counted_only():
    """Queues without an adapter this round: counted so the report names them."""
    c = {}
    def n_lines(p):
        try:
            return sum(1 for _ in open(p)) - 1
        except OSError:
            return None
    c['family'] = (S + '/take-family-r24/work/final-unfinished-follow.tsv', n_lines(S + '/take-family-r24/work/final-unfinished-follow.tsv'))
    c['border'] = (S + '/take-border-r24/work/unstarted.tsv', n_lines(S + '/take-border-r24/work/unstarted.tsv'))
    return c


# Hit rate per queue: (finished runs that certified below their bar) / (finished runs), from the r24 reports:
# invent saved starts 3 of 35 ended (978, 599, 645); harvest backlog 0 of 1 (prior 1 of 10 as a floor).
PRIOR = {'invent': (3, 35, 6e-6), 'harvest': (0.1, 1.0, 2e-6)}


def main():
    base = load_base(sys.argv[1]); out = sys.argv[2]
    rates = dict(PRIOR)
    if '--rates' in sys.argv:
        p = sys.argv[sys.argv.index('--rates') + 1]
        if os.path.exists(p):
            for k, v in json.load(open(p)).items():
                rates[k] = tuple(v)
    items = invent_items(base) + harvest_items(base)
    kept, dropped = [], {}
    for it in items:
        if not os.path.exists(it['start']):
            dropped[it['id']] = 'start missing'; continue
        v = verdict(it.pop('text'), it['n'], it['start'])
        if v != 'clean':
            dropped[it['id']] = v; continue
        hits, runs, drop = rates[it['owner']]
        p = (hits + 0.5) / (runs + 1.0)
        # a start below the bar is a near-certain gain of its own size; above it needs a drop larger than the gap
        it['pred'] = (-it['gap'] if it['gap'] < 0 else 0.0) + p * max(0.0, drop - max(0.0, it['gap']))
        kept.append(it)
    kept.sort(key=lambda it: -it['pred'])
    # one item per (owner, n, start score to 1e-9): identical starts run once
    seen, uniq = set(), []
    for it in kept:
        k = (it['owner'], it['n'], round(it['start_score'], 9))
        if k in seen:
            dropped[it['id']] = 'duplicate start'; continue
        seen.add(k); uniq.append(it)
    json.dump(dict(items=uniq, dropped=dropped, counted_only=counted_only(), rates=rates), open(out + '.tmp', 'w'), indent=0)
    os.replace(out + '.tmp', out)
    from collections import Counter
    print('kept', Counter(i['owner'] for i in uniq), 'dropped', Counter(v.split(' ')[0] for v in dropped.values()))
    for it in uniq[:12]:
        print(it['id'], it['n'], '%.3e' % it['gap'], '%.3e' % it['pred'])


if __name__ == '__main__':
    main()
