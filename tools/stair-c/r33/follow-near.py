"""Pin a close own composition for certified-file fq and one bounded kick."""
import hashlib
import json
import math
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parents[3])]
import coordinator as C

def plain_metadata(meta):
    result=dict(meta,whole_kick=False)
    previous=result.pop('source_kick',None)
    if previous and previous.get('invoked'):
        result['previous_kick']=previous
        result['after_kick']=True
    return result

def stage_target(target, rows, meta):
    target=pathlib.Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    side=target.with_suffix('.json')
    if target.exists():
        old=json.loads(side.read_text())
        assert old['source_sha256']==meta['source_sha256'],'Changed input at existing target'
        coords=lambda rr:[tuple(str(r[k])for k in['n','square_id','x','y','angle'])for r in rr]
        assert coords(C.rows(str(target)))==coords(rows),'Changed certified coordinates at existing target'
        return True
    C.write(str(target),rows)
    temp=side.with_suffix('.json.tmp');temp.write_text(json.dumps(meta,indent=2));temp.replace(side)
    return False


def eligible(n, margin):
    m = math.isqrt(n - 1)
    return 28 <= m <= 31 and 17 <= n - m * m <= 45 and margin < (.0002 if n == 805 else .00002)


def offer(path):
    path = pathlib.Path(path).resolve()
    assert path.parent == pathlib.Path(C.TAKE, 'near').resolve()
    n = int(path.name.split('-')[0])
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    meta = plain_metadata(C.manifest(json.loads(path.with_suffix('.csv.json').read_text())))
    complete = C.full_admission(str(path), n, meta)
    assert complete is not None, 'Unresolved full CSV ancestry'
    meta['source'] += '; full-input source walk ' + complete['source']
    _, rows, score, reason = C.floatsafe.work((n, C.rows(str(path))))
    assert rows is not None, reason
    side = (1 + score) * math.sqrt(n)
    margin = side - (1 + C.bar()[n]) * math.sqrt(n)
    assert eligible(n, margin), (n, margin)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    snapshot = pathlib.Path(C.WORK, 'donors', f'own-near-{n}-{digest[:12]}.csv')
    snapshot.write_bytes(payload)
    target = pathlib.Path(C.WORK, 'cert-in', f'{n}-own-near-{digest[:12]}.csv')
    meta.update(whole_layout_follow=True, own_near_follow=True,
                source_snapshot=str(snapshot), source_sha256=digest,
                built=side, predicted=side)
    reused=stage_target(target,rows,meta)
    host = C.HOSTS[n % 3][0]
    result = subprocess.run(['rsync', '-a', str(target), str(target.with_suffix('.json')),
                             host + ':scratch/squares-stair-c/cert-in/'],
                            capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stderr
    C.state(f'START own-near{n} certified-file fq on {host}; snapshot {snapshot} '
            f'sha256 {digest}; side margin {margin!r}. kick_follow offers one bounded '
            'leg from this certified file. Log worker.log; deadline00:15Z on November16.')
    print(json.dumps(dict(n=n, side=side, margin=margin, sha256=digest, host=host,reused=reused)))


if __name__ == '__main__':
    if sys.argv[1] == '--control':
        assert eligible(805, .00015)
        assert not eligible(805, .00025)
        assert eligible(871, .0000024)
        assert not eligible(871, .00003)
        assert not eligible(915, .0000024)
        print('CONTROL own near: source-cleared805 at+.00015 and close871 admitted; far805, far871 and count915 refused')
    else:
        offer(sys.argv[1])
