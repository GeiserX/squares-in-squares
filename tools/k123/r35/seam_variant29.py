from pathlib import Path
W=Path(__file__).resolve().parent
p=W/'lane/k123_join_diverse29.py';s=(W/'lane/k123_join.py').read_text()
s=s.replace("q.add_argument('--only', default=''", "q.add_argument('--seam-bins', type=int, default=3)\n    q.add_argument('--only', default=''")
s=s.replace('j1 if only else 0)', 'j1 if only else min(a.seam_bins-1, (j1-5)*a.seam_bins//max(1,len(X.G)-9)))')
s=s.replace('for (n2, m2, _), (Ln, j1', 'for (n2, m2, _), (Ln, j1')
p.write_text(s)
p=W/'divsel29.py';s=(W/'sel21.py').read_text().replace('key = round(b, 4)',"m=re.search(r'-j(\\d+)-',tag);key = (round(b, 4),int(m[1])//6)")
p.write_text(s)
