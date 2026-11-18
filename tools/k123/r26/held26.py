"""Resolve recorded held references with the assembler-compatible quench walker."""
import sys,functools
sys.dont_write_bytecode=True
sys.path.insert(0,'.')
import quench_walk as walker
@functools.lru_cache(None)
def resolve(n,round_number):
 return walker.held(n,round_number)
def edges(text):
 out=set()
 for rx,flip in walker.HELD:
  for g in rx.findall(text):
   a,b=(g[1],g[0]) if flip else (g[0],g[1]);n=int(a);k=int(b) if b else None
   if 1<=n<=1000:out.add((n,k))
 return out
