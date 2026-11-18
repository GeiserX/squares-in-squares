"""structure lane: straight tilted-row slot clipped to the container, exact upright fill (Evan Daniel's fillfast, MIT, imported from his clone)."""
import sys, os, math, time
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import numpy as np, fillfast
def slot_rows(L, c, th, xoff, Y0, x_lo=0.0, y_lo=0.0, y_hi=None):
    """rows of c unit squares tilted th (rad), stacked vertically at pitch sec(th); leftmost corner at x_lo+xoff.
    keep squares fully inside [x_lo.., L] x [y_lo, y_hi]. returns list (cx, cy, deg)"""
    if y_hi is None: y_hi=L
    co,si=math.cos(th),math.sin(th); pitch=1/co
    u=(co,si); v=(-si,co)
    out=[]
    r0=int(math.floor((y_lo-Y0)/pitch))-c-2; r1=int(math.ceil((y_hi-Y0)/pitch))+2
    for r in range(r0,r1+1):
        ax=x_lo+xoff+si; ay=Y0+r*pitch
        for i in range(c):
            bx=ax+i*co; by=ay+i*si   # bottom-left corner of square i
            xs=(bx,bx+co,bx+co-si,bx-si); ys=(by,by+si,by+si+co,by+co)
            if min(xs)>=x_lo-1e-12 and max(xs)<=L+1e-12 and min(ys)>=y_lo-1e-12 and max(ys)<=y_hi+1e-12:
                out.append((bx+(co-si)/2, by+(si+co)/2, math.degrees(th)))
    return out
def count(L,T,mode='exact'):
    T=np.array(T,float).reshape(-1,3)
    return len(fillfast.fill(L,T,mode=mode))
def theta_flush(c,w):
    """solve c*cos(t)+sin(t)=w for the larger-tilt root (t>atan(1/c))"""
    lo=math.atan(1/c); hi=math.pi/2
    for _ in range(80):
        mid=(lo+hi)/2
        if c*math.cos(mid)+math.sin(mid)>w: lo=mid
        else: hi=mid
    return hi
if __name__=='__main__':
    m=int(sys.argv[1]); f=float(sys.argv[2]); L=m+f
    best=[]
    t0=time.time()
    for c in range(6,m+1):
        j=c-1
        th=theta_flush(c,j+f)
        pitch=1/math.cos(th)
        res=[]
        for iy in range(12):
            Y0=iy*pitch/12
            T=slot_rows(L,c,th,0.0,Y0)
            N=count(L,T)
            res.append((N-m*m,len(T),round(Y0,3)))
        res.sort(reverse=True)
        print('c',c,'theta %.2f'%math.degrees(th),'rate %.3f'%(f-math.sin(th)),'best gain',res[0],'t %.0fs'%(time.time()-t0),flush=True)
