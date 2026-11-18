from pathlib import Path
import pickle,json,csv,sys,hashlib,shutil,math,time
W=Path(__file__).parent;B=W.parent.parent;O=B/'take-twoshort-r24/work/boxE24'
sys.path.insert(0,str(W));from admit25 import module_allowed,store;from bar25 import bars
base,_,_,live=bars();bar={str(n):(s+1)*math.sqrt(n) for n,s in live.items()};(W/'bar.json').write_text(json.dumps(bar))
with open(W/'details-bar.csv','w',newline='') as f:
 cw=csv.writer(f);cw.writerow(['n','L','score','min_gap']);cw.writerows([n,bar[str(n)],live[n],2.2e-11] for n in sorted(live))
stats=[]
claims=(B/'handoff-r25.log').read_text()
for d in sorted((O/'designs').iterdir()):
 if not (d/'unstarted.json').exists():continue
 rows=json.load(open(d/'unstarted.json'))
 if not rows:continue
 if any('backlog ->' in l and d.name in l and 'claim' in l.lower() for l in claims.splitlines()):continue
 lib=pickle.load(open(d/'lib/library.pkl','rb'));lens=pickle.load(open(d/'lib/lens.pkl','rb'));want={r[k] for r in rows for k in ['corner','far1','far2']}
 good={m['id'] for m in lib['mods'] if m['id'] in want and module_allowed(m)}
 clean=[r for r in rows if all(r[k] in good for k in ['corner','far1','far2'])]
 clean.sort(key=lambda r:float(r.get('predicted_side',r.get('predicted',float(r.get('held_side',bar[r['n']]))+float(r.get('predicted_minus_held',0)))))-bar[r['n']])
 stats.append(dict(origin=str(d),total=len(rows),clean=len(clean),dropped=len(rows)-len(clean)))
 if not clean:continue
 tag='saved25-'+d.name;dd=W/'designs'/tag;(dd/'lib').mkdir(parents=True,exist_ok=True)
 want={r[k] for r in clean for k in ['corner','far1','far2']};lib['mods']=[m for m in lib['mods'] if m['id'] in want];lib['layouts']=[]
 pickle.dump(lib,open(dd/'lib/library.pkl','wb'));pickle.dump({k:v for k,v in lens.items() if k in want},open(dd/'lib/lens.pkl','wb'))
 (dd/'specifications.json').write_text(json.dumps(clean,indent=2));(dd/'intake.json').write_text(json.dumps(stats[-1],indent=2))
 priority=10+len(stats);job=dict(kind='specs',tag=tag,priority=priority)
 (W/'jobs'/('%03d-%s.json'%(priority,tag))).write_text(json.dumps(job))
 with open(B/'handoff-r25.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> backlog: CLAIM saved specification batch '+d.name+' ('+str(len(clean))+' clean items), '+str(dd/'specifications.json')+'\n')
(W/'pending-admission.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats));print('clean',sum(x['clean'] for x in stats),'total',sum(x['total'] for x in stats))
