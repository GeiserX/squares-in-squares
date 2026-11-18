from common29 import *
from public_review30 import review_ref
from light29 import load
passed=[]
for ref,n,member in [('kmmmvs/squares-in-squares-private-packings',931,'local_bank.csv'),('busyaprime/squares-in-squares-fq-quenched-packings',501,'packings.csv')]:
 path=S/'harvest/ds'/ref.replace('/','__')/'data.zip'
 result=review_ref(ref,n,[str(path)])
 assert len(result['variants'])==1,(ref,result)
 v=result['variants'][0];assert v['member']==member and len(load(v['row']['snapshot'],{n})[n])==n
 negative=review_ref(ref,1001,[str(path)]);assert not negative['complete'] and not negative['variants']
 passed.append(dict(ref=ref,n=n,member=member,share=v['share'],positive='exact count parsed from named member',negative='absent count unapproved',archive_sha256=v['archive']['sha256']))
 print(passed[-1],flush=True)
atomic(W/'member-controls30.json',dict(passed=True,checks=passed));note('CONTROL named CSV member adapters PASS: exact931 local_bank and501 packings read; absent1001 remains unapproved. Share gates and exact-version requirements unchanged.')
