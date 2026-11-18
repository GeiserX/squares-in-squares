"""Verify SHA-bound source wrappers before retrying the new three-way geometry."""
import pathlib,json,sys,copy
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import ancestry28 as A
S=W.parents[1];p=S/'take-k123-r32/work/ancestry/fb707dd0b3e35307e83a841bc810d66d4feae293214ec70f28c9313b855adf1c.json';d=json.load(open(p));assert A.captured_record(d,d['source'],d['licence'],str(p))==str(p)
bad=copy.deepcopy(d);bad['layout']['ancestry_sha256']='0'*64
assert A.captured_record(bad,bad['source'],bad['licence'],str(p))is None
wrong_count=copy.deepcopy(d);wrong_count['layout']['n']=448
assert A.captured_record(wrong_count,wrong_count['source'],wrong_count['licence'],str(p))is None
assert __import__('source_gate28').banned('prvsiyan/squares-verified-best-of-1105')
a=A.audit(S/'take-k123-r32/near/367-threeway28-f159a52bca3abcc5.csv',367);print(json.dumps(a)[:2200]);assert a['ok'],a
result=dict(actual_held_wrapper_uses_pinned_source=True,wrong_ancestry_hash_refused=True,wrong_count_refused=True,literal_1105_refused=True,actual367_graph_closes=True);(W/'controls-wrapper32.json').write_text(json.dumps(result));print(json.dumps(result))
