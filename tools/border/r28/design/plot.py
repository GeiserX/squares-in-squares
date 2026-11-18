import csv,math,sys,collections
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
src=sys.argv[1];ns=[int(x) for x in sys.argv[2].split(',')]
by=collections.defaultdict(list)
for r in csv.DictReader(open(src)):
    n=int(r['n'])
    if n in ns:by[n].append((float(r['x']),float(r['y']),float(r['angle'])))
for n in ns:
    sq=by[n];fig,ax=plt.subplots(figsize=(10,10),facecolor='#111')
    ax.set_facecolor('#111')
    for x,y,a in sq:
        c,s=math.cos(a),math.sin(a);pts=[(x+c*u-s*v,y+s*u+c*v) for u,v in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5))]
        d=abs(((math.degrees(a)%90)+45)%90-45)
        ax.add_patch(Polygon(pts,closed=True,fc=('#3a6' if d<1e-6 else '#e84'),ec='#000',lw=.3))
    xs=[x for x,y,a in sq];ax.set_xlim(min(xs)-1,max(xs)+1);ax.set_ylim(min(xs)-1,max(xs)+1);ax.set_aspect('equal')
    ax.tick_params(colors='#aaa')
    fig.savefig(f'{n}.png',dpi=70,facecolor='#111');plt.close(fig)
