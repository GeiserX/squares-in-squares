import pathlib,sys,subprocess,json,csv,shutil
csv.field_size_limit(16*1024*1024)
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));from policy24 import classify
assert classify('held n = 365 of Samanyu-dev/squares_in_squares','no licence')['seeds']==[365]
assert classify('public Apache own design','ours')['status']=='none'
assert classify('Samanyu source with no seed count','unknown')['status']=='unknown'
assert classify('983h.F1 <held: seed merged0>; 804h.F2 <held: seed merged0>','see README')['seeds']==[804,983]
C=W/'policy-control';C.mkdir(exist_ok=True)
raw=W/'boxE-raw/f204516x503x167/final';sc=json.load(open(raw.parent/'done.json'))['new']
s=(W/'certrest-policy24.py').read_text().replace('# CONTROL_OVERRIDE',f'held[503]={sc-1e-5!r};held22[503]={sc+1e-5!r};bar[503]={sc-2e-5!r};freebar[503]={sc+1e-5!r}')
script=C/'certrest-control.py';script.write_text(s)
for name,source,lic,expected in [('free','public Apache own design','Apache 2.0',1),('seed','n = 365 of Samanyu-dev/squares_in_squares','no licence',0),('unknown','Samanyu source unresolved','unresolved',0)]:
 t=C/name;t.mkdir(exist_ok=True)
 for p in t.glob('*'):p.unlink()
 p=subprocess.run([sys.executable,'-I',str(script),str(t),str(raw)+'|'+source+'|'+lic],text=True,capture_output=True,check=True)
 rs=list(csv.DictReader(open(t/'take.tsv'),delimiter='\t'));assert len(rs)==expected,(name,p.stdout,p.stderr)
 print('CONTROL',name,'accepted',len(rs),'expected',expected)
(C/'result.json').write_text(json.dumps(dict(free_above_original_candidate_accepted=True,lower_seed_bar_does_not_mask_free=True,seeded_above_original_candidate_rejected=True,unknown_rejected=True,seed_804_983_aliases_resolved=True)))
