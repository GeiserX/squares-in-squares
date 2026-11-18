"""Port the round 29 twoshort tools to round 30 paths, the bar30 bar, seeds 1125 and a 17:45 UTC deadline.

Round 30 changes: the live round is r30 (quench_walk QUENCH_LIVE_ROUND '29|30', and the walk also reads handoff-r30.log
and the r30 ancestry dirs), every r29 take dir is frozen, gather/round28-2026-11-15b.csv is a held root
(gate/cand-round28-1115b), our own r26 to r29 kicks are credited from their local mirrors, the r29 boxE mirror is the
already-run pool (OLD). Every rule of round 29 (finesafe certify, 900 s midm kicks of fresh take rows and bar-side
forensics rectangles, 180 s lkicks above the bar) is kept.
"""
from pathlib import Path
import shutil, datetime, re, hashlib
B = Path('$SCRATCH/bounties-squares'); W = B / 'take-twoshort-r30/work'; O = B / 'take-twoshort-r29/work'
for x in ['lane', 'starts', 'jobs', 'locks', 'runs', 'done', 'q', 'tmp', 'designs', 'stage', 'reference', 'boxE30', 'intake',
          'proofs', 'libraries', 'withdrawn', 'qmeta', 'pin']:
    (W / x).mkdir(parents=True, exist_ok=True)
for p in Path('.').glob('*.py'):
    shutil.copy2(p, W / 'lane' / p.name)
for name in ['shape974.py', 'control22.py', 'cornerhot22.py', 'cornerlk22.py', 'finesafe.py', 'finesafe.sha256']:
    shutil.copy2(O / name, W / name)
for name in ['quench_walk.r27snap.py', 'quench_walk.r29snap.py']:
    shutil.copy2(O / 'pin' / name, W / 'pin' / name)
shutil.copy2('quench_walk.py', W / 'pin/quench_walk.r30snap.py')
LP = """def lp_polish(n,qfile,qdir,j):
 if time.time()+480>=int(open('deadline').read()):return
 sys.path.insert(0,str(R/'lane'));import floatsafe
 try:
  with open(qdir/'lp.log','w') as log:lrc=bounded([PY,'-I','lane/methods_lp.py',str(qfile),str(qdir/'lp'),'--ns',str(n),'--jobs','1'],limit=420,stdout=log,stderr=subprocess.STDOUT)
  lpf=qdir/'lp'/'raw'/('%d.csv'%n)
  if not lpf.exists():j['lp_polish']=dict(rc=lrc,moved=False);return
  rd=lambda q:[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(q))]
  a0=floatsafe.work((n,rd(qfile)));a1=floatsafe.work((n,rd(lpf)))
  j['lp_polish']=dict(rc=lrc,before=a0[2],after=a1[2],kept=False)
  if a1[1] is not None and (a0[1] is None or a1[2]<a0[2]-1e-13):
   with open(qfile,'w',newline='') as f:
    cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(a1[1])
   j['lp_polish']['kept']=True
  event('LP '+str(n)+' '+json.dumps(j['lp_polish']))
 except Exception as ex:event('LP ERROR '+str(n)+' '+repr(ex))
"""
MODS = sorted(p.stem[:-2] for p in O.glob('*29.py') if p.stem not in ('setup29',))
SH = sorted(p.stem[:-2] for p in O.glob('*29.sh'))
def port(s):
    for m in MODS + SH:
        s = re.sub(r'\b' + m + r'29\b', m + '30', s)
    s = s.replace('take-twoshort-r29', 'take-twoshort-r30').replace('handoff-r29.log', 'handoff-r30.log')
    s = s.replace('boxE29', 'boxE30').replace('STOP29', 'STOP30').replace('take-*-r29', 'take-*-r30')
    s = s.replace(']+-r29/', ']+-r30/')
    s = s.replace('round29-briefs/bar29.tsv', 'round30-briefs/bar30.tsv').replace('round29-briefs/bar30.tsv', 'round30-briefs/bar30.tsv')
    s = s.replace('deadline11:45UTC', 'deadline17:45UTC').replace("'11:45UTC'", "'17:45UTC'")
    s = re.sub(r'(?<!\d)1025(?!\d)', '1125', s)
    s = s.replace('twoshort round29', 'twoshort round30').replace('twoshort round 29', 'twoshort round 30').replace('round 29 walk', 'round 30 walk')
    s = s.replace('gate/cand-round27-1115b/details.csv', 'gate/cand-round28-1115b/details.csv')
    return s
for m in MODS:
    s = port((O / (m + '29.py')).read_text())
    if m == 'qwalk':
        old = "os.environ['QUENCH_LIVE_ROUND'] = '2[89]'"; assert old in s
        s = s.replace(old, "os.environ['QUENCH_LIVE_ROUND'] = '29|30'")
        # Round 30: the lane walker globs handoff-r2[2-9].log and take-*-r2[2-9] ancestry dirs; read the r30 ones too
        # (a text change on the source we exec, never an edit of the lane file).
        old = "    src = open(src_path).read()\n"; assert old in s
        s = s.replace(old, old + "    if 'handoff-r3' not in src:\n        src = src.replace(\"sorted(glob.glob(S + 'handoff-r2[2-9].log'))\", \"(sorted(glob.glob(S + 'handoff-r2[2-9].log')) + sorted(glob.glob(S + 'handoff-r3[0-9].log')))\")\n        src = src.replace(\"sorted(glob.glob(S + 'take-*-r2[2-9]/work/ancestry'))\", \"(sorted(glob.glob(S + 'take-*-r2[2-9]/work/ancestry')) + sorted(glob.glob(S + 'take-*-r3[0-9]/work/ancestry')))\")\n        src = src.replace(\"sorted(glob.glob(S + 'take-*-r2[2-9]/work/*/ancestry'))\", \"(sorted(glob.glob(S + 'take-*-r2[2-9]/work/*/ancestry')) + sorted(glob.glob(S + 'take-*-r3[0-9]/work/*/ancestry')))\")\n")
    if m == 'admit':
        for old, new in [
            ("gather/(round2[3-7]-2026-11-1[3-5][ab])", "gather/(round2[3-8]-2026-11-1[3-5][ab])"),
            ("FROZEN=re.compile(r'/take-[a-z0-9-]+-r(?:[1-9]|1[0-9]|2[0-8])/')", "FROZEN=re.compile(r'/take-[a-z0-9-]+-r(?:[1-9]|1[0-9]|2[0-9])/')"),
            ("LIVE_SNAP=re.compile(r'/take-[a-z0-9-]+-r2[89]/work/", "LIVE_SNAP=re.compile(r'/take-[a-z0-9-]+-r(?:29|30)/work/"),
            ("B/'take-twoshort-r28/work/intake')", "B/'take-twoshort-r28/work/intake',B/'take-twoshort-r29/work/intake')"),
            ("(round23-2026-11-13b|round25-2026-11-14b|round26-2026-11-14b|round27-2026-11-15b).csv", "(round23-2026-11-13b|round25-2026-11-14b|round26-2026-11-14b|round27-2026-11-15b|round28-2026-11-15b).csv"),
            ("'round27-2026-11-15b':'cand-round27-1115b'}", "'round27-2026-11-15b':'cand-round27-1115b','round28-2026-11-15b':'cand-round28-1115b'}"),
            ("'round27-2026-11-15b.csv'):", "'round27-2026-11-15b.csv','round28-2026-11-15b.csv'):"),
            ("only files moved out of frozen r20-r28 take dirs", "only files moved out of frozen r20-r29 take dirs"),
            ("parent/'boxE30',B/'take-twoshort-r28/work/boxE28',", "parent/'boxE30',B/'take-twoshort-r29/work/boxE29',B/'take-twoshort-r28/work/boxE28',"),
        ]:
            assert old in s, old; s = s.replace(old, new)
    if m == 'manage':
        old = "OLD=B/'take-twoshort-r28/work/boxE28'"; assert old in s
        s = s.replace(old, "OLD=B/'take-twoshort-r29/work/boxE29'")
    if m == 'manage':
        # Round 30: forensics claims its own 900 s kicks of bar-side rectangles in the handoff log ('claims first900s
        # rectangle bar-side kick'); a claim by any other lane now waits behind unclaimed work, as a backlog claim did.
        old = "   if ' backlog -> ' in line and ' claims ' in line:c.update("; assert old in s
        s = s.replace(old, "   if ' claims ' in line and ' twoshort -> ' not in line:c.update(")
    if m == 'worker':
        # Round 30: a contact LP polish (methods_lp.py) of the fq-quenched file, kept only when floatsafe certifies it
        # lower. midm r29: its 504 ended 2.75e-11 under ours, short of the 1e-10 rule; border measured 1.5e-10 to
        # 5e-10 of score from the LP on raw layouts, and the polishing lanes LP every fresh take within a minute.
        old = "  with open(qdir/'run.log','w') as log:qrc=bounded([PY,'-I','lane/zone_corner.py','quench',str(qdir),str(n)],stdout=log,stderr=subprocess.STDOUT)\n"
        assert old in s, 'worker lp anchor'
        s = s.replace(old, old + "  if qrc==0:lp_polish(n,qfile,qdir,j)\n")
        old = "def runjob(p):\n"; assert old in s
        s = s.replace(old, LP + old)
    if m == 'manage':
        # Round 30: claim each 900 s midm kick of a fresh take row in the handoff log when it is queued, so the other
        # kick lanes (rebuild, backlog, quench, midm) can skip it (midm r29: 6 of 8 crossings were matched within 10 to
        # 90 minutes by lanes running the same kick on the same take).
        old = "   jp=W/'jobs'/('%03d-%s-1125.json'%(priority,tag));atom(jp,job)\n"; assert old in s, 'claim anchor'
        s = s.replace(old, old + "   if job.get('tool')=='midm' and job['priority']==0:hand('claims 900 s midm_scan lkick,kick kick n=%d (seed 1125, boxE, job %s), start %s (byte snapshot %s, sha256 %s)'%(n,jp.name,p,dst,key.removeprefix('file:')))\n")
    if m == 'manage':
        # Round 30 12:45Z: the backlog 594 kick deferred on source30.credited_cells. Its input record names the union's
        # upstream donors as 'upstream per-n donors: owner/notebook :: submission.csv', which the old pattern missed.
        # _upstream now also reads the intake record of the snapshot and takes 'owner/name ::' references.
        old = " for q in (pathlib.Path(str(snap)+'.json'),):\n"; assert old in s, 'upstream anchor'
        s = s.replace(old, " for q in (pathlib.Path(str(snap)+'.json'),W/'intake'/(pathlib.Path(str(snap)).stem+'.json')):\n")
        old = "re.findall(r'(?:notebooks/|datasets/|upstream\\s+|->\\s*)([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)',txt)"; assert old in s, 'upstream regex'
        s = s.replace(old, "re.findall(r'(?:notebooks/|datasets/|upstream\\s+|->\\s*)([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)|([A-Za-z0-9_-]+/[A-Za-z0-9_-]+)\\s*::',txt)")
        old = "refs=sorted({r for r in re.findall("; assert old in s
        s = s.replace(old, "refs=sorted({(r[0] or r[1]) if isinstance(r,tuple) else r for r in re.findall(")
        s = s.replace("::',txt) if not r.startswith('areebbb/')})", "::',txt)} - {''})\n refs=[r for r in refs if not r.startswith('areebbb/')]")
    if m == 'worker':
        # Round 30 13:05Z: the backlog lane took our 594 midm row 2.1e-8 of score lower with one 180 s invent_rest lkick
        # (no fq inside) of our certified file; our own 900 s midm leg from the raw best had not moved. A midm kick that
        # moves now runs one 180 s invent_rest lkick from its best in the same job before the quench, so the row we
        # publish is already past that follow.
        old = "  m=['n=%d start %.12f best %.12f tries %d (midm lkick,kick)'%(n,start,best,tries)]\n"; assert old in s, 'midm lk anchor'
        new = ("  extra=''\n"
               "  if finds and best<start-1e-9 and time.time()+480<int(open('deadline').read()):\n"
               "   D2=D/'lk';D2.mkdir(exist_ok=True)\n"
               "   cmd2=[PY,'-I','lane/invent_rest.py',str(n),cur,str(D2),'--seconds','180','--seed',str(seed),'--modes','lkick','--bar',str(bar),'--deadline','deadline']\n"
               "   with open(D2/'run.log','w') as log:rc2=bounded(cmd2,limit=780,stdout=log,stderr=subprocess.STDOUT)\n"
               "   sl=D2/('slide-%d-%d.tsv'%(n,seed));lk_best=best;lk_cur=None;lk_tries=0\n"
               "   if sl.exists():\n"
               "    for line in sl.read_text().splitlines():\n"
               "     q=line.split('\\t')\n"
               "     if len(q)==7:lk_tries+=1\n"
               "     if len(q)==7 and q[-1]=='BEST' and float(q[3])<lk_best and (D2/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0]))).exists():lk_best=float(q[3]);lk_cur=str(D2/'raw'/('%d-sl%d-%s.csv'%(n,seed,q[0])))\n"
               "   event('LKICK AFTER MIDM %d %.12f -> %.12f tries %d rc %s'%(n,best,lk_best,lk_tries,rc2))\n"
               "   j['lkick_after']=dict(before=best,after=lk_best,tries=lk_tries,rc=rc2)\n"
               "   if lk_cur:best=lk_best;cur=lk_cur;extra=' + lkick 180 s'\n"
               "  m=['n=%d start %.12f best %.12f tries %d (midm lkick,kick%s)'%(n,start,best,tries,extra)]\n")
        s = s.replace(old, new)
    if m == 'manage':
        # Round 30 13:30Z: order the queue by the measured crossing rate (r28 and r29 boxE chains). Forensics rectangles
        # 0 to 1e-4 above the bar crossed 7 of 51 chains, 1e-4 to 2e-3 crossed 2 of 49, above 2e-3 0 of 9; modules 0 of
        # 24 and stair 0 of 11; fresh take rows (priority 0) 4 of 9. boxE is shared at load 40 to 55 and the queue
        # holds more than the 2 slots can run by 17:45.
        old = "   if hashlib.sha256(p.read_bytes()).hexdigest() in withdrawn_shas():"; assert old in s, 'order anchor'
        s = s.replace(old, "   if 1<=priority<50 and not long_kick and not isold:priority=1 if (lane in ('forensics','k123') and gap<1e-4) else 2 if (lane in ('forensics','k123') and gap<2e-3) else 6 if gap>2e-3 else 4\n" + old, 1)
    if m == 'manage':
        # Round 30 13:50Z: rebuild claimed a 900 s kick of the backlog 378 take row ('claim: 900 s ...') and we queued and
        # claimed the same file a minute later: the claim reader wanted ' claims ', skipped inputs of the backlog dir, and
        # the take-row override set priority 0 after the claim check. Now any 'claim'/'claims' line of another lane counts,
        # for every input lane, and also after the take-row override.
        old = "   if ' claims ' in line and ' twoshort -> ' not in line:c.update("; assert old in s, 'claim reader'
        s = s.replace(old, "   if re.search(r'\\bclaims?\\b',line) and ' twoshort -> ' not in line:c.update(")
        old = "   if lane!='backlog' and str(p) in backlog_claims():priority=max(priority,50)\n"; assert old in s, 'claim lane'
        s = s.replace(old, "   if str(p) in backlog_claims():priority=max(priority,50)\n")
        old = "    priority=0;job['priority']=0\n"; assert old in s, 'override anchor'
        s = s.replace(old, "    priority=0;job['priority']=0\n    if str(p) in backlog_claims():priority=50;job['priority']=50\n")
    if m == 'certify':
        # Round 30: each certified row also gets a CERT line in STATE.txt (the handoff line alone was the record).
        old = " print('KEEP',n,base[n]-s,live[n]-s)\n"; assert old in s, 'cert state anchor'
        s = s.replace(old, old + " open(T/'STATE.txt','a').write(time.strftime('%FT%TZ',time.gmtime())+' boxA CERT n=%d gain %.4g against bar30, %.4g below the live r30 rows, %s\\n'%(n,base[n]-s,live[n]-s,dst))\n")
    if m == 'certify':
        assert 'import finesafe as floatsafe' in s
    if m == 'bar':
        # Round 30 13:31Z: round 29 b was submitted (gate/cand-round29-1115b); the bar is the lower of bar30 and that file.
        old = " a={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round30-briefs/bar30.tsv'),delimiter='\\t')}\n return a\n"; assert old in s, 'bar anchor'
        s = s.replace(old, " a={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round30-briefs/bar30.tsv'),delimiter='\\t')}\n # Round 30 13:31Z: round 29 b (gate/cand-round29-1115b, Kaggle ref 58386105) is the newer held file; the bar is the lower of the two (376, 503).\n for r in csv.DictReader(open(B/'gate/cand-round29-1115b/details.csv')):\n  n=int(r['n']);a[n]=min(a[n],float(r['score']))\n return a\n")
    if m == 'manage':
        # Round 30 16:32Z: held rows of round 28 b that no kick line of rounds 28 to 30 names (work/reopen.txt, lane reopen-held28b)
        # get a 600 s midm kick. Border's held-row kicks crossed 2 of 13 (791 7.5e-5 of side at 300 s, 494 1.6e-4 at 900 s);
        # our last 12 kicks of fresh take rows crossed none.
        old = "long_kick=(lane in ('forensics','reopen-held27') and abs(gap)<1e-8)"; assert old in s, 'reopen-held'
        s = s.replace(old, "long_kick=((lane=='forensics' or lane.startswith('reopen-held')) and abs(gap)<1e-8)")
        old = 'seconds=900 if long_kick else 180,'; assert old in s, 'reopen-held'
        s = s.replace(old, "seconds=(600 if lane.startswith('reopen-held') else 900) if long_kick else 180,")
    (W / (m + '30.py')).write_text(s)
for m in SH:
    t = W / (m + '30.sh'); t.write_text(port((O / (m + '29.sh')).read_text())); t.chmod(0o755)
end = int(datetime.datetime(2026, 11, 15, 17, 45, tzinfo=datetime.timezone.utc).timestamp())
(W / 'deadline').write_text(str(end)); (W / 'search-deadline').write_text(str(end - 12 * 60))
if not (W.parent / 'take.tsv').exists():
    (W.parent / 'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
shutil.copy2(O / 'starts/control793.csv', W / 'starts/control793.csv')
shutil.copy2(O / 'bare-index.txt', W / 'bare-index.txt')
(W / 'NO-FAMILY-PROMOTE').write_text('round 30: family screens stay behind fresh layouts and legs\n')
print('setup complete', end, MODS, SH)
# Round 30: the two extra walkers (b walks the queue newest first, p walks live take rows, then forensics and k123 near files).
for name in ['qwalker29b.py', 'qwalker29p.py']:
    s = port((O / name).read_text()).replace('-r29/near/', '-r30/near/').replace('r29 lanes', 'r30 lanes')
    (W / name.replace('29', '30')).write_text(s)
