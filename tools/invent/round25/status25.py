import pathlib,json,csv,collections,datetime
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
csv.field_size_limit(32*1024*1024)
j=json.load(open(W/'jobs.json'));done=[json.load(open(p))for p in (W/'boxE-raw').glob('*/done.json')];rs=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'))
print(json.dumps(dict(time=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ'),jobs=len(j),kinds=dict(collections.Counter(v['kind']for v in j)),completed=len(done),errors=sum('error'in v for v in done),retained=[int(r['n'])for r in rs],gain=sum(float(r['gain'])for r in rs),deferred=json.load(open(W/'deferred.json'))if(W/'deferred.json').exists()else[],latest=(W/'controller.log').read_text().splitlines()[-1])))
