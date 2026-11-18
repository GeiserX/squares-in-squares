#!/usr/bin/env python3
"""Draw a layout with its rigid stacks coloured by length, on a dark background.

  frontier_draw.py SUB.csv OUT_DIR N[:label] [N[:label] ...]

Upright squares are grey. A tilted square is coloured by the length c of the stack it belongs to
(frontier_stacks.py); tilted squares outside any stack of 3 or more are white outlines.
Our own code; reads data only. Run with python -I.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from frontier_read import load, normal
from frontier_stacks import stacks

COL = {3: '#5b6cff', 4: '#3aa0ff', 5: '#22c1c3', 6: '#2ecc71', 7: '#f1c40f', 8: '#e67e22', 9: '#e74c3c', 10: '#e84393', 11: '#b56cff'}


def draw(sq, n, label, path):
    s, A = normal(sq)
    m = math.isqrt(n - 1)
    t = np.abs(A[:, 2]) > 0.5      # a square turned by less than half a degree is drawn as upright
    T = A[t]
    _, best = stacks(T) if len(T) else ([], [])
    fig, ax = plt.subplots(figsize=(9, 9), facecolor='#0d1117')
    ax.set_facecolor('#0d1117')
    def poly(x, y, d, **kw):
        c, si = math.cos(math.radians(d)) / 2, math.sin(math.radians(d)) / 2
        ax.add_patch(Polygon([(x - c + si, y - si - c), (x + c + si, y + si - c), (x + c - si, y + si + c), (x - c - si, y - si + c)], **kw))
    for x, y, d in A[~t]:
        poly(x, y, 0, fc='#2b313b', ec='#0d1117', lw=0.4)
    used = set()
    for i, (x, y, d) in enumerate(T):
        c = len(best[i]) if best[i] is not None else 0
        if c >= 3:
            used.add(min(c, 11)); poly(x, y, d, fc=COL[min(c, 11)], ec='#0d1117', lw=0.4)
        else:
            poly(x, y, d, fc='#0d1117', ec='#c9d1d9', lw=0.6)
    ax.plot([0, s, s, 0, 0], [0, 0, s, s, 0], color='#c9d1d9', lw=1)
    ax.set_xlim(-0.3, s + 0.3); ax.set_ylim(-0.3, s + 0.3); ax.set_aspect('equal'); ax.axis('off')
    for j, c in enumerate(sorted(used)):
        ax.text(0.01 + 0.085 * j, -0.035, 'c=%d%s' % (c, '+' if c == 11 else ''), color=COL[c], transform=ax.transAxes, fontsize=11)
    ax.set_title('n = %d = %d² + %d, side %d + %.4f, %d tilted%s' % (n, m, n - m * m, m, s - m, len(T), (' — ' + label) if label else ''),
                 color='#c9d1d9', fontsize=12)
    fig.savefig(path, dpi=110, facecolor=fig.get_facecolor(), bbox_inches='tight'); plt.close(fig)


def main():
    P = load(sys.argv[1]); out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for a in sys.argv[3:]:
        n, _, label = a.partition(':')
        tag = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        draw(P[int(n)], int(n), label, os.path.join(out, '%s-%s.png' % (n, tag)))


if __name__ == '__main__':
    main()
