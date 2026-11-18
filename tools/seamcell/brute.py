"""Third check: explicit patch, pairwise intersection area by convex clipping."""
import json, math, sys, numpy as np

def poly(x, y, t):
    c, s = math.cos(t), math.sin(t)
    return [(x + c*a - s*b, y + s*a + c*b) for a, b in ((.5,.5),(-.5,.5),(-.5,-.5),(.5,-.5))]

def clip(P, Q):
    def inside(p, a, b): return (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0]) >= 0
    def inter(p, q, a, b):
        x1,y1=p;x2,y2=q;x3,y3=a;x4,y4=b
        d=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        t=((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/d
        return (x1+t*(x2-x1), y1+t*(y2-y1))
    out = P
    for i in range(len(Q)):
        a, b = Q[i], Q[(i+1)%len(Q)]
        inp, out = out, []
        if not inp: break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j+1)%len(inp)]
            if inside(q, a, b):
                if not inside(p, a, b): out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p, a, b): out.append(inter(p, q, a, b))
    return out

def area(P):
    return 0.5*abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P)))) if len(P) > 2 else 0.0

def check(r, T=8):
    k, p, D, ox, oy = r['k'], r['p'], r['D'], r['ox'], r['oy']
    C = np.array(r['coords'])
    # bring the cell near the origin along the seam
    tilt = []
    for (x, y, t) in C:
        sh = round((x + y) / (2 * p)) * p
        for tt in range(-T, T + 1):
            tilt.append((x - sh + tt * p, y - sh + tt * p, t))
    S = list(tilt)
    R = T * p + 4
    for I in range(-R - 3, R + 3):
        for J in range(-R - 3, R + 3):
            if I - J >= D and abs(I - J) < 6: S.append((ox + I + .5, J + .5, 0.0))
            if J - I >= 0 and abs(I - J) < 6: S.append((I + .5, oy + J + .5, 0.0))
    S = [s for s in S if abs(s[0] + s[1]) < 2 * (T * p - 2)]
    worst = 0.0
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            if (S[i][0]-S[j][0])**2 + (S[i][1]-S[j][1])**2 > 2.01: continue
            a = area(clip(poly(*S[i]), poly(*S[j])))
            worst = max(worst, a)
    # count per step in the middle: tilted centres with u in one period window
    return worst

for l in open(sys.argv[1]):
    r = json.loads(l)
    print(r['p'], r['k'], r['D'], 'f*', round(r['f_star'], 6), 'max pairwise overlap area', check(r))
