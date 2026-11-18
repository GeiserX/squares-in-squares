#!/usr/bin/env python3
"""Round 27: reopen the held rows that the Samanyu-dev rule took out of the candidate files (round 23 a held 20 counts on
it, round 25 a held k123 982). Each row becomes one job of the round:

  * its bytes go to W/cq/run/N-TAG/raw as a result, so collect certifies the row itself against the bar and the live
    takes and runs its certified fq quench (a reopened row counts when no live take holds it lower);
  * the same bytes start a pass chain on a box (two 140 s islands, an 1800 s island on a find, fq), at the head of the
    queue (qorder: tag z).

  reopen.py GATHER_FILE TAKE_SOURCES_TSV N[,N...] [MODE]
"""
import csv, hashlib, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctl, policy, provenance
csv.field_size_limit(1 << 28)


def main():
    gather, srcfile, ns = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
    mode = sys.argv[4] if len(sys.argv) > 4 else 'pass'
    label = 'round' + os.path.basename(gather).split('-')[0][5:] + os.path.basename(gather)[-5]   # round23a, round25a
    rows = {}
    for r in csv.DictReader(open(gather, newline='')):
        n = int(r['n'])
        if n in ns:
            rows.setdefault(n, []).append({k: r[k] for k in ctl.KEYS})
    src = {}
    for r in csv.DictReader(open(srcfile), delimiter='\t'):
        try:
            src[int(r['n'])] = (r.get('source') or '', r.get('licence') or '')
        except ValueError:
            continue
    held = ctl.held_scores()
    for k, n in enumerate(ns):
        rr = rows.get(n, [])
        if len(rr) != n:
            print('SKIP', n, 'rows', len(rr)); continue
        tag = 'z' + label[5:]
        pl = ctl.load_plan()
        if any(j['n'] == n and j['tag'] == tag for j in pl['jobs']):
            print('SKIP', n, 'already a job'); continue
        donor = '%s/donors/%d-%s.csv' % (ctl.W, n, label)
        os.makedirs(os.path.dirname(donor), exist_ok=True)
        ctl.write_rows(donor, rr)
        sha = hashlib.sha256(open(donor, 'rb').read()).hexdigest()
        s0, l0 = src.get(n, ('', ''))
        source = ('held %s row of n=%d (%s, sha256 of the extracted rows %s), reopened by the round 27 lift of the Samanyu-dev '
                  'rule; recorded source: %s' % (label, n, gather, sha[:16], s0))
        licence = l0
        json.dump(dict(n=n, source=source, licence=licence, gather=gather, sha256=sha), open(donor + '.json', 'w'), indent=1)
        proof = provenance.trace(gather if label.startswith('round23') else srcfile.replace('take.tsv', '%d.csv' % n), n)
        if not proof.get('ok'):
            print('REFUSE', n, proof.get('reason')); continue
        sp = policy.classify(source, licence, proof)
        _, score, _ = ctl.cert((donor, donor))
        if score is None:
            print('REFUSE', n, 'does not certify'); continue
        start = '%s/starts/%d-%s.csv' % (ctl.W, n, tag)
        ctl.write_rows(start, rr)
        raw = '%s/cq/run/%d-%s/raw' % (ctl.W, n, tag); os.makedirs(raw, exist_ok=True)
        ctl.write_rows('%s/%d-reopen-0.csv' % (raw, n), rr)
        box = ctl.WATCH_SLOTS[len(pl['jobs']) % len(ctl.WATCH_SLOTS)]
        if not ctl.push(box, start, '%d %s %s' % (n, tag, mode)):
            print('PUSH FAILED', n, box); continue
        pl = ctl.load_plan()
        pl['jobs'].append(dict(n=n, tag=tag, kind='reopen', where='take', start=score, held=held[n], path=donor, source=source,
                               licence=licence, ancestry=ctl.store_ancestry(proof), source_policy=sp, mode=mode,
                               layout_gain=held[n] - score, box=box, rank=len(pl['jobs']), added=time.strftime('%H:%M:%S', time.gmtime()),
                               file_score=None, monitor_bar=held[n], reopened=label))
        ctl.save_plan(pl)
        with open(ctl.T + '/STATE.txt', 'a') as f:
            f.write('%s boxA START reopen n=%d %s score %.12f bar %.12f (%+.3e) %s on %s; log work/%s/run/%d-%s; deadline 23:45Z\n' % (
                time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime()), n, label, score, held[n], held[n] - score, mode, box, box, n, tag))
        print('ADD', n, tag, label, score, held[n], box)


if __name__ == '__main__':
    main()
