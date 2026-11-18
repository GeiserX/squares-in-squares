"""Compare full poses without relying on rounded-coordinate hash bins."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree
import forensics_compose as fc
import forensics_rect as rect


def same(left, right, tolerance=1e-6):
    if len(left) != len(right):
        return False
    side, a = fc.frame(left)
    _, b = fc.frame(right)
    target = np.column_stack((b[:, :2], np.cos(4*b[:, 2]), np.sin(4*b[:, 2])))
    tree = cKDTree(target)
    for _, q in rect.sym8(a, side):
        pose = np.column_stack((q[:, :2], np.cos(4*q[:, 2]), np.sin(4*q[:, 2])))
        distance, index = tree.query(pose)
        if len(np.unique(index)) == len(b) and np.max(distance) <= tolerance:
            return True
    return False


def control():
    a = np.array([[.5, .5, 0.], [1.5, .5, 0.], [.5, 1.5, .02]])
    shifted = a.copy()
    shifted[:, :2] += [13., -5.]
    assert same(a, shifted)
    turned = a.copy()
    turned[:, :2] = a[:, 1::-1]
    turned[:, 2] = np.pi/2-a[:, 2]
    assert same(a, turned)
    noisy = a.copy()
    noisy[0, 0] += 1e-9
    assert same(a, noisy)
    changed = a.copy()
    changed[1, 0] += .02
    assert not same(a, changed)
    assert not same(a, a[:2])
    print('CONTROL full-pose translation, reflection and noise match; changed spacing and count fail', flush=True)


if __name__ == '__main__':
    control()
