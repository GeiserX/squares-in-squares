"""Round 30 settings for tools/softround (own lane tools only).

Changes against round 29:
  1. round 30 names (take dir, box scratch, follow dirs take-*-r30, deadlines 17:38Z search, 17:45Z jobs, 17:53Z collect);
  2. the held file is gather/round28-2026-11-15b.csv (gate cand-round28-1115b, Kaggle ref 58375092); a row of it resolves
     to the take file that results/round28-best-2026-11-15.tsv names, else to the round 27 b logic; the base bar is
     bar30.tsv (work/base-extra.json holds its rows from r29 takes);
  3. held 801 is open (round 30 rule 3: the 801 row is our own layout); its recorded root text no longer refuses a trace;
  4. withdrawals read from handoff-r27 to r30 logs.
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


# ---------------------------------------------------------------- ctl.py
p = h / 'ctl.py'; s = p.read_text()
s = sub(s, 'RN = 29', 'RN = 30')
s = sub(s, "take-soft-r28/work'", "take-soft-r29/work'")
s = sub(s, "HELD_FILE = S + '/gather/round27-2026-11-15b.csv'; GATE = S + '/gate/cand-round27-1115b'",
        "HELD_FILE = S + '/gather/round28-2026-11-15b.csv'; GATE = S + '/gate/cand-round28-1115b'")
s = sub(s, "BEST_TSV = LANE + '/results/round27-best-2026-11-15.tsv'", "BEST_TSV = LANE + '/results/round28-best-2026-11-15.tsv'")
s = sub(s, 'squares-soft-r29', 'squares-soft-r30')
s = sub(s, "for r in ('29',)", "for r in ('30',)")
s = sub(s, "# round 29 budget: processes per box", "# round 30 budget: processes per box")
s = sub(s, '# Round 29 follows fresh geometry with a clean ancestry record.', '# Round 30 follows fresh geometry with a clean ancestry record.')
s = sub(s, 'soft-r29.csv', 'soft-r30.csv')
s = s.replace('deadline 11:45Z', 'deadline 17:45Z')
p.write_text(s)

# ---------------------------------------------------------------- provenance.py
p = h / 'provenance.py'; s = p.read_text()
s = sub(s, "rnd = int(rnd[1]) if rnd else 29", "rnd = int(rnd[1]) if rnd else 30")
s = sub(s, """CANDIDATE_R27B = S / 'gather/round27-2026-11-15b.csv'
R27_TABLE = LANE / 'results/round27-best-2026-11-15.tsv'""", """CANDIDATE_R27B = S / 'gather/round27-2026-11-15b.csv'
R27_TABLE = LANE / 'results/round27-best-2026-11-15.tsv'
CANDIDATE_R28B = S / 'gather/round28-2026-11-15b.csv'
R28_TABLE = LANE / 'results/round28-best-2026-11-15.tsv'""")
s = sub(s, """    if p == CANDIDATE_R27B:
        # Round 29:""", """    if p == CANDIDATE_R28B:
        # Round 30: a row of the held round 28 b file resolves to the take file its round 28 table names, else to round 27 b.
        row = next((r for r in csv.DictReader(open(R28_TABLE), delimiter='\\t') if int(r['n']) == n), None)
        if row:
            names = re.findall(r'take-[a-z0-9-]+-r\\d+', row.get('take', ''))
            if len(set(names)) != 1:
                return False, dict(path=str(p), n=n, reason='unresolved round28b donor')
            ok, proof = _trace_b(Path(scratch) / names[0] / ('%d.csv' % n), n, scratch, active)
        else:
            ok, proof = _trace_b(CANDIDATE_R27B, n, scratch, active)
        return ok, dict(path=str(p), n=n, parent=proof, reason='round28b row resolved to its recorded donor')
    if p == CANDIDATE_R27B:
        # Round 29:""")
# Round 30 rule 3: the 801 row is our own layout. The held 801 is open as a root in every held file.
s = sub(s, """        if n == 801:
            return False, dict(path=str(p), n=n, reason='held801 in round27b: recorded source names the prvsiyan 1105 file')
""", "")
s = sub(s, """        if n == 801:
            return False, dict(path=str(p), n=n, reason='prohibited held801 in round26b')
""", "")
s = sub(s, """        if n == 801:
            return False, dict(path=str(p), n=n, reason='prohibited held801 in round25b')
""", "")
s = sub(s, "        if n in (801, 907):\n", "        if n in (907,):          # round 30: held 801 is ours (rule 3)\n")
s = sub(s, "                'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv')",
        "                'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv', 'round28-2026-11-15b.csv')")
s = sub(s, """    if 801 in roots:
        return 'held 801 (prvsiyan, CC BY-SA) in ancestry'
""", """    roots.discard(801)        # round 30 rule 3: the 801 row is our own layout; its old root text is not read as a marker
""")
s = sub(s, """        if path in (CANDIDATE, CANDIDATE_B, CANDIDATE_R25B, CANDIDATE_R26B, CANDIDATE_R27B) and n == 801:
            return dict(ok=False, reason='held n801 is excluded as a donor', path=str(path), n=n)
""", "")
s = sub(s, """        if excluded_held(detail):
            ok = False""", """        if False and excluded_held(detail):     # round 30 rule 3: held 801 is ours
            ok = False""")
p.write_text(s)

# ---------------------------------------------------------------- follow.py
p = h / 'follow.py'; s = p.read_text()
s = sub(s, "take-%s-r29/[0-9]*.csv", "take-%s-r30/[0-9]*.csv")
s = sub(s, "take-%s-r29/near/**/*.csv", "take-%s-r30/near/**/*.csv")
s = s.replace('frozen round 28', 'frozen round 29')
s = s.replace('deadline11:45Z', 'deadline17:45Z').replace('11:45Z', '17:45Z').replace('11:38Z', '17:38Z').replace('11:53Z', '17:53Z')
p.write_text(s)

# ---------------------------------------------------------------- r28check.py (withdrawal reader)
p = h / 'r28check.py'; s = p.read_text()
s = sub(s, "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log')   # round 29 adds its own log",
        "LOGS = (S + '/handoff-r27.log', S + '/handoff-r28.log', S + '/handoff-r29.log', S + '/handoff-r30.log')   # round 30 adds its own log")
p.write_text(s)

for name in ('setup.sh', 'status.sh', 'verify.sh'):
    p = h / name; p.write_text(p.read_text().replace('squares-soft-r29', 'squares-soft-r30'))
print('configured round 30')
