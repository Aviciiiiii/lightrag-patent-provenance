import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import signal, zipfile, json, hashlib
signal.alarm(45)
r=legacy_root()
names=[
 'report/LightRAG_patent_provenance_report_zh.html','report/research_interest.txt',
 'data/selected_patents.json','data/manifest.json','data/manifest.csv',
 'data/source_verification.json','data/data_quality_flags.json','data/dis2pat_train_rows_0000.source.json',
 'results/run_status.json','results/questions.json','results/chunk_probe.json',
 'results/question_chunk_mapping.json','results/natural_cross_chunk_candidates.json',
 'evidence/official_stable_audit.json','evidence/official_release_check.json',
 'evidence/environment_preflight.json','evidence/timing.json','evidence/question_ground_truth.txt',
 'evidence/question_validation.json','evidence/final_quality_check.json','evidence/requirements_installed.json',
 'scripts/chunk_probe.py','scripts/build_questions.py','scripts/map_question_chunks.py',
 'scripts/data_fetch.py','scripts/data_validate.py','scripts/data_sourcecheck.py','scripts/data_verify_sources.py',
]
names += [str(p.relative_to(r)) for p in sorted((r/'data/documents').glob('*.txt'))]
out=r/'LightRAG_patent_small_evidence_20261029.zip'
hashes={}
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    z.writestr('README.txt','Partial result: NO official index or LLM query completed. All10 questions not_run.\nOpen report/LightRAG_patent_provenance_report_zh.html.\nSelected raw patents, documents, actual48chunks and verified evidence included.\nFull100row APIresponse, source HTML pages and official code archive remain in the local task directory.\nNo keys, model weights or virtual environment included.\n')
    for i,name in enumerate(names):
        data=(r/name).read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
        z.writestr(name,data)
        print('packed',i+1,name,flush=True)
    z.writestr('artifact_checksums.json',json.dumps(hashes,indent=2))
print(json.dumps({'file':str(out),'bytes':out.stat().st_size,'entries':len(names)+2}),flush=True)
