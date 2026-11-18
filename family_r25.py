#!/usr/bin/env python3
"""Round 25 of the family follow: one strict source rule, the held round 23 b file as the clean pool.

  family_r25.py beats   WORK                 r24 frozen take rows as bar files (all rows but explicit Samanyu ones)
  family_r25.py carry   WORK PREVWORK        audit PREVWORK/final-unfinished-follow.tsv into 1200/1600 carry jobs
  family_r25.py control WORK                 positive and negative controls of the source rule
  family_r25.py loop    WORK --deadline E --follow-until E [--every 120]

A row counts only when its whole recorded ancestry passes `clean`: no excluded source of the brief, no
Samanyu-dev seed (only the CC0 and Apache Kaggle sets samanyu1808/sis-final-packings and sis-submit pass),
and no 'seed merged0' whose origin is not known. A donor equal to its held row of
gather/round23-2026-11-13b.csv is the clean pool and its own history is not walked. Reads local data only.
"""
import argparse, csv, datetime, hashlib, json, os, re, shutil, sys, time
from pathlib import Path
csv.field_size_limit(50_000_000)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import family_loop as fl          # noqa: E402
import family_clean as fc         # noqa: E402
from family_lineage import Lineage  # noqa: E402

S = Path('$SCRATCH/bounties-squares')
LANE = Path(__file__).resolve().parent
HELD = 'gather/round23-2026-11-13b.csv'
GATE = 'gate/cand-round23-1113b'
OK_SAMANYU = r'samanyu1808/sis-(?:final-packings|submit)'
LABELS = r'Samanyu(?:-dev)?\s+(?:seed\s+)?ancestry:\s*(?:none|no|absent)\b'
EXCLUDED = ['squares-verified-best-of-1105', 'squares-joegun-boxed-certified-union', 'prvsiyan/squares-verified']


def clean(n, source, licence, lineage):
    """None when the recorded ancestry is clean, else the reason."""
    text = source + ' ' + licence
    text = re.sub(r'«HELD».*?«/HELD»', ' ', text, flags=re.S)
    for x in EXCLUDED:
        if x in text:
            return 'excluded source ' + x
    if re.search(r'(?:held|packing of|donor)\s*(?:packing of\s*)?n\s*=\s*801\b', text):
        return 'excluded held801'
    if n == 981 and '801' in text:
        return 'excluded 981 on 801'
    for m in re.finditer(r'take-(harvest|forensics|midm|invent)-r(\d+)/(?:near/|work/donors/)?(\d+)', text):
        lane, rnd, dn = m[1], int(m[2]), int(m[3])
        if (lane == 'harvest' and rnd == 22 and dn in {639, 691, 745, 858, 918}) or (rnd == 23 and dn == 639) or \
                (lane == 'forensics' and rnd <= 23 and dn in {918, 980}):
            return 'excluded frozen ancestor ' + m[0]
    # A family unread/ file carries no source record of its own (round 25: the staged 927 reached the
    # 931h and 811h seed far zones through take-family-r22/work/unread/810-rdn22.csv), so it is untraced.
    if re.search(r'/work/unread/\d+-[\w-]+\.csv', text):
        return 'untraced unread/ ancestor'
    stripped = re.sub(OK_SAMANYU, ' ', re.sub(LABELS, ' ', text, flags=re.I), flags=re.I)
    if re.search(r'samanyu', stripped, re.I):
        return 'Samanyu named in ancestry'
    if re.search(r'seed merged0', stripped, re.I):
        q = lineage.classify(n, source, licence)
        if q['status'] != 'no':
            return 'seed merged0 ancestry %s %s' % (q['status'], q['seeds'] or q['unknown'])
    return None


class Audit(fc.Audit):
    BASE = HELD

    def __init__(self, scratch, lane, work):
        super().__init__(scratch, lane, work)
        self.lineage = Lineage(str(scratch), str(work))

    def base_source(self, n):
        so, lic = super().base_source(n)
        return ('«HELD»held packing of n=%d in %s (round 25 clean pool); its source %s«/HELD»' % (n, HELD, so),
                '«HELD»' + lic + '«/HELD»')

    def __call__(self, n, path, source, licence):
        try:
            st = os.stat(path); key = (n, str(path), st.st_mtime_ns, st.st_size, source, licence)
        except OSError:
            return None
        memo = self.__dict__.setdefault('memo', {})
        if key in memo:       # the rule reads texts of up to 178 kB: once per file version
            return memo[key]
        r = super().__call__(n, path, source, licence)
        if r is None:         # an ancestor ledger can arrive later: ask again next cycle
            return None
        why = clean(n, r[0], r[1], self.lineage)
        if why:
            self.rejected[str(path) + '#' + str(n)] = why
            r = None
        memo[key] = r
        return r


def state(msg):
    with (S / 'take-family-r25/STATE.txt').open('a') as h:
        h.write(datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') + ' boxA ' + msg + '\n')


def cmd_beats(a):
    """deploy/beat-r24-<lane>.tsv: every frozen r24 take row, except a row whose own record names Samanyu."""
    w = Path(a.work); lin = Lineage(str(S), str(w)); out = {}
    for d in sorted(S.glob('take-*-r24')):
        lane = d.name[5:-4]
        if lane == 'family' or not (d / 'take.tsv').exists():
            continue
        rows = []; drop = []
        for r in csv.DictReader(open(d / 'take.tsv'), delimiter='\t'):
            why = clean(int(r['n']), r.get('source', ''), r.get('licence', ''), lin)
            if why and ('Samanyu' in why or 'excluded' in why):
                drop.append((r['n'], why)); continue
            rows.append(r)
        p = w / 'deploy' / ('beat-r24-%s.tsv' % lane)
        with open(str(p) + '.tmp', 'w', newline='') as h:
            wr = csv.DictWriter(h, fieldnames=['n', 'new'], delimiter='\t', extrasaction='ignore', lineterminator='\n')
            wr.writeheader(); wr.writerows(rows)
        os.replace(str(p) + '.tmp', p)
        out[lane] = dict(kept=len(rows), dropped=drop)
    (w / 'r24-beats.json').write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps({k: (v['kept'], len(v['dropped'])) for k, v in out.items()}))


def cmd_control(a):
    w = Path(a.work); au = Audit(S, LANE, w); lin = au.lineage
    held = S / HELD
    ok = au(927, held, 'old generic', 'see old ledger')
    assert ok is not None and '«HELD»' in ok[0], ok
    bad = [('the x result (Samanyu-dev/squares_in_squares seed n=365)', 'none'),
           ('take-harvest-r22/639.csv', 'Apache'), ('x', 'CC BY-SA prvsiyan/squares-verified-best-of-1105'),
           ('from take-forensics-r23/980.csv', 'ours'), ('take-invent-r23/639.csv', 'ours')]
    for so, li in bad:
        assert clean(990, so, li, lin) is not None, so
    src = Path(a.work) / 'sources.tsv'
    rec = next(r for r in csv.DictReader(open(src), delimiter='\t') if r['donor'] == '990-rdn23b')
    assert clean(990, rec['source'], rec['licence'], lin) == 'untraced unread/ ancestor'
    good = ('k123_join.py from samanyu1808/sis-final-packings n=812', 'CC0 | Samanyu ancestry: no')
    assert clean(812, *good, lin) is None
    print('control: held927 admitted as clean pool; 5 excluded texts refused; samanyu1808 CC0 text admitted')


def cmd_carry(a):
    w = Path(a.work); prev = Path(a.prev); au = Audit(S, LANE, w)
    rows = list(csv.DictReader(open(prev / 'final-unfinished-follow.tsv'), delimiter='\t'))
    jobs = []; audit = []; src = fl.sources(str(w))
    for r in rows:
        name = r['donor']; p = prev / 'deploy/donors' / (name + '.csv')
        res = au(int(name.split('-')[0]), p, r['source'], r['licence'])
        if res is None:
            audit.append(dict(job=r['job'], status='rejected', reason=au.rejected.get(str(p) + '#' + name.split('-')[0], ''))); continue
        old = prev / 'deploy/jobs' / r['job']
        if not old.exists():
            audit.append(dict(job=r['job'], status='missing job')); continue
        text = old.read_text(); mt = re.search(r'jobs/(\S+\.tsv)', text)
        if not mt:
            audit.append(dict(job=r['job'], status='no spec')); continue
        spec = prev / 'deploy/jobs' / mt[1]
        new = ('1600-carry-' if 'near miss' in r['source'] else '1200-carry-') + re.sub(r'^\d+-(?:\d{6}-|carry-)?', '', r['job'])
        shutil.copy2(p, w / 'deploy/donors' / p.name); shutil.copy2(spec, w / 'deploy/jobs' / spec.name)
        (w / 'deploy/jobs' / new).write_text(text)
        src[name] = '\t'.join((name, *res)); jobs.append(new); audit.append(dict(job=new, status='admitted', donor=name))
    fl.save_sources(str(w), src); au.save()
    (w / 'carried-audit.json').write_text(json.dumps(audit, indent=1) + '\n')
    (w / 'carried-jobs.json').write_text(json.dumps(jobs) + '\n')
    print('carried', len(jobs), 'of', len(rows))


def fresh_name(job, deadline, now):
    """Newest walks first. A walk from a frozen round 24 layout waits behind every round 25 design (1100)."""
    if int(job[:4]) <= 1049:
        return job
    m = re.search(r'-fol-\d+-[a-z]+(\d\d)', job)
    return '%s-%06d-%s' % ('1100' if m and m[1] == '24' else '1050', max(0, int(deadline - now)), job[5:])


def publish(w, strict, take):
    """Copy the strict rows whose recorded ancestry is clean to TAKE, take.tsv last and by rename."""
    lin = Lineage(str(S), str(w)); rows = []; refused = {}
    if (strict / 'take.tsv').exists():
        for r in csv.DictReader(open(strict / 'take.tsv'), delimiter='\t'):
            why = clean(int(r['n']), r['source'], r['licence'], lin)
            if why:
                refused[r['n']] = why; continue
            rows.append(r)
    for r in rows:
        src = strict / (r['n'] + '.csv'); dst = take / (r['n'] + '.csv')
        if not dst.exists() or dst.read_bytes() != src.read_bytes():
            shutil.copy2(src, str(dst) + '.tmp'); os.replace(str(dst) + '.tmp', dst)
    for r in rows:   # the source cells must not carry the internal marks
        for k in ('source', 'licence'):
            r[k] = r[k].replace('«HELD»', '').replace('«/HELD»', '')
    with open(take / 'take.tsv.tmp', 'w', newline='') as h:
        wr = csv.DictWriter(h, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t',
                            extrasaction='ignore', lineterminator='\n')
        wr.writeheader(); wr.writerows(sorted(rows, key=lambda r: int(r['n'])))
    os.replace(take / 'take.tsv.tmp', take / 'take.tsv')
    (w / 'publication-refused.json').write_text(json.dumps(refused, indent=1) + '\n')
    return rows


def cmd_loop(a):
    w = Path(a.work); take = w.parent; d = w / 'deploy'
    if a.final:     # one last collect, certify and publish after the deadline; no new walks
        a.deadline = time.time() + 900; a.follow_until = 0; a.once = True
    audit = Audit(S, LANE, w); fl.FOLLOW_AUDIT = audit
    fl.WALK_MISSES = 1; fl.FILL_HERE = True; fl.NEAR_COPY = 1e-6; fl.NEAR_OUT = 1e-4; fl.STAIR_ENV = 'SQ_CUTREACH=9 SQ_STAIRCUT=1 '
    fl.TAGS.update({'gap': 'gp', 'rebuild': 'rb', 'backlog': 'bl', 'quench': 'qn'})
    bx = fl.boxes(str(w))
    follow = argparse.Namespace(round='r25', scratch=str(S), fresh=['r24'], logs=[], gate=str(S / GATE / 'gate.json'),
                                best=str(LANE / 'results/round23-best-2026-11-13.tsv'), held=str(S / HELD),
                                first=['gap', 'rebuild', 'stair-c', 'corners', 'readers', 'twoshort', 'border', 'modules', 'invent', 'forensics'],
                                newall=True)
    (w / 'loop.pid').write_text(str(os.getpid()) + '\n')
    state('START collector family_r25.py loop, log work/loop.out, follow until %s, deadline %s.' % (
        time.strftime('%H:%MZ', time.gmtime(a.follow_until)), time.strftime('%H:%MZ', time.gmtime(a.deadline))))
    if a.carry:
        jobs = json.loads((w / 'carried-jobs.json').read_text()); got = fl.deal(str(w), bx, jobs)
        state('ADOPT %d source-admitted carry jobs (1200/1600, behind fresh walks), dealt %s.' % (len(jobs), got))
    lastcheck = 0; previous = {}
    if (take / 'take.tsv').exists():
        previous = {r['n']: r['new'] for r in csv.DictReader(open(take / 'take.tsv'), delimiter='\t')}
    while time.time() < a.deadline and not (w / 'STOPLOOP').exists():
        t0 = time.time()
        takes = fl.other_takes(str(take), 'r25', str(S))
        r24 = {k + '-r24': v for k, v in fl.other_takes(str(take), 'r24', str(S)).items() if k != 'family'}
        beats = [x + '/take.tsv' for x in takes.values()] + sorted(str(p) for p in d.glob('beat-r24-*.tsv'))
        fl.collect(str(w), bx)
        strict = w / 'strict-publication'
        keep, qj = fl.certify_after_quench(str(w), str(strict), str(d / 'details.csv'), beats, bx)
        rows = publish(w, strict, take)
        fl.prune(str(w), str(take))
        selected = {r['n']: r['new'] for r in rows}
        keep = [l for l in keep if l.split()[1] in selected]
        fl.announce(str(w), str(take), follow, keep)
        fl.near_out(str(w), str(take), follow, beats)
        fl.push_beats(str(w), bx, takes)
        fj = fl.follow_pass(str(w), str(take), follow, {**r24, **takes}) if time.time() < a.follow_until else []
        renamed = []
        for j in fj:
            new = fresh_name(j, a.deadline, time.time())
            if new != j:
                (d / 'jobs' / j).replace(d / 'jobs' / new)
            renamed.append(new)
        got = fl.deal(str(w), bx, qj + renamed); audit.save()
        for n, v in selected.items():
            if previous.get(n) != v:
                r = next(x for x in rows if x['n'] == n)
                state('PUBLISHED n=%s new %s gain %s (remote quench from certified csv), %s' % (n, v, r['gain'], r['source'][:160]))
        previous = selected
        fl.log(str(w), 'cycle kept%d quenches%d fresh%d accepted%d rejected%d dealt%s elapsed%.1fs' % (
            len(rows), len(qj), len(fj), len(audit.proofs), len(audit.rejected), got, time.time() - t0))
        if time.time() - lastcheck >= 600:
            state('CHECK handoff-r25.log and all r25 take/near folders read (r24 frozen as fresh starts). Take n=%s; workers 3/2.' % ','.join(sorted(selected, key=int)))
            lastcheck = time.time()
        if a.once:
            break
        end = min(t0 + a.every, a.deadline)
        while time.time() < end and not (w / 'STOPLOOP').exists():
            time.sleep(min(5, max(0.1, end - time.time())))
    state('FINISH collector loop.')


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    for c in ('beats', 'control'):
        sub.add_parser(c).add_argument('work')
    q = sub.add_parser('carry'); q.add_argument('work'); q.add_argument('prev')
    q = sub.add_parser('loop'); q.add_argument('work'); q.add_argument('--deadline', type=float, required=True)
    q.add_argument('--follow-until', type=float, required=True); q.add_argument('--every', type=float, default=120)
    q.add_argument('--once', action='store_true'); q.add_argument('--carry', action='store_true'); q.add_argument('--final', action='store_true')
    a = ap.parse_args()
    dict(beats=cmd_beats, control=cmd_control, carry=cmd_carry, loop=cmd_loop)[a.cmd](a)


if __name__ == '__main__':
    main()
