import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import urllib.request,pathlib,ssl,certifi,json,datetime
base=(legacy_root()/'data');(base/'source_checks').mkdir(exist_ok=True)
ctx=ssl.create_default_context(cafile=certifi.where())
urls={'hf_metadata':'https://huggingface.co/api/datasets/lj408/Dis2Pat','US9514753B2':'https://patents.google.com/patent/US9514753B2/en','US10867122B1':'https://patents.google.com/patent/US10867122B1/en'}
for name,url in urls.items():
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),context=ctx,timeout=25) as res: raw=res.read(5_000_001)
  if len(raw)>5_000_000: raise ValueError('source size cap exceeded')
  (base/'source_checks'/f'{name}.{"json" if name=="hf_metadata" else "html"}').write_bytes(raw)
  print(name,'ok',len(raw))
 except Exception as e: print(name,type(e).__name__,str(e))
