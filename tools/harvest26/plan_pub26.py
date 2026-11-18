"""Build the round 26 public queue: per n the source file, the source cell and the licence cell (data read only).
  python -I plan_pub26.py > origin/plan.tsv"""
import csv, json, re, glob, sys
D = 'public/data/nb/'
ns = [850, 972, 971, 453, 791, 910, 909, 706, 761, 459, 375, 818, 695, 814, 654, 595, 646, 499, 416]
scan = [r for r in csv.DictReader(open('origin/r26.tsv'), delimiter='\t')]
excl = {}
for l in open('origin/excl.log'):
    n = int(l.split()[0]); excl[n] = l.split('| excl:')[1].replace(' (Samanyu-dev seed)', '').replace(' (CC BY-SA)', '').strip()
luc = {}
for f in sorted(glob.glob(D + 'lucifer19__think-select-reclose/validation_v5[45].json')):
    j = json.load(open(f)); v = re.findall(r'v(\d+)', f)[0]
    for k, s in (j.get('sources') or {}).items():
        for n in s.get('puzzles', []):
            luc.setdefault(n, {}).setdefault('v' + v, []).append(k.split(':')[0])
km = json.load(open(D + 'kmmmvs__squares-public-merge-daily/merge_report.json'))['replaced_groups']
ac = dict(r.split(',')[:2] for r in open(D + 'alexchilton__fault-line-dp-basin-hopping-lb-22-2620/merged_sources.csv').read().split('\n')[1:] if r)
def short(p):
    p = p.split('/data/')[-1]
    return re.sub(r'^(nb|ds)/', '', p).replace('__', '/', 1)
print('n\tsrc\tsource\tlicence')
for n in ns:
    exact = [r for r in scan if int(r['n']) == n and float(r['dist']) < 1e-9 and float(r['dside']) == 0.0 and 'take-harvest-r25' not in r['file']]
    exact.sort(key=lambda r: r['updated'])
    luc_f = [r for r in exact if 'lucifer19__think-select-reclose/submission.csv' in r['file']]
    jz = [r for r in exact if 'jazivxt__boxed-in-sub/submission.csv' in r['file']]
    pick = (luc_f or jz)[0]
    if pick is luc_f[0] if luc_f else False:
        head = 'lucifer19/think-select-reclose :: submission.csv (notebook output, session 369519698, run 2026-11-14T07:30Z)'
    else:
        head = 'jazivxt/boxed-in-sub :: submission.csv (notebook output, session 369436278, run 2026-11-14T07:51Z)'
    hd = {}
    for r in exact:
        k = '/'.join(short(r['file']).split('/')[:2])
        hd[k] = min(hd.get(k, 'z'), r['updated'][:16] + 'Z')
    holders = [f'{k} ({v})' for k, v in sorted(hd.items(), key=lambda x: x[1])]
    cred = []
    if n in luc:
        cred.append('lucifer19 validation ' + '; '.join(f"{v}: {', '.join(sorted(set(x)))}" for v, x in sorted(luc[n].items())))
    if str(n) in km:
        cred.append('kmmmvs/squares-public-merge-daily merge_report (run 06:03Z): ' + km[str(n)]['source'].replace('notebooks/', '').replace('datasets/', ''))
    if str(n) in ac:
        cred.append('alexchilton fault-line merged_sources (run 09:31Z): ' + ac[str(n)])
    src = (f"{head}; the layout is new on 2026-11-14 (in no harvested public file up to 2026-11-13T23:21Z); "
           f"the same layout (centre distance below 1e-9, same side) is in: {'; '.join(holders)}; "
           f"per-n credits: {' | '.join(cred)}; "
           f"no copy of a layout of rules a-d (max centre distance: {excl[n]})")
    lic = ('Apache 2.0 (Kaggle default for public notebooks); every credited upstream is a public notebook output under Apache 2.0, '
           'and the starter-kit best_current.csv that kmmmvs credits is byte-identical (sha256 fd8866…) to the alexchilton fault-line notebook output that lucifer19 credits')
    print(f"{n}\t{pick['file']}\t{src}\t{lic}")
