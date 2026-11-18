"""Admit changed rectangle compositions with a complete imported source walk."""
import sys,json,time,csv,hashlib,math,os
sys.dont_write_bytecode=True
from pathlib import Path
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));import run32 as C
sys.path.insert(0,str(C.R));from light29 import load,side
# The imported checker writes its caches only into this lane's work directory.
from source32 import F,controls,output_public
controls()
seen=C.read(W/'fresh-seen.json',{});base,live=C.bars();added=0;now=time.time()
for p in sorted((C.S/'take-forensics-r32/near').glob('*.csv'),key=lambda p:-p.stat().st_mtime):
 try:
  digest=C.sha(p)
  if digest in seen or C.claimed(digest):continue
  meta=C.read(Path(str(p)+'.json'),{})
  if len(meta.get('parts',{}))<2:continue
  # Leave a fresh publication's first follow to backlog and its producer.
  if now-p.stat().st_mtime<600:continue
  n=int(p.name.split('-')[0]);P=load(p,{n})[n];start=side(P)
  if start>(1+live[n])*math.sqrt(n)+.0005:continue
  heldP=load(W/'held'/f'{n}.csv',{n})[n]
  from physical30 import key
  if key(P,decimals=3)==key(heldP,decimals=3):seen[digest]=dict(n=n,reason='unchanged held geometry');continue
  before=C.sha(p)
  if C.withdrawn(before):seen[digest]=dict(n=n,reason='withdrawn bytes');continue
  ok,proof=F.queue_source_check(p,n,C.S,seconds=25)
  if not ok:seen[digest]=dict(n=n,reason=proof.get('reason'),proof=proof);continue
  if C.sha(p)!=before:continue
  proofpath=W/'proofs'/f'fresh-{digest}.json';C.atom(proofpath,dict(path=str(p),sha256=digest,checked_utc=C.now(),clean=True,source_closure=proof,public_first=output_public(proof)))
  record=str(p)+'; own fresh rectangle composition; complete ancestry '+str(proofpath)
  if C.dispatch(n,p,record,'own composition; inherited terms in complete pinned ancestry '+str(proofpath),'fresh-rectangle',2,3301,900,proof=str(proofpath)):
   seen[digest]=dict(n=n,admitted=True,proof=str(proofpath));added+=1
  if added>=2:break
 except Exception as e:
  C.note('FRESH_DEFER '+str(p)+' '+repr(e))
C.atom(W/'fresh-seen.json',seen);C.note('FRESH_SCAN inspected'+str(len(seen))+' added'+str(added));print('FRESH_SCAN',added,flush=True)
