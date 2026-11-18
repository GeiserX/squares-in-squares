"""Round 31, second step (after configure31.py): the public-first rule of the round 30 assembler.

The round 30 assembler dropped our 910 (and backlog's 972): a soft-box search from forensics warm partners whose roots are
public files (take-harvest-r26/850.csv, take-harvest-r26/972.csv) with no held row in the tree, and an ICP share of 0.456
at 1e-2 against the prvsiyan 1105 row. Measured at 19:55Z on the 17 round 30 soft near files: 17 of 17 read 0.47 to 0.93
at 1e-2. So a public-first tree that reaches no held row cannot give a row, and such a start is refused at admission.
A row whose tree reaches a held row (a row of a submitted file) is our own layout: no share test (main 12:40:55Z ruling,
round 31 rule 2). The output share test stays for a public-first row that reaches no held row.
"""
from pathlib import Path
h = Path('tools/softround')


def sub(s, a, b, count=None):
    if a not in s:
        raise SystemExit('pattern missing: ' + a[:120])
    return s.replace(a, b) if count is None else s.replace(a, b, count)


p = h / 'ctl.py'; s = p.read_text()
s = sub(s, """    if n in OUT_N:
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n""",
        """    if proof['ok']:
        import r28check
        if r28check.public_first(proof, path) and not reaches_held(proof, path):
            LAST_ADMISSION_REASON = 'round 31: public-first tree with no held row (round 30 assembler dropped 910 and 972 at 1e-2)'
            print('REFUSE', path, LAST_ADMISSION_REASON, flush=True)
            return False
    if n in OUT_N:
        LAST_ADMISSION_REASON = 'round 31: n=%d public-first rows dropped by the round 29 and 30 skeptics at 1e-2' % n""")
s = sub(s, """        why = prv_share_out(n, '%s/cert/%s.csv' % (W, md5)) if r28check.public_first(anc, j.get('path', '')) else None""",
        """        why = prv_share_out(n, '%s/cert/%s.csv' % (W, md5)) if (r28check.public_first(anc, j.get('path', ''))
                                                                and not reaches_held(anc, j.get('path', ''))) else None""")
s = sub(s, """OUT_N = (582, 972)""", """OUT_N = (582, 972)
HELD_MARKS = ('round23-2026-11-13a.csv', 'round23-2026-11-13b.csv', 'round24-2026-11-13a.csv', 'round25-2026-11-14b.csv',
              'round26-2026-11-14b.csv', 'round27-2026-11-15b.csv', 'round28-2026-11-15b.csv', 'round29-2026-11-15b.csv',
              'round30-2026-11-15c.csv')


def reaches_held(proof, path=None):
    \"\"\"True when the trace names a held file (a row of a file we submitted): our own layout, no share test.\"\"\"
    text = json.dumps(proof, default=str) + ' ' + (path or '')
    return any(m in text for m in HELD_MARKS)""")
p.write_text(s)
print('configured round 31 b')
