"""Round 33 settings for tools/softround (own lane tools only). Run once on the round 32 files.

Changes against round 32:
  1. round 33 names: take dir, box scratch, follow dirs take-*-r33, deadlines 00:05Z search, 00:13Z jobs, 00:22Z collect;
  2. the held file is gather/round32-2026-11-16a.csv (gate cand-round32-1116a, = bar33.tsv); its rows are our own layout
     and clean roots (rule 2), and a byte copy of a held row traces as that row;
  3. the lkick start is the held round 32 a row (work/held33/N.csv); the pool is sel33.py (n 400 to 699 only, lesson 6b);
  4. withdrawals read from the handoff-r27 to r33 logs.
The share test stays the frozen round 31 measure (share31.py max_nonown, lesson 6f).
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


# ---------------------------------------------------------------- ctl.py
p = h / 'ctl.py'; s = p.read_text()
s = sub(s, 'RN = 32', 'RN = 33')
s = sub(s, "take-soft-r31/work'", "take-soft-r32/work'")
s = sub(s, "HELD_FILE = S + '/gather/round31-2026-11-16b.csv'; GATE = S + '/gate/cand-round31-1116b'",
        "HELD_FILE = S + '/gather/round32-2026-11-16a.csv'; GATE = S + '/gate/cand-round32-1116a'")
s = sub(s, "BEST_TSV = LANE + '/results/round31-best-2026-11-16.tsv'", "BEST_TSV = LANE + '/results/round32-best-2026-11-16.tsv'")
s = sub(s, 'squares-soft-r32', 'squares-soft-r33')
s = sub(s, "for r in ('32',)", "for r in ('33',)")
s = sub(s, "# round 32 budget: processes per box", "# round 33 budget: processes per box")
s = sub(s, '# Round 32 follows fresh geometry with a clean ancestry record.', '# Round 33 follows fresh geometry with a clean ancestry record.')
s = sub(s, 'soft-r32.csv', 'soft-r33.csv')
s = s.replace('deadline 17:15Z', 'deadline 00:15Z')
s = sub(s, "              'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv')\n",
        "              'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv', 'round32-2026-11-16a.csv')\n")
s = sub(s, "label='soft32-%d' % n", "label='soft33-%d' % n")
p.write_text(s)

# ---------------------------------------------------------------- provenance.py
p = h / 'provenance.py'; s = p.read_text()
s = sub(s, "rnd = int(rnd[1]) if rnd else 32", "rnd = int(rnd[1]) if rnd else 33")
s = sub(s, """CANDIDATE_R31B = S / 'gather/round31-2026-11-16b.csv'
""", """CANDIDATE_R31B = S / 'gather/round31-2026-11-16b.csv'
CANDIDATE_R32A = S / 'gather/round32-2026-11-16a.csv'
""")
s = sub(s, "    if p in (CANDIDATE_R31B, CANDIDATE_R30C, CANDIDATE_R29B):", "    if p in (CANDIDATE_R32A, CANDIDATE_R31B, CANDIDATE_R30C, CANDIDATE_R29B):")
s = sub(s, "        for f in (CANDIDATE_R31B, CANDIDATE_R30C):", "        for f in (CANDIDATE_R32A, CANDIDATE_R31B, CANDIDATE_R30C):")
s = s.replace("rows equal a held row (round31-2026-11-16b.csv or round30-2026-11-15c.csv; round 32 rule 2)",
              "rows equal a held row (round32-2026-11-16a.csv, round31-2026-11-16b.csv or round30-2026-11-15c.csv; rule 2)")
s = sub(s, "                'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv')",
        "                'round30-2026-11-15c.csv', 'round31-2026-11-16b.csv', 'round32-2026-11-16a.csv')")
p.write_text(s)

# ---------------------------------------------------------------- follow.py
p = h / 'follow.py'; s = p.read_text()
s = sub(s, "take-%s-r32/[0-9]*.csv", "take-%s-r33/[0-9]*.csv")
s = sub(s, "take-%s-r32/near/**/*.csv", "take-%s-r33/near/**/*.csv")
s = s.replace('17:15Z', '00:15Z').replace('17:05Z', '00:05Z').replace('17:22Z', '00:22Z')
s = sub(s, "ctl.W + '/held32'", "ctl.W + '/held33'")
s = sub(s, "the held round 31 b row of n as W/held32/N.csv", "the held round 32 a row of n as W/held33/N.csv")
s = sub(s, "'the held round31-2026-11-16b.csv row of n=%d (%s)'", "'the held round32-2026-11-16a.csv row of n=%d (%s)'")
s = sub(s, "'held round31-2026-11-16b.csv row of n=%d (byte copy held32/%d.csv; rule 2)'",
        "'held round32-2026-11-16a.csv row of n=%d (byte copy held33/%d.csv; rule 2)'")
s = sub(s, "'START lk n=%d held round 31 b row", "'START lk n=%d held round 32 a row")
s = sub(s, "a kick or claim line of another lane in handoff-r32.log", "a kick or claim line of another lane in handoff-r33.log")
p.write_text(s)

# ---------------------------------------------------------------- r28check.py (withdrawal reader)
p = h / 'r28check.py'; s = p.read_text()
s = sub(s, "        S + '/handoff-r32.log')   # round 32 adds its own log",
        "        S + '/handoff-r32.log', S + '/handoff-r33.log')   # round 33 adds its own log")
p.write_text(s)

for name in ('setup.sh', 'status.sh', 'verify.sh'):
    p = h / name; p.write_text(p.read_text().replace('squares-soft-r32', 'squares-soft-r33'))
print('configured round 33')
