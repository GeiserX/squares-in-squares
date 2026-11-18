"""List fresh certified rows of other lanes (handoff-r31 'certified' lines) that no lane claimed or kicked after the
certification line, older than 10 minutes."""
import re, time, calendar, sys
from pathlib import Path
B=Path('$SCRATCH/bounties-squares')
lines=open(B/'handoff-r31.log',errors='replace').read().splitlines()
def ts(l):
 m=re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)',l)
 return calendar.timegm(time.strptime(m[1],'%Y-%m-%dT%H:%M:%S')) if m else None
now=time.time();out=[]
for i,l in enumerate(lines):
 m=re.match(r'\S+ (\S+) ->',l)
 if not m or m[1]=='twoshort' or not re.search(r'certified',l,re.I):continue
 ns=re.findall(r'\bn ?= ?(\d+)',l)
 if not ns:continue
 n=ns[0];t=ts(l)
 if t is None or now-t<600:continue
 later=[x for x in lines[i+1:] if re.search(r'claim|kick',x,re.I) and re.search(r'\bn ?= ?%s\b'%n,x)]
 if not later:out.append((n,l[:220]))
for n,l in out:print(n,'|',l)
