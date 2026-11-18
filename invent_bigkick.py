#!/usr/bin/env python3
"""A kick scan with chosen kick sizes: midm_scan.py with the sigmas of its full kick set from the command line.

Usage: invent_bigkick.py --kicks 0.02,0.04 --n N --sub FILE --out DIR --fq PATH --modes kick [--seconds S] [--seed K]
                         [--max-tries T] [--deadline FILE]
  --kicks  the sigmas the mode `kick` draws from (midm_scan.py draws from 0.003, 0.01, 0.02 and 0.04)
  every other argument goes to midm_scan.py unchanged; its tables and raw files are the same

Why: in the pooled tries of round 17 (invent_kickrows.py) the full kick at sigma 0.02 and 0.04 gave most of the
large steps for its share of the seconds. This tool lets a scan run those sizes only, so that the share can be
tested. It changes nothing in midm_scan.py: it sets the tuple the mode reads and calls its main().
Our own code; midm_scan.py and fq are used as they are.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import midm_scan as ms  # noqa: E402

if '--kicks' in sys.argv:
    i = sys.argv.index('--kicks')
    ms.KICKS = tuple(float(x) for x in sys.argv[i + 1].split(','))
    assert ms.KICKS and all(0 < k < 1 for k in ms.KICKS), 'sigmas are in units of one square, between 0 and 1'
    del sys.argv[i:i + 2]
ms.main()
