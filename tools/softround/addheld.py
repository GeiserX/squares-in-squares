#!/usr/bin/env python3
"""addheld.py N BOX [N BOX ...]: a start from the held packing of N (any kind) at the head of the queue of BOX, with the
held source in plan.json. For idle slots once the family, readers, band and modules files have had their pass."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctl
if __name__ == '__main__':
    args = sys.argv[1:]; want = {int(args[i]): args[i + 1] for i in range(0, len(args), 2)}
    rows = {}
    for r in csv.DictReader(open(ctl.HELD_FILE, newline='')):
        if int(r['n']) in want:
            rows.setdefault(int(r['n']), []).append({k: r[k] for k in ctl.KEYS})
    d = ctl.W + '/heldx'; os.makedirs(d, exist_ok=True)
    for n in [int(args[i]) for i in range(0, len(args), 2)]:
        p = '%s/%d.csv' % (d, n)
        ctl.write_rows(p, sorted(rows[n], key=lambda r: int(r['square_id'])))
        src, lic = ctl.source_of(n); kind = ctl.kind_of(src)
        ctl.add(n, p, kind, want[n])
        pl = ctl.load_plan()
        for j in pl['jobs']:
            if j['n'] == n and j['path'] == p:
                j['source'] = 'the held packing (%s)' % src; j['licence'] = lic; j['where'] = 'held'
        ctl.save_plan(pl)
