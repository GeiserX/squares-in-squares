"""Port the round 28 twoshort tools to round 29 paths, the bar29 bar, seeds 1025 and an 11:45 UTC deadline.

Round 29 changes: the live round is r29 (quench_walk QUENCH_LIVE_ROUND '2[89]'), r28 take dirs are frozen,
gather/round27-2026-11-15b.csv is a held root (gate/cand-round27-1115b), our own r26 to r28 kicks are credited from
their local mirrors, the r28 boxE mirror is the already-run pool (OLD), certification uses border's finesafe.py
(bisected dilation, a byte copy pinned here), forensics rectangles at the bar side and fresh certified take rows of
other lanes get one 900 s kick (rebuild r28: the 684 rectangle at the bar side gave 9.0e-5 in one 900 s kick).
"""
from pathlib import Path
import shutil, datetime, re, hashlib
B = Path('$SCRATCH/bounties-squares'); W = B / 'take-twoshort-r29/work'; O = B / 'take-twoshort-r28/work'
for x in ['lane', 'starts', 'jobs', 'locks', 'runs', 'done', 'q', 'tmp', 'designs', 'stage', 'reference', 'boxE29', 'intake',
          'proofs', 'libraries', 'withdrawn', 'qmeta', 'pin']:
    (W / x).mkdir(parents=True, exist_ok=True)
for p in Path('.').glob('*.py'):
    shutil.copy2(p, W / 'lane' / p.name)
for name in ['shape974.py', 'control22.py', 'cornerhot22.py', 'cornerlk22.py']:
    shutil.copy2(O / name, W / name)
shutil.copy2(O / 'pin/quench_walk.r27snap.py', W / 'pin/quench_walk.r27snap.py')
shutil.copy2('quench_walk.py', W / 'pin/quench_walk.r29snap.py')
fs = B / 'take-border-r28/work/finesafe.py'; shutil.copy2(fs, W / 'finesafe.py')
(W / 'finesafe.sha256').write_text(hashlib.sha256(fs.read_bytes()).hexdigest() + '  ' + str(fs) + '\n')
MODS = sorted(p.stem[:-2] for p in O.glob('*28.py') if p.stem not in ('setup28',))
SH = sorted(p.stem[:-2] for p in O.glob('*28.sh'))
def port(s):
    for m in MODS + SH:
        s = re.sub(r'\b' + m + r'28\b', m + '29', s)
    s = s.replace('take-twoshort-r28', 'take-twoshort-r29').replace('handoff-r28.log', 'handoff-r29.log')
    s = s.replace('boxE28', 'boxE29').replace('STOP28', 'STOP29').replace('take-*-r28', 'take-*-r29')
    s = s.replace(']+-r28/', ']+-r29/')
    s = s.replace('round28-briefs/bar28.tsv', 'round29-briefs/bar29.tsv').replace('round28-briefs/bar29.tsv', 'round29-briefs/bar29.tsv')
    s = s.replace('deadline05:45UTC', 'deadline11:45UTC').replace("'05:45UTC'", "'11:45UTC'")
    s = re.sub(r'(?<!\d)925(?!\d)', '1025', s)
    s = s.replace('twoshort round28', 'twoshort round29').replace('twoshort round 28', 'twoshort round 29').replace('round 28 walk', 'round 29 walk')
    s = s.replace('gate/cand-round26-1114b/details.csv', 'gate/cand-round27-1115b/details.csv')
    return s
for m in MODS:
    s = port((O / (m + '28.py')).read_text())
    if m == 'qwalk':
        old = "os.environ['QUENCH_LIVE_ROUND'] = '2[78]'"; assert old in s
        s = s.replace(old, "os.environ['QUENCH_LIVE_ROUND'] = '2[89]'")
    if m == 'admit':
        # Round 29 09:25Z: the quench lane's held27 start files name their root as the relative path gather/round27-2026-11-15b.csv.
        old = "   for lane,count in re.findall(r'\\b(take-[a-z-]+-r\\d+) n\\s*=\\s*(\\d+)\\b',s):visit(B/lane/(count+'.csv'))\n"; assert old in s, 'admit gather anchor'
        s = s.replace(old, old + "   for name in re.findall(r'(?<![A-Za-z0-9/])gather/(round2[3-7]-2026-11-1[3-5][ab])\\.csv',s):visit(B/'gather'/(name+'.csv'))\n")
        for old, new in [
            # Round 29: every take dir of rounds 1 to 28 is frozen (a backlog/rebuild 551 tree names take-family-r14/871.csv).
            ("FROZEN=re.compile(r'/take-[a-z0-9-]+-r2[0-7]/')", "FROZEN=re.compile(r'/take-[a-z0-9-]+-r(?:[1-9]|1[0-9]|2[0-8])/')"),
            ("LIVE_SNAP=re.compile(r'/take-[a-z0-9-]+-r2[78]/work/", "LIVE_SNAP=re.compile(r'/take-[a-z0-9-]+-r2[89]/work/"),
            # Round 29: k123 keeps its byte snapshots in work/input-snapshots; forensics r29 take rows 376 and 991 reach them.
            ("(?:starts|pins|cert|donors)/[^/]+\\.csv$')", "(?:starts|pins|cert|donors|input-snapshots)/[^/]+\\.csv$|/take-[a-z0-9-]+-r29/work/.+\\.csv$')"),
            ("B/'take-twoshort-r27/work/intake')", "B/'take-twoshort-r27/work/intake',B/'take-twoshort-r28/work/intake')"),
            ("(round23-2026-11-13b|round25-2026-11-14b|round26-2026-11-14b).csv", "(round23-2026-11-13b|round25-2026-11-14b|round26-2026-11-14b|round27-2026-11-15b).csv"),
            ("'round26-2026-11-14b':'cand-round26-1114b'}", "'round26-2026-11-14b':'cand-round26-1114b','round27-2026-11-15b':'cand-round27-1115b'}"),
            ("    if p.name in ('round25-2026-11-14b.csv','round26-2026-11-14b.csv'):", "    if p.name in ('round25-2026-11-14b.csv','round26-2026-11-14b.csv','round27-2026-11-15b.csv'):"),
            ("only files moved out of frozen r20-r27 take dirs", "only files moved out of frozen r20-r28 take dirs"),
            # Round 29: a live r29 take csv that its lane rewrote since a child pinned it (harvest 90 under backlog 90)
            # counts like a gone one: the child keeps the old bytes in its own snapshot, and quench_walk decides.
            (" return e[1]=='missing recorded ancestor' and bool(LIVE_TAKE.match(p))", " return e[1] in ('missing recorded ancestor','pinned ancestor hash differs','pinned ancestor metadata differs','recorded ancestor hash differs') and bool(LIVE_TAKE.match(p) or LIVE_NEAR.match(p))\nLIVE_NEAR=re.compile(r'^$SCRATCH/bounties-squares/take-[a-z0-9-]+-r29/near/[^/]+$')"),
            # Round 29 10:25Z: forensics rewrote near/808-rect.csv under a pinned 752 chain (no WITHDRAW line); quench_walk
            # finds the 752 leg clean, our gate refused it. A rewritten live r29 near file counts like a rewritten take csv.
            ("key=hashlib.sha256(('v28a:'", "key=hashlib.sha256(('v29b:'"),
            # Round 29: seeds/merged0.csv (our seed of 2026-11-07: each n from Couzo, MIT, or the Samanyu-dev seed, which
            # rules 2 and 3 of round 29 make ours) is a root. It deferred 7 of the first 8 forensics r29 rectangles.
            ("   if p.parent.name=='gather':\n",
             "   if str(p) in ('$SCRATCH/bounties-squares/seeds/merged0.csv','$SCRATCH/bounties-squares/seeds/samanyu_bestfit.csv','$SCRATCH/bounties-squares/seeds/samanyu_22249.csv','$SCRATCH/bounties-squares/seeds/couzo.csv'):roots.append(str(p)+' original seed file (Couzo MIT, or the Samanyu-dev seed that round 29 rules 2 and 3 make ours)');return\n   if p.parent.name=='gather':\n"),
            ("for _R in (Path(__file__).resolve().parent/'boxE29',B/'take-twoshort-r27/work/boxE27',",
             "for _R in (Path(__file__).resolve().parent/'boxE29',B/'take-twoshort-r28/work/boxE28',B/'take-twoshort-r27/work/boxE27',"),
        ]:
            assert old in s, old; s = s.replace(old, new)
    if m == 'manage':
        # Round 29: a midm job names midm_scan.py in its source record, not the invent_rest lkick.
        old = "source='twoshort round 29: invent_rest.py lkick (180 s legs, seed '+str(j['seed'])+') of '"; assert old in s
        s = s.replace(old, "source='twoshort round 29: '+('midm_scan.py --modes lkick,kick (%d s, seed %d)'%(j.get('seconds',900),j['seed']) if j.get('tool')=='midm' else 'invent_rest.py lkick (180 s legs, seed '+str(j['seed'])+')')+' of '")
        old = "OLD=B/'take-twoshort-r27/work/boxE27'"; assert old in s
        s = s.replace(old, "OLD=B/'take-twoshort-r28/work/boxE28'")
        # Round 29: forensics rectangles at the bar side get one 900 s kick at the head of the queue (rebuild r28 684:
        # 9.0e-5 in one 900 s kick; our r28 180 s kicks of 9 such rectangles moved nothing). Fresh certified take rows of
        # other lanes get one 900 s kick too (rebuild r28: the first kick moved 748 by 3.1e-5 and 910 by 8.4e-6).
        old = "   if lane=='forensics' and abs(gap)<1e-8 and priority>0:priority=50"; assert old in s
        s = s.replace(old, "   long_kick=(lane in ('forensics','reopen-held27') and abs(gap)<1e-8) or (bool(re.search(r'/take-[a-z0-9-]+-r29/\\d+\\.csv$',str(p))) and gap<1e-8)\n   if long_kick:priority=min(priority,1)")
        old = "remaining=2 if gap<.001 else 1,seconds=180,"; assert old in s
        s = s.replace(old, "remaining=1 if long_kick else 2 if gap<.001 else 1,seconds=900 if long_kick else 180,")
        old = "   if input_proof:job['input_ancestry_proof']=str(input_proof)\n"; assert old in s
        s = s.replace(old, old + "   if long_kick:job['tool']='midm'\n")
        # Round 29: midm kicks of fresh take rows go before midm kicks of bar-side rectangles (rebuild r28: gains on the
        # fresh rows 748, 910, 805, 978 and 642; 1 of 18 bar-side rectangles moved).
        old = "   jp=W/'jobs'/('%03d-%s-1025.json'%(priority,tag));atom(jp,job)"; assert old in s
        s = s.replace(old, "   if long_kick and re.search(r'/take-[a-z0-9-]+-r29/\\d+\\.csv$',str(p)):\n    priority=0;job['priority']=0\n    for _q in W.glob('jobs/000-*-'+str(n)+'-*.json'):\n     if _q.name.startswith('000-00-') or (R/'locks'/_q.name).exists():continue\n     try:_jq=json.load(open(_q))\n     except ValueError:continue\n     if _jq.get('tool')=='midm' and _jq.get('n')==n and load(W/_jq['start'])[1]<=side+1e-12:priority=50;job['priority']=50;break\n" + old)
    if m == 'worker':
        # Round 29: a per-job wall limit (the job's seconds plus 600 s). A forensics 909 kick hung 27 min inside one
        # squeeze (invent_rest checks its budget only between tries). On the limit the worker reads the slide log.
        old = "def bounded(cmd,**kw):\n end=int((R/'deadline').read_text())\n"; assert old in s
        s = s.replace(old, "def bounded(cmd,limit=None,**kw):\n end=int((R/'deadline').read_text())\n if limit:end=min(end,time.time()+limit)\n")
        old = "rc=bounded(cmd,stdout=log,stderr=subprocess.STDOUT)\n text=(D/'run.log').read_text();m=re.search(r'n=\\d+ start ([\\d.]+) best ([\\d.]+) tries (\\d+)',text)\n"
        assert old in s, 'worker anchor'
        s = s.replace(old, "rc=bounded(cmd,limit=j['seconds']+600,stdout=log,stderr=subprocess.STDOUT)\n text=(D/'run.log').read_text();m=re.search(r'n=\\d+ start ([\\d.]+) best ([\\d.]+) tries (\\d+)',text)\n if not m and rc==125 and (D/('slide-%d-%d.tsv'%(n,seed))).exists():\n  sl=(D/('slide-%d-%d.tsv'%(n,seed))).read_text();h=re.search(r'start=([\\d.]+)',sl)\n  data=[l.split('\\t') for l in sl.splitlines() if l and not l.startswith('#')]\n  bs=[float(q[3]) for q in data if len(q)==7 and q[-1]=='BEST']\n  if h:m=['n=%d start %s best %.12f tries %d (wall limit)'%(n,h[1],min(bs+[float(h[1])]),len(data)),h[1],repr(min(bs+[float(h[1])])),str(len(data))];event('WALL LIMIT '+p.name)\n")
    if m == 'manage':
        # Round 29: the backlog lane claims items in the handoff log before it starts them; a claimed input waits behind
        # the unclaimed fresh work (2 boxE slots), and runs only if the slots are free.
        old = "   if lane=='invent':priority=max(priority,50)\n"; assert old in s
        s = s.replace(old, old + "   if lane!='backlog' and str(p) in backlog_claims():priority=max(priority,50)\n")
        # Round 29 08:50Z: forensics withdrew 182 near files by sha256; a withdrawn input is dropped at queue time.
        s = s.replace(old + "   if lane!='backlog'", "   if hashlib.sha256(p.read_bytes()).hexdigest() in withdrawn_shas():state('DROP withdrawn by its lane (sha256 in a WITHDRAW handoff line) '+str(p));continue\n" + old + "   if lane!='backlog'")
        old = "def once(intake=True):\n"; assert old in s
        s = s.replace(old, "_claims=[None,set()]\ndef backlog_claims():\n hp=B/'handoff-r29.log'\n try:st=hp.stat().st_size\n except OSError:return set()\n if _claims[0]!=st:\n  c=set()\n  for line in hp.read_text().splitlines():\n   if ' backlog -> ' in line and ' claims ' in line:c.update(re.findall(r'$DATA/[^\\s,;]+\\.csv',line))\n  _claims[:]=[st,c]\n return _claims[1]\n_wd=[None,set()]\ndef withdrawn_shas():\n hp=B/'handoff-r29.log'\n try:st=hp.stat().st_size\n except OSError:return set()\n if _wd[0]!=st:\n  c=set()\n  for line in hp.read_text().splitlines():\n   if 'WITHDRAW' in line:c.update(re.findall(r'sha256 ([0-9a-f]{64})',line))\n  _wd[:]=[st,c]\n return _wd[1]\n" + old)
    if m == 'worker':
        # Round 29: a job with tool 'midm' runs midm_scan.py --modes lkick,kick instead of the invent_rest lkick.
        # Rebuild r28: a 900 s midm kick of the forensics 684 rectangle at the bar side gave 9.0e-5, where our 180 s
        # invent_rest lkicks of the same file had moved it 1.3e-9. midm writes fq-quenched finds to raw/.
        a0 = s.index(" cmd=[PY,'-I','lane/invent_rest.py'"); a1 = s.index(" improved=start-best>1e-8")
        inv = ''.join(' ' + l + '\n' for l in s[a0:a1].rstrip('\n').split('\n'))
        mid = (" if j.get('tool')=='midm':\n"
               "  cmd=[PY,'-I','lane/midm_scan.py','--n',str(n),'--sub',j['start'],'--out',str(D),'--fq',os.environ['SQ_FQ'],'--seconds',str(j['seconds']),'--modes','lkick,kick','--deadline','deadline','--seed',str(seed)]\n"
               "  event('START '+p.name+' '+repr(cmd))\n"
               "  with open(D/'run.log','w') as log:rc=bounded(cmd,limit=j['seconds']+600,stdout=log,stderr=subprocess.STDOUT)\n"
               "  sc=D/('scan-%d-%d.tsv'%(n,seed));st=sc.read_text() if sc.exists() else '';h=re.search(r'held=([\\d.]+)',st)\n"
               "  if not h:\n"
               "   j.update(error=(D/'run.log').read_text()[-1500:],rc=rc);atomic(R/'done'/p.name,j);event('FAIL '+p.name);return\n"
               "  start=float(h[1]);finds=re.findall(r'# FIND try \\d+ mode (\\w+) .*? side ([\\d.]+)',st)\n"
               "  tries=len([l for l in st.splitlines() if l and not l.startswith('#')])\n"
               "  raws=list((D/'raw').glob('%d-*.csv'%n)) if (D/'raw').exists() else []\n"
               "  best=min([float(f[1]) for f in finds]+[start]);cur=str(max(raws,key=lambda q:int(q.stem.rsplit('-',1)[1]))) if finds and raws else j['start']\n"
               "  m=['n=%d start %.12f best %.12f tries %d (midm lkick,kick)'%(n,start,best,tries)]\n"
               "  if tag.startswith('control793'):j['control_pass']=abs(start-28.672864930769137)<2e-10 and best<=start and tries>0;event('CONTROL '+str(j['control_pass'])+' '+m[0])\n"
               " else:\n")
        s = s[:a0] + mid + inv + s[a1:]
    if m == 'manage':
        # Round 29 10:30Z: a chain through the areebbb union must name its upstream notebooks in the source cell
        # (source29.credited_cells); the 752 leg deferred because our short source cell named only our snapshot.
        old = "one fq quench of the floatsafe-certified raw best on boxE'"; assert old in s, 'clean_record anchor'
        s = s.replace(old, old + "+_upstream(snap)", 1)
        old = "def clean_record(j,lic):\n"; assert old in s
        s = s.replace(old, "def _upstream(snap):\n txt=''\n for q in (pathlib.Path(str(snap)+'.json'),):\n  if q.is_file():txt+=q.read_text()\n refs=sorted({r for r in re.findall(r'(?:notebooks/|datasets/|upstream\\s+|->\\s*)([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)',txt) if not r.startswith('areebbb/')})\n return ('; upstream credits named by the input record: '+', '.join('upstream '+r for r in refs)) if refs else ''\n" + old)
        # Round 29: a top-level certified take csv of another live lane is walked before every near file (rank -1);
        # the bar already holds the live rows, so their gap is 0 and they waited behind hundreds of near files.
        old = "   rank=0 if t[1]<0 or t[5] in ['forensics','k123']"; assert old in s
        s = s.replace(old, "   rank=-1 if re.search(r'/take-[a-z0-9-]+-r29/\\d+\\.csv$',str(t[4])) else 0 if t[1]<0 or t[5] in ['forensics','k123']")
    if m == 'worker':
        # Round 29: worker 1 takes the 900 s midm kicks first and worker 2 the 180 s lkicks first (legs first on both),
        # so the r28-proven short kicks of fresh rectangles keep one slot. The stop file is STOP29b, and a worker
        # re-executes itself when worker29.py changes on disk (no drain needed for a code change).
        old = "while not (R/'STOP29').exists() and"; assert old in s
        s = s.replace(old, "_ME=os.stat(__file__).st_mtime\ndef _midm(p):\n try:return json.load(open(p)).get('tool')=='midm'\n except (ValueError,OSError):return False\ndef _order(ps):\n return sorted(ps,key=lambda p:(not p.name.startswith('000-00-leg'),(not p.name[:3].isdigit()) or int(p.name[:3])>=50,_midm(p)!=(sys.argv[1]=='1'),p.name))\nwhile not (R/'STOP29b').exists() and")
        old = " for p in sorted((R/'jobs').glob('*.json')):\n"; assert old in s
        s = s.replace(old, " if os.stat(__file__).st_mtime!=_ME:event('RELOAD');os.execv(sys.executable,[sys.executable,'-I',os.path.abspath(__file__),sys.argv[1]])\n for p in _order([q for q in (R/'jobs').glob('*.json') if not (R/'locks'/q.name).exists()]):\n")
    if m == 'certify':
        old = "import floatsafe\n"; assert old in s
        s = s.replace(old, "import finesafe as floatsafe  # round 29: border's bisected dilation (pinned copy, finesafe.sha256)\n", 1)
    (W / (m + '29.py')).write_text(s)
for m in SH:
    t = W / (m + '29.sh'); t.write_text(port((O / (m + '28.sh')).read_text())); t.chmod(0o755)
end = int(datetime.datetime(2026, 11, 15, 11, 45, tzinfo=datetime.timezone.utc).timestamp())
(W / 'deadline').write_text(str(end)); (W / 'search-deadline').write_text(str(end - 12 * 60))
if not (W.parent / 'take.tsv').exists():
    (W.parent / 'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
shutil.copy2(O / 'starts/control793.csv', W / 'starts/control793.csv')
shutil.copy2(O / 'bare-index.txt', W / 'bare-index.txt')
print('setup complete', end, MODS, SH)
