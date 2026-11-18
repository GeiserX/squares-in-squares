"""floatsafe every n the merge took from the harvest; keep those that certify below the held score. -> DIR/<n>.csv

  angle_take.py MERGED_DIR HELD OUT_DIR      HELD: a tsv or the gate's details.csv with columns n and score

Licence allow-list: a win from a source whose licence the lane has not accepted is dropped here, and the
merge's second choice for that n (MERGED_DIR/alt, the best packing from an accepted source) is tried instead.
"""
import csv, sys, os, math
LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
ACCEPTED = ('apache 2.0', 'apache-2.0', 'cc by 4.0', 'cc-by-4.0', 'cc0')   # plus our own work
OWN = ('ours', 'own search')


def accepted(licence):
    """Is this licence text one the lane takes packings under? Unknown, empty, "Other", SA/NC/ND and MIT are not."""
    l = (licence or '').strip().lower()
    return l.startswith(OWN) or any(a in l for a in ACCEPTED)


def table(path):
    if not os.path.exists(path):
        return {}
    return {int(r['n']): r for r in csv.DictReader(open(path), delimiter='\t')}


def job(a):
    import floatsafe
    n, path = a
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(path))]
    rows = [dict(r, n=str(n)) for r in rows]
    _, fr, score, e = floatsafe.work((n, rows))
    return n, fr, score, e


if __name__ == '__main__':
    from multiprocessing import Pool
    merged, basetsv, out = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out, exist_ok=True)
    head = open(basetsv).readline()
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(basetsv), delimiter='\t' if '\t' in head else ',')}
    src, alt = table(merged + '/best.tsv'), table(merged + '/alt.tsv')
    use, jobs = {}, []
    for n in sorted(src):
        if src[n]['source'] == 'seed merged0':
            continue
        if accepted(src[n]['licence']):
            use[n] = src[n]; jobs.append((n, '%s/best/%d.csv' % (merged, n)))
            continue
        second = alt.get(n)
        print('licence drop', n, 'score', src[n]['score'], 'held', held[n], repr(src[n]['licence']), src[n]['source'],
              '-> second choice', second['source'] if second else 'none', flush=True)
        if second and accepted(second['licence']):
            use[n] = second; jobs.append((n, '%s/alt/%d.csv' % (merged, n)))
    won = sum(1 for n in src if src[n]['source'] != 'seed merged0')
    print(len(jobs), 'n taken by the merge from an accepted licence;', won - len(jobs), 'left out for their licence'); tot = 0; kept = 0
    with Pool(3) as pool, open(out + '/take.tsv', 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for n, fr, score, e in pool.imap_unordered(job, jobs):
            if fr is None or score is None or not (score < held[n] - 1e-10):
                print('drop', n, score, held[n], e, flush=True); continue
            with open('%s/%d.csv' % (out, n), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            tot += held[n] - score; kept += 1
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, use[n]['source'], use[n]['licence']))
    print('kept', kept, 'gain', tot)
