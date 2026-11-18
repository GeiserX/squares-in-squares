"""Port the shared quench walk's round-33 held-row fixes without replacing lane-specific checks."""
from pathlib import Path
import ast
W=Path(__file__).resolve().parent;Q=Path('quench_walk.py').read_text();p=W/'walker30.py';s=p.read_text()
if 'NOT_WITHDRAW = ' not in s:
 line=next(line for line in Q.splitlines() if line.startswith('NOT_WITHDRAW = '));s=s.replace('\ndef load_withdrawn():','\n'+line+'\n\ndef load_withdrawn():')
 needle='            # case-insensitive since round 27:'
 s=s.replace(needle,"            if NOT_WITHDRAW.search(_l) and not re.search(r'WITHDR|WITHH[EO]LD', _l):\n                continue\n"+needle)
if 'HELD_PIN = ' not in s:
 block=Q[Q.index('HELD_PIN = {}'):Q.index('def norm(',Q.index('HELD_PIN = {}'))];s=s.replace('def norm(',block+'def norm(',1)
old="""                    up, held_chain = p, False
                    for _ in range(60):
                        up = via.get(up)
                        if up is None:
                            break
                        if isinstance(up, tuple) and up[0] == 'held':
                            held_chain = True; break"""
assert old in s;s=s.replace(old,"                    held_chain = _through_held(p, via)")
needle="        for f in seen:\n            if not isinstance(f, str):\n                continue\n            if through_held(f):"
assert needle in s;s=s.replace(needle,"        for f in seen:\n            if not isinstance(f, str):\n                continue\n            if held_bytes(f):continue\n            if through_held(f):")
ast.parse(s);p.write_text(s)
p=W/'policy27.py';s=p.read_text().replace("  if p in text:\n   from replacements25 import allowed", "  if p in text:\n   if hasattr(quench_walk,'held_bytes') and quench_walk.held_bytes(str(S/p)):continue\n   from replacements25 import allowed");ast.parse(s);p.write_text(s)
for name in ['source25.py','stage24.py','collect22.py']:
 p=W/name;p.write_text(p.read_text().replace('r33-scoped-walk-v2','r33-held-path-walk-v3'))
(W/'restart-stage28').touch();(W/'restart-collect25').touch()
print('ported 45dd8ad held-chain/claim/held-byte fixes; kept scoped registry, walk-cap and public-output gates')
