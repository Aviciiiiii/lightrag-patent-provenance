"""Create a reproducibility capsule; scan for credential values without emitting them."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root, ENV_FILE  # path mapping only, see paths.py
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,zipfile,signal,os
from dotenv import dotenv_values

signal.alarm(180)
ROOT=legacy_root('round2');R=ROOT/'round2'
files=[]
for folder in ['round2/results','round2/evidence','round2/logs','round2/scripts','round2/report','round2/storage_smoke','round2/storage_full','data/documents','data/claims','data/source_checks']:
 for parent,dirs,names in os.walk(ROOT/folder,followlinks=False):
  dirs[:]=[x for x in dirs if x!='__pycache__']
  for name in names:
   p=Path(parent)/name
   if p.is_file() and not p.is_symlink():files.append(p)
for name in ['data/selected_patents.json','data/manifest.json','data/manifest.csv','data/source_verification.json','data/data_quality_flags.json',
             'data/dis2pat_train_rows_0000.source.json','data/dis2pat_splits.json',
             'results/questions.json','results/chunk_probe.json','results/question_chunk_mapping.json','results/natural_cross_chunk_candidates.json',
             'evidence/official_stable_audit.json','evidence/official_release_check.json','evidence/official_audit.json',
             'evidence/question_ground_truth.txt','evidence/question_validation.json','evidence/requirements_installed.json',
             'report/LightRAG_patent_provenance_report_zh.html']:
 files.append(ROOT/name)
files=sorted(set(files))
cfg=dotenv_values(str(ENV_FILE))
secret_values=[str(v).encode() for k,v in cfg.items() if v and ('API_KEY' in k.upper() or k.upper().endswith(('_TOKEN','_PASSWORD','_SECRET')))]
del cfg
out=R/'LightRAG_patent_round2_evidence_20261029.zip'
hashes={};byte_count=0
readme='''LightRAG patent provenance experiment, round 2 (2026-10-29)

Open round2/report/LightRAG_patent_provenance_report_zh.html in a browser.
The first-round report remains at report/LightRAG_patent_provenance_report_zh.html.

ACTUAL RUN: official v1.5.7, commit 28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c;
20 patents, 48 chunks, 612 nodes, 994 edges. Ten main questions in two modes,
plus two natural cross-chunk diagnostic answers and four separate budget probes.
Not a reproduction of the paper artifact. No causal cross-chunk loss established.

Data: 20 selected raw Dis2Pat records, independent input documents, Claims,
source-page verification, and manifests are included. The original 100-row fetch
remains in the local experiment folder; its source metadata and hash are included.

Storage: smoke and full index files, vectors, graphs, chunks, and extraction cache
are included. Baseline results are not overwritten by supplementary results.
LLM request messages, generated responses and usage are retained. Embedding logs
retain input text and returned metadata; indexed vectors are retained separately.
API 191 was truncated and not normally cached, so its raw response is essential.

Reproduction: exact official core source is round2/evidence/official_core_v1.5.7.tar.gz.
Extract it into src/LightRAG-v1.5.7; dependency versions are recorded in
evidence/requirements_installed.json. Installed package metadata says 1.5.8, but
actual runs directly imported pinned 1.5.7 source. No official core was edited.
round2/scripts/safe_api.py reads the user's configuration only at runtime.
No credentials are included. Absolute deadlines prevent unapproved future runs.
Any replay requires its own authorized time window, budget, and local API
configuration. Do not remove safeguards to blindlyrerun this artifact.

Wrappers: safe_api_full_runtime_snapshot.py records the full run's imported wrapper.
A later defensive patch affects only an unobserved reasoning/missing-usage case.
See guard_review.json for exact limits. No benchmark or method-superiority claim is made.

Integrity: artifact_checksums.json gives SHA256 for every packaged source file.
artifact_validation.json records a zero-hit check for actual credential values.
No secrets file, virtual environment, model weights, or transfer helpers are included.
'''
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 z.writestr('README.txt',readme)
 for i,p in enumerate(files):
  if ROOT not in p.resolve().parents:raise RuntimeError('file outside experiment root')
  data=p.read_bytes()
  if any(s in data for s in secret_values):raise RuntimeError('credential-value scan matched; package must not be delivered')
  name=str(p.relative_to(ROOT));hashes[name]=hashlib.sha256(data).hexdigest();byte_count+=len(data)
  z.writestr(name,data)
  if i%25==0:print(json.dumps({'packed_files':i+1,'total_files':len(files)}),flush=True)
 validation={'created_utc':datetime.now(timezone.utc).isoformat(),'files_checked':len(files),'credential_value_matches':0,
             'uncompressed_bytes':byte_count,'all_inputs_within_experiment_root':True}
 z.writestr('artifact_validation.json',json.dumps(validation,indent=2))
 z.writestr('artifact_checksums.json',json.dumps(hashes,sort_keys=True,indent=2))
del secret_values
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for name,want in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==want
status={'finished_utc':datetime.now(timezone.utc).isoformat(),'file':str(out),'bytes':out.stat().st_size,
        'entries':len(files)+3,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'crc_passed':True,'sha256_checks_passed':len(files),
        'credential_value_matches':0}
(R/'artifact_package_status.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2),flush=True)
