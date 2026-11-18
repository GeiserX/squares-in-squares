from common29 import *
def withdrawn(line):
 m=re.search(r'->[^:]+:\s*WITHDRAW\b',line)
 if not m:return []
 text=line[m.end():]
 if re.search(r'share|similarity',text,re.I) and not re.search(r'public[- ]first|first[- ]public|SOURCE_NOTICES|prvsiyan/squares-verified-best-of-1105',text,re.I):return []
 return sorted(set(re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/(?:near/|work/)?[^\s;,()<>]+\.csv',text)))
if sys.argv[1:]==['--control']:
 assert withdrawn('t x -> all: not the withheld take-a-r27/12.csv')==[]
 assert withdrawn('t x -> all: keeps take-a-r27/12.csv')==[]
 assert withdrawn('t x -> all: WITHDRAW take-a-r27/12.csv (bad donor)')==['take-a-r27/12.csv']
 print('WITHDRAW_CONTROL_PASS');raise SystemExit()
holds=read(W/'source-holds.json',{});seen=set(read(W/'withdrawal-events.json',[]));changes=0
for line in (S/'handoff-r30.log').read_text().splitlines():
 event=hashlib.sha256(line.encode()).hexdigest()
 if event in seen:continue
 if re.search(r'->[^:]+:\s*(?:REINSTATE|REOPEN)\b',line):
  for path in re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/(?:near/|work/)?[^\s;,()<>]+\.csv',line):
   path=path.removeprefix(str(S)+'/')
   if path in holds:del holds[path];changes+=1
 for path in withdrawn(line):
  path=path.removeprefix(str(S)+'/')
  if path in holds:continue
  full=S/path;match=re.search(r'(?i)(?:sha256|sha|hash)[=: ]+([0-9a-f]{12,64})',line)
  digest=match[1].lower() if match else (hashlib.sha256(full.read_bytes()).hexdigest() if full.is_file() else None)
  if digest is None:
   state=S/path.split('/')[0]/'STATE.txt'
   if state.is_file():
    for record in state.read_text().splitlines():
     if path in record:
      match=re.search(r'(?i)sha256[ =:]+([0-9a-f]{12,64})',record)
      if match:digest=match[1].lower()
  holds[path]=dict(reason='explicit round29 withdrawal of pinned bytes',line=line,sha256=digest);changes+=1
 seen.add(event)
atomic(W/'withdrawal-events.json',sorted(seen))
if changes:atomic(W/'source-holds.json',holds);note(f'SOURCE_HOLDS changed{changes} explicit byte events and reinstatements')
