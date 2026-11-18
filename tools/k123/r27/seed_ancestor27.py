"""Check concrete original-seed ancestors under the round27 share rule."""
import pathlib,sys,re,json,csv,time
sys.dont_write_bytecode=True
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent
sys.path[:0]=[str(W),'.',str(W/'lane')]
import quench_walk,policy27,methods_lp as mlp
rx=re.compile(r'(?:original seed:\s*n\s*=\s*(\d+)\s+of|n\s*=\s*(\d+)\s+of\s+(?:Samanyu-dev/squares_in_squares|franciscouzo/square-packing))',re.I)
rows=list(csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'));allns=set();found={}
for row in rows:
 n=int(row['n']);texts,missing,seen,helds,refused=quench_walk.walk(str(W.parent/f'{n}.csv'),n)
 ns={int(a or b) for _,t in texts for a,b in rx.findall(t)};allns|=ns;found[n]=sorted(ns)
P=mlp.load(str(S/'seeds/merged0.csv'),allns|{983,861});shares={n:policy27.share(n,A) for n,A in P.items()}
assert abs(shares[983]-0.5503560528992879)<1e-12 and shares[861]==0,shares
out={'time':time.strftime('%FT%TZ',time.gmtime()),'positive_seed983_share':shares[983],'allowed_seed861_share':shares[861],'rows':[{ 'n':n,'seeds':[{'n':k,'share':shares.get(k)} for k in ns],'excluded':[k for k in ns if shares.get(k,0)>=.4]} for n,ns in found.items()]}
(W/'seed-ancestors27.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
