"""Construct the known row jog and its two-axis extension as integer cell sets."""
def row(width,height,p):
 return {(i,j) for j in range(height) for i in range(1 if j<p else 0,width+(1 if j<p else 0)+(1 if j==p else 0))}
def double(width,height,p,c):
 out=set()
 for i,j in row(width,height,p):
  out.add((i,j-1) if i<=c else (i,j))
  if i==c+1:out.add((i,j-1))
 # Frame the ordinary13x13 core as1..13 in the15x15 candidate grid.
 return {(i+1,j+1) for i,j in out}
