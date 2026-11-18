import pathlib,sys,json
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import legacy_credit,S,mlp
p=S/'take-k123-r26/580.csv';A=mlp.load(str(p),{580})[580];c=legacy_credit(580,A,str(p));print('legacy',bool(c),flush=True)
s=(W/'source25.py').read_text();ns={'__name__':'debugsource'}
lines=s.splitlines()
for i,l in enumerate(lines):
 if 'return None' in l and i<100:lines[i]=l.replace('return None',f"print('REFUSE at source25 line {i+1}',str(locals().get('node',locals().get('c','')))[:150],flush=True);return None")
exec('\n'.join(lines),ns)
r=ns['audit_text'](json.dumps(c));print('audit accepted',bool(r),flush=True)
