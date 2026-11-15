"""Seal a small, credential-free package for the generation/extraction controls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root, ENV_FILE  # path mapping only, see paths.py
from pathlib import Path
import json,hashlib,zipfile,datetime,signal
ROOT=legacy_root('round3');R=ROOT/'round3';signal.alarm(180)
# Exact authorized API credential values only, used in memory for exclusion.
from dotenv import dotenv_values
secrets=[v.encode() for k,v in dotenv_values(str(ENV_FILE)).items() if k.endswith('_API_KEY') and v]
assert secrets,'No actual API credential values available for exclusion check'
selected=[]
for folder in ['scripts','evidence','conditions','results','logs','report']:
    selected += [p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
for rel in ['round2/logs/api_0392_request.json','round2/logs/api_0392_response.json','round2/results/supplement_budget_Q11_supplementary_mix.json','round2/storage_full/patent_r2_full/kv_store_text_chunks.json','round2/storage_full/patent_r2_full/kv_store_full_docs.json','round2/storage_full/patent_r2_full/graph_chunk_entity_relation.graphml','round2/logs/api_0191_request.json','round2/logs/api_0191_response.json','round2/evidence/extraction_truncation_parser_replay.json','round2/evidence/official_core_v1.5.7.tar.gz','evidence/requirements_installed.json','data/manifest.json','data/source_checks/source_verification.json']:
    p=ROOT/rel
    if p.is_file():selected.append(p)
for folder in ['data/documents','data/selected_raw']:
    selected += [p for p in (ROOT/folder).glob('*') if p.is_file()]
selected=sorted(set(selected));assert all(p.is_relative_to(ROOT) for p in selected)
readme='''LightRAG patent provenance controls — round3,2026-10-29\n\nReport: round3/report/LightRAG_patent_provenance_report_zh.html\nA/B/C requests, reversible field diffs and source verification: round3/conditions/\nActual21LLM calls: round3/logs/api_* (noAuthorization/credentials)\nOutput/evaluation: round3/results/, round3/evidence/\nChunk raw-source/token boundaries and official prompt: chunk_conditions.json\nOfficial parser source harness and its round2 cross-check are included.\nOriginal claims and exact official code archive are included; no database download or model weights.\n\nOffline reproduction: inspect prepared prompts and responses; run evaluation/parse scripts with the recorded existing dependencies and officialv1.5.7 source at src/LightRAG-v1.5.7. The source tar.gz contains the core necessary to restore that source path; full original repository can be checked out at the recorded commit. Paths are relative to this experiment root.\n\nNew paid replication is NOT automatic: API runner has an expired absolute deadline and expects an explicitly authorized config path outside the package. Use a fresh isolated round directory, fresh budget/deadline authorization and your own service credentials before intentionally dispatching requests. Do not overwrite these records. Sampling/hosted-model versions may vary; temperature0 is not guaranteed deterministic.\n\nAll results are small controlled observations, not corpus-wide error rates. C adds claim evidence as well as provenance; citation reference list is frozen by design. The boundary control uses2stateless calls/condition, a93-token excerpt and zerooverlap; no full-graph merge/downstreamquery is tested.\n'''
manifest=[];out=R/'LightRAG_patent_round3_controls_20261029.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in selected:
        b=p.read_bytes();rel=str(p.relative_to(ROOT))
        if any(s in b for s in secrets):raise RuntimeError('Credential exclusion check failed for '+rel)
        manifest.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});z.writestr(rel,b)
    z.writestr('README.txt',readme)
    z.writestr('PACKAGE_MANIFEST.json',json.dumps(manifest,indent=2))
    z.writestr('PACKAGE_VALIDATION.json',json.dumps({'actual_api_credential_value_matches':0,'file_count':len(manifest),'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for item in manifest:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
status={'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'file':str(out),'bytes':out.stat().st_size,'entries':len(manifest)+3,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'crc_passed':True,'sha256_checks_passed':len(manifest),'credential_value_matches':0}
(R/'artifact_package_status.json').write_text(json.dumps(status,indent=2)+'\n');print(json.dumps(status,indent=2))
