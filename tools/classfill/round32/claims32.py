"""Check external reservations even when our own claim appears first."""
import sys,datetime
from pathlib import Path
W=Path(__file__).parent;sys.path.insert(0,str(W));import run32 as C

def controls():
 now=datetime.datetime.now(datetime.timezone.utc);fmt=lambda d:d.strftime('%Y-%m-%dT%H:%M:%SZ');digest='a1'*32
 own=fmt(now)+' classfill -> all: claims sha256 '+digest
 other=fmt(now)+' backlog -> classfill: claims sha256 '+digest
 expired=fmt(now-datetime.timedelta(hours=2))+' backlog -> classfill: claims sha256 '+digest
 cutoff=now.timestamp()-3600
 assert C.claim_from([own,other],digest,cutoff)==other
 assert C.claim_from([other,own],digest,cutoff)==other
 assert C.claim_from([expired,own],digest,cutoff)==own
 assert C.claim_from([own,other],'b2'*32,cutoff) is None
 print('CLAIM_ORDER_CONTROL_PASS external reservation wins in both log orders; expired and different-byte claims do not block')

def audit():
 lines=(C.S/'handoff-r32.log').read_text().splitlines();issues=[]
 for p in (W/'jobs').glob('*.json'):
  j=C.read(p)
  if j.get('n',0)<=40:continue
  stamp=datetime.datetime.fromisoformat(j['created_utc'].replace('Z','+00:00')).timestamp()
  prior=[]
  for line in lines:
   try:at=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
   except (ValueError,IndexError):continue
   if at<=stamp:prior.append(line)
  claim=C.claim_from(prior,j['input_sha256'],stamp-3600)
  if claim and ' classfill -> ' not in claim:issues.append(dict(job=str(p),created=j['created_utc'],claim=claim))
 C.atom(W/'claim-order-audit.json',dict(time=C.now(),jobs=len(list((W/'jobs').glob('*.json'))),violations=issues))
 print('CLAIM_HISTORY_AUDIT',len(issues),'external reservations were bypassed')
 return issues
if __name__=='__main__':controls();audit()
