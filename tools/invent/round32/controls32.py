"""Verify held ownership, byte pins, and current-round withdrawal selection."""
import pathlib,sys,json,tempfile
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import source_gate28 as G,public_branch30 as B
j=json.load(open(W/'late989-parent.json'));start=W/j['start']
G.refresh_walker();assert G.Q.LIVE=='32'
assert 'handoff-r32.log'in [p.name for p in G.handoff_logs()]
saved=G.prv_share;share=B.P.share
G.prv_share=lambda *a:(_ for _ in()).throw(AssertionError('owned input received share gate'))
B.P.share=lambda *a:(_ for _ in()).throw(AssertionError('held ancestry received share gate'))
r=G.check(j,start);assert r['clean'],r
G.prv_share=saved;B.P.share=share
bad=G.check(dict(j,evidence_sha256='0'*64),start);assert not bad['clean']
original_logs=G.handoff_logs
with tempfile.TemporaryDirectory(dir=W)as tmp:
 log=pathlib.Path(tmp)/'handoff-r32.log';log.write_text('')
 G.handoff_logs=lambda:[log]
 assert G.check(j,start)['clean']
 snap=next(p for p in json.load(open(j['evidence']))['snapshots']if 'take-'in p['original']and p['original'].endswith('.csv'))
 rel=snap['original'].removeprefix(str(G.S)+'/')
 log.write_text(f'2026-11-16T11:00:00Z test -> all: WITHDRAW n989 source missing proof {rel} sha256={snap["sha256"]}\n')
 assert not G.check(j,start)['clean']
 log.write_text(f'2026-11-16T11:00:00Z test -> all: WITHDRAW n989 source missing proof {rel} sha256={"0"*64}\n')
 assert G.check(j,start)['clean']
G.handoff_logs=original_logs
result=dict(owned_without_share=True,wrong_evidence_refused=True,current_round_withdrawal_selected=True,exact_byte_withdrawal_refused=True,wrong_hash_notice_ignored=True)
(W/'controls32.json').write_text(json.dumps(result))
print(json.dumps(result))
