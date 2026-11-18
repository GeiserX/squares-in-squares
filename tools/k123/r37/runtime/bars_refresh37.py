from pathlib import Path
import csv
import fcntl
import math
import os

WORK = Path(__file__).resolve().parent
SCRATCH = WORK.parent.parent


def refresh():
    csv.field_size_limit(1 << 28)
    with (SCRATCH / 'round37-briefs/bar37.tsv').open() as stream:
        scores = {int(row['n']): (float(row['bar']), 'held') for row in csv.DictReader(stream, delimiter='\t')}
    for table in SCRATCH.glob('take-*-r37/take.tsv'):
        with table.open() as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                count = int(row['n'])
                score = float(row['new'])
                packing = table.parent / (str(count) + '.csv')
                if math.isfinite(score) and packing.exists() and score < scores[count][0]:
                    scores[count] = score, str(packing)
    with (WORK / 'base.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        temporary = WORK / ('bars-live37.' + str(os.getpid()) + '.tmp')
        temporary.write_text(''.join(f'{count}\t{(score + 1) * count ** .5:.14f}\t{score!r}\t{origin}\n' for count, (score, origin) in sorted(scores.items())))
        temporary.replace(WORK / 'bars.tsv')
    return sum(origin != 'held' for score, origin in scores.values())


if __name__ == '__main__':
    print(refresh())
