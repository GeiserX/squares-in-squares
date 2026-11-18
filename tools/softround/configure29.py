"""Round 29 settings for tools/softround (own lane tools only).

Changes against round 28:
  1. round 29 names (take dir, box scratch, follow dirs take-*-r29, deadlines 11:38Z search, 11:45Z jobs, 11:53Z collect);
  2. the held file is gather/round27-2026-11-15b.csv (gate cand-round27-1115b); a row of it resolves to the take file
     that results/round27-best-2026-11-15.tsv names, else to the round 26 b logic; the base bar is bar29.tsv
     (work/base-extra.json holds the rows of r28 takes below the held file);
  3. held 801 stays out of soft starts as before (its recorded source text names the prvsiyan 1105 file, which the round
     29 rule still excludes by name; one n, not worth a trace dispute this round);
  4. certify with border's finesafe.py (bisected dilation; round 28 measured 3e-10 to 8e-10 of side below the ladder);
  5. withdrawals read from handoff-r27, r28 and r29 logs.
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


# ---------------------------------------------------------------- ctl.py
p = h / 'ctl.py'; s = p.read_text()
s = sub(s, 'RN = 28', 'RN = 29')
s = sub(s, "take-soft-r27/work'", "take-soft-r28/work'")
s = sub(s, "HELD_FILE = S + '/gather/round26-2026-11-14b.csv'; GATE = S + '/gate/cand-round26-1114b'",
        "HELD_FILE = S + '/gather/round27-2026-11-15b.csv'; GATE = S + '/gate/cand-round27-1115b'")
s = sub(s, "BEST_TSV = LANE + '/results/round26-best-2026-11-14.tsv'", "BEST_TSV = LANE + '/results/round27-best-2026-11-15.tsv'")
s = sub(s, 'squares-soft-r28', 'squares-soft-r29')
s = sub(s, "for r in ('28',)", "for r in ('29',)")
s = sub(s, "# round 28 budget: processes per box", "# round 29 budget: processes per box")
s = sub(s, '# Round 28 follows fresh geometry with a clean ancestry record.', '# Round 29 follows fresh geometry with a clean ancestry record.')
s = sub(s, 'soft-r28.csv', 'soft-r29.csv')
s = s.replace('deadline 05:45Z', 'deadline 11:45Z')
# Round 29: certify with the bisected dilation of border r28 (same clearance test and metric, smaller dilation).
s = sub(s, """        import floatsafe
        _, fr, score, e = floatsafe.work((n, rows))""", """        sys.path.insert(0, LANE + '/tools/border/r28')
        import finesafe                  # round 29: bisected dilation, 3e-10 to 8e-10 of side below the ladder (border r28)
        _, fr, score, e = finesafe.work((n, rows))""")
p.write_text(s)

# ---------------------------------------------------------------- provenance.py
p = h / 'provenance.py'; s = p.read_text()
s = sub(s, "rnd = int(rnd[1]) if rnd else 28", "rnd = int(rnd[1]) if rnd else 29")
s = sub(s, """CANDIDATE_R26B = S / 'gather/round26-2026-11-14b.csv'
R26_TABLE = LANE / 'results/round26-best-2026-11-14.tsv'""", """CANDIDATE_R26B = S / 'gather/round26-2026-11-14b.csv'
R26_TABLE = LANE / 'results/round26-best-2026-11-14.tsv'
CANDIDATE_R27B = S / 'gather/round27-2026-11-15b.csv'
R27_TABLE = LANE / 'results/round27-best-2026-11-15.tsv'""")
s = sub(s, """    if p == CANDIDATE_R26B:
        # Round 28:""", """    if p == CANDIDATE_R27B:
        # Round 29: a row of the held round 27 b file resolves to the take file its round 27 table names, else to round 26 b.
        if n == 801:
            return False, dict(path=str(p), n=n, reason='held801 in round27b: recorded source names the prvsiyan 1105 file')
        row = next((r for r in csv.DictReader(open(R27_TABLE), delimiter='\\t') if int(r['n']) == n), None)
        if row:
            names = re.findall(r'take-[a-z0-9-]+-r\\d+', row.get('take', ''))
            if len(set(names)) != 1:
                return False, dict(path=str(p), n=n, reason='unresolved round27b donor')
            ok, proof = _trace_b(Path(scratch) / names[0] / ('%d.csv' % n), n, scratch, active)
        else:
            ok, proof = _trace_b(CANDIDATE_R26B, n, scratch, active)
        return ok, dict(path=str(p), n=n, parent=proof, reason='round27b row resolved to its recorded donor')
    if p == CANDIDATE_R26B:
        # Round 28:""")
s = sub(s, "                'round26-2026-11-14b.csv')", "                'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv')")
s = sub(s, "        if path in (CANDIDATE, CANDIDATE_B, CANDIDATE_R25B, CANDIDATE_R26B) and n == 801:",
        "        if path in (CANDIDATE, CANDIDATE_B, CANDIDATE_R25B, CANDIDATE_R26B, CANDIDATE_R27B) and n == 801:")
p.write_text(s)

# ---------------------------------------------------------------- follow.py
p = h / 'follow.py'; s = p.read_text()
s = sub(s, "take-%s-r28/[0-9]*.csv", "take-%s-r29/[0-9]*.csv")
s = sub(s, "take-%s-r28/near/**/*.csv", "take-%s-r29/near/**/*.csv")
s = s.replace('frozen round 27', 'frozen round 28')
s = s.replace('deadline05:45Z', 'deadline11:45Z').replace('05:45Z', '11:45Z').replace('05:38Z', '11:38Z').replace('05:53Z', '11:53Z')
p.write_text(s)

# ---------------------------------------------------------------- r28check.py (withdrawal reader)
p = h / 'r28check.py'; s = p.read_text()
s = sub(s, "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log')",
        "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log')   # round 29 adds its own log")
p.write_text(s)

for name in ('setup.sh', 'status.sh', 'verify.sh'):
    p = h / name; p.write_text(p.read_text().replace('squares-soft-r28', 'squares-soft-r29'))
print('configured round 29')
