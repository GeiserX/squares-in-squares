"""Allow one active layout per count across the three slots."""
import pathlib

def claim(root, job):
 root=pathlib.Path(root);lock=root/'locks'/job['id'];active=root/'active'/str(job['n'])
 lock.parent.mkdir(exist_ok=True);active.parent.mkdir(exist_ok=True)
 try:lock.mkdir()
 except FileExistsError:return False
 try:active.mkdir()
 except FileExistsError:lock.rmdir();return False
 return True

def release(root, job):
 (pathlib.Path(root)/'active'/str(job['n'])).rmdir()
