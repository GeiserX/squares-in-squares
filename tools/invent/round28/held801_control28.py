import pathlib,sys,csv,json,hashlib
W=pathlib.Path(__file__).resolve().parent;S=W.parents[1];sys.path.insert(0,str(W))
p=W/'held801-control.csv'
with open(S/'gather/round26-2026-11-14b.csv')as stream:
 reader=csv.DictReader(stream);fields=reader.fieldnames;rows=[v for v in reader if v['n']=='801']
assert len(rows)==801
with p.open('w',newline='')as stream:
 writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
import ancestry28 as A,source_gate28 as G
r,ledger=A.POL.held_record(801,26);assert 'own construction'in r['source']
assert A.rejected('prvsiyan/squares-verified-best-of-1105 :: submission.csv','CC BY-SA 4.0')
r802,l802=A.POL.held_record(802,26);old802,oldl=A._original_held_record(802,26);assert(r802,l802)==(old802,oldl)
a=A.audit(p,801,'held n = 801 of round 26',r['licence']);assert a['ok'],a
v=G.freeze(p,801,a['proof']);assert v['clean'],v
result=dict(graph_ok=a['ok'],full_walk=v,direct_public_by_sa_refused=True,unrelated_held802_unchanged=True,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(W/'held801-control.json').write_text(json.dumps(result));print(json.dumps(result),flush=True)
