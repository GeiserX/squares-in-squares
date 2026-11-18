"""band lane: certify a layout text file (`n s` / `x y deg`) with the lane's floatsafe (official metric, as written and
after a pandas read, 2.2e-11 clearance). Prints the certified side, or FAIL."""
import sys, os, math
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import floatsafe
def read_txt(path):
    L=[l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n=int(L[0][0]); return n,float(L[0][1]),[[float(v) for v in q[:3]] for q in L[1:n+1]]
def certify(n,X):
    rows=[{'n':str(n),'square_id':str(i),'x':repr(float(x)),'y':repr(float(y)),'angle':repr(math.radians(float(d)))} for i,(x,y,d) in enumerate(X)]
    _,fr,score,e=floatsafe.work((n,rows))
    if fr is None: return None,None
    return (score+1.0)*math.sqrt(n),fr
if __name__=='__main__':
    for p in sys.argv[1:]:
        n,s,X=read_txt(p); L,fr=certify(n,X)
        print(p,'n',n,'model side',s,'certified side',L if L is not None else 'FAIL')
