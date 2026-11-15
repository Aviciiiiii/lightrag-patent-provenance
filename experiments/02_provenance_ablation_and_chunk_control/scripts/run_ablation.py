"""Matched small-sample generation-only ablation; no retrieval/index mutation."""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    from repro_runtime import get_runtime
    get_runtime(create=True)

import asyncio, hashlib, json, signal
from pathlib import Path
from safe_api import ROOT, ROUND, SafeAPI, now, write_json, DEADLINE

def digest(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

async def main():
    order=[('A',1),('B',1),('C',1),('B',2),('C',2),('A',2),('C',3),('A',3),('B',3)]
    conditions={c:json.loads((ROUND/'conditions'/f'{c}_request.json').read_text()) for c in 'ABC'}
    original=json.loads((ROOT/'round2/logs/api_0392_request.json').read_text())
    fields=['model','messages','max_tokens','temperature','stream','extra_body']
    assert all(conditions['A'][k]==original[k] for k in fields)
    assert all(len(x['messages'])==2 and [m['role'] for m in x['messages']]==['system','user'] for x in conditions.values())
    assert len({x['messages'][1]['content'] for x in conditions.values()})==1
    status={'started_utc':now().isoformat(),'order':order,'calls':[],'status':'running','seed':None,'repeats_per_condition':3,'not_retrieval_or_index_rebuild':True}
    write_json(ROUND/'results/ablation_run_status.json',status)
    api=SafeAPI('ablation')
    try:
        for condition,repeat in order:
            request=conditions[condition]
            assert request['model']==api.llm_model
            api.stage=f'ablation_{condition}_r{repeat}'
            cid=len(api.ledger['calls'])+1
            content=await api.complete(request['messages'][1]['content'],system_prompt=request['messages'][0]['content'],_experiment_max_tokens=request['max_tokens'])
            actual=json.loads((ROUND/'logs'/f'api_{cid:04d}_request.json').read_text())
            assert all(actual[k]==request[k] for k in fields)
            response=json.loads((ROUND/'logs'/f'api_{cid:04d}_response.json').read_text())
            row={'condition':condition,'repeat':repeat,'call_id':cid,'request_exact_match':True,'messages_sha256':digest(request['messages']),'response':response}
            write_json(ROUND/'results'/f'ablation_{condition}_r{repeat}.json',row)
            status['calls'].append({k:v for k,v in row.items() if k!='response'})
            write_json(ROUND/'results/ablation_run_status.json',status)
            print(json.dumps({'condition':condition,'repeat':repeat,'call_id':cid,'finish_reason':response['finish_reason'],'usage':response['usage']}),flush=True)
        status['status']='completed'
    finally:
        await api.close();status['finished_utc']=now().isoformat();write_json(ROUND/'results/ablation_run_status.json',status)

if __name__=='__main__':
    signal.alarm(max(1,min(2100,int((DEADLINE-now()).total_seconds()))))
    asyncio.run(main())
