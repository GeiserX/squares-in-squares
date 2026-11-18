"""Explain one source refusal without changing its admission decision."""
import pathlib,sys,json
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,legacy_credit,banned
from seed_notice24 import notice
path=sys.argv[1];n=int(sys.argv[2]);A=mlp.load(path,{n})[n];c=legacy_credit(n,A,path)
print('legacy',bool(c),flush=True)
if not c:raise SystemExit
print('root',banned(json.dumps(c)),notice(c['source'],c['licence'])[0],flush=True)
(W/f'debug-{n}-root26.json').write_text(json.dumps(c))
s=(W/'source25.py').read_text().replace("  if banned(t) or notice(t,'')[1] is not False:return None", "  if banned(t) or notice(t,'')[1] is not False:\n   print('node refused',banned(t),notice(t,'')[0],flush=True)\n   (W/f'debug-{N}-node26.json').write_text(t)\n   return None")
lines=s.splitlines()
for i,l in enumerate(lines):
 if 'return None' in l and i<100:lines[i]=l.replace('return None',f"print('REFUSE line {i+1}',str(locals().get('bare',locals().get('pp','')))[:180],flush=True);return None")
ns={'__name__':'debugsource','N':n};exec('\n'.join(lines),ns)
result=ns['audit_text'](json.dumps(c));print('accepted',bool(result),flush=True)
