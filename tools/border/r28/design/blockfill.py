"""Tilted block plus upright fill (border r28 design, m*m+k counts).
A block of a x b unit squares turned by theta sits in the box [0,W] x [0,H] (W = S - p after p full upright columns
at the right wall, H = S). Every other square is upright, in unit rows: rows 0..J-1 sit on the bottom wall, the other
floor(H)-J rows hang from the top wall. In a row the uprights run from the left wall to the block and from the block
to the right wall. count(config, S) is the number of squares; layout() writes the squares (centre x, y, angle rad)."""
import math, numpy as np
EPS=1e-9
def corners(cx,cy,a,b,t):
    c,s=math.cos(t),math.sin(t)
    return [(cx+c*u-s*v,cy+s*u+c*v) for u,v in ((-a/2,-b/2),(a/2,-b/2),(a/2,b/2),(-a/2,b/2))]
def slab_x(poly,y0,y1):
    """x-range of the convex polygon inside the slab y0<=y<=y1, or None."""
    pts=[]
    n=len(poly)
    for i in range(n):
        (x0,ya),(x1,yb)=poly[i],poly[(i+1)%n]
        if y0<=ya<=y1:pts.append(x0)
        for yy in (y0,y1):
            if (ya-yy)*(yb-yy)<0:
                pts.append(x0+(x1-x0)*(yy-ya)/(yb-ya))
    if not pts:
        return None
    return min(pts),max(pts)
def rows_count(poly,W,H):
    """best split J: list of (count, J, per-row details)"""
    R=int(math.floor(H+EPS))
    full=int(math.floor(W+EPS))
    def row(y0):
        r=slab_x(poly,y0,y0+1)
        if r is None:return full,(None,)
        xl,xr=r
        return int(math.floor(xl+EPS))+int(math.floor(W-xr+EPS)),(xl,xr)
    bot=[row(j)[0] for j in range(R)]
    top=[row(H-1-t)[0] for t in range(R)]
    best=(-1,0)
    cb=np.concatenate([[0],np.cumsum(bot)]);ct=np.concatenate([[0],np.cumsum(top)])
    for J in range(R+1):
        v=cb[J]+ct[R-J]
        if v>best[0]:best=(int(v),J)
    return best
def count(S,a,b,t,cx,cy,p):
    W=S-p;H=S
    poly=corners(cx,cy,a,b,t)
    xs=[x for x,y in poly];ys=[y for x,y in poly]
    if min(xs)<-EPS or max(xs)>W+EPS or min(ys)<-EPS or max(ys)>H+EPS:return -1,0
    v,J=rows_count(poly,W,H)
    return a*b+p*int(math.floor(H+EPS))+v,J
def layout(S,a,b,t,cx,cy,p,J):
    W=S-p;H=S;out=[]
    c,s=math.cos(t),math.sin(t)
    for i in range(a):
        for j in range(b):
            u=i-(a-1)/2;v=j-(b-1)/2
            out.append((cx+c*u-s*v,cy+s*u+c*v,t))
    for q in range(p):
        x=S-0.5-q
        for k in range(int(math.floor(H+EPS))):out.append((x,0.5+k,0.0))
    poly=corners(cx,cy,a,b,t)
    R=int(math.floor(H+EPS));full=int(math.floor(W+EPS))
    ys=[j for j in range(J)]+[H-1-t2 for t2 in range(R-J)]
    for y0 in ys:
        r=slab_x(poly,y0,y0+1)
        if r is None:
            for k in range(full):out.append((0.5+k,y0+0.5,0.0))
            continue
        xl,xr=r
        for k in range(int(math.floor(xl+EPS))):out.append((0.5+k,y0+0.5,0.0))
        for k in range(int(math.floor(W-xr+EPS))):out.append((W-0.5-k,y0+0.5,0.0))
    return out
