"""Round 31 settings for tools/softround (own lane tools only).

Changes against round 30:
  1. round 31 names (take dir, box scratch, follow dirs take-*-r31, deadlines 00:08Z search, 00:15Z jobs, 00:23Z collect);
  2. the held file is gather/round30-2026-11-15c.csv (gate cand-round30-1115c, = bar31.tsv); a row of it, and a row of the
     held round 29 b file, is our own layout (round 31 rule 2) and a clean root; the recorded source text of the row is
     still read for the excluded markers (prvsiyan 1105 itself, penguin069);
  3. claims (round 31 lesson b): ctl.add skips a start whose exact bytes another lane claimed in the last 60 minutes, and
     posts a claim line with the sha256 of the bytes it queues;
  4. the output share test of a public-first row is the round 30 assembler's share30.py (ICP, tolerances 1e-3 and 1e-2),
     not prvsim26.py at 1e-3 only (the round 30 assembler dropped our 910 at 0.456 at 1e-2, which prvsim26 read as 0.07);
  5. withdrawals read from handoff-r27 to r31 logs;
  6. a fresh take row of another lane gets our island only 10 minutes after it was written (backlog follows first).
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


# ---------------------------------------------------------------- ctl.py
p = h / 'ctl.py'; s = p.read_text()
s = sub(s, 'RN = 30', 'RN = 31')
s = sub(s, "take-soft-r29/work'", "take-soft-r30/work'")
s = sub(s, "HELD_FILE = S + '/gather/round28-2026-11-15b.csv'; GATE = S + '/gate/cand-round28-1115b'",
        "HELD_FILE = S + '/gather/round30-2026-11-15c.csv'; GATE = S + '/gate/cand-round30-1115c'")
s = sub(s, "BEST_TSV = LANE + '/results/round28-best-2026-11-15.tsv'", "BEST_TSV = LANE + '/results/round30-best-2026-11-15.tsv'")
s = sub(s, 'squares-soft-r30', 'squares-soft-r31')
s = sub(s, "for r in ('30',)", "for r in ('31',)")
s = sub(s, "# round 30 budget: processes per box", "# round 31 budget: processes per box")
s = sub(s, '# Round 30 follows fresh geometry with a clean ancestry record.', '# Round 31 follows fresh geometry with a clean ancestry record.')
s = sub(s, 'soft-r30.csv', 'soft-r31.csv')
s = s.replace('deadline 17:45Z', 'deadline 00:15Z')
# claims (round 31 lesson b)
s = sub(s, """    pl = load_plan(); held = held_scores(); jobs = pl['jobs']
    source_policy = policy.classify(proof.get('source',''), proof.get('licence',''), proof)""",
        """    if n in OUT_N:
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n
        print('REFUSE', path, LAST_ADMISSION_REASON, flush=True)
        return False
    isha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    who = claimed_by_other(isha)
    if who:
        LAST_ADMISSION_REASON = 'claimed: ' + who
        print('REFUSE claimed', path, who, flush=True)
        return False
    pl = load_plan(); held = held_scores(); jobs = pl['jobs']
    source_policy = policy.classify(proof.get('source',''), proof.get('licence',''), proof)""")
s = sub(s, """    save_plan(pl)
    print('ADD n=%d %s %s file score %s held %.12f start %.12f -> %s %s' % (n, t, kind, score, held[n], start, box, path))
    return True""", """    save_plan(pl)
    post_claim(n, isha, path, mode)
    print('ADD n=%d %s %s file score %s held %.12f start %.12f -> %s %s' % (n, t, kind, score, held[n], start, box, path))
    return True


# Round 31 lesson b: one kick per start. A start whose exact bytes another lane claimed in the last 60 minutes is skipped,
# and every start we queue gets a claim line with its sha256 (our chains end in 900 s kick legs).
OUT_N = (582, 972)
CLAIM_TTL = 3600


def claimed_by_other(sha):
    import calendar
    try:
        lines = open(HANDOFF).read().splitlines()
    except OSError:
        return None
    now = time.time()
    for line in lines:
        if sha not in line or 'claim' not in line.lower():
            continue
        m = re.match(r'(\\d{4}-\\d\\d-\\d\\d)[T ](\\d\\d:\\d\\d:\\d\\d)', line)
        if not m:
            continue
        lane = re.match(r'\\S+\\s+(?:\\S+\\s+)?([a-z0-9-]+)\\s*->', line)
        if lane and lane[1] == 'soft':
            continue
        t = calendar.timegm(time.strptime(m[1] + ' ' + m[2], '%Y-%m-%d %H:%M:%S'))
        if now - t <= CLAIM_TTL:
            return line[:160]
    return None


def post_claim(n, sha, path, mode):
    line = '%s soft -> all: claims kick n=%d sha256=%s, start %s (soft %s chain: island or kick legs, then fq)\\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sha, path, mode)
    with open(HANDOFF, 'a') as f:
        f.write(line)""")
# round 31 change 4: the output share test of a public-first row with the assembler's share30.py (ICP, 1e-3 and 1e-2)
s = sub(s, """    key = hashlib.md5(open(path, 'rb').read()).hexdigest()
    if key not in PRV_SHARE:
        r = subprocess.run([sys.executable, '-I', LANE + '/tools/classfill/round26/prvsim26.py', '%d:%s' % (n, path)],
                           capture_output=True, text=True, timeout=600)
        m = re.search(r'within1e-3 ([0-9.]+)', r.stdout)
        if m:
            PRV_SHARE[key] = float(m[1])
        elif re.search(r'rows 0 ', r.stdout):
            PRV_SHARE[key] = 0.0          # no prvsiyan row of this n
        else:
            PRV_SHARE[key] = None""", """    key = hashlib.md5(open(path, 'rb').read()).hexdigest()
    if key not in PRV_SHARE:
        # round 31: the round 30 assembler's share30.py (ICP, max of 1e-3 and 1e-2 over every harvested 1105 version)
        d = W + '/share'; os.makedirs(d, exist_ok=True)
        items = '%s/item-%s.json' % (d, key); outp = '%s/out-%s.json' % (d, key)
        json.dump([dict(label='soft31-%d' % n, path=path, n=n)], open(items, 'w'))
        r = subprocess.run([sys.executable, '-I', S + '/take-assemble-r30/scripts/share30.py', items, outp],
                           capture_output=True, text=True, timeout=1800)
        try:
            res = json.load(open(outp))
            res = res.get('items', res) if isinstance(res, dict) else res
            vals = [v for it in res if isinstance(it, dict) and it.get('n') == n for v in _share_values(it)]
            PRV_SHARE[key] = max(vals) if vals else None
        except (OSError, ValueError):
            PRV_SHARE[key] = None""")
s = sub(s, """def prv_share_out(n, path):""", """def _share_values(it):
    out = []
    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ('0.001', '0.01') and isinstance(x, (int, float)):
                    out.append(float(x))
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(it.get('share', it))
    return out


def prv_share_out(n, path):""")
p.write_text(s)

# ---------------------------------------------------------------- provenance.py
p = h / 'provenance.py'; s = p.read_text()
s = sub(s, "rnd = int(rnd[1]) if rnd else 30", "rnd = int(rnd[1]) if rnd else 31")
s = sub(s, """CANDIDATE_R28B = S / 'gather/round28-2026-11-15b.csv'
R28_TABLE = LANE / 'results/round28-best-2026-11-15.tsv'
""", """CANDIDATE_R28B = S / 'gather/round28-2026-11-15b.csv'
R28_TABLE = LANE / 'results/round28-best-2026-11-15.tsv'
CANDIDATE_R29B = S / 'gather/round29-2026-11-15b.csv'
CANDIDATE_R30C = S / 'gather/round30-2026-11-15c.csv'
""")
s = sub(s, """    if p == CANDIDATE_R28B:
        # Round 30:""", """    if p in (CANDIDATE_R30C, CANDIDATE_R29B):
        # Round 31 rule 2: every row of a file we submitted is our own layout, a clean root. r26_check still reads its
        # recorded source text (root_text) for the excluded markers.
        return True, dict(path=str(p), n=n, reason='held %s row: our own layout (round 31 rule 2)' % p.name)
    if p == CANDIDATE_R28B:
        # Round 30:""")
s = sub(s, "                'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv', 'round28-2026-11-15b.csv')",
        "                'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv', 'round28-2026-11-15b.csv', 'round29-2026-11-15b.csv',\n"
        "                'round30-2026-11-15c.csv')")
p.write_text(s)

# ---------------------------------------------------------------- follow.py
p = h / 'follow.py'; s = p.read_text()
s = sub(s, "take-%s-r30/[0-9]*.csv", "take-%s-r31/[0-9]*.csv")
s = sub(s, "take-%s-r30/near/**/*.csv", "take-%s-r31/near/**/*.csv")
s = s.replace('frozen round 29', 'frozen round 30')
s = s.replace('deadline17:45Z', 'deadline00:15Z').replace('17:45Z', '00:15Z').replace('17:38Z', '00:08Z').replace('17:53Z', '00:23Z')
# round 31 change 6: backlog follows fresh take rows of other lanes first (10 minutes)
s = sub(s, "        if kind not in KICK or time.time() - mtime > 2400:", "        if kind not in KICK or time.time() - mtime > 2400 or time.time() - mtime < 600:")
p.write_text(s)

# ---------------------------------------------------------------- r28check.py (withdrawal reader)
p = h / 'r28check.py'; s = p.read_text()
s = sub(s, "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log', S + '/handoff-r30.log')   # round 30 adds its own log",
        "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log', S + '/handoff-r30.log', S + '/handoff-r31.log')   # round 31 adds its own log")
p.write_text(s)

for name in ('setup.sh', 'status.sh', 'verify.sh'):
    p = h / name; p.write_text(p.read_text().replace('squares-soft-r30', 'squares-soft-r31'))
print('configured round 31')
