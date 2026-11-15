"""Supplemental same-question query-budget sensitivity; baseline files stay intact."""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    from repro_runtime import get_runtime
    get_runtime(create=False)

import asyncio,json,signal,hashlib
from safe_api import ROOT,ROUND,SafeAPI,now,write_json
from lightrag import LightRAG,QueryParam
from lightrag.utils import EmbeddingFunc,TiktokenTokenizer
from run_experiment import EVIDENCE_PROMPT

async def main():
 api=SafeAPI('supplement_default_sized_budgets');rag=None
 qs=json.loads((ROOT/'results/questions.json').read_text())['questions']
 questions=[next(q for q in qs if q['id']=='Q06'),json.loads((ROUND/'evidence/optional_question11.json').read_text())]
 paths=[ROUND/'storage_full/patent_r2_full'/x for x in ['vdb_chunks.json','kv_store_text_chunks.json','graph_chunk_entity_relation.graphml']]
 before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 settings={'supplement_only':True,'same_questions_and_models':True,'top_k':40,'chunk_top_k':20,
  'max_entity_tokens':6000,'max_relation_tokens':8000,'max_total_tokens':30000,'enable_rerank':False,
  'note':'Retrieval budgets match source defaults; rerank remains disabled, same custom models and base index. Not a rerun of the main20 answers.'}
 write_json(ROUND/'evidence/budget_sensitivity_settings.json',settings)
 try:
  async def llm(*args,**kwargs):return await api.complete(*args,**kwargs)
  async def embed(*args,**kwargs):return await api.embed(*args,**kwargs)
  rag=LightRAG(working_dir=str(ROUND/'storage_full'),workspace='patent_r2_full',llm_model_func=llm,
    llm_model_name=api.llm_model,embedding_func=EmbeddingFunc(embedding_dim=1024,max_token_size=8192,model_name=api.embedding_model,func=embed),
    tokenizer=TiktokenTokenizer('gpt-4o-mini'),chunk_token_size=1200,chunk_overlap_token_size=100,
    llm_model_max_async=2,embedding_func_max_async=2,embedding_batch_num=8,entity_extract_max_gleaning=0,
    default_llm_timeout=85,default_embedding_timeout=85)
  await rag.initialize_storages()
  for q in questions:
   for mode in ['naive','mix']:
    api.stage=f"supplement_budget_{q['id']}_{mode}";start=now();before_call=len(api.ledger['calls'])
    p=QueryParam(mode=mode,stream=False,include_references=True,enable_rerank=False,
       top_k=40,chunk_top_k=20,max_entity_tokens=6000,max_relation_tokens=8000,max_total_tokens=30000,user_prompt=EVIDENCE_PROMPT)
    result=await asyncio.wait_for(rag.aquery_llm(q['question'],param=p),timeout=240)
    row={'question_id':q['id'],'mode':mode,'question':q['question'],'started_utc':start.isoformat(),
      'finished_utc':now().isoformat(),'api_call_id_range':[before_call+1,len(api.ledger['calls'])],
      'settings':settings,'result':result}
    write_json(ROUND/'results'/f"supplement_budget_{q['id']}_{mode}.json",row)
    print(json.dumps({'q':q['id'],'mode':mode,'status':result.get('status'),'chunks':len(result.get('data',{}).get('chunks',[])),
      'target_references':[x for x in result.get('data',{}).get('references',[]) if 'US799' in x.get('file_path','')]}),flush=True)
 finally:
  if rag:await rag.finalize_storages()
  await api.close()
  after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
  write_json(ROUND/'evidence/budget_sensitivity_index_integrity.json',{'before':before,'after':after,'unchanged':before==after,'finished_utc':now().isoformat()})

if __name__=='__main__':
 signal.alarm(1000)
 asyncio.run(main())
