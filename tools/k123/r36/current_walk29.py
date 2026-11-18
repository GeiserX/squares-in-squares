"""Honor the ownership rule and one explanatory handoff note."""
TARGET='take-stair-c-r17/near/921-29e12ff3.csv'
DATES={'2026-11-13T23:17:11Z','2026-11-14T01:27:36Z'}
def lifted_pair(path,line):
 return path==TARGET and line.split(' ',1)[0] in DATES

def retention_note(line):
 return (line.startswith('2026-11-15T08:40:36Z rebuild -> main: note for the share line:') and 'will withdraw them if you rule otherwise' in line) or line.startswith('2026-11-16T11:24:24Z rebuild -> all: claim: 900 s midm_scan lkick,kick (probe 330 s) of n=911') or line.startswith('2026-11-15T22:19:50.280750+00:00 harvest -> quench,main: PRIORITY safe911 fallback:')

def configure(walker):
 raw=walker.load_withdrawn
 if getattr(raw,'_k123_wrapped29',False):raw=raw._k123_base29
 def load():
  raw()
  walker.WITHDRAWN_LINES[:]=[(p,line) for p,line in walker.WITHDRAWN_LINES if not lifted_pair(p,line) and not retention_note(line)]
 load._k123_wrapped29=True;load._k123_base29=raw
 walker.load_withdrawn=load
 load()
 return walker
