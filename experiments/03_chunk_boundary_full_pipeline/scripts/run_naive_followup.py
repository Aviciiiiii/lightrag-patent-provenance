"""Query-only naive comparison on completed new full-group indexes; no insertion."""
import asyncio,json,sys,hashlib,datetime as dt,traceback,argparse
from pathlib import Path

# Followup must reuse the indexing session; it cannot start a new time window.
if __name__=='__main__':
 argparse.ArgumentParser(description=__doc__).parse_args()
 from repro_runtime import get_runtime
 get_runtime(create=False)

from safe_api import ROOT,ROUND,SafeAPI,write_json,now,safe_error,QUERY_DEADLINE
from run_pipeline import PARAMS,make_precomputed_chunker,ranges_for
from lightrag import LightRAG,QueryParam
from lightrag.utils import EmbeddingFunc,TiktokenTokenizer

def hashes(path):return {n:hashlib.sha256((path/n).read_bytes()).hexdigest() for n in ['graph_chunk_entity_relation.graphml','vdb_chunks.json','kv_store_text_chunks.json']}
def validate_completed_runs(groups):
 if len(groups)!=3 or {g['id'] for g in groups}!={'F01','F05','F04'}:
  raise RuntimeError('Naive followup requires all three frozen groups')
 for g in groups:
  for cond in ['A','B']:
   for repeat in [1,2,3]:
    rid=f"{g['id']}_{cond}_r{repeat}";base=ROUND/'results'/rid
    status_path=base/'status.json'
    if not status_path.is_file():raise RuntimeError(f'Missing completed run: {rid}')
    status=json.loads(status_path.read_text())
    if status.get('status')!='completed':raise RuntimeError(f'Run is not completed: {rid}')
    expected_storage=ROUND/'storage'/rid
    if Path(status['storage']).resolve()!=expected_storage.resolve():raise RuntimeError(f'Unexpected index path: {rid}')
    if status['workspace']!='patent_r4_'+rid.lower():raise RuntimeError(f'Unexpected workspace: {rid}')
    if (base/'natural_naive.json').exists():raise RuntimeError(f'Naive result already exists: {rid}')
    hashes(expected_storage/status['workspace'])

async def main():
 groups=json.loads((ROUND/'conditions/frozen_groups.json').read_text())['groups'];groups=[g for g in groups if g['id'] in ['F01','F05','F04']]
 validate_completed_runs(groups)
 api=SafeAPI('naive_followup');summary={'started_utc':now().isoformat(),'scope':'query-only naive followup of existing new full-group indexes; no extraction/insertion','runs':[]}
 try:
  for g in groups:
   for cond,r in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
    if now()>=QUERY_DEADLINE:summary['stopped_for_review']=True;return
    rid=f"{g['id']}_{cond}_r{r}";base=ROUND/'results'/rid;status=json.loads((base/'status.json').read_text());assert status['status']=='completed';dest=base/'natural_naive.json';assert not dest.exists();storage=Path(status['storage']);workspace=status['workspace'];before_hash=hashes(storage/workspace);rag=None;result=None;entry={'run_id':rid,'started_utc':now().isoformat(),'forced_evidence':False,'mode':'naive'}
    try:
     async def llm(*a,**k):return await api.complete(*a,**k)
     async def emb(*a,**k):return await api.embed(*a,**k)
     rag=LightRAG(working_dir=str(storage),workspace=workspace,llm_model_func=llm,llm_model_name=api.llm_model,embedding_func=EmbeddingFunc(embedding_dim=1024,max_token_size=8192,model_name=api.embedding_model,func=emb),tokenizer=TiktokenTokenizer('gpt-4o-mini'),chunk_token_size=1200,chunk_overlap_token_size=100,llm_model_max_async=2,embedding_func_max_async=2,embedding_batch_num=8,max_parallel_insert=2,default_llm_timeout=85,default_embedding_timeout=85,entity_extract_max_gleaning=0,addon_params={'language':'English'})
     await rag.initialize_storages();api.stage=rid+'_natural_naive';first=len(api.ledger['calls'])+1;params={**PARAMS,'mode':'naive'}
     result=await asyncio.wait_for(rag.aquery_llm(g['query'],param=QueryParam(**params)),timeout=160)
     calls=api.ledger['calls'][first-1:];assert any(c['kind']=='llm' and c['state']=='success' for c in calls),'Require actual new answer call, not cached response'
     entry.update(query=g['query'],params=params,result=result,call_id_range=[first,len(api.ledger['calls'])],actual_new_answer_call=True,status='completed')
    except Exception as e:entry.update(status='failed',error=safe_error(e),error_locations=[{'file':x.filename,'line':x.lineno,'function':x.name} for x in traceback.extract_tb(e.__traceback__)])
    finally:
     if rag:
      try:await asyncio.wait_for(rag.finalize_storages(),timeout=30)
      except Exception as e:entry['finalize_error']=safe_error(e)
     after_hash=hashes(storage/workspace);entry.update(ended_utc=now().isoformat(),core_index_hashes_before=before_hash,core_index_hashes_after=after_hash,core_index_unchanged=before_hash==after_hash);write_json(dest,entry)
     summary['runs'].append({'run_id':rid,'status':entry['status'],'core_index_unchanged':entry['core_index_unchanged']});write_json(ROUND/'results/naive_followup_status.json',summary);print(json.dumps(summary['runs'][-1]),flush=True)
    if entry['status']!='completed':return
  summary['status']='completed'
 finally:
  await api.close();summary['ended_utc']=now().isoformat();write_json(ROUND/'results/naive_followup_status.json',summary)
if __name__=='__main__':asyncio.run(main())
