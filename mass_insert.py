from pathlib import Path
import os

files=[]
for path in Path("/home/aaron/Downloads/gcn_notice_dir/").rglob('*.xml'):
    fullpath=path.resolve()
    files.append(fullpath)

for file in files:
    os.system(f"python3 gcnlistener.py {file}")