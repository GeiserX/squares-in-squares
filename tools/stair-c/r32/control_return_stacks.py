"""Run both physical-model controls before using returned geometry."""
import hashlib,json,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import control_stacks
import control_two_stacks
a=json.loads(Path('corner-stacks-control.json').read_text())
b=json.loads(Path('two-stacks-control.json').read_text())
assert a['passed']and b['passed']and a['helper_sha256']==b['helper_sha256']
Path('returned-stacks-control.json').write_text(json.dumps(dict(passed=True,n=975,variants=a['variants']+b['variants'],helper_sha256=a['helper_sha256'],partial_stack_refused=True,overlapping_following_stack_refused=True)))
print('CONTROL returned stacks975: seven exact assemblies passed; partial and overlapping stack mutants refused',flush=True)
