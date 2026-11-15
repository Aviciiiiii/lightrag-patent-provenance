"""Package allowlisted read-only evidence; no credentials and no network."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from io import BytesIO
import datetime, hashlib, json, re, tarfile, zipfile
O=legacy_root('round2_multisource_audit')/'round2_multisource_audit';ROOT=legacy_root('round2_multisource_audit');R=ROOT/'round2';S=R/'storage_full/patent_r2_full'
sha=lambda b:hashlib.sha256(b).hexdigest()
files=[]
for folder in ['scripts','evidence','dossiers','reviews','report']:
 files.extend(p for p in (O/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.tmp'])
for n in ['source_mapping_audit.py','source_mapping_audit.json','README_REPRODUCE.txt']:files.append(O/n)
main_hashes=json.loads((O/'evidence/original_input_hashes.json').read_text())
for rel,info in main_hashes.items():
 p=ROOT/rel;assert sha(p.read_bytes())==info['sha256'];files.append(p)
mapping=json.loads((O/'source_mapping_audit.json').read_text())
for name,info in mapping['input_hashes'].items():
 p=S/name;assert sha(p.read_bytes())==info['sha256'];files.append(p)
for name in ['official_core_v1.5.7.tar.gz','full_settings.json','extraction_truncation_probe.json','extraction_truncation_parser_replay.json','actual_chunk_source_mapping.json']:files.append(R/'evidence'/name)
for name in ['manifest.json','manifest.csv','source_verification.json','data_quality_flags.json']:files.append(ROOT/'data'/name)
docs=json.loads((O/'evidence/document_registry.json').read_text())
for pub in docs:
 files.append(ROOT/'data/claims'/f'{pub}.json');files.append(ROOT/'data/documents'/f'{pub}.txt')
payload={str(p.relative_to(ROOT)):p.read_bytes() for p in sorted(set(files))}
patterns=[re.compile(rb'sk-[A-Za-z0-9_-]{24,}'),re.compile(rb'AKIA[A-Z0-9]{16}'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'Authorization["\x27]?\s*:\s*["\x27]?Bearer\s+[A-Za-z0-9._-]{20,}')]
scan_objects=0;hits=[]
def scan(name,b):
 global scan_objects
 scan_objects+=1
 for i,p in enumerate(patterns):
  for m in p.finditer(b):
   token=m.group(0)
   # Public template placeholders consisting only of x's are not credentials.
   if token.startswith(b'sk-') and len(set(token[3:].lower()))==1 and token[3:4].lower()==b'x':continue
   hits.append({'file':name,'pattern_index':i,'matched_value_sha256':sha(token)})
 if name.endswith('.tar.gz'):
  with tarfile.open(fileobj=BytesIO(b),mode='r:gz') as t:
   for member in t.getmembers():
    if member.isfile():scan(name+'::'+member.name,t.extractfile(member).read())
for name,b in payload.items():
 assert Path(name).name!='.env' and '/secrets/' not in name
 scan(name,b)
assert not hits, 'Potential credential literals found; inspect only redacted hashes before delivery'
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'read-only round2 multi-publication audit','files':[{'path':name,'bytes':len(b),'sha256':sha(b)} for name,b in sorted(payload.items())],'credential_check':{'secret_config_read':False,'allowlisted_files_only':True,'common_credential_literal_pattern_matches':0,'scanned_objects_including_official_archive':scan_objects,'note':'Pattern scan,not a comparison against actual keys; secret configuration was not read.'}}
verify='''from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent;m=json.loads((r/'MANIFEST.json').read_text());bad=[]
for x in m['files']:
 p=r/x['path']
 if not p.is_file():bad.append([x['path'],'missing']);continue
 b=p.read_bytes()
 if len(b)!=x['bytes'] or hashlib.sha256(b).hexdigest()!=x['sha256']:bad.append([x['path'],'hash_or_size_mismatch'])
print(json.dumps({'verified_files':len(m['files']),'errors':bad},indent=2));raise SystemExit(bool(bad))
'''
out=O/'LightRAG_round2_multisource_audit_evidence_20261030.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,b in sorted(payload.items()):z.writestr(name,b)
 z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');z.writestr('verify_package_contents.py',verify)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for x in manifest['files']:assert sha(z.read(x['path']))==x['sha256']
assert out.stat().st_size<10_000_000
status={'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'payload_entries':len(payload),'crc_passed':True,'all_payload_hashes_verified':True,'original_source_hashes_unchanged':True,'credential_pattern_matches':0,'secret_configuration_read':False,'new_model_or_embedding_api_calls':0}
(O/'package_validation.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n');(O/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(O/'SHA256SUMS.txt').write_text(status['sha256']+'  '+out.name+'\n');print(json.dumps(status,indent=2))
