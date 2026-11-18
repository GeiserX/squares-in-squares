import pathlib,subprocess,sys,time
root=pathlib.Path('finalwindow-control');root.mkdir(exist_ok=True);(root/'NO_NEW_BUILDS').touch();(root/'deadline').write_text(str(time.time()+60));(root/'quench22.py').write_text("open('allowed','w').write('quench')\n")
if (root/'allowed').exists():(root/'allowed').unlink()
guard=str(pathlib.Path('guard.py').resolve())
a=subprocess.run([sys.executable,'-I',guard,sys.executable,'-c',"raise RuntimeError('search should not run')"],cwd=root,capture_output=True,text=True)
assert a.returncode==0 and 'FINAL WINDOW' in a.stdout
b=subprocess.run([sys.executable,'-I',guard,sys.executable,'quench22.py'],cwd=root,check=True)
assert (root/'allowed').read_text()=='quench'
print('CONTROL final window blocked search and allowed certified-quench command',flush=True)
