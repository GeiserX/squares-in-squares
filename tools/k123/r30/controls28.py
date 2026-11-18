import pathlib,sys,json,time
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp,credit,S
from policy27 import share
from seed_rule27 import check_numbers
out={'seeds':check_numbers([503,811,861,983]),'source':[]}
assert [r['excluded'] for r in out['seeds']]==[False,False,False,False],out
for n,path,expect in [(752,'take-k123-r27/752.csv',True),(753,'take-k123-r27/753.csv',True),(742,'take-harvest-r22/742.csv',False),(684,'take-forensics-r24/work/donors/684-6d78315914dc85da2cb4.csv',True)]:
 p=S/path;A=mlp.load(str(p),{n})[n];ss=share(n,A) if n==742 else None;c=credit(n,A,str(p));out['source'].append({'n':n,'path':str(p),'share':ss,'accepted':bool(c)});assert (bool(c)==expect) if n!=684 else (__import__('csv_rule27').one(p)['excluded'] is False),out
(W/'controls28.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH source controls: allow own752/753/684 and own original seeds; reject fetched harvest742 under new00:19:03Z rule. Proof work/controls28.json. Deadline17:45Z.\n')
