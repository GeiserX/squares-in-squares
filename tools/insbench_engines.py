#!/usr/bin/env python3
"""Engines for insbench (command template 'insbench_engines.py KIND {in} {side} {out} {n} {cpu} {drop} EVAND').

  putback  the trivial control: add the removed pose back, change nothing else
  fqadd    add the removed pose back, then an fq quench (side free)
  ftmc     Evan Daniel's ftmc.py (MIT) for {cpu} s, started at the case side with the
           full-line test off (--k 999); its best file is the output
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path


def load(p):
    L = [l.split() for l in open(p) if l.strip() and not l.startswith('#')]
    n, s = int(L[0][0]), float(L[0][1])
    return s, [l[:3] for l in L[1:n + 1]]


def write(p, s, Q):
    with open(p, 'w') as h:
        h.write(f'{len(Q)} {s!r}\n')
        for q in Q:
            h.write(' '.join(q) + '\n')


kind, inp, side, out, n, cpu, drop, evand = sys.argv[1:9]
side, n, cpu = float(side), int(n), float(cpu)
packer = Path(evand).resolve() / 'search' / 'packer'
_, Q = load(inp)
_, D = load(drop)
if kind == 'putback':
    write(out, side, Q + D)
elif kind == 'fqadd':
    t = tempfile.mkdtemp(prefix='insb-')
    write(f'{t}/a.txt', side, Q + D)
    subprocess.run([str(packer / 'target/release/fq'), 'quench', '--in', f'{t}/a.txt', '--out', out],
                   capture_output=True, timeout=cpu)
    shutil.rmtree(t, ignore_errors=True)
elif kind == 'ftmc':
    t = tempfile.mkdtemp(prefix='insb-')
    write(f'{t}/init.txt', side, Q)
    subprocess.run([sys.executable, 'ftmc.py', '--n', str(n), '--k', '999', '--init', f'{t}/init.txt',
                    '--time', str(cpu), '--out', f'{t}/r'], cwd=packer, capture_output=True)
    if os.path.exists(f'{t}/r.best.txt'):
        shutil.copy(f'{t}/r.best.txt', out)
    shutil.rmtree(t, ignore_errors=True)
else:
    sys.exit(f'unknown engine {kind}')
