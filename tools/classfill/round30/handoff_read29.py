from common29 import *
seen=set(read(W/'addressed-seen.json',[]));new=[]
for line in (S/'handoff-r30.log').read_text().splitlines():
 if line in seen:continue
 seen.add(line)
 if re.search(r'->[^:]*classfill|main ->|RULE CHANGE',line):new.append(line)
atomic(W/'addressed-seen.json',sorted(seen))
for line in new[-12:]:print(line)
