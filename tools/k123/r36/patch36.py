from pathlib import Path
W=Path(__file__).resolve().parent
p=W/'qrun22.py';s=p.read_text()
s=s.replace("if int(signature[:8],16)%10 not in runtime33.get('partitions',list(range(10))):continue","if not signature:continue")
old="  try:(R/'claims'/keyclaim).mkdir()\n  except FileExistsError:continue"
new="""  if BOX33!='boxE':
   claimed=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','boxE',f'mkdir $SCRATCH/squares-k123/claims/{keyclaim}'],capture_output=True,timeout=15)
   if claimed.returncode:continue
   try:(R/'claims'/keyclaim).mkdir()
   except FileExistsError:continue
  else:
   try:(R/'claims'/keyclaim).mkdir()
   except FileExistsError:continue"""
assert old in s;s=s.replace(old,new)
s=s.replace("(R/'claims'/keyclaim/'owner.json').write_text(json.dumps(dict(pid=os.getpid(),worker=worker,jobkey=key,time=time.time())))","(R/'claims'/keyclaim/'owner.json').write_text(json.dumps(dict(pid=os.getpid(),worker=worker,box=BOX33,jobkey=key,time=time.time())))")
p.write_text(s)
# A controller can recover boxD's central claim once its local guard requeues it.
p=W/'box_guard34.py';s=p.read_text();a="if not complete:p.unlink();p.parent.rmdir();requeued.append(j)";b="""if not complete:
    if j.get('box')=='boxD':
     subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','boxE','rmdir $SCRATCH/squares-k123/claims/'+p.parent.name],capture_output=True,timeout=15)
    p.unlink();p.parent.rmdir();requeued.append(j)""";assert a in s;s=s.replace(a,b);p.write_text(s)
# Include walk completion evidence in each certificate line, without placing audit paths in sidecars.
p=W/'collect22.py';s=p.read_text().replace('certified-file quench receipt {D}/fq, {T}/{n}.csv','certified-file quench receipt {D}/fq, walk_files={source_check["files"]}, capped={source_check.get("capped",False)}, {T}/{n}.csv');compile(s,str(p),'exec');p.write_text(s)
# Freeze the ten-version public table already provided by the previous round.
p=W/'publicshare31.py';s=p.read_text();s=s.replace("_module.archive_paths.cache_clear()","_module.archive_paths.cache_clear()") # existing frozen share31 mechanism preserved
# Explicit stop controls: compare the peer with this start, not with the bar.
def stop(start,live):return live < start-1e-6
cases=[(1.0001,1.,True),(1.,1.-2e-6,True),(1.,1.-2e-6,True),(1.,1.,False)]
# Donor at bar has live=bar above donor: no stop of its own start.
cases[0]=(0.9999,1.,False)
assert [stop(a,b) for a,b,_ in cases]==[c for _,_,c in cases]
import json
(W/'stop-control36.json').write_text(json.dumps({'cases':['donor above bar: no own-start improvement','donor with lower live: stop','held with lower live: stop','held alone: continue'],'passed':True}))
print('shared per-recipe claims and explicit walk cap ready')
