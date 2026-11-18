#!/usr/bin/env python3
"""A coarse map of one layout: one character for each unit cell (the cell that holds a centre).

Usage: invent_map.py SUB.csv N OUT.txt
  the tilt classes are those of the held 979: 20 to 22.5 degrees (its arm of 9) and 17 to 20 degrees (its arm of 11)
"""
import csv, sys
import numpy as np
src, n, out = sys.argv[1], sys.argv[2], sys.argv[3]
R = [r for r in csv.DictReader(open(src)) if r['n'] == n]
X = np.array([float(r['x']) for r in R]); Y = np.array([float(r['y']) for r in R]); A = np.array([float(r['angle']) for r in R])
d = np.abs(((np.degrees(A) + 45) % 90) - 45)
m = int(max(X.max(), Y.max())) + 1
grid = [['.'] * m for _ in range(m)]
for x, y, a in zip(X, Y, d):
    c = '#' if a <= 0.5 else ('9' if 20 <= a < 22.5 else '1' if 17 <= a < 20 else 'o')
    grid[int(y)][int(x)] = c
with open(out, 'w') as h:
    h.write('n = %s, %d squares. # plain, 9 tilt 20 to 22.5 degrees (the arm of 9), 1 tilt 17 to 20 degrees (the arm of 11),\n' % (n, len(R)))
    h.write('o another tilt, . no centre in this cell. The origin is at the bottom left.\n\n')
    for i in range(m - 1, -1, -1): h.write('%2d %s\n' % (i, ''.join(grid[i])))
    h.write('   ' + ''.join(str(j % 10) for j in range(m)) + '\n')
print(open(out).read())
