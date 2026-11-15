import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import ENV_FILE  # path mapping only, see paths.py
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED
from collections import defaultdict
from io import BytesIO
import datetime, hashlib, json, re
from dotenv import dotenv_values

D=Path(__file__).resolve().parent
R=D.parent
ORIGINAL=R/'LightRAG_chunk_boundary_full_evidence_20261030.zip'
EXPECTED='db4d11eae19ad74dd74f4d267ad08e869f8f2d5272b10fb8eaef4cb5e3837a7b'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(ORIGINAL.read_bytes())==EXPECTED
keys=[v.encode() for k,v in dotenv_values(str(ENV_FILE)).items() if k.endswith('_API_KEY') and v]
assert keys, 'Credential exclusion could not be checked'
names=['LightRAG_evidence_1_report_scripts_and_calls.zip','LightRAG_evidence_2_graphs_and_indexes.zip','LightRAG_evidence_3_remaining_calls.zip']
payload={};sizes={}
with ZipFile(ORIGINAL) as z:
    assert z.testzip() is None
    for i in z.infolist():
        assert not i.is_dir()
        assert not PurePosixPath(i.filename).is_absolute() and '..' not in PurePosixPath(i.filename).parts
        payload[i.filename]=z.read(i.filename);sizes[i.filename]=i.compress_size
original_names=set(payload)
for fn in ['endpoint_metric_audit.json','endpoint_metric_audit.txt']:
    p=D/fn
    assert p.exists(), 'Endpoint audit is not ready'
    payload['delivery_notes/'+fn]=p.read_bytes()
payload['delivery_notes/build_split_delivery.py']=Path(__file__).read_bytes()
scanned=0
def scan(b,depth=0):
    global scanned
    scanned+=1
    assert not any(k in b for k in keys), 'Credential exclusion failed'
    if b[:4]==b'PK\x03\x04' and depth<4:
        with ZipFile(BytesIO(b)) as nested:
            for item in nested.infolist():
                if not item.is_dir(): scan(nested.read(item.filename),depth+1)
for p,b in payload.items():
    assert PurePosixPath(p).name!='.env' and '/secrets/' not in p
    scan(b)
assignment={};groups=defaultdict(list)
for p in payload:
    if p.startswith('round4_full_20261030/storage/'):
        assignment[p]=1
    elif p.startswith('round4_full_20261030/logs/api_'):
        groups[re.search(r'api_(\d+)_',p).group(1)].append(p)
    else: assignment[p]=0
base=sum(sizes.get(p,3000) for p,v in assignment.items() if v==0)
api_total=sum(sizes[p] for g in groups.values() for p in g)
target=(base+api_total)/2
current=base
for gid,ps in sorted(groups.items()):
    group_size=sum(sizes[p] for p in ps)
    part=0 if current+group_size/2<target else 2
    if part==0: current+=group_size
    for p in ps: assignment[p]=part
rows=[{'path':p,'bytes':len(b),'sha256':sha(b),'part':assignment[p]+1,'archive':names[assignment[p]],'original_payload':p in original_names} for p,b in sorted(payload.items())]
manifest={'schema':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_archive':ORIGINAL.name,'original_sha256':EXPECTED,'original_bytes':ORIGINAL.stat().st_size,'original_entries':len(original_names),'added_delivery_only_files':len(payload)-len(original_names),'archives':names,'files':rows,'credential_value_matches':0,'credential_scan_objects_including_nested_zip_entries':scanned}
manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
readme='''LightRAG evidence delivery: three independent ZIP files

No experiments or model API calls were performed for this delivery operation.
The original complete ZIP is unchanged. All 1,321 entries from it are assigned
exactly once across these three independently extractable ZIP files. Each is
strictly below 10,000,000 bytes. Additional delivery-only notes clearly audit
the limits of the exact-endpoint metric and do not change the original report.

Part 1: original report, scripts, configuration/evaluation/source evidence,
prior minimal-control archive, and an early consecutive range of API calls.
Part 2: all 18 persistent graph/index workspaces.
Part 3: the remaining API calls. Each call's request and responses stay together.
See SPLIT_MANIFEST.json for exact membership, byte sizes and file SHA256 values.

RECONSTRUCTION
1. Download all three ZIPs and place them in one directory.
2. Verify their SHA256 values against the accompanying SHA256SUMS.txt.
3. Extract each ZIP into the same NEW empty directory, retaining paths.
   SPLIT_README.txt and SPLIT_MANIFEST.json are identical in all three archives;
   overwriting these two identical control files is safe. The original 1,321
   entries are disjoint across parts. Do not extract over earlier experiments.
4. Open round4_full_20261030/report/LightRAG_patent_provenance_report_zh.html.
5. Read delivery_notes/endpoint_metric_audit.txt before interpreting edge scores.
6. Run python3 verify_split_contents.py from the reconstructed directory.
   It checks every payload's byte length and SHA256 against SPLIT_MANIFEST.json.

This restores byte-identical evidence FILES, not a byte-identical ZIP container.
The original complete ZIP SHA256 is recorded in SPLIT_MANIFEST.json.
This is not a .z01 multipart archive; every ZIP can be inspected independently.
No credentials or model/virtual-environment binaries were added. Existing old
deadlines and budgets in scripts remain; do not run paid scripts without fresh
authorization. Packaging and post-hoc graph audit are not new experimental data.
'''
verify='''from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
m=json.loads((r/'SPLIT_MANIFEST.json').read_text())
bad=[]
for x in m['files']:
 p=r/x['path']
 if not p.is_file(): bad.append((x['path'],'missing')); continue
 b=p.read_bytes()
 if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:bad.append((x['path'],'mismatch'))
if bad:print(json.dumps({'passed':False,'errors':bad},indent=2));raise SystemExit(1)
print(json.dumps({'passed':True,'verified_payload_files':len(m['files']),'original_entries_restored':m['original_entries']}))
'''
(D/'SPLIT_MANIFEST.json').write_bytes(manifest_bytes)
(D/'SPLIT_README.txt').write_text(readme)
statuses=[]
for part,name in enumerate(names):
    out=D/name
    with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for row in rows:
            if row['part']==part+1:z.writestr(row['path'],payload[row['path']])
        z.writestr('SPLIT_README.txt',readme)
        z.writestr('SPLIT_MANIFEST.json',manifest_bytes)
        z.writestr('verify_split_contents.py',verify)
    assert out.stat().st_size<10_000_000, 'Archive exceeds strict 10 MB cap'
    with ZipFile(out) as z:
        assert z.testzip() is None
        for row in rows:
            if row['part']==part+1: assert sha(z.read(row['path']))==row['sha256']
    statuses.append({'part':part+1,'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'payload_entries':sum(x['part']==part+1 for x in rows),'crc_passed':True,'sha256_passed':True})
assert sha(ORIGINAL.read_bytes())==EXPECTED
(D/'SHA256SUMS.txt').write_text(''.join(x['sha256']+'  '+Path(x['path']).name+'\n' for x in statuses))
status={'archives':statuses,'original_unchanged':True,'original_sha256':EXPECTED,'original_entries_reconstructed':len(original_names),'total_payload_entries':len(rows),'credential_matches':0,'new_model_api_calls':0}
(D/'split_delivery_validation.json').write_text(json.dumps(status,indent=2)+'\n')
print(json.dumps(status,indent=2))
