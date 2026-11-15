"""Fresh official indexes for every frozen group/condition/repetition."""
import asyncio,json,hashlib,sys,datetime as dt,traceback
from pathlib import Path
from safe_api import ROOT,ROUND,SafeAPI,now,write_json,DEADLINE,safe_error
from custom_chunker import make_precomputed_chunker
from lightrag import LightRAG,QueryParam
from lightrag._version import __version__
from lightrag.utils import EmbeddingFunc,TiktokenTokenizer,resolve_user_prompt
from lightrag.prompt import PROMPTS
from lightrag.operate import _process_extraction_result

EVIDENCE_PROMPT=('Use only retrieved evidence. State the patent publication number and the exact Claim number only when present in the evidence. '
 'Quote the supporting wording exactly, keeping each quotation short. Distinguish document facts from comparisons and inference. '
 'If evidence is insufficient, state what is missing. Do not invent links between patents. Answer in English in at most 350 words and preserve source references.')
SOFT_STOP=dt.datetime.fromisoformat('2026-10-30T03:53:08+00:00')
PARAMS={'mode':'mix','stream':False,'include_references':True,'enable_rerank':False,'top_k':12,'chunk_top_k':8,'max_entity_tokens':2000,'max_relation_tokens':2000,'max_total_tokens':8000,'user_prompt':EVIDENCE_PROMPT}

def clean_edge_map(edges):return [{'endpoints':list(k),'records':v} for k,v in edges.items()]
def ranges_for(condition):
 out=[]
 for c in condition['chunks']:
  out.append(c.get('global_token_span',c.get('token_span')) or [c['token_start'],c['token_end']])
 return out

def diagnostic_text(g):
 if g.get('diagnostic_text'):return g['diagnostic_text']
 claims=g.get('claims')
 if claims:
  if isinstance(claims,dict):items=list(claims.values())
  else:items=claims
  return '\n\n'.join(x if isinstance(x,str) else x.get('text',x.get('content','')) for x in items)
 anchors=g['evidenceanchors'];items=list(anchors.values()) if isinstance(anchors,dict) else anchors
 return '\n\n'.join(x.get('text',x.get('quote','')) for x in items)

async def capture_parsed(api,start_id,end_id,chunks,dest):
 records=[]
 for cid in range(start_id,end_id+1):
  p=ROUND/'logs'/f'api_{cid:04d}_request.json';resp=ROUND/'logs'/f'api_{cid:04d}_response.json'
  if not(p.exists() and resp.exists()):continue
  req=json.loads(p.read_text());messages=req.get('messages',[])
  if not messages or 'Knowledge Graph Specialist' not in messages[0].get('content',''):continue
  user=messages[-1]['content'];matches=[(k,v) for k,v in chunks.items() if v.get('content') and ('```\n'+v['content']+'\n```') in user]
  if len(matches)!=1:raise RuntimeError('Extraction request did not map unambiguously to persisted chunk')
  chunk_id,chunk=matches[0];response=json.loads(resp.read_text());text=response['content']
  if response['finish_reason']=='length':
   from lightrag.utils import TruncatedResponse
   text=TruncatedResponse(text)
  nodes,edges=await _process_extraction_result(text,chunk_id,0,chunk.get('file_path',''),tuple_delimiter='<|#|>',completion_delimiter='<|COMPLETE|>')
  records.append({'call_id':cid,'chunk_id':chunk_id,'file_path':chunk.get('file_path'),'finish_reason':response['finish_reason'],'completion_tokens':response['usage'].get('completion_tokens'),'completion_delimiter_present':'<|COMPLETE|>' in response['content'],'nodes':dict(nodes),'edges':clean_edge_map(edges)})
 write_json(dest,{'method':'normal official imported parser replay, timestamp0','records':records})
 return records

async def run_one(api,g,condition,repeat):
 rid=f"{g['id']}_{condition}_r{repeat}";base=ROUND/'results'/rid;base.mkdir(parents=True,exist_ok=False)
 storage=ROUND/'storage'/rid
 if storage.exists():raise RuntimeError('Fresh index directory already exists; refusing response-cache reuse')
 storage.mkdir();workspace='patent_r4_'+rid.lower();rag=None
 status={'run_id':rid,'group':g['id'],'condition':condition,'repeat':repeat,'scope':g['scope'],'started_utc':now().isoformat(),'status':'running','storage':str(storage),'workspace':workspace,'no_reused_extraction_or_answer_cache':True,'embedding_cache_reused':False,'publication_number':g['publication_number']}
 write_json(base/'status.json',status)
 try:
  async def llm(*a,**kw):return await api.complete(*a,**kw)
  async def embed(*a,**kw):return await api.embed(*a,**kw)
  cb=make_precomputed_chunker(g['content'],ranges_for(g['conditions'][condition]),audit_path=base/'actual_chunking.json')
  rag=LightRAG(working_dir=str(storage),workspace=workspace,llm_model_func=llm,llm_model_name=api.llm_model,
    embedding_func=EmbeddingFunc(embedding_dim=1024,max_token_size=8192,model_name=api.embedding_model,func=embed),
    tokenizer=TiktokenTokenizer('gpt-4o-mini'),chunking_func=cb,chunk_token_size=1200,chunk_overlap_token_size=100,
    llm_model_max_async=2,embedding_func_max_async=2,embedding_batch_num=8,max_parallel_insert=2,
    default_llm_timeout=85,default_embedding_timeout=85,entity_extract_max_gleaning=0,addon_params={'language':'English'})
  await rag.initialize_storages();api.stage=rid+'_index';first=len(api.ledger['calls'])+1
  await asyncio.wait_for(rag.ainsert(g['content'],ids=g['publication_number'],file_paths=g.get('file_path',g['publication_number']+'.txt')),timeout=min(600,(DEADLINE-now()).total_seconds()-900))
  end=len(api.ledger['calls']);status['index_call_id_range']=[first,end]
  counts=await rag.doc_status.get_all_status_counts();status['doc_counts']=counts
  doc=await rag.doc_status.get_by_id(g['publication_number']);write_json(base/'doc_status.json',doc)
  nodes=await rag.chunk_entity_relation_graph.get_all_nodes();edges=await rag.chunk_entity_relation_graph.get_all_edges()
  write_json(base/'merged_graph.json',{'nodes':nodes,'edges':edges});status['graph_counts']={'nodes':len(nodes),'edges':len(edges)}
  chunks_path=storage/workspace/'kv_store_text_chunks.json';chunks=json.loads(chunks_path.read_text())
  write_json(base/'chunks.json',chunks)
  parsed=await capture_parsed(api,first,end,chunks,base/'parsed_extraction.json')
  status['truncated_extraction_call_ids']=[x['call_id'] for x in parsed if x['finish_reason']=='length']
  status['boundary_causal_eligible']=not status['truncated_extraction_call_ids']
  if counts.get('processed',0)!=1:raise RuntimeError('Document did not process successfully')
  api.stage=rid+'_natural_mix';qfirst=len(api.ledger['calls'])+1
  result=await asyncio.wait_for(rag.aquery_llm(g['query'],param=QueryParam(**PARAMS)),timeout=240)
  write_json(base/'natural_query.json',{'query':g['query'],'mode':'mix','params':PARAMS,'call_id_range':[qfirst,len(api.ledger['calls'])],'result':result,'forced_evidence':False})
  status['natural_status']=result.get('status');status['natural_answer_generated']=(result.get('llm_response') or {}).get('llm_generated',False)
  evidence=diagnostic_text(g)
  if not evidence:raise RuntimeError('Frozen diagnostic evidence empty')
  context='Document Chunks (FORCED original evidence diagnostic; not naturally retrieved):\n\n```\n'+json.dumps({'reference_id':'1','file_path':g.get('file_path',g['publication_number']+'.txt'),'content':evidence},ensure_ascii=False)+'\n```\n\nReference Document List:\n\n```\n[1] '+g.get('file_path',g['publication_number']+'.txt')+'\n```'
  system=PROMPTS['rag_response'].format(response_type='Multiple Paragraphs',user_prompt=resolve_user_prompt(EVIDENCE_PROMPT,'',False).slot,context_data=context)
  api.stage=rid+'_forced_diagnostic';cid=len(api.ledger['calls'])+1
  answer=await api.complete(g['query'],system_prompt=system)
  write_json(base/'forced_diagnostic.json',{'query':g['query'],'call_id':cid,'forced_evidence':True,'not_natural_retrieval_score':True,'supplied_evidence':evidence,'reference_mapping':{'1':g.get('file_path',g['publication_number']+'.txt')},'content':answer,'prompt_constraints':EVIDENCE_PROMPT})
  status['status']='completed'
 except Exception as e:
  status['status']='failed';status['error']=safe_error(e);status['error_locations']=[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(e.__traceback__)]
 finally:
  if rag is not None:
   try:await asyncio.wait_for(rag.finalize_storages(),timeout=40)
   except Exception as e:status['finalize_error']=safe_error(e)
  status['finished_utc']=now().isoformat();status['cumulative_conservative_cost_cny']=api.ledger['estimated_observed_cost_cny']+api.ledger['reserved_unknown_cny'];write_json(base/'status.json',status)
  print(json.dumps(status,ensure_ascii=False),flush=True)
 return status

async def main():
 assert __version__=='1.5.7'
 groups=json.loads((ROUND/'conditions/frozen_groups.json').read_text())['groups']
 if len(sys.argv)>1:groups=[g for g in groups if g['id'] in sys.argv[1:]]
 api=SafeAPI('round4');overall={'started_utc':now().isoformat(),'official_version':__version__,'groups':[g['id'] for g in groups],'runs':[],'status':'running','settings':PARAMS,'same_original_model_and_embedding':True,'fresh_index_per_run':True,'natural_retrieval_scope':'one complete target document per full group; minimalgroup clippedclaims only; no20docbackgroundcorpus'}
 write_json(ROUND/'results'/('run_status_'+('-'.join(g['id'] for g in groups))+'.json'),overall)
 try:
  for g in groups:
   for c,n in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
    if now()>=SOFT_STOP:overall['status']='stopped_for_review_time';return
    status=await run_one(api,g,c,n);overall['runs'].append(status);write_json(ROUND/'results'/('run_status_'+('-'.join(g['id'] for g in groups))+'.json'),overall)
    if status['status']!='completed':overall['status']='stopped_on_failure';return
  overall['status']='completed'
 finally:
  await api.close();overall['finished_utc']=now().isoformat();write_json(ROUND/'results'/('run_status_'+('-'.join(g['id'] for g in groups))+'.json'),overall)

if __name__=='__main__':asyncio.run(main())
