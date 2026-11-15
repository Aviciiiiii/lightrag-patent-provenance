"""One-off: compute the three bge-m3 query vectors of experiment 01's original Q11 call. ONE paid-API call.

LightRAG v1.5.7 embeds [question, ", ".join(ll_keywords), ", ".join(hl_keywords)] in one batch for a
mix query (operate.py L5198-L5225). The texts are rebuilt from the committed question and the Q11
keywords in the original index's LLM cache, and checked against the original embedding log
(API 391) if it is available locally. The vectors are saved, with model, date and inputs, to
experiments/01_baseline_index_qa/evidence/q11_query_vectors_bge-m3.json so that
tools/demo_context_provenance.py can rerun the original retrieval with 0 API calls.

    LRP_ENV_FILE=<key file> python tools/compute_q11_query_vectors.py
The key value is read from the env file and never printed or written.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import httpx
import numpy as np
from dotenv import dotenv_values

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from paths import ENV_FILE, RUNS  # noqa: E402

EXP = REPO / 'experiments/01_baseline_index_qa'
CACHE = RUNS / '01_baseline_index_qa/original/storage_full/patent_r2_full/kv_store_llm_response_cache.json'
LOG391 = RUNS / '01_baseline_index_qa/original/logs/api_0391_embedding.json'
OUT = EXP / 'evidence/q11_query_vectors_bge-m3.json'


def q11_texts():
    question = json.loads((EXP / 'evidence/optional_question11.json').read_text())['question']
    for v in json.loads(CACHE.read_text()).values():
        if v.get('cache_type') == 'keywords' and question in str(v.get('original_prompt', '')):
            kw = json.loads(v['return'])
            return question, [question, ', '.join(kw['low_level_keywords']), ', '.join(kw['high_level_keywords'])]
    raise SystemExit('Q11 keywords not found in the original LLM cache')


def main():
    question, texts = q11_texts()
    logged = json.loads(LOG391.read_text())['texts'] if LOG391.exists() else None
    if logged is not None and logged != texts:
        raise SystemExit('rebuilt texts differ from the original embedding log API 391; not calling the API')
    cfg = dotenv_values(ENV_FILE)
    model = cfg['EMBEDDING_MODEL']
    if model != 'BAAI/bge-m3':
        raise SystemExit(f'expected BAAI/bge-m3, env file says {model}')
    r = httpx.post(cfg['EMBEDDING_BINDING_HOST'].rstrip('/') + '/embeddings',
                   headers={'Authorization': 'Bearer ' + cfg['EMBEDDING_BINDING_API_KEY']},
                   json={'model': model, 'input': texts, 'encoding_format': 'float'}, timeout=60)
    r.raise_for_status()
    body = r.json()
    rows = sorted(body['data'], key=lambda x: x['index'])
    vecs = np.asarray([x['embedding'] for x in rows], dtype=np.float32)
    assert vecs.shape == (3, 1024)
    OUT.write_text(json.dumps({
        'purpose': 'query vectors of experiment 01 original Q11 supplementary mix call (API 391), recomputed',
        'computed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'model_requested': model, 'model_returned': body.get('model'), 'provider_host': cfg['EMBEDDING_BINDING_HOST'],
        'usage': body.get('usage'), 'question': question,
        'texts': texts, 'purposes': ['query', 'll_keywords', 'hl_keywords'],
        'texts_equal_original_log_api_0391': logged == texts if logged is not None else 'log not available',
        'original_log_usage': json.loads(LOG391.read_text()).get('usage') if LOG391.exists() else None,
        'norms': [float(np.linalg.norm(v)) for v in vecs],
        'vectors': [[float(x) for x in v] for v in vecs],
        'note': 'Original vectors were not saved by the original run; these are a recomputation with the same model '
                'name on a later date. Equality with the original retrieval is checked by tools/demo_context_provenance.py.',
    }, ensure_ascii=False) + '\n')
    print(f'saved {OUT.relative_to(REPO)}: model_returned={body.get("model")}, usage={body.get("usage")}, '
          f'texts_equal_original_log={logged == texts if logged is not None else "n/a"}')


if __name__ == '__main__':
    main()
