#!/usr/bin/env python3
"""rigidsoft_pin: the shear scan of rigidsoft_scan.py with a block that is sheared along both diagonals.

The held soft blocks (230, 451 at 43.60 degrees, 261 at 41.88 degrees) keep the centres of their squares close
to the 45-degree lattice and turn every square by the same small angle eps. A square then touches its two
neighbours along full sides and is slid against each by about tan(eps) (rigidsoft.md section 7). `sblock` of
rigidsoft_scan.py slides the squares along one diagonal only. This tool builds the block with both slides and
gives it to the same scan: tolerant fill of the uprights (Evan Daniel's fillfast, MIT, imported), then the quench.

  rigidsoft_pin.py shear JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv N A B [the options of rigidsoft_scan.py shear]
        A chains of B squares; eps < 0 turns the squares the other way
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft_scan as SC  # noqa: E402

S2 = math.sqrt(2.0)


def pblock(a, b, eps_deg, cx, cy):
    """a chains of b squares, centres on the 45-degree lattice with step sec(eps), every square at 45 - eps"""
    eps = math.radians(eps_deg); phi = math.pi / 4 - eps
    st = 1.0 / math.cos(eps) / S2
    out = []
    for k in range(b):
        for j in range(a):
            u = (k - (b - 1) / 2) * st; v = (j - (a - 1) / 2) * st
            out.append((cx + u - v, cy + u + v, math.degrees(phi)))
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'shear':
        sys.exit(__doc__)
    SC.sblock = pblock
    SC.cmd_shear(sys.argv[2:])
