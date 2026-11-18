"""r36: keep the cap-3000 walks of the top donors ready, so dfeed36 does not wait on walks (two of these run, PART 0 and 1)."""
import csv, sys, hashlib, os, time
exec(open(__file__.replace('prewalk.py', 'dfeed36.py')).read().split('def pending')[0])
part = int(os.environ['PART'])
while time.time() < END - 1500:
    try:
        rows = list(csv.DictReader(open(W / 'rank/donors.tsv'), delimiter='\t'))
        c = [r for r in rows if float(r['room']) > 0 and not (float(r['above']) >= 1e-4 and float(r['room']) < 1e-4) and int(r['claims']) < 2 and float(r['above']) >= 1e-8][:60]
        todo = [r for r in c if not any((W / 'walks').glob(r['sha16'] + '*.json'))]
        for i, r in enumerate(todo[:6]):
            if i % 2 != part: continue
            full = hashlib.sha256(open(r['path'], 'rb').read()).hexdigest()
            print(time.strftime('%H:%M:%S'), r['n'], r['sha16'], walk(r['path'], full), flush=True)
    except Exception as e: print('err', e, flush=True)
    time.sleep(30)
