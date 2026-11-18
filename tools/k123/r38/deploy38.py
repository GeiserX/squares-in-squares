from pathlib import Path
import json
import shutil
import subprocess
import tarfile

SCRATCH = Path('$SCRATCH/bounties-squares')
WORK = SCRATCH / 'take-k123-r38/work'


def deploy():
    shutil.copy(SCRATCH / 'take-k123-r33/work/fq-boxCD33', WORK / 'fq')
    for host in ['boxE', 'boxD']:
        configuration = WORK if host == 'boxE' else WORK / host
        config = json.loads((configuration / 'runtime33.json').read_text())
        archive = WORK / (host + '-boot38.tgz')
        with tarfile.open(archive, 'w:gz') as bundle:
            for source in WORK.glob('*.py'):
                bundle.add(source, arcname=source.name)
            for name in ['deadline', 'search-deadline', 'own-follow-deadline', 'details-base25.csv', 'completed-geometries26.json', 'queue.tsv', 'refused-inputs26.json', '444-control.csv', 'board.tsv', 'enable-wide30', 'fq']:
                bundle.add(WORK / name, arcname=name)
            for name in ['runtime33.json', 'box33']:
                bundle.add(configuration / name, arcname=name)
            bundle.add(WORK / 'lane', arcname='lane')
        subprocess.run(['ssh', host, 'test ! -d $SCRATCH/squares-k123 && mkdir -p $SCRATCH/squares-k123/out $SCRATCH/squares-k123/claims $SCRATCH/squares-k123/tasks $SCRATCH/squares-k123/taskdone'], check=True, timeout=30)
        subprocess.run(['scp', '-q', str(archive), host + ':scratch/squares-k123/boot38.tgz'], check=True, timeout=90)
        subprocess.run(['ssh', host, 'cd $SCRATCH/squares-k123 && tar xzf boot38.tgz && rm boot38.tgz && chmod +x fq'], check=True, timeout=60)
        command = f'cd $SCRATCH/squares-k123 && {config["python"]} -I lane/k123_turn.py 444-control.csv 444 control444 {config["fq"]} --turns=0 --modes self --loosen 1.001 --bar 21.5647 --keep'
        result = subprocess.run(['ssh', host, command], check=True, text=True, capture_output=True, timeout=180)
        (configuration / 'control444.log').write_text(result.stdout + result.stderr)
        output = subprocess.check_output(['ssh', host, 'cat $SCRATCH/squares-k123/control444/turn-444.tsv'], text=True, timeout=30)
        assert '21.564693167754' in output, output
        receipt = {'side': 21.564693167754, 'output': output, 'passed': True}
        (configuration / 'control38.json').write_text(json.dumps(receipt))
        print(host, json.dumps(receipt), flush=True)


if __name__ == '__main__':
    deploy()
