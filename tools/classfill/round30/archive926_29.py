"""Exact archived source bindings for the saved926 lineage."""
from common29 import *
import numpy as np
import forensics_compose as fc
from light29 import load
from harvest_copy29 import coords,verify_dilation
ARCHIVE={'48bc58a09300393ecd144867bca054a9ec51ddd5c69ebb0a6033975ed4de9007':'989-r23ha62ac3e25767f9f4','56c1c121990850a4dddf0d3a5a3e42c449b4b8a5e23e03e8062d67c394a328f5':'989-r23h9e63aeb8a773e74d','ee7c3cd24175bdd05a9865a475560fc0698dc0d592eb58b17854102781238fd0':'989-r23h36512139ad49d111'}
def framed(p,n):
 a=load(str(p),{n})[n];assert len(a)==n
 _,q=fc.frame(np.asarray(a));return hashlib.sha256(np.round(q,12).tobytes()).hexdigest()
def legacy_record(p):
 p=Path(p);origin=read(str(p)+'.origin.json',{});digest=origin.get('digest')
 if digest not in ARCHIVE:return None
 assert origin['n']==989 and framed(p,989)==digest
 donor=ARCHIVE[digest];archive=S/'take-readers-r23/work/box/donors'/(donor+'.csv');ledger=S/'take-readers-r23/work/sources-all.tsv'
 expected=donor.split('r23h')[1];assert hashlib.sha256(archive.read_bytes()).hexdigest().startswith(expected)
 assert framed(archive,989)==digest
 row=next(r for r in rows(ledger) if r['donor']==donor)
 return dict(n=989,source=row['source'],licence=row['licence'],pins=[p,Path(str(p)+'.origin.json'),archive,ledger])
def exact_wire(p,n,wire):
 fit=verify_dilation(coords(p,n),coords(wire,n));assert fit['scale']==1.0 and fit['error']==0.0
 rec=wire.with_suffix('.json');meta=read(rec);assert meta['n']==n and meta.get('parts')
 return dict(metadata=meta,pins=[p,wire,rec])
