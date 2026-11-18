import csv,json,pathlib,sys,hashlib
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import source_gate28 as G
G.refresh_walker()
assert G.Q.LIVE=='29'
own=G.prv_share(W/'starts/control907.csv',907)
p=W/'share-control.csv'
with p.open('w',newline='')as stream:
 writer=csv.DictWriter(stream,fieldnames=['n','x','y']);writer.writeheader();writer.writerows(dict(n=907,**row)for row in G._prv[907])
exact=G.prv_share(p,907);assert exact==1.0 and own<.4
bad=G.S/'take-forensics-r24/work/donors/684-6d78315914dc85da2cb4.csv'
badshare=G.prv_share(bad,684);assert badshare>=.4
assert not G.public_first(bad,{})
assert G.public_first(G.S/'take-harvest-r28/684.csv',{})
assert G.lifted_policy('WITHDRAW our910: ancestor684 prvsiyan share 1.0')
assert not G.lifted_policy('WITHDRAW actual prvsiyan/squares-verified-best-of-1105 input')
assert G.banned('prvsiyan/squares-verified-best-of-1105')
assert not G.Q.NAMES.search('held n = 801')
result=dict(own907_share=own,excluded907_share=exact,own_ancestor684_share=badshare,own_ancestor_share_gate=False,public_first_share_gate=True,retention_note_refused=False,actual_withdrawal_detected=True,live_round=G.Q.LIVE)
(W/'source-controls.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
