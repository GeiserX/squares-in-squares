import pathlib, json, shutil,csv,math,time
B=pathlib.Path('$SCRATCH/bounties-squares'); T=B/'take-twoshort-r22'; W=T/'work'; S=B/'take-twoshort-r21/work/boxE21'
for d in ['lane','starts','jobs','locks','runs','done','q','tmp']: (W/d).mkdir(exist_ok=True)
for p in pathlib.Path('.').glob('*.py'):shutil.copy2(p,W/'lane'/p.name)
held=list(csv.DictReader(open(B/'gate/cand-round20-1113a/details.csv'))); bar={int(r['n']):float(r['score']) for r in held}
for t in list(B.glob('take-*-r21/take.tsv'))+list(B.glob('take-*-r22/take.tsv')):
 for r in csv.DictReader(open(t),delimiter='\t'):
  try:n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
  except:pass
json.dump({str(n):(1+s)*math.sqrt(n) for n,s in bar.items()},open(W/'bar.json','w'))
(W/'deadline').write_text(str(int(time.mktime(time.strptime('2026-11-13 15:20:00','%Y-%m-%d %H:%M:%S'))-time.timezone)))
starts=[('control793',793,'scr-cd6800s6/793-91947552',21,1,60,0),('911a',911,'scr-xhp/911-2576829e',122,5,300,1),('794a',794,'scr-e36948/794-a25d9cdf',122,5,300,1),('852a',852,'scr-f46760/852-990f7716',122,4,300,2),('974a',974,'scr-xhk/974-e3b6ea1a',122,4,300,3),('793h',793,'scr-hp96/793-25d7a44b',122,5,300,4),('794c',794,'scr-cm7120/794-6e645725',122,4,300,4),('853c',853,'scr-e36948/853-767010ad',122,5,300,5)]
for tag,n,p,seed,steps,secs,pri in starts:
 src=S/(p+'.csv');dst=W/'starts'/(tag+'.csv');shutil.copy2(src,dst)
 md=json.load(open(S/(p+'.json')));json.dump(md,open(dst.with_suffix('.json'),'w'),indent=2)
 job=dict(tag=tag,n=n,start='starts/'+dst.name,seed=seed,remaining=steps,seconds=secs,miss=0,priority=pri,source='twoshort family build '+str(src)+'; modules '+json.dumps(md['modules']),licence='our own design')
 json.dump(job,open(W/'jobs'/('%03d-%s-%d.json'%(pri,tag,seed)),'w'))
