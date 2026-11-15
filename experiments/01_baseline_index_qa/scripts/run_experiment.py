"""Run the unmodified official LightRAG core with bounded real service callbacks."""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['smoke','full'])
    run_args = parser.parse_args()
    from repro_runtime import get_runtime
    get_runtime(create=True)

import asyncio, argparse, dataclasses, datetime as dt, json, os, signal, sys, time, traceback
from pathlib import Path
from safe_api import ROOT,ROUND,SafeAPI,DEADLINE,QUERY_DEADLINE,now,write_json,safe_error
from lightrag import LightRAG, QueryParam
from lightrag._version import __version__
from lightrag.utils import EmbeddingFunc,TiktokenTokenizer
import lightrag

EVIDENCE_PROMPT=('Use only retrieved evidence. State the patent publication number and the exact Claim number only when present in the evidence. '
 'Quote the supporting wording exactly, keeping each quotation short. Distinguish document facts from comparisons and inference. '
 'If evidence is insufficient, state what is missing. Do not invent links between patents. Answer in English in at most 350 words and preserve source references.')

async def snapshot(rag,tag,ids):
    nodes=await rag.chunk_entity_relation_graph.get_all_nodes()
    edges=await rag.chunk_entity_relation_graph.get_all_edges()
    counts=await rag.doc_status.get_all_status_counts()
    docs={i:await rag.doc_status.get_by_id(i) for i in ids}
    write_json(ROUND/'results'/f'{tag}_graph.json',{'nodes':nodes,'edges':edges,'captured_utc':now().isoformat()})
    write_json(ROUND/'results'/f'{tag}_doc_status.json',{'counts':counts,'documents':docs})
    return {'nodes':len(nodes),'edges':len(edges),'counts':counts,'documents':docs}

async def run(phase):
    started=now();api=SafeAPI(phase);rag=None
    original=json.loads((ROOT/'results/questions.json').read_text())['questions']
    selected=json.loads((ROOT/'data/selected_patents.json').read_text())
    ids=[x['publication_number'] for x in selected]
    if phase=='smoke':ids=['US9514753B2','US7991757B2']
    inputs=[(ROOT/'data/documents'/f'{i}.txt').read_text() for i in ids]
    storage=ROUND/f'storage_{phase}'
    settings={'official_version':__version__,'source_commit':'28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c',
              'imported_source':str(Path(lightrag.__file__).resolve()),'phase':phase,'ids':ids,
              'chunk_size':1200,'overlap':100,'tokenizer':'gpt-4o-mini/o200k_base',
              'llm_model':api.llm_model,'embedding_model':api.embedding_model,'embedding_dim':api.dim,
              'entity_extract_max_gleaning':0,'global_api_concurrency':2,'max_parallel_insert':2,
              'embedding_batch_num':8,'query_top_k':12,'query_chunk_top_k':8,'query_max_entity_tokens':2000,
              'query_max_relation_tokens':2000,'query_max_total_tokens':8000,'rerank':False,'user_prompt':EVIDENCE_PROMPT}
    write_json(ROUND/'evidence'/f'{phase}_settings.json',settings)
    status={'phase':phase,'started_utc':started.isoformat(),'status':'started'}
    try:
        assert __version__=='1.5.7'
        # Plain functions remain deepcopy-safe in the official dataclass config;
        # bound client methods would try to copy live HTTP client locks.
        async def llm_callback(*args,**kwargs):return await api.complete(*args,**kwargs)
        async def embedding_callback(*args,**kwargs):return await api.embed(*args,**kwargs)
        embedding=EmbeddingFunc(embedding_dim=api.dim,max_token_size=api.embedding_token_limit,model_name=api.embedding_model,func=embedding_callback)
        rag=LightRAG(working_dir=str(storage),workspace=f'patent_r2_{phase}',llm_model_func=llm_callback,
            llm_model_name=api.llm_model,embedding_func=embedding,tokenizer=TiktokenTokenizer('gpt-4o-mini'),
            chunk_token_size=1200,chunk_overlap_token_size=100,llm_model_max_async=2,
            embedding_func_max_async=2,embedding_batch_num=8,max_parallel_insert=2,
            default_llm_timeout=85,default_embedding_timeout=85,entity_extract_max_gleaning=0,
            addon_params={'language':'English'})
        await rag.initialize_storages()
        print(json.dumps({'phase':phase,'event':'index_start','docs':len(ids),'utc':now().isoformat()}),flush=True)
        timeout=min(1800,(QUERY_DEADLINE-now()).total_seconds()) if phase=='smoke' else min(2400,(DEADLINE-now()).total_seconds()-1200)
        if timeout<=0:raise TimeoutError('phase deadline has no remaining time')
        track=await asyncio.wait_for(rag.ainsert(inputs,ids=ids,file_paths=[f'{i}.txt' for i in ids]),timeout=timeout)
        snap=await snapshot(rag,phase,ids)
        status['index']={'track_id':track,'nodes':snap['nodes'],'edges':snap['edges'],'counts':snap['counts']}
        print(json.dumps({'phase':phase,'event':'index_finished',**status['index']},default=str),flush=True)
        if snap['counts'].get('processed',0)!=len(ids):
            raise RuntimeError('not all documents reached processed status; see saved document states')
        querylist=[original[0]] if phase=='smoke' else original
        if phase=='full':
            optional=json.loads((ROUND/'evidence/optional_question11.json').read_text())
            if isinstance(optional,dict) and 'question' in optional:querylist=querylist+[optional]
        results=[]
        for q in querylist:
            qid=q.get('id',q.get('question_id','Q11'))
            text=q['question']
            for mode in ['naive','mix']:
                if phase=='smoke' and now()>=QUERY_DEADLINE:raise TimeoutError('official query milestone elapsed')
                if now()>DEADLINE-dt.timedelta(minutes=15):
                    status['stopped_queries_for_review_budget']=True;break
                api.stage=f'{phase}_{qid}_{mode}'
                param=QueryParam(mode=mode,stream=False,include_references=True,enable_rerank=False,
                    top_k=12,chunk_top_k=8,max_entity_tokens=2000,max_relation_tokens=2000,
                    max_total_tokens=8000,user_prompt=EVIDENCE_PROMPT)
                before=len(api.ledger['calls']);qstart=now()
                print(json.dumps({'event':'query_start','phase':phase,'question':qid,'mode':mode}),flush=True)
                try:
                    query_deadline=QUERY_DEADLINE if phase=='smoke' else DEADLINE
                    result=await asyncio.wait_for(rag.aquery_llm(text,param=param),timeout=min(240,(query_deadline-now()).total_seconds()))
                    entry={'question_id':qid,'mode':mode,'question':text,'started_utc':qstart.isoformat(),
                           'finished_utc':now().isoformat(),'api_call_id_range':[before+1,len(api.ledger['calls'])],
                           'result':result}
                except Exception as e:
                    entry={'question_id':qid,'mode':mode,'question':text,'started_utc':qstart.isoformat(),
                           'finished_utc':now().isoformat(),'error':safe_error(e),'result':None}
                write_json(ROUND/'results'/f'{phase}_{qid}_{mode}.json',entry);results.append(entry)
                rr=entry.get('result') or {};data=rr.get('data') or {};llm=rr.get('llm_response') or {}
                ok=rr.get('status')=='success' and llm.get('llm_generated') is True and bool(data.get('chunks')) and bool(llm.get('content'))
                print(json.dumps({'event':'query_finished','phase':phase,'question':qid,'mode':mode,
                    'status':rr.get('status'),'llm_generated':llm.get('llm_generated'),'chunks':len(data.get('chunks',[])),
                    'entities':len(data.get('entities',[])),'relationships':len(data.get('relationships',[])),'gate_success':ok}),flush=True)
                if phase=='smoke' and ok and now()<QUERY_DEADLINE:
                    write_json(ROUND/'results/official_query_gate.json',{'passed':True,'passed_utc':now().isoformat(),
                        'phase':'smoke','question_id':qid,'mode':mode,'processed_documents':len(ids),
                        'official_version':__version__,'generated_answer':True,'retrieved_chunks':len(data.get('chunks',[]))})
        status['queries_attempted']=len(results)
        status['status']='completed'
    except Exception as e:
        status.update(status='failed',error=safe_error(e))
        status['error_locations']=[{'file':f.filename,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(e.__traceback__)]
        print(json.dumps({'phase':phase,'event':'phase_failed','error':safe_error(e)}),flush=True)
    finally:
        if rag is not None:
            try:await asyncio.wait_for(rag.finalize_storages(),timeout=45)
            except Exception as e:status['finalize_error']=safe_error(e)
        await api.close()
        status['finished_utc']=now().isoformat()
        status['conservative_cost_cny']=api.ledger['estimated_observed_cost_cny']+api.ledger['reserved_unknown_cny']
        write_json(ROUND/'results'/f'{phase}_run_status.json',status)
        print(json.dumps(status,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    signal.alarm(max(1,int((DEADLINE-now()).total_seconds())))
    asyncio.run(run(run_args.phase))
