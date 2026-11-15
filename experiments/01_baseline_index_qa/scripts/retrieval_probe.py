"""Supplement: rank existing chunk vectors; no reindexing or answer generation."""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    from repro_runtime import get_runtime
    get_runtime(create=False)

import asyncio,json,signal,hashlib
from safe_api import ROOT,ROUND,SafeAPI,now,write_json
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc,TiktokenTokenizer

async def main():
 api=SafeAPI('supplement_vector_rank');rag=None
 originals=json.loads((ROOT/'results/questions.json').read_text())['questions']
 q6=next(q for q in originals if q['id']=='Q06')
 q11=json.loads((ROUND/'evidence/optional_question11.json').read_text())
 paths=[ROUND/'storage_full/patent_r2_full'/x for x in ['vdb_chunks.json','kv_store_text_chunks.json','graph_chunk_entity_relation.graphml']]
 before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 previous=ROUND/'evidence/retrieval_rank_probe.json'
 result=json.loads(previous.read_text()) if previous.exists() else {'started_utc':now().isoformat(),'purpose':'diagnostic vector ranking only; baseline queries unchanged','rows':[],'index_hashes_before':before}
 try:
  async def llm(*args,**kwargs):return await api.complete(*args,**kwargs)
  async def embed(*args,**kwargs):return await api.embed(*args,**kwargs)
  rag=LightRAG(working_dir=str(ROUND/'storage_full'),workspace='patent_r2_full',llm_model_func=llm,
    llm_model_name=api.llm_model,embedding_func=EmbeddingFunc(embedding_dim=1024,max_token_size=8192,model_name=api.embedding_model,func=embed),
    tokenizer=TiktokenTokenizer('gpt-4o-mini'),chunk_token_size=1200,chunk_overlap_token_size=100,
    llm_model_max_async=2,embedding_func_max_async=2,embedding_batch_num=8,entity_extract_max_gleaning=0)
  await rag.initialize_storages()
  for q in [q6,q11]:
   if any(row['question_id']==q['id'] for row in result['rows']):continue
   ranked=await rag.chunks_vdb.query(q['question'],top_k=48)
   rows=[{'rank':i+1,**{k:v for k,v in x.items() if k!='content'}} for i,x in enumerate(ranked)]
   result['rows'].append({'question_id':q['id'],'question':q['question'],'requested_top_k':48,'threshold':0.2,'ranked':rows,
     'target_US7991757B2':[r for r in rows if 'US7991757B2' in str(r)]})
   print(json.dumps({'question':q['id'],'candidates':len(rows),'target':result['rows'][-1]['target_US7991757B2']},default=str),flush=True)
 finally:
  if rag:await rag.finalize_storages()
  await api.close()
  result['finished_utc']=now().isoformat()
  result['index_hashes_after']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
  result['baseline_index_unchanged']=result['index_hashes_after']==before
  write_json(ROUND/'evidence/retrieval_rank_probe.json',result)

if __name__=='__main__':
 signal.alarm(180)
 asyncio.run(main())
