"""Tabulate a corner near its own fraction and retain the original table shape."""
import numpy as np
import modules as M

def tabulate(q,span=.015):
    grid=M.GRID
    keep=np.flatnonzero(abs(grid-q['f0'])<=span+1e-9)
    assert len(keep)>=2
    M.GRID=grid[keep]
    try:result=M.tabulate(q)
    finally:M.GRID=grid
    table=np.full((len(M.COST),2,len(grid)),np.nan)
    table[:,:,keep]=result['tab']
    return dict(result,tab=table,sparse_grid_indices=keep.tolist(),sparse_span=span)
