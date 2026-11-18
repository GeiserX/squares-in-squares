from common28 import *
# Only an explicit leading withdrawal directive adds a hold. Retention notes do not.
def withdrawn(line):
 m=re.search(r'->[^:]+:\s*WITHDRAW\b',line)
 if not m:return []
 text=line[m.end():]
 if re.search(r'share|similarity',text,re.I) and not re.search(r'prvsiyan/squares-verified-best-of-1105',text):return []
 return sorted(set(re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/(?:near/|work/)?[^\s;,()<>]+\.csv',text)))
if sys.argv[1:]==['--control']:
 assert withdrawn('t x -> all: not the withheld take-a-r27/12.csv')==[]
 assert withdrawn('t x -> all: keeps take-a-r27/12.csv')==[]
 assert withdrawn('t x -> all: WITHDRAW take-a-r27/12.csv (bad donor)')==['take-a-r27/12.csv']
 print('WITHDRAW_CONTROL_PASS retention notes ignored; explicit directive retained')
 raise SystemExit()
holds=read(W/'source-holds.json',{});changes=0
for line in (S/'handoff-r28.log').read_text().splitlines():
 for p in withdrawn(line):
  # Normalize the short relative form so either citation form is matched.
  p=p.removeprefix(str(S)+'/')
  if p not in holds:holds[p]=dict(reason='explicit round28 withdrawal',line=line);changes+=1
if changes:atomic(W/'source-holds.json',holds);note(f'SOURCE_HOLDS add{changes} explicit round28 withdrawals')
