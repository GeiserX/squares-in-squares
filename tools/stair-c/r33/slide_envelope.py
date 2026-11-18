"""Propagate core-edge slides instead of accepting an overlapping native layout."""
import ast,inspect
import modules as M
import corner_paths as C
INSTALLED=False

def install():
 global INSTALLED
 if INSTALLED:return
 C.install();tree=ast.parse(inspect.getsource(M.assemble));changed=[]
 repair='''for i in range(ni - 1):
    if (i, 0) not in gone and (i + 1, 0) not in gone:
        old = off[(i + 1, 0)]
        off[(i + 1, 0)] = (max(old[0], off[(i, 0)][0]), old[1])
for j in range(nj - 1):
    if (0, j) not in gone and (0, j + 1) not in gone:
        old = off[(0, j + 1)]
        off[(0, j + 1)] = (old[0], max(old[1], off[(0, j)][1]))
'''
 class Patch(ast.NodeTransformer):
  def visit_Return(self,node):
   if isinstance(node.value,ast.Tuple)and any(isinstance(v,ast.Constant)and v.value=='the corner grants a far zone no slide'for v in node.value.elts):
    changed.append(True);return ast.parse(repair).body
   return node
 tree=Patch().visit(tree);ast.fix_missing_locations(tree);assert len(changed)==1
 ns=dict(M.__dict__);exec(compile(tree,'stair-c-slide-envelope','exec'),ns);M.assemble=ns['assemble'];INSTALLED=True
