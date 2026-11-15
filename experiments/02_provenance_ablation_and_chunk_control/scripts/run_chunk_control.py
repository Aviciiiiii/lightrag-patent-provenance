"""Artificial boundary control with equal source text and two calls per condition."""

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    from repro_runtime import get_runtime
    get_runtime(create=True)

import asyncio, json, signal
from safe_api import ROOT, ROUND, SafeAPI, now, write_json, DEADLINE

async def main():
    prepared=json.loads((ROUND/'evidence/chunk_conditions.json').read_text())
    conditions=prepared['conditions']
    assert all(''.join(v['content'] for v in c['chunks'])==prepared['source_excerpt'] for c in conditions.values())
    assert all(len(c['chunks'])==2 for c in conditions.values())
    assert len({v['messages'][0]['content'] for c in conditions.values() for v in c['chunks']})==1
    order=[('SAME',1),('CROSS',1),('CROSS',2),('SAME',2),('SAME',3),('CROSS',3)]
    status={'started_utc':now().isoformat(),'status':'running','order':order,'calls':[],'max_tokens':8192,'repeats':3}
    write_json(ROUND/'results/chunk_run_status.json',status)
    api=SafeAPI('chunk_control')
    try:
        for condition,repeat in order:
            for chunk in conditions[condition]['chunks']:
                index=chunk['chunk_order_index'];api.stage=f'chunk_{condition}_r{repeat}_c{index}'
                cid=len(api.ledger['calls'])+1
                content=await api.complete(chunk['messages'][1]['content'],system_prompt=chunk['messages'][0]['content'],_experiment_max_tokens=8192)
                actual=json.loads((ROUND/'logs'/f'api_{cid:04d}_request.json').read_text())
                assert actual['messages']==chunk['messages']
                response=json.loads((ROUND/'logs'/f'api_{cid:04d}_response.json').read_text())
                row={'condition':condition,'repeat':repeat,'chunk_index':index,'chunk_id':chunk['chunk_id'],'file_path':chunk['file_path'],'call_id':cid,'request_messages_exact_match':True,'response':response,'completion_delimiter_present':'<|COMPLETE|>' in response['content'],'valid_nontruncated':response['finish_reason']=='stop'}
                write_json(ROUND/'results'/f'chunk_{condition}_r{repeat}_c{index}.json',row)
                status['calls'].append({k:v for k,v in row.items() if k!='response'})
                write_json(ROUND/'results/chunk_run_status.json',status)
                print(json.dumps({'condition':condition,'repeat':repeat,'chunk':index,'call_id':cid,'finish_reason':response['finish_reason'],'usage':response['usage']}),flush=True)
        status['status']='completed'
    finally:
        await api.close();status['finished_utc']=now().isoformat();write_json(ROUND/'results/chunk_run_status.json',status)

if __name__=='__main__':
    signal.alarm(max(1,min(2400,int((DEADLINE-now()).total_seconds()))))
    asyncio.run(main())
