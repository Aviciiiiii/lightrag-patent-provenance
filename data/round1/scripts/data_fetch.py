import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import urllib.request,urllib.parse,json,pathlib,ssl,certifi,datetime,sys
base=(legacy_root()/'data')
ctx=ssl.create_default_context(cafile=certifi.where())
offset=int(sys.argv[1]) if len(sys.argv)>1 else 0
url='https://datasets-server.huggingface.co/rows?'+urllib.parse.urlencode({'dataset':'lj408/Dis2Pat','config':'default','split':'train','offset':offset,'length':100})
req=urllib.request.Request(url,headers={'User-Agent':'LightRAG-Patent-Provenance-Experiment/1.0'})
with urllib.request.urlopen(req,context=ctx,timeout=35) as res:
 raw=res.read(30_000_001); headers=dict(res.headers)
if len(raw)>30_000_000: raise RuntimeError('Small batch size cap exceeded')
p=base/f'dis2pat_train_rows_{offset:04d}.json';p.write_bytes(raw)
(base/f'dis2pat_train_rows_{offset:04d}.source.json').write_text(json.dumps({'url':url,'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'headers':headers,'bytes':len(raw)},indent=2))
d=json.loads(raw)
print('bytes',len(raw),'total',d.get('num_rows_total'),'rows',len(d.get('rows',[])))
for row in d.get('rows',[]):
 r=row['row'];print(row['row_idx'],r['publication_number'],r['title'],len(r.get('claims','')),row.get('truncated_cells'))
