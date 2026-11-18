#!/usr/bin/env python3
"""Bound an island's wall time, including its LP and legalisation calls."""
import os
import subprocess
import sys
import time


def main():
    limit = float(sys.argv[1])
    deadline = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deadline')
    if os.path.exists(deadline):
        limit = min(limit, float(open(deadline).read()) - time.time())
    if limit <= 0:
        print('SOFTTIMEOUT common deadline', flush=True)
        return 124
    try:
        return subprocess.run(sys.argv[2:], timeout=limit).returncode
    except subprocess.TimeoutExpired:
        print('SOFTTIMEOUT wall limit %.1fs' % limit, flush=True)
        return 124


if __name__ == '__main__':
    sys.exit(main())
