"""structure lane: load a submission CSV (angles in radians), bounding side, angle folding, dark renderer."""
import os
import csv, math, collections
BEST=os.environ.get('SQUARES_BEST','$SCRATCH/bounties-squares/gather/assembled-2026-11-09d-safe.csv')
def load(path=BEST):
    P=collections.defaultdict(list)
    with open(path) as f:
        r=csv.reader(f); next(r)
        for row in r:
            P[int(row[1])].append((float(row[3]),float(row[4]),float(row[5])))
    return P
def hw(a):
    t=a; return (abs(math.cos(t))+abs(math.sin(t)))/2
def bbox(sq):
    x0=min(x-hw(a) for x,y,a in sq); x1=max(x+hw(a) for x,y,a in sq)
    y0=min(y-hw(a) for x,y,a in sq); y1=max(y+hw(a) for x,y,a in sq)
    return x0,y0,x1,y1
def side(sq):
    x0,y0,x1,y1=bbox(sq); return max(x1-x0,y1-y0)
def norm(a):
    a=math.degrees(a)%90.0
    return a if a<=45 else a-90
def draw(sq,fn,title=''):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    x0,y0,x1,y1=bbox(sq)
    fig,ax=plt.subplots(figsize=(11,11)); fig.patch.set_facecolor('#111'); ax.set_facecolor('#111')
    for x,y,a in sq:
        t=a; c,s=math.cos(t)/2,math.sin(t)/2
        pts=[(x+c-s,y+s+c),(x-c-s,y-s+c),(x-c+s,y-s-c),(x+c+s,y+s-c)]
        na=abs(norm(a))
        col='#345' if na<1e-6 else plt.cm.plasma(min(1,na/45+0.2))
        ax.add_patch(Polygon(pts,closed=True,fc=col,ec='#ccc',lw=0.3))
    ax.set_xlim(x0,x0+max(x1-x0,y1-y0)); ax.set_ylim(y0,y0+max(x1-x0,y1-y0)); ax.set_aspect('equal'); ax.set_title(title,color='w'); ax.axis('off')
    fig.savefig(fn,dpi=110,bbox_inches='tight'); plt.close(fig)
