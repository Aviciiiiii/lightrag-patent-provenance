import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from datetime import datetime, timezone
import os, json, hashlib, signal, zipfile

signal.alarm(45)
root = legacy_root()
files=[]
for name in ['data','evidence','results','scripts','report','logs']:
    for parent, dirs, names in os.walk(root/name, followlinks=False):
        dirs[:] = [d for d in dirs if d!='__pycache__']
        for name in names:
            p=Path(parent)/name
            if p.is_file() and p.stat().st_size and not p.is_symlink():
                files.append(p)
    print('collected',name,len(files),flush=True)
hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
print('hashed',len(hashes),flush=True)
archive=root/'LightRAG_patent_provenance_evidence_20261029.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
    z.writestr('README.txt',
        'Open report/LightRAG_patent_provenance_report_zh.html in a browser.\n'
        'PARTIAL RESULT: no official LightRAG index or LLM query completed.\n'
        'Model/embedding service unavailable in this execution environment; zero paid model calls.\n'
        'Actual official v1.5.7 chunker:20 patents,42087 tokens,48 chunks,1200/100.\n'
        'All 10 query records are not_run; no synthetic answers.\n'
        'Raw data, exact official source archive, evidence and reproduction scripts included.\n'
        'No credentials, model weights or virtual environment included.\n'
        'Review was AI-assisted, not an independent human gold standard.\n')
    z.writestr('artifact_checksums.json',json.dumps(hashes,sort_keys=True,indent=2))
    for i,p in enumerate(sorted(files)):
        z.write(p,p.relative_to(root))
        if i%30==0:print('packed',i,flush=True)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
result={'utc':datetime.now(timezone.utc).isoformat(),'files':len(files)+2,
        'zip_path':str(archive),'bytes':archive.stat().st_size,
        'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(root/'artifact_package_status.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2),flush=True)
