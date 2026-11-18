from pathlib import Path
import sys,json,csv,time
W=Path(__file__).resolve().parent;S=W.parent.parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True;csv.field_size_limit(1<<28)
import provenance24 as p,admission32 as a,walker30
n=989;A=p.mlp.load(str(S/'gather/round23-2026-11-13b.csv'),{n})[n]
c={'n':n,'origin':'held round23b','sha256_geometry':p.key(n,A),'source':'held round23b','licence':'own held packing; source terms in submitted results table'};assert a.held_binding32(n,A)==23
calls=[];original=walker30.prv_share;oldfail=walker30.pol_fail
walker30.prv_share=lambda *v,**k: (_ for _ in ()).throw(AssertionError('share called on exact held copy'))
walker30.pol_fail=walker30.prv_share
start=time.time();r=a.audit_text(json.dumps(c));assert r,'held989 refused'
walker30.prv_share=original;walker30.pol_fail=oldfail
B=A.copy();B[0,0]+=0.01;assert a.held_binding32(n,B) is None,'changed geometry misidentified as held'
bad={**c,'source':'recorded input prvsiyan/squares-verified-best-of-1105','licence':'CC BY-SA 4.0'}
assert a.audit_text(json.dumps(bad)) is None,'excluded ancestry allowed through held boundary'
result={'n':989,'bound_to_held_round':23,'accepted':True,'share_calls':0,'changed_geometry_not_held':True,'explicit_excluded_ancestry_refused':True,'seconds':time.time()-start}
(W/'historical-held-control32.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
