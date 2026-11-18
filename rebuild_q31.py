"""q28.py BOX KEY N SRC [MODE]: pin SRC (byte copy, sha256) and queue one rebuild_run job on BOX (mm = boxB, st = boxE).
MODE: '' (turn + fq loop), 'quench', 'kick:SECONDS'. Appends one line to work/queue-log.tsv (time, box, key, n, src, sha256, pin, mode)."""
import csv, hashlib, math, os, shutil, subprocess, sys, time
# quench jobs first, then kicks of our own rows (k2- and up), then follow kicks of fresh rows (f-), then insert, rectangle or held kicks (i-, x-, h-), then the rest
REORDER = "{ awk -F'\\t' '$5==\"quench\"' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^k[2-9]-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^s-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^f-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 ~ /^[ixh]-/' queue.tsv; awk -F'\\t' '$5!=\"quench\" && $1 !~ /^k[2-9]-/ && $1 !~ /^s-/ && $1 !~ /^f-/ && $1 !~ /^[ixh]-/' queue.tsv; } > queue.ord && mv queue.ord queue.tsv"
S = '$SCRATCH/bounties-squares/'
W = S + 'take-rebuild-r31/work/'
box, key, n, src = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
mode = sys.argv[5] if len(sys.argv) > 5 else ''
src = src if src.startswith('/') else S + src
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S + 'take-rebuild-r31/work/bar31.tsv'), delimiter='\t')}
b = open(src, 'rb').read(); sha = hashlib.sha256(b).hexdigest()
os.makedirs(W + 'pins', exist_ok=True)
pin = W + 'pins/%d-%s.csv' % (n, sha[:16])
if not os.path.isfile(pin):
    open(pin, 'wb').write(b)
for ext in ('.json', '.origin.json'):
    if os.path.isfile(src + ext) and not os.path.isfile(pin + ext):
        shutil.copy2(src + ext, pin + ext)
host, root = {'boxB': ('boxB', '$SCRATCH/squares-rebuild'), 'boxE': ('boxE', 'scratch/squares-rebuild'), 'boxD': ('boxD', 'scratch/squares-rebuild')}[box]
rel = 'starts/%d-%s.csv' % (n, sha[:16])
subprocess.run(['scp', '-q', pin, '%s:%s/%s' % (host, root, rel)], check=True)
line = '\t'.join([key, str(n), '%.12f' % ((1 + bar[n]) * math.sqrt(n)), rel] + ([mode] if mode else []))
if os.environ.get('FRONT') == '1':  # place it first: the worker reads the queue in file order
    subprocess.run(['ssh', host, ('cd %s && { cat; cat queue.tsv; } > queue.new && mv queue.new queue.tsv && ' % root) + REORDER], input=(line + '\n').encode(), check=True)
else:
    subprocess.run(['ssh', host, 'cat >> %s/queue.tsv' % root], input=(line + '\n').encode(), check=True)
with open(W + 'queue-log.tsv', 'a') as h:
    h.write('\t'.join([time.strftime('%H:%M:%SZ', time.gmtime()), box, key, str(n), src.replace(S, ''), sha, pin.replace(S, ''), mode]) + '\n')
print(line)
