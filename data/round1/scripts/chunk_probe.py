"""Run only the official deterministic chunker; never represents a RAG query."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import datetime
import hashlib
import importlib.metadata
import json
import os
import sys
import signal
from pathlib import Path

ROOT = legacy_root()
signal.alarm(30)
sys.path.insert(0, str(ROOT / 'src/LightRAG-v1.5.7'))
os.environ['TIKTOKEN_CACHE_DIR'] = str(ROOT / 'tiktoken_cache')
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

from lightrag.chunker import chunking_by_token_size
from lightrag.utils import TiktokenTokenizer
from lightrag._version import __version__
import lightrag

print('initializing_official_tokenizer', flush=True)
tokenizer = TiktokenTokenizer('gpt-4o-mini')
print('official_tokenizer_ready', flush=True)
records = []
for path in sorted((ROOT / 'data/documents').glob('*.txt')):
    print('chunking', path.name, flush=True)
    text = path.read_text()
    chunks = chunking_by_token_size(
        tokenizer, text, chunk_token_size=1200,
        chunk_overlap_token_size=100, _emit_source_span=True,
    )
    for c in chunks:
        span = c.get('_source_span')
        if span:
            assert text[span['start']:span['end']] == c['content']
        c['diagnostic_chunk_id'] = hashlib.sha256(c['content'].encode()).hexdigest()
    records.append({'publication_number':path.stem,'file_path':path.name,
                    'document_sha256':hashlib.sha256(text.encode()).hexdigest(),
                    'input_tokens':len(tokenizer.encode(text)),'chunks':chunks})
result = {
    'execution_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status':'official_chunker_executed_no_embedding_no_extraction_no_retrieval_no_generation',
    'lightrag_version':__version__,
    'installed_distribution_version':importlib.metadata.version('lightrag-hku'),
    'imported_source_path':str(Path(lightrag.__file__).resolve()),
    'source_commit':'28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c',
    'chunk_function_module':chunking_by_token_size.__module__,
    'tokenizer':'tiktoken gpt-4o-mini / o200k_base; tokenizer identifier is not an executed LLM',
    'chunk_size':1200,'overlap':100,
    'diagnostic_emit_source_span':True,
    'natural_chunking':True,
    'total_documents':len(records),
    'total_input_tokens':sum(r['input_tokens'] for r in records),
    'total_chunks':sum(len(r['chunks']) for r in records),
    'model_api_calls':0,'api_cost_usd':0,
    'documents':records,
}
(ROOT/'results/chunk_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='documents'},ensure_ascii=False,indent=2))
