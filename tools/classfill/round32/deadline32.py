"""Keep the final admission window inside the search and archive deadlines."""
import sys,time
from pathlib import Path
W=Path(__file__).parent;sys.path.insert(0,str(W));import run32 as C

def controls():
 assert C.bounded_seconds(900,C.END-1801)==900
 assert C.bounded_seconds(900,C.END-1800)==180
 assert C.bounded_seconds(150,C.END-1700)==150
 saved=C.ADMIT_UNTIL
 try:
  C.ADMIT_UNTIL=time.time()-1
  assert not C.dispatch(849,Path('/nonexistent/deadline-control.csv'),'control','own',kind='own-control')
 finally:C.ADMIT_UNTIL=saved
 assert C.ADMIT_UNTIL+180+400<C.END-420
 print('DEADLINE_CONTROL_PASS 900s before16:45, cap180s after16:45, expired admission refused before reading input; latest job wall ends before17:08')
 C.atom(W/'deadline-controls.json',dict(time=C.now(),passed=True,admit_until=C.ADMIT_UNTIL,last_wall=C.ADMIT_UNTIL+580,archive_stop=C.END-420))
if __name__=='__main__':controls()
