"""Show, on the saved experiment-01 index, that provenance is in the store but not in the LLM context.

No LLM call and no embedding API call is made:
* the LLM function raises if LightRAG ever calls it;
* query vectors (default): the three bge-m3 vectors of the original Q11 call, recomputed once and
  saved in experiments/01_baseline_index_qa/evidence/q11_query_vectors_bge-m3.json
  (tools/compute_q11_query_vectors.py). The embedding function only looks texts up in that file
  and raises for any other text, so retrieval can be compared with the original Q11 retrieval;
* --proxy-vector [ENTITY]: older stand-in mode, every text gets the stored vector of ENTITY
  (default "Registration Module"); retrieval is then that entity's neighbourhood, not Q11's;
* keywords are the ones LightRAG extracted for Q11 in the original run (read from the index's own
  LLM cache); parameters (budgets, user_prompt) are the original Q11 call's.
* --replay-answer: additionally run the original aquery_llm call; it can only answer from the
  index's LLM cache (keyword + query cache), because the LLM function raises.

The saved index is copied to runs/demo_context/ first; the original is never opened for writing.

    python tools/demo_context_provenance.py                      # cached original query vectors
    python tools/demo_context_provenance.py --proxy-vector       # stand-in vector (older demo)
    python tools/demo_context_provenance.py --replay-answer --md out.md [--lang zh]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LANG = 'en'
sys.path.insert(0, str(REPO))
from paths import RUNS, original_index_dir  # noqa: E402

os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(RUNS / 'tiktoken_cache'))

import numpy as np  # noqa: E402
from lightrag import LightRAG, QueryParam  # noqa: E402
from lightrag._version import __version__  # noqa: E402
from lightrag.utils import EmbeddingFunc, TiktokenTokenizer, compute_mdhash_id  # noqa: E402

EXP = REPO / 'experiments' / '01_baseline_index_qa'
SRC_STORE = original_index_dir()  # committed experiments/01_baseline_index_qa/index/, else runs/
WORKSPACE = 'patent_r2_full'
# Same budgets as the original Q11 supplementary run (evidence/budget_sensitivity_settings.json).
PARAMS = dict(mode='mix', top_k=40, chunk_top_k=20, max_entity_tokens=6000, max_relation_tokens=8000,
              max_total_tokens=30000, enable_rerank=False, include_references=True, stream=False,
              user_prompt=json.loads((EXP / 'evidence' / 'full_settings.json').read_text())['user_prompt'])
VECS = EXP / 'evidence' / 'q11_query_vectors_bge-m3.json'


class MissingVector(RuntimeError):
    pass


class LLMCalled(RuntimeError):
    pass


async def forbidden_llm(*args, **kwargs):
    raise LLMCalled('demo must not call the LLM')


def q11_keywords(cache_file: Path, question: str):
    cache = json.loads(cache_file.read_text())
    for value in cache.values():
        if value.get('cache_type') == 'keywords' and question in str(value.get('original_prompt', '')):
            kw = json.loads(value['return'])
            return kw['high_level_keywords'], kw['low_level_keywords']
    raise RuntimeError('Q11 keywords not found in the saved LLM cache')


def compare_with_original(d: dict) -> dict:
    """Overlap with the original Q11 retrieval (same index, same keywords, same budgets, real bge-m3 query vector)."""
    orig = json.loads((EXP / 'results' / 'supplement_budget_Q11_supplementary_mix.json').read_text())['result']['data']
    rel_key = lambda r: frozenset((r['src_id'], r['tgt_id']))  # noqa: E731
    sets = {
        'entities': ({e['entity_name'] for e in d['entities']}, {e['entity_name'] for e in orig['entities']}),
        'relations': ({rel_key(r) for r in d['relationships']}, {rel_key(r) for r in orig['relationships']}),
        'chunks': ({c['chunk_id'] for c in d.get('chunks', [])}, {c['chunk_id'] for c in orig['chunks']}),
    }
    out = {k: {'demo': len(a), 'original_q11': len(b), 'overlap': len(a & b)} for k, (a, b) in sets.items()}
    out['source'] = 'experiments/01_baseline_index_qa/results/supplement_budget_Q11_supplementary_mix.json'
    return out


def _kg_block(text: str) -> str:
    """From 'Knowledge Graph Data (Entity)' to the end of the Reference Document List code block."""
    i = text.find('Knowledge Graph Data (Entity)')
    j = text.find('Reference Document List', i)
    if i < 0 or j < 0:
        return ''
    k = text.find('```', text.find('```', j) + 3)
    return text[i:k + 3].strip()


def compare_context(ctx_text: str) -> dict:
    """Is the context string identical to the context inside the original prompt (API 392)?"""
    req = EXP / 'results' / 'key_logs' / 'api_0392_request.json'
    orig = _kg_block(json.loads(req.read_text())['messages'][0]['content'])
    mine = _kg_block(ctx_text)
    same = bool(orig) and orig == mine
    out = {'identical': same, 'original_chars': len(orig), 'demo_chars': len(mine)}
    if not same and orig and mine:
        n = next((i for i, (a, b) in enumerate(zip(orig, mine)) if a != b), min(len(orig), len(mine)))
        out['first_difference_at_char'] = n
        ol, ml = orig.splitlines(), mine.splitlines()
        out['same_lines_as_set'] = sorted(ol) == sorted(ml)
        out['lines'] = len(ol)
        out['lines_in_different_position'] = sum(a != b for a, b in zip(ol, ml))
    return out


async def replay_answer(rag, question: str) -> dict:
    """Run the original Q11 call; the LLM function raises, so only a cache hit can produce an answer."""
    param = QueryParam(**{k: v for k, v in PARAMS.items()})
    orig = json.loads((EXP / 'results' / 'key_logs' / 'api_0392_response.json').read_text())['content']
    try:
        res = await rag.aquery_llm(question, param=param)
    except LLMCalled:
        return {'answer_from_cache': False, 'reason': 'LightRAG tried to call the LLM (cache miss)'}
    except Exception as e:  # noqa: BLE001
        if 'LLMCalled' in repr(e) or 'must not call the LLM' in repr(e):
            return {'answer_from_cache': False, 'reason': 'LightRAG tried to call the LLM (cache miss)'}
        raise
    content = ((res or {}).get('llm_response') or {}).get('content') or ''
    return {'answer_from_cache': bool(content), 'identical_to_original_api_0392_answer': content == orig,
            'answer_chars': len(content), 'original_chars': len(orig), 'answer_start': content[:160]}


def graphml_node(graphml: Path, name: str) -> dict:
    import networkx as nx
    g = nx.read_graphml(graphml)
    return dict(g.nodes[name]) if name in g.nodes else {}


async def main(entity: str | None, md_out: Path | None, replay: bool):
    if not (SRC_STORE / WORKSPACE).is_dir():
        sys.exit(f'Saved index not found: {SRC_STORE / WORKSPACE}\n'
                 'Expected in experiments/01_baseline_index_qa/index/ (committed) or runs/01_baseline_index_qa/original/storage_full/.')
    work = RUNS / 'demo_context'
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(SRC_STORE / WORKSPACE, work / WORKSPACE)

    question = json.loads((EXP / 'evidence' / 'optional_question11.json').read_text())['question']
    hl, ll = q11_keywords(work / WORKSPACE / 'kv_store_llm_response_cache.json', question)
    vdb = json.loads((work / WORKSPACE / 'vdb_entities.json').read_text())
    dim = int(vdb['embedding_dim'])
    calls = {'embedding_function': 0, 'texts': []}
    anchor = {'vec': None}
    table = {}
    if entity is None:
        if not VECS.exists():
            sys.exit(f'{VECS.relative_to(REPO)} missing; run tools/compute_q11_query_vectors.py or use --proxy-vector')
        vj = json.loads(VECS.read_text())
        table = {t: np.asarray(v, dtype=np.float32) for t, v in zip(vj['texts'], vj['vectors'])}
        vector_source = f"cached bge-m3 vectors of the original Q11 texts ({VECS.relative_to(REPO)}, computed {vj['computed_utc'][:10]})"
    else:
        vector_source = f'stand-in: stored vector of entity "{entity}" for every text'

    async def embedding(texts, **kwargs):
        calls['embedding_function'] += 1
        calls['texts'] += list(texts)
        if entity is not None:
            return np.repeat(anchor['vec'][None, :], len(texts), axis=0)
        missing = [t for t in texts if t not in table]
        if missing:
            raise MissingVector(f'no cached vector for text: {missing[0][:80]!r}')
        return np.stack([table[t] for t in texts])

    rag = LightRAG(working_dir=str(work), workspace=WORKSPACE, llm_model_func=forbidden_llm,
                   llm_model_name='deepseek-ai/DeepSeek-V4.1-Flash',
                   embedding_func=EmbeddingFunc(embedding_dim=dim, max_token_size=8192, model_name='BAAI/bge-m3',
                                                func=embedding),
                   tokenizer=TiktokenTokenizer('gpt-4o-mini'), chunk_token_size=1200, chunk_overlap_token_size=100,
                   entity_extract_max_gleaning=0, addon_params={'language': 'English'})
    await rag.initialize_storages()
    replay_out = None
    try:
        if entity is not None:
            ent_id = compute_mdhash_id(entity, prefix='ent-')
            vecs = await rag.entities_vdb.get_vectors_by_ids([ent_id])
            if ent_id not in vecs:
                sys.exit(f'Entity not in index: {entity}')
            anchor['vec'] = np.asarray(vecs[ent_id], dtype=np.float32)
        data = await rag.aquery_data(question, param=QueryParam(hl_keywords=hl, ll_keywords=ll, **PARAMS))
        ctx = await rag.aquery(question, param=QueryParam(hl_keywords=hl, ll_keywords=ll, only_need_context=True, **PARAMS))
        if replay:
            replay_out = await replay_answer(rag, question)
    finally:
        await rag.finalize_storages()
    entity = entity or 'Registration Module'

    d = data['data']
    ents, rels = d['entities'], d['relationships']
    ctx_text = ctx if isinstance(ctx, str) else json.dumps(ctx)
    ctx_lines = [json.loads(l) for l in ctx_text.splitlines() if l.startswith('{"entity')]
    ctx_ents = [x for x in ctx_lines if 'entity' in x]
    ctx_rels = [x for x in ctx_lines if 'entity1' in x]
    refs = [r['file_path'] for r in d.get('references', [])]

    stored = graphml_node(work / WORKSPACE / 'graph_chunk_entity_relation.graphml', entity)
    s_rec = next((e for e in ents if e['entity_name'] == entity), None)
    c_rec = next((e for e in ctx_ents if e['entity'] == entity), None)
    same_doc_rels = [r for r in rels if entity in (r['src_id'], r['tgt_id'])]

    out = {
        'lightrag_version': __version__,
        'index': f'{SRC_STORE.relative_to(REPO) if SRC_STORE.is_relative_to(REPO) else SRC_STORE}/{WORKSPACE} (copied to runs/demo_context)',
        'question': question, 'keywords_from_saved_cache': {'high_level': hl, 'low_level': ll},
        'query_vectors': vector_source, 'params': {k: v for k, v in PARAMS.items() if k != 'user_prompt'},
        'api_calls': {'llm': 0, 'embedding_api': 0, 'local_embedding_function_calls': calls['embedding_function']},
        'embedded_texts': calls['texts'][:3],
        'graph_store_node': {k: stored.get(k) for k in ('entity_id', 'entity_type', 'file_path', 'source_id')},
        'aquery_data_entity': {k: s_rec.get(k) for k in ('entity_name', 'file_path', 'source_id')} if s_rec else None,
        'llm_context_entity_line': c_rec,
        'counts': {
            'aquery_data_entities': len(ents), 'aquery_data_entities_with_file_path': sum(1 for e in ents if e.get('file_path')),
            'aquery_data_relations': len(rels), 'aquery_data_relations_with_file_path': sum(1 for r in rels if r.get('file_path')),
            'context_entity_lines': len(ctx_ents), 'context_entity_lines_with_file_path': sum(1 for e in ctx_ents if 'file_path' in e),
            'context_relation_lines': len(ctx_rels), 'context_relation_lines_with_file_path': sum(1 for r in ctx_rels if 'file_path' in r),
            'context_chunks': len(d.get('chunks', [])),
        },
        'entity_file_path_in_reference_list': (s_rec or {}).get('file_path') in refs,
        'reference_list': refs,
        # entities whose (every) source document contributes no chunk to the context:
        # the model sees their description but no document of theirs in the Reference Document List
        'entities_whose_source_docs_are_absent_from_reference_list': sorted(
            e['entity_name'] for e in ents
            if e.get('file_path') and not set(e['file_path'].split('<SEP>')) & set(refs)),
        'relations_of_entity_in_aquery_data': [{k: r.get(k) for k in ('src_id', 'tgt_id', 'file_path', 'source_id')} for r in same_doc_rels][:5],
        'vs_original_q11': compare_with_original(d),
        'context_vs_original_prompt': compare_context(ctx_text),
        'replay_answer': replay_out,
    }
    text = json.dumps(out, ensure_ascii=False, indent=2)
    print(text)
    if md_out:
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(render_md(out, LANG), encoding='utf-8')


def render_md(o: dict, lang: str = 'en') -> str:
    def L(zh, en):
        return zh if lang == 'zh' else en
    c, v = o['counts'], o['vs_original_q11']
    cx, rp = o['context_vs_original_prompt'], o.get('replay_answer')
    proxy = o['query_vectors'].startswith('stand-in')
    same = v['entities']['overlap'] == v['entities']['demo'] == v['entities']['original_q11'] and \
        v['relations']['overlap'] == v['relations']['demo'] == v['relations']['original_q11'] and \
        v['chunks']['overlap'] == v['chunks']['demo'] == v['chunks']['original_q11']
    absent = o['entities_whose_source_docs_are_absent_from_reference_list']
    cmd = f"python tools/demo_context_provenance.py{' --proxy-vector' if proxy else ''}{' --replay-answer' if rp else ''}{' --lang zh' if lang == 'zh' else ''} --md <this file>"
    ent = o['aquery_data_entity'] or {}
    ent_name, ent_fp = ent.get('entity_name', ''), ent.get('file_path')
    absent_s = ', '.join(absent[:12]) + (' …' if len(absent) > 12 else '')
    if cx['identical']:
        ctx = L('**逐字相同**', '**identical**')
    elif cx.get('same_lines_as_set'):
        ctx = L(f"**内容相同、部分行顺序不同**：两边都是 {cx.get('lines')} 行，行的集合完全相同，其中 {cx.get('lines_in_different_position')} 行位置不同（原因无法从保存的数据中确定，见 docs/FAQ.md）",
                f"**same lines, partly different order**: both have {cx.get('lines')} lines and the same set of lines; {cx.get('lines_in_different_position')} lines are in a different position (the cause cannot be determined from the saved data; see [docs/FAQ.md](../../../../docs/FAQ.md))")
    else:
        ctx = L('内容不同', 'different content')
    row3 = json.dumps(o['llm_context_entity_line'], ensure_ascii=False)
    md = L(f"""# 现场复现：来源在库里，但不在送给模型的上下文里

由 `{cmd}` 生成；LightRAG {o['lightrag_version']}；**0 次 LLM 调用、0 次 Embedding API 调用**（本地 embedding 函数被调用 {o['api_calls']['local_embedding_function_calls']} 次，只查表或返回替身向量）。

- 查询向量：{o['query_vectors']}
- 关键词：原索引 LLM 缓存中 Q11 的关键词；预算与 user_prompt 与原始 Q11（扩展预算、mix）调用相同；索引是原始索引的副本。

## 同一个实体，三处对比

| 位置 | 内容 |
|---|---|
| 图存储（GraphML 节点） | `{json.dumps(o['graph_store_node'], ensure_ascii=False)}` |
| `aquery_data` 结构化返回 | `{json.dumps(o['aquery_data_entity'], ensure_ascii=False)}` |
| `only_need_context=True` 返回的、将送进 LLM 的那一行 | `{row3}` |

## 整体计数

| | 条数 | 其中带 `file_path` |
|---|---|---|
| `aquery_data` 实体 | {c['aquery_data_entities']} | {c['aquery_data_entities_with_file_path']} |
| `aquery_data` 关系 | {c['aquery_data_relations']} | {c['aquery_data_relations_with_file_path']} |
| LLM 上下文中的实体行 | {c['context_entity_lines']} | {c['context_entity_lines_with_file_path']} |
| LLM 上下文中的关系行 | {c['context_relation_lines']} | {c['context_relation_lines_with_file_path']} |

Reference Document List（只由 chunk 生成）：{', '.join(o['reference_list']) or '（空）'}

- “{ent_name}” 的来源文件 `{ent_fp}` {'在' if o['entity_file_path_in_reference_list'] else '**不在**'} Reference Document List 里。无论在不在，上下文里都没有字段把实体和 `[n]` 编号对应起来：实体行只有名称、类型、描述。
- 上下文里有 **{len(absent)}** 个实体，其来源文档一个 chunk 都没进上下文；模型能看到它们的描述，但在 Reference Document List 里找不到出处：{absent_s}

## 与原始 Q11 检索是否一致

| | 本次 | 原始 Q11 | 重合 |
|---|---|---|---|
""", f"""# Live reproduction: the source is in the store but not in the context sent to the model

Generated by `{cmd}`; LightRAG {o['lightrag_version']}; **0 LLM calls, 0 embedding API calls** (the local embedding function was called {o['api_calls']['local_embedding_function_calls']} times; it only looks vectors up or returns a stand-in).

- Query vectors: {o['query_vectors']}
- Keywords: Q11's keywords from the index's own LLM cache; budgets and user_prompt are those of the original Q11 call (extended budget, mix); the index is a copy of the original index.

## The same entity in three places

| place | content |
|---|---|
| graph store (GraphML node) | `{json.dumps(o['graph_store_node'], ensure_ascii=False)}` |
| `aquery_data` structured result | `{json.dumps(o['aquery_data_entity'], ensure_ascii=False)}` |
| the line that goes into the LLM context (`only_need_context=True`) | `{row3}` |

## Counts

| | records | with `file_path` |
|---|---|---|
| `aquery_data` entities | {c['aquery_data_entities']} | {c['aquery_data_entities_with_file_path']} |
| `aquery_data` relations | {c['aquery_data_relations']} | {c['aquery_data_relations_with_file_path']} |
| entity lines in the LLM context | {c['context_entity_lines']} | {c['context_entity_lines_with_file_path']} |
| relation lines in the LLM context | {c['context_relation_lines']} | {c['context_relation_lines_with_file_path']} |

Reference Document List (built from chunks only): {', '.join(o['reference_list']) or '(empty)'}

- The source file of “{ent_name}”, `{ent_fp}`, is {'' if o['entity_file_path_in_reference_list'] else '**not** '}in the Reference Document List. Either way, no field in the context links the entity to an `[n]` number: entity lines carry only name, type and description.
- **{len(absent)}** entities in the context come from documents none of whose chunks reached the context; the model sees their descriptions but cannot find a source for them in the Reference Document List: {absent_s}

## Same retrieval as the original Q11?

| | this run | original Q11 | overlap |
|---|---|---|---|
""")
    md += (f"| {L('实体', 'entities')} | {v['entities']['demo']} | {v['entities']['original_q11']} | {v['entities']['overlap']} |\n"
           f"| {L('关系（无向端点对）', 'relations (unordered endpoint pairs)')} | {v['relations']['demo']} | {v['relations']['original_q11']} | {v['relations']['overlap']} |\n"
           f"| chunk | {v['chunks']['demo']} | {v['chunks']['original_q11']} | {v['chunks']['overlap']} |\n\n")
    md += L(f"结论：**{'完全一致' if same else '不一致'}**。原始结果：`{v['source']}`。\n上下文字符串与原始请求（API 392）里的上下文：{ctx}（原始 {cx['original_chars']} 字符，本次 {cx['demo_chars']} 字符）。\n",
            f"Result: **{'identical' if same else 'different'}**. Original result: `{v['source']}`.\nContext string vs. the context in the original request (API 392): {ctx} (original {cx['original_chars']} characters, this run {cx['demo_chars']}).\n")
    if proxy:
        md += L("\n替身模式下三路检索搜的都是该实体的邻域，因此与原始 Q11 不一致是预期的；它证明的是机制，不是重现原始检索。\n",
                "\nIn stand-in mode all three searches look at that entity's neighbourhood, so a mismatch with the original Q11 is expected; this shows the mechanism, not the original retrieval.\n")
    if rp:
        reason = ('（' + rp['reason'] + '）') if 'reason' in rp else ''
        md += L(f"\n## LLM 缓存回放\n\n用原始 Q11 的完整参数调用 `aquery_llm`，LLM 函数是一调用就报错的桩：\n- 从缓存得到回答：**{rp['answer_from_cache']}**{reason}\n",
                f"\n## LLM cache replay\n\n`aquery_llm` was called with the full parameters of the original Q11; the LLM function is a stub that raises if called:\n- answer obtained from the cache: **{rp['answer_from_cache']}**{reason}\n")
        if rp.get('answer_from_cache'):
            md += L(f"- 与原始 API 392 的回答逐字相同：**{rp['identical_to_original_api_0392_answer']}**（{rp['answer_chars']} / {rp['original_chars']} 字符）\n",
                    f"- identical to the original API 392 answer: **{rp['identical_to_original_api_0392_answer']}** ({rp['answer_chars']} / {rp['original_chars']} characters)\n")
        md += L("""
缓存命中**能证明**：LightRAG 用与原始调用相同的问题、模式、预算、关键词和 user_prompt 查到了原来存下的回答（v1.5.7 查询缓存的键由这些组成，见 `operate.py` 中 `kg_query` 的 `compute_args_hash`），全程没有调用 LLM。
缓存命中**不能证明**：① 模型今天会给出同样的回答——回答只是原样取出，并非重新生成；② 检索到的上下文与原始相同——上下文不在缓存键里，是否相同要看上面单独的比较。
""", """
A cache hit **shows** that LightRAG looked up the stored answer with the same question, mode, budgets, keywords and user_prompt as the original call (in v1.5.7 these make up the query-cache key, see `compute_args_hash` in `kg_query`, `operate.py`), and that no LLM was called.
A cache hit **does not show** (1) that the model would give the same answer today (the answer is retrieved, not regenerated), or (2) that the retrieved context is the same as the original (the context is not part of the cache key; see the separate comparison above).
""")
    md += L(f"\n问题：{o['question']}\n", f"\nQuestion: {o['question']}\n")
    return md


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--proxy-vector', nargs='?', const='Registration Module', default=None, metavar='ENTITY',
                    help='stand-in mode: use the stored vector of ENTITY for every text')
    ap.add_argument('--replay-answer', action='store_true', help='also try to replay the original answer from the LLM cache')
    ap.add_argument('--md', type=Path)
    ap.add_argument('--lang', choices=['en', 'zh'], default='en', help='language of the --md output')
    a = ap.parse_args()
    LANG = a.lang
    asyncio.run(main(a.proxy_vector, a.md, a.replay_answer))
