import pathlib,json,csv,math,time
csv.field_size_limit(16*1024*1024)
W=pathlib.Path(__file__).resolve().parent;js=json.load(open(W/'jobs.json'));done={p.parent.name:json.load(open(p))for p in(W/'boxE-raw').glob('*/done.json')}
old=json.load(open(W/'watch-seen.json'))if(W/'watch-seen.json').exists()else[]
for j in js:
 d=done.get(j['id'])
 if not d or j['id']in old:continue
 print('FINISHED',j['id'],'n',j['n'],'kind',j['kind'],'raw',d.get('raw'),'side_gain',round(j['side']-(d['new']+1)*math.sqrt(j['n']),10)if 'new'in d else None,'ERROR',d.get('error'))
rs=list(csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t'))
original={int(r['n']):float(r['score']) for r in csv.DictReader(open(W.parent.parent/'gate/cand-round23-1113a/details.csv'))}
print(time.strftime('%H:%M:%SZ',time.gmtime()),'finished',sum(j['id'] in done and j['kind']!='control' for j in js),'saved',sum(bool(j.get('backlog'))and j['id']in done for j in js),'/47 eligible','queued',len(js)-len(done),'take',[int(r['n'])for r in rs],'candidate_gain',sum(original[int(r['n'])]-float(r['new'])for r in rs))
(W/'watch-seen.json').write_text(json.dumps(list(done)))
log=(W/'controller.log').read_text().splitlines();print(log[-1]if log else 'no completed collection pass')

hp=W.parent.parent/'handoff-r24.log';lines=hp.read_text().splitlines();mark=W/'watch-handoff-count'
old=int(mark.read_text()) if mark.exists() else len(lines)
for line in lines[old:]:
 if 'main ->' in line or 'WITHDRAW' in line or 'prohibited' in line.lower():print('HANDOFF',line[:4000])
mark.write_text(str(len(lines)))
