"""Round 32 settings for tools/softround (own lane tools only). Run once on the round 31 files.

Changes against round 31:
  1. round 32 names: take dir, box scratch, follow dirs take-*-r32, deadlines 17:05Z search, 17:13Z jobs, 17:22Z collect;
  2. the held file is gather/round31-2026-11-16b.csv (gate cand-round31-1116b, = bar32.tsv); its rows are our own layout
     and clean roots (rule 2), and a byte copy of a held row traces as that row;
  3. the share test of a public-first row with no held row is the round 31 assembler's share31.py, read as the share
     against the 1105 versions that are not our own seed (max_nonown, rule 2);
  4. claims: a held-row lkick (mode lk) posts a claim and is skipped when another lane claimed the same bytes (the
     check already matches the sha256 prefixes other lanes write);
  5. OUT_N (582, 972) refuses only trees that reach no held row (a held row of any n is ours);
  6. withdrawals read from the handoff-r27 to r32 logs.
The follow changes (fresh forensics rect files only, in the hour they appear; no islands on other lanes' rows; the held-row
lkick fill) are in follow.py itself, with their reasons.
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


# ---------------------------------------------------------------- ctl.py
p = h / 'ctl.py'; s = p.read_text()
s = sub(s, 'RN = 31', 'RN = 32')
s = sub(s, "take-soft-r30/work'", "take-soft-r31/work'")
s = sub(s, "HELD_FILE = S + '/gather/round30-2026-11-15c.csv'; GATE = S + '/gate/cand-round30-1115c'",
        "HELD_FILE = S + '/gather/round31-2026-11-16b.csv'; GATE = S + '/gate/cand-round31-1116b'")
s = sub(s, "BEST_TSV = LANE + '/results/round30-best-2026-11-15.tsv'", "BEST_TSV = LANE + '/results/round31-best-2026-11-16.tsv'")
s = sub(s, 'squares-soft-r31', 'squares-soft-r32')
s = sub(s, "for r in ('31',)", "for r in ('32',)")
s = sub(s, "# round 31 budget: processes per box", "# round 32 budget: processes per box")
s = sub(s, '# Round 31 follows fresh geometry with a clean ancestry record.', '# Round 32 follows fresh geometry with a clean ancestry record.')
s = sub(s, 'soft-r31.csv', 'soft-r32.csv')
s = s.replace('deadline 00:15Z', 'deadline 17:15Z')
s = sub(s, "              'round30-2026-11-15c.csv')\n\n\ndef reaches_held",
        "              'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv')\n\n\ndef reaches_held")
s = sub(s, "S + '/take-assemble-r30/scripts/share30.py'", "S + '/take-assemble-r31/scripts/share31.py'")
s = sub(s, "label='soft31-%d' % n", "label='soft32-%d' % n")
s = sub(s, """def _share_values(it):
    out = []""", """def _share_values(it):
    # round 32 rule 2: the share that counts is the one against 1105 versions that are not our own seed (share31.py
    # max_nonown; 0.0 when every version of the row is our own seed)
    if isinstance(it.get('max_nonown'), dict):
        return [float(v) for v in it['max_nonown'].values()]
    out = []""")
s = sub(s, """    if n in OUT_N:
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n""",
        """    if n in OUT_N and not (proof.get('ok') and reaches_held(proof, path)):
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n""")
s = sub(s, "    who = claimed_by_other(isha) if mode in ('kick', 'lpq') else None    # round 31: the claim rule is for kicks",
        "    who = claimed_by_other(isha) if mode in ('kick', 'lpq', 'lk') else None    # round 31: the claim rule is for kicks")
s = sub(s, """    if mode in ('kick', 'lpq'):          # round 31: an island is not a kick; its kick leg runs only from its own find
        post_claim(n, isha, path, mode)""", """    if mode in ('kick', 'lpq', 'lk'):    # round 31: an island is not a kick; its kick leg runs only from its own find
        post_claim(n, isha, path, mode)""")
s = sub(s, """    line = '%s soft -> all: claims kick n=%d sha256=%s, start %s (soft %s chain: island or kick legs, then fq)\\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sha, path, mode)""",
        """    what = ('150 s invent_rest.py lkick legs while a leg moves 1e-8 of side, up to 8, then fq' if mode == 'lk'
            else 'island or kick legs, then fq')
    line = '%s soft -> all: claims kick n=%d sha256=%s, start %s (soft %s chain: %s)\\n' % (
        time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), n, sha, path, mode, what)""")
p.write_text(s)

# ---------------------------------------------------------------- provenance.py
p = h / 'provenance.py'; s = p.read_text()
s = sub(s, "rnd = int(rnd[1]) if rnd else 31", "rnd = int(rnd[1]) if rnd else 32")
s = sub(s, """CANDIDATE_R30C = S / 'gather/round30-2026-11-15c.csv'
""", """CANDIDATE_R30C = S / 'gather/round30-2026-11-15c.csv'
CANDIDATE_R31B = S / 'gather/round31-2026-11-16b.csv'
""")
s = sub(s, "    if p in (CANDIDATE_R30C, CANDIDATE_R29B):", "    if p in (CANDIDATE_R31B, CANDIDATE_R30C, CANDIDATE_R29B):")
s = sub(s, """def held_copy(p, n):
    \"\"\"True when the csv at p has the rows (square_id, x, y, angle as numbers) of n in the held round 30 c file.\"\"\"
    try:
        if not _HELD30C:
            for r in csv.DictReader(open(CANDIDATE_R30C)):
                _HELD30C.setdefault(int(r['n']), []).append((int(r['square_id']), r['x'], r['y'], r['angle']))
        def num(v):
            return float(str(v).lstrip('s'))
        want = sorted((i, num(x), num(y), num(a)) for i, x, y, a in _HELD30C.get(n, []))
        got = sorted((int(r['square_id']), num(r['x']), num(r['y']), num(r['angle'])) for r in csv.DictReader(open(p)) if int(r['n']) == n)
        return len(want) == n and got == want
    except (OSError, ValueError, KeyError):
        return False""", """def held_copy(p, n):
    \"\"\"True when the csv at p has the rows (square_id, x, y, angle as numbers) of n in the held round 31 b file or the
    held round 30 c file (round 32: both are files we submitted, rule 2).\"\"\"
    try:
        def num(v):
            return float(str(v).lstrip('s'))
        got = sorted((int(r['square_id']), num(r['x']), num(r['y']), num(r['angle'])) for r in csv.DictReader(open(p)) if int(r['n']) == n)
        for f in (CANDIDATE_R31B, CANDIDATE_R30C):
            if f not in _HELD30C:
                d = _HELD30C[f] = {}
                for r in csv.DictReader(open(f)):
                    d.setdefault(int(r['n']), []).append((int(r['square_id']), r['x'], r['y'], r['angle']))
            want = sorted((i, num(x), num(y), num(a)) for i, x, y, a in _HELD30C[f].get(n, []))
            if len(want) == n and got == want:
                return True
        return False
    except (OSError, ValueError, KeyError):
        return False""")
s = s.replace("reason='rows equal the held round30-2026-11-15c.csv row (round 31 rule 2)'",
              "reason='rows equal a held row (round31-2026-11-16b.csv or round30-2026-11-15c.csv; round 32 rule 2)'")
s = sub(s, "                'round30-2026-11-15c.csv')", "                'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv')")
p.write_text(s)

# ---------------------------------------------------------------- follow.py (names only; the policy edits are by hand)
p = h / 'follow.py'; s = p.read_text()
s = sub(s, "take-%s-r31/[0-9]*.csv", "take-%s-r32/[0-9]*.csv")
s = sub(s, "take-%s-r31/near/**/*.csv", "take-%s-r32/near/**/*.csv")
s = s.replace('frozen round 30', 'frozen round 31')
s = s.replace('deadline00:15Z', 'deadline17:15Z').replace('00:15Z', '17:15Z').replace('00:08Z', '17:05Z').replace('00:23Z', '17:22Z')
p.write_text(s)

# ---------------------------------------------------------------- r28check.py (withdrawal reader)
p = h / 'r28check.py'; s = p.read_text()
s = sub(s, "S + '/handoff-r30.log', S + '/handoff-r31.log')   # round 31 adds its own log",
        "S + '/handoff-r30.log', S + '/handoff-r31.log',\n        S + '/handoff-r32.log')   # round 32 adds its own log")
p.write_text(s)

for name in ('setup.sh', 'status.sh', 'verify.sh'):
    p = h / name; p.write_text(p.read_text().replace('squares-soft-r31', 'squares-soft-r32'))
print('configured round 32')
