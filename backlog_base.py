#!/usr/bin/env python3
"""backlog_base: the per-n base bar of the backlog lane (avenues/backlog.md, Round 25).

Until the main session posts a "main -> all: BASE <file> <gate dir>" line in the handoff log, the bar of n is the
lower of the held gate details (gate/cand-round23-1113b/details.csv) and the frozen take-*-r24 rows whose ancestry
the round 24 assembler traced clean (take-assemble-r24/trace.log: group A, no issues, no blocks). Rows at the out
counts of (a) to (c) never lower the clean bar. The strict bar also takes every other r24 row, clean or not.
After a BASE line, both bars are the details.csv of the gate dir that line names.

  backlog_base.py OUT.tsv      writes n, clean score, clean side, clean origin, strict score
"""
import csv, math, os, re, sys

S = '$SCRATCH/bounties-squares'
OUT_N = {639, 691, 745, 858, 918, 980, 981, 801}
csv.field_size_limit(1 << 30)


def details(path):
    return {int(r['n']): float(r['score']) for r in csv.DictReader(open(path))}


def base_line():
    p = S + '/handoff-r25.log'
    last = None
    if os.path.exists(p):
        for line in open(p):
            if re.search(r'\bmain -> all: BASE\b', line):
                last = line
    return last


def trace_verdicts():
    ok = {}
    p = S + '/take-assemble-r24/trace.log'
    for line in open(p):
        t = line.split()
        if line.startswith('cached ancestry'):
            n, d, g = int(t[2]), t[3], t[4]
            ok[(n, d)] = g == 'A'
        elif len(t) >= 3 and t[0].isdigit():
            m = re.match(r'(\d+) (\S+) (\w) seeds \[(.*?)\] issues (\d+) blocks \[(.*?)\]', line)
            if m:
                ok[(int(m[1]), m[2])] = m[3] == 'A' and m[4] == '' and m[5] == '0' and m[6].strip() == ''
    return ok


def bars():
    line = base_line()
    if line:
        m = re.search(r'(gate/\S+)', line)
        if m:
            d = details(os.path.join(S, m[1].rstrip(',;.'), 'details.csv'))
            return {n: (s, 'BASE ' + m[1]) for n, s in d.items()}, dict(d), line.strip()
    held = details(S + '/gate/cand-round23-1113b/details.csv')
    clean = {n: (s, 'held round23b') for n, s in held.items()}
    strict = dict(held)
    ver = trace_verdicts()
    import glob
    for t in sorted(glob.glob(S + '/take-*-r24/take.tsv')):
        d = os.path.basename(os.path.dirname(t))
        for r in csv.DictReader(open(t), delimiter='\t'):
            try:
                n, s = int(r['n']), float(r['new'])
            except (KeyError, ValueError):
                continue
            strict[n] = min(strict[n], s)
            if ver.get((n, d)) and n not in OUT_N and s < clean[n][0]:
                clean[n] = (s, d)
    return clean, strict, None


def side(n, score):
    return (score + 1) * math.sqrt(n)


def main():
    clean, strict, line = bars()
    with open(sys.argv[1] + '.tmp', 'w') as h:
        h.write('n\tclean_score\tclean_side\tclean_origin\tstrict_score\n')
        for n in sorted(clean):
            s, o = clean[n]
            h.write('%d\t%r\t%r\t%s\t%r\n' % (n, s, side(n, s), o, strict[n]))
    os.replace(sys.argv[1] + '.tmp', sys.argv[1])
    moved = sum(1 for n in clean if clean[n][1] != 'held round23b')
    print('base', line or 'interim (held round23b + traced clean r24 rows)', 'rows', len(clean), 'lowered by r24', moved)


if __name__ == '__main__':
    main()
