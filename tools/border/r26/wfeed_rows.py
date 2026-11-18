import csv,math
def window_rows(path,a,b,s,c):
 rows=list(csv.DictReader(open(path)))
 P=[(float(r['x']),float(r['y']),float(r['angle'])) for r in rows]
 pick=[]
 for x,y,t in P:
  h=(abs(math.cos(t))+abs(math.sin(t)))/2
  if x-h>=a-1e-12 and y-h>=b-1e-12 and x+h<=a+s+1e-12 and y+h<=b+s+1e-12:pick.append((x,y,t))
 pick=pick[:c]
 if len(pick)!=c:return None
 return [dict(n=str(c),square_id=str(i),x=repr(x-a),y=repr(y-b),angle=repr(t)) for i,(x,y,t) in enumerate(pick)]
