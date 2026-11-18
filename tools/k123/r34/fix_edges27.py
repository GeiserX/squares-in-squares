import pathlib,re,json,time
W=pathlib.Path(__file__).resolve().parent;R=pathlib.Path('.')
p=W/'policy_walk27.py';s=p.read_text();shared=(R/'quench_walk.py').read_text();block=shared[shared.index('_tree = {}'):shared.index('def walk(start, n, cap=3000):')];s=s.replace('def walk(start, n, cap=3000):',block+'def walk(start, n, cap=3000):')
s=s.replace("            if not os.path.isfile(p):\n                if not t:","            if not os.path.isfile(p) and not t:\n                mv=moved_copy(p)\n                if mv:\n                    queue.append(mv);via.setdefault(mv,p);texts.append((p,'moved copy: '+mv));continue\n            if not os.path.isfile(p):\n                if not t:")
p.write_text(s)
p=W/'source25.py';s=p.read_text().replace("   if str(p) in seen:continue", "   if not p.exists():\n    moved=walker.moved_copy(str(p))\n    if moved:p=pathlib.Path(moved)\n   if str(p) in seen:continue")
s=s.replace("    records.append({'path':str(p),'record':j});queue.append(j)","    if p.exists():records.append({'path':str(p),'record':j})\n    else:records.append({'source_record_kind':'historical held record','record':j})\n    queue.append(j)")
s=s.replace("'walked_paths':sorted(seen)","'walked_paths':sorted(p for p in seen if pathlib.Path(p).exists())")
s=s.replace('r27-full-tree-v2:','r27-full-tree-v3:');p.write_text(s)
for name in ['stage24.py','collect22.py']:
 p=W/name;p.write_text(p.read_text().replace('r27-full-tree-v2:','r27-full-tree-v3:'))
p=W/'collect-state.json'
if p.exists():
 d=json.load(open(p))
 for k in list(d):
  if d[k].get('n')==932 and d[k]['status']=='source-refused':del d[k]
 p.write_text(json.dumps(d,indent=2))
# Retry only the known corrected932 entry. Other measured refusals remain cached by version.
p=W/'fresh-seen.json'
if p.exists():
 d=json.load(open(p));d.pop(str(W/'reopened/932-reopened-r26.csv'),None);p.write_text(json.dumps(d))
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FIX audit metadata had promoted a missing historical harvest703 under accepted held597 to a direct source edge. Keep its resolved historical record without inventing a current CSV edge. Added the shared walk moved-copy lookup for distinctive archived source names. Recheck932 through complete publication walker, retain missing-parent refusals. Deadline07:25Z.\n')
